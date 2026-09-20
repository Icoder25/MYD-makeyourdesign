"""Core models for DesignPulse state, versioning, constraint ledger, and diffs.

This module defines the structured representation of a design in progress:
- DesignState: the authoritative, multi-domain snapshot of a bathroom configuration.
- ConstraintLedger: the persistent, transparent health of the project across Space,
  Budget, Compatibility, Installation, Style, Water, and Verification.
- DecisionRecord: persistent memory of why a design choice was made.
- DesignStateDiff: exact arithmetic and fixture delta between versions (V1 -> V2).
- VersionHistory: the version tree for a project.

Zero AI invention: all numeric fields, statuses, and diffs are computed from
deterministic catalog, layout, and constraint facts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from backend.api.schemas import BathroomBrief, CandidatePlan
from backend.constraints.models import CheckResult, ConfigurationReport, Product
from backend.layout.models import DoorSpec, RoomLayout
from backend.sustainability.calculator import WaterImpactEstimate

LedgerStatus = Literal["pass", "warning", "fail"]


class ConstraintLedgerEntry(BaseModel):
    """Health verdict for one functional domain."""

    model_config = ConfigDict(extra="forbid")

    domain: str
    status: LedgerStatus
    summary: str
    blocking_count: int = 0
    warning_count: int = 0
    verification_count: int = 0
    checks: list[CheckResult] = Field(default_factory=list)


class ConstraintLedger(BaseModel):
    """Consolidated project health dashboard across all 7 design domains."""

    model_config = ConfigDict(extra="forbid")

    space: ConstraintLedgerEntry
    budget: ConstraintLedgerEntry
    compatibility: ConstraintLedgerEntry
    installation: ConstraintLedgerEntry
    style: ConstraintLedgerEntry
    water: ConstraintLedgerEntry
    verification: ConstraintLedgerEntry

    @property
    def is_feasible(self) -> bool:
        """True when no domain has a blocking failure."""
        return all(
            entry.status != "fail"
            for entry in [
                self.space,
                self.budget,
                self.compatibility,
                self.installation,
                self.style,
            ]
        )

    @property
    def has_pending_verifications(self) -> bool:
        """Is something still waiting on a measurement or a confirmation?

        Deliberately not "is any domain warning". A tight budget margin is a
        warning worth showing, but it is not a thing anybody can go and verify,
        and counting it here put "Pending Verification" on the header of a
        design whose every field assumption was already confirmed.
        """
        return any(
            entry.verification_count > 0 or entry.status == "warning"
            for entry in [
                self.space,
                self.compatibility,
                self.installation,
                self.verification,
            ]
        )

    @property
    def requires_verification(self) -> bool:
        """Alias for :attr:`has_pending_verifications`, named for the UI contract."""
        return self.has_pending_verifications

    @property
    def overall_status(self) -> str:
        """One verdict for the whole ledger.

        Kept deliberately three-valued. "Needs verification" is not the same
        answer as "infeasible": the first means a measurement is outstanding,
        the second means the geometry or budget provably does not work. Folding
        them together would tell a user their bathroom is impossible when all
        we actually need is a tape measure.
        """
        if not self.is_feasible:
            return "infeasible"
        if self.has_pending_verifications:
            return "feasible_pending_verification"
        return "feasible"

    @property
    def domains(self) -> dict[str, "ConstraintLedgerEntry"]:
        """The seven domain entries keyed by name.

        The ledger stores its domains as named fields so every one of them is
        guaranteed present and type-checked. Consumers that need to render or
        iterate all seven — the designer export sheet, the ledger dock — want a
        mapping, and building it here keeps the domain list in one place.
        """
        return {
            "space": self.space,
            "budget": self.budget,
            "compatibility": self.compatibility,
            "installation": self.installation,
            "style": self.style,
            "water": self.water,
            "verification": self.verification,
        }

    def as_dict(self) -> dict[str, LedgerStatus]:
        return {
            "space": self.space.status,
            "budget": self.budget.status,
            "compatibility": self.compatibility.status,
            "installation": self.installation.status,
            "style": self.style.status,
            "water": self.water.status,
            "verification": self.verification.status,
        }


def build_constraint_ledger(
    report: ConfigurationReport,
    water: WaterImpactEstimate,
    budget_limit: float | None,
    total_price: float,
) -> ConstraintLedger:
    """Aggregate individual CheckResults into domain-level ledger entries.

    Preserves the 3-state verdict:
    - Proven failure -> 'fail'
    - Outstanding verification / cautionary warning -> 'warning'
    - Verified compliant -> 'pass'
    """
    domain_map: dict[str, list[CheckResult]] = {
        "space": [],
        "budget": [],
        "compatibility": [],
        "installation": [],
        "style": [],
        "verification": [],
    }

    for check in report.checks:
        c_name = check.constraint
        if c_name in {"spatial_fit", "fixture_zone_fit", "layout_fit", "circulation"}:
            domain_map["space"].append(check)
        elif c_name == "budget":
            domain_map["budget"].append(check)
        elif c_name == "compatibility":
            domain_map["compatibility"].append(check)
        elif c_name in {"electrical", "installation"}:
            domain_map["installation"].append(check)
        elif c_name in {"user_constraints", "category_requirements"}:
            domain_map["style"].append(check)

        if not check.passed and not check.blocking:
            domain_map["verification"].append(check)

    def evaluate_entry(domain: str, checks: list[CheckResult], custom_summary: str | None = None) -> ConstraintLedgerEntry:
        fails = [c for c in checks if not c.passed and c.blocking]
        verifications = [c for c in checks if not c.passed and not c.blocking]
        warnings = [c for c in checks if c.status == "warning"]

        if fails:
            status: LedgerStatus = "fail"
            summary = fails[0].reason
        elif verifications or warnings:
            status = "warning"
            summary = verifications[0].reason if verifications else warnings[0].reason
        else:
            status = "pass"
            summary = custom_summary or f"All {domain} checks passed."

        return ConstraintLedgerEntry(
            domain=domain,
            status=status,
            summary=summary,
            blocking_count=len(fails),
            warning_count=len(warnings),
            verification_count=len(verifications),
            checks=checks,
        )

    # Space domain
    space_entry = evaluate_entry("space", domain_map["space"], "All fixtures hold legal clearances and room is navigable.")

    # Budget domain
    budget_checks = domain_map["budget"]
    if budget_limit is not None and total_price > budget_limit:
        budget_status: LedgerStatus = "fail"
        budget_summary = f"Configuration exceeds budget by {total_price - budget_limit:,.0f}."
    elif budget_limit is not None and (budget_limit - total_price) < 0.05 * budget_limit:
        budget_status = "warning"
        budget_summary = f"Within budget, but margin is very tight ({budget_limit - total_price:,.0f} remaining)."
    else:
        budget_status = "pass"
        remaining_str = f"{budget_limit - total_price:,.0f} remaining" if budget_limit else "No budget ceiling set"
        budget_summary = f"Configuration costs {total_price:,.0f} ({remaining_str})."

    budget_entry = ConstraintLedgerEntry(
        domain="budget",
        status=budget_status,
        summary=budget_summary,
        blocking_count=1 if budget_status == "fail" else 0,
        warning_count=1 if budget_status == "warning" else 0,
        verification_count=0,
        checks=budget_checks,
    )

    # Compatibility domain
    compat_entry = evaluate_entry("compatibility", domain_map["compatibility"], "All mounting interfaces and fixture drillings match.")

    # Installation domain
    install_entry = evaluate_entry("installation", domain_map["installation"], "Installation and rough-in specifications verified.")

    # Style domain
    style_entry = evaluate_entry("style", domain_map["style"], "All requested fixtures and style preferences satisfied.")

    # Water domain (from Sustainability calculator)
    if water.status == "calculated" and water.percent_saved is not None:
        if water.percent_saved > 0:
            water_status: LedgerStatus = "pass"
            water_summary = f"{water.percent_saved:.0f}% water reduction vs regulatory baseline ({water.annual_litres_saved:,.0f} L/yr saved)."
        else:
            water_status = "warning"
            water_summary = "Estimated water use meets baseline but achieves no additional savings."
    else:
        water_status = "warning"
        unquantified = ", ".join(water.unquantified_products) if water.unquantified_products else "fixtures"
        water_summary = f"Flow rate not documented for {unquantified}; verification recommended."

    water_entry = ConstraintLedgerEntry(
        domain="water",
        status=water_status,
        summary=water_summary,
        blocking_count=0,
        warning_count=1 if water_status == "warning" else 0,
        verification_count=0,
        checks=[],
    )

    # Global Verification domain
    all_verifs = report.verification_requirements
    if all_verifs:
        verif_status: LedgerStatus = "warning"
        verif_summary = f"{len(all_verifs)} item(s) require field confirmation before procurement."
    else:
        verif_status = "pass"
        verif_summary = "All technical and field assumptions fully confirmed."

    verif_entry = ConstraintLedgerEntry(
        domain="verification",
        status=verif_status,
        summary=verif_summary,
        blocking_count=0,
        warning_count=0,
        verification_count=len(all_verifs),
        checks=domain_map["verification"],
    )

    return ConstraintLedger(
        space=space_entry,
        budget=budget_entry,
        compatibility=compat_entry,
        installation=install_entry,
        style=style_entry,
        water=water_entry,
        verification=verif_entry,
    )


class DecisionRecord(BaseModel):
    """A formal record of why a design decision was made."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    category: str
    action: Literal["initial_selection", "designer_change", "tradeoff_accepted", "relaxation"]
    product_id: str | None = None
    product_name: str | None = None
    client_requirement_ref: str | None = None
    rationale: str


class DesignState(BaseModel):
    """The central state of the bathroom configuration in DesignPulse.

    Holds room geometry, fixture positions, products, constraints, budget,
    water performance, and historical decision memory for a given version.
    """

    model_config = ConfigDict(extra="forbid")

    project_id: str
    version_id: str
    version_number: int = 1
    parent_version_id: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Room parameters
    room_width_ft: float | None = None
    room_length_ft: float | None = None
    ceiling_height_ft: float | None = None
    door: DoorSpec | None = None
    electrical_available: bool | None = None
    toilet_rough_in_in: float | None = None

    # Selected product suite
    selected_products: list[Product]
    total_price: float
    budget_limit: float | None = None
    currency: str = "INR"
    remaining_budget: float | None = None

    # Solved outputs
    layout: RoomLayout
    constraint_report: ConfigurationReport
    water_impact: WaterImpactEstimate
    ledger: ConstraintLedger

    # Design intelligence memory
    decision_records: list[DecisionRecord] = Field(default_factory=list)
    vision_analysis: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_product(self, category: str) -> Product | None:
        return next((p for p in self.selected_products if p.category == category), None)

    def get_product_by_id(self, product_id: str) -> Product | None:
        return next((p for p in self.selected_products if p.id == product_id), None)


class DesignStateDiff(BaseModel):
    """Structured delta between two design versions (e.g. V1 -> V2)."""

    model_config = ConfigDict(extra="forbid")

    from_version: str
    to_version: str
    added_products: list[Product]
    removed_products: list[Product]
    modified_categories: list[str]
    price_delta: float
    remaining_budget_delta: float | None
    water_annual_litres_saved_delta: float | None
    ledger_changes: dict[str, tuple[LedgerStatus, LedgerStatus]]
    new_verification_items: list[str]
    resolved_verification_items: list[str]
    summary: str


def compute_design_state_diff(v1: DesignState, v2: DesignState) -> DesignStateDiff:
    """Compute the exact delta between version 1 and version 2."""
    v1_products = {p.id: p for p in v1.selected_products}
    v2_products = {p.id: p for p in v2.selected_products}

    added = [p for pid, p in v2_products.items() if pid not in v1_products]
    removed = [p for pid, p in v1_products.items() if pid not in v2_products]

    v1_cats = {p.category: p.id for p in v1.selected_products}
    v2_cats = {p.category: p.id for p in v2.selected_products}
    all_cats = set(v1_cats.keys()).union(v2_cats.keys())

    modified_cats = [
        cat for cat in sorted(all_cats)
        if v1_cats.get(cat) != v2_cats.get(cat)
    ]

    price_delta = v2.total_price - v1.total_price
    rem_delta = (
        (v2.remaining_budget - v1.remaining_budget)
        if v2.remaining_budget is not None and v1.remaining_budget is not None
        else None
    )

    v1_saved = v1.water_impact.annual_litres_saved or 0.0
    v2_saved = v2.water_impact.annual_litres_saved or 0.0
    water_delta = v2_saved - v1_saved

    v1_dict = v1.ledger.as_dict()
    v2_dict = v2.ledger.as_dict()
    ledger_changes = {
        domain: (v1_dict[domain], v2_dict[domain])
        for domain in v1_dict
        if v1_dict[domain] != v2_dict[domain]
    }

    v1_verifs = set(v1.constraint_report.verification_requirements)
    v2_verifs = set(v2.constraint_report.verification_requirements)
    new_verifs = sorted(v2_verifs - v1_verifs)
    resolved_verifs = sorted(v1_verifs - v2_verifs)

    # Build concise summary
    changes_desc: list[str] = []
    if modified_cats:
        changes_desc.append(f"modified categories: {', '.join(modified_cats)}")
    if price_delta > 0:
        changes_desc.append(f"cost increased by {price_delta:,.0f} {v2.currency}")
    elif price_delta < 0:
        changes_desc.append(f"cost reduced by {-price_delta:,.0f} {v2.currency}")
    else:
        changes_desc.append("cost unchanged")

    summary = f"Version {v1.version_id} -> {v2.version_id}: " + "; ".join(changes_desc) + "."

    return DesignStateDiff(
        from_version=v1.version_id,
        to_version=v2.version_id,
        added_products=added,
        removed_products=removed,
        modified_categories=modified_cats,
        price_delta=price_delta,
        remaining_budget_delta=rem_delta,
        water_annual_litres_saved_delta=water_delta,
        ledger_changes=ledger_changes,
        new_verification_items=new_verifs,
        resolved_verification_items=resolved_verifs,
        summary=summary,
    )


def create_design_state_from_candidate(
    candidate: CandidatePlan,
    brief: BathroomBrief,
    project_id: str,
    version_id: str = "v1",
    version_number: int = 1,
    parent_version_id: str | None = None,
    decisions: list[DecisionRecord] | None = None,
    vision_analysis: Any | None = None,
) -> DesignState:
    """Instantiate a DesignState from an evaluated CandidatePlan."""
    ledger = build_constraint_ledger(
        report=candidate.constraint_report,
        water=candidate.water_impact,
        budget_limit=brief.budget,
        total_price=candidate.total_price,
    )

    initial_decisions = decisions or [
        DecisionRecord(
            category=product.category,
            action="initial_selection",
            product_id=product.id,
            product_name=product.name,
            client_requirement_ref=None,
            rationale=f"Selected {product.name} during initial planning optimization.",
        )
        for product in candidate.products
    ]

    return DesignState(
        project_id=project_id,
        version_id=version_id,
        version_number=version_number,
        parent_version_id=parent_version_id,
        room_width_ft=brief.room_width_ft,
        room_length_ft=brief.room_length_ft,
        ceiling_height_ft=brief.ceiling_height_ft,
        door=brief.door,
        electrical_available=brief.electrical_available,
        toilet_rough_in_in=brief.toilet_rough_in_in,
        selected_products=candidate.products,
        total_price=candidate.total_price,
        budget_limit=brief.budget,
        currency=candidate.currency,
        remaining_budget=candidate.remaining_budget,
        layout=candidate.layout,
        constraint_report=candidate.constraint_report,
        water_impact=candidate.water_impact,
        ledger=ledger,
        decision_records=initial_decisions,
        vision_analysis=vision_analysis,
        metadata={"strengths": candidate.strengths, "trade_offs": candidate.trade_offs},
    )


class VersionHistory(BaseModel):
    """Manages the version timeline for a project in DesignPulse."""

    model_config = ConfigDict(extra="forbid")

    project_id: str
    versions: dict[str, DesignState] = Field(default_factory=dict)
    active_version_id: str | None = None

    def add_version(self, state: DesignState, set_active: bool = True) -> None:
        self.versions[state.version_id] = state
        if set_active or self.active_version_id is None:
            self.active_version_id = state.version_id

    def get_version(self, version_id: str) -> DesignState | None:
        return self.versions.get(version_id)

    def get_active(self) -> DesignState | None:
        if self.active_version_id:
            return self.versions.get(self.active_version_id)
        return None

    def diff(self, from_version_id: str, to_version_id: str) -> DesignStateDiff:
        v1 = self.versions.get(from_version_id)
        v2 = self.versions.get(to_version_id)
        if not v1 or not v2:
            raise KeyError(f"Both versions must exist to compute diff: {from_version_id}, {to_version_id}")
        return compute_design_state_diff(v1, v2)

    def next_version_id(self) -> str:
        return f"v{len(self.versions) + 1}"
