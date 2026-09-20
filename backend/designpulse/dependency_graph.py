"""Dependency Graph for bathroom fixtures and architectural constraints.

This module formalizes the relationships between fixtures, room geometry,
plumbing/electrical infrastructure, and budget.

It explicitly distinguishes:
- HARD_CONSTRAINT: Code clearances (IRC), spatial boundaries, direct interface mounts.
- MODEL_SPECIFIC_REQUIREMENT: Dual faucets for double vanity, GFCI outlet for smart bidet.
- DESIGN_HEURISTIC: Proportional mirror sizing (60-85% vanity width), aesthetic coordination.
- UNKNOWN_VERIFICATION: Unmeasured rough-in, hidden in-wall pipe positions.

The dependency graph drives deterministic impact analysis; it is never decorative.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from backend.constraints.models import Product


class DependencyClass(str, Enum):
    HARD_CONSTRAINT = "hard_constraint"
    MODEL_SPECIFIC_REQUIREMENT = "model_specific_requirement"
    DESIGN_HEURISTIC = "design_heuristic"
    UNKNOWN_VERIFICATION = "unknown_verification"


@dataclass(frozen=True)
class DependencyRule:
    """A directed dependency from source category to target domain or category."""

    source_category: str
    target: str  # e.g., "space", "budget", "basin", "faucet", "mirror", "installation"
    dependency_class: DependencyClass
    description: str
    impact_property: str  # e.g., "width_in", "provides_interfaces", "price"


# Canonical architectural dependencies
DEPENDENCY_RULES: list[DependencyRule] = [
    # Vanity dependencies
    DependencyRule(
        source_category="vanity",
        target="space",
        dependency_class=DependencyClass.HARD_CONSTRAINT,
        description="Vanity width directly consumes wall span and determines front clearance zone.",
        impact_property="dimensions.width_in",
    ),
    DependencyRule(
        source_category="vanity",
        target="budget",
        dependency_class=DependencyClass.HARD_CONSTRAINT,
        description="Vanity price changes impact total project budget.",
        impact_property="price",
    ),
    DependencyRule(
        source_category="vanity",
        target="basin",
        dependency_class=DependencyClass.HARD_CONSTRAINT,
        description="Vanity top interface must match basin mounting (e.g., vanity_top interface).",
        impact_property="provides_interfaces",
    ),
    DependencyRule(
        source_category="vanity",
        target="faucet",
        dependency_class=DependencyClass.MODEL_SPECIFIC_REQUIREMENT,
        description="Double-basin or expanded vanities typically require dual faucet installations.",
        impact_property="dimensions.width_in",
    ),
    DependencyRule(
        source_category="vanity",
        target="storage",  # Mirror / mirrored cabinets
        dependency_class=DependencyClass.DESIGN_HEURISTIC,
        description="Mirror width should proportionally match vanity width (typically 60%–85% of vanity width).",
        impact_property="dimensions.width_in",
    ),
    DependencyRule(
        source_category="vanity",
        target="installation",
        dependency_class=DependencyClass.UNKNOWN_VERIFICATION,
        description="Plumbing supply and drain rough-in line locations must be verified for wider vanities.",
        impact_property="dimensions.width_in",
    ),
    # Toilet dependencies
    DependencyRule(
        source_category="toilet",
        target="space",
        dependency_class=DependencyClass.HARD_CONSTRAINT,
        description="Toilet requires minimum 15 in centerline clearance to side walls/fixtures and 21 in front clearance.",
        impact_property="dimensions.width_in",
    ),
    DependencyRule(
        source_category="toilet",
        target="installation",
        dependency_class=DependencyClass.HARD_CONSTRAINT,
        description="Floor-mounted toilet requires 12 in waste rough-in match; wall-hung requires in-wall carrier.",
        impact_property="installation.rough_in_in",
    ),
    DependencyRule(
        source_category="smart_toilet",
        target="installation",
        dependency_class=DependencyClass.MODEL_SPECIFIC_REQUIREMENT,
        description="Smart bidet toilet requires dedicated electrical supply point adjacent to fixture.",
        impact_property="electrical_required",
    ),
    DependencyRule(
        source_category="toilet",
        target="water",
        dependency_class=DependencyClass.HARD_CONSTRAINT,
        description="Toilet flush volume directly determines domestic daily water consumption.",
        impact_property="water.flush_volume_gal",
    ),
    # Shower dependencies
    DependencyRule(
        source_category="shower",
        target="space",
        dependency_class=DependencyClass.HARD_CONSTRAINT,
        description="Shower requires minimum 30 in x 30 in interior dimension and 24 in entry clearance.",
        impact_property="dimensions.width_in",
    ),
    DependencyRule(
        source_category="smart_shower",
        target="installation",
        dependency_class=DependencyClass.MODEL_SPECIFIC_REQUIREMENT,
        description="Digital shower valve requires electrical supply and digital controller cable routing.",
        impact_property="electrical_required",
    ),
    DependencyRule(
        source_category="shower",
        target="water",
        dependency_class=DependencyClass.HARD_CONSTRAINT,
        description="Showerhead flow rate (GPM) determines annual water impact vs baseline.",
        impact_property="water.flow_rate_gpm",
    ),
]


class BathroomDependencyGraph:
    """Graph query engine for fixture dependencies."""

    def __init__(self, rules: list[DependencyRule] | None = None) -> None:
        self._rules = rules or list(DEPENDENCY_RULES)

    def get_dependencies_for_category(self, category: str) -> list[DependencyRule]:
        """Return all direct dependencies originating from a fixture category."""
        target_cats = {category}
        if category == "smart_toilet":
            target_cats.add("toilet")
        elif category == "smart_shower":
            target_cats.add("shower")
        return [rule for rule in self._rules if rule.source_category in target_cats]

    def partition_affected_categories(
        self,
        changed_category: str,
        all_present_categories: list[str],
        additional_affected: set[str] | None = None,
    ) -> tuple[list[str], list[str]]:
        """Partition all categories in the bathroom into affected vs unaffected.

        Hard dependencies and heuristic targets are marked affected.
        Unrelated fixtures (e.g. toilet/shower when vanity changes, unless co-located
        on the same wall with clearance issues) are classified as unaffected.
        """
        deps = self.get_dependencies_for_category(changed_category)
        direct_affected_targets = {d.target for d in deps}

        affected_set = {changed_category}
        if additional_affected:
            affected_set.update(additional_affected)

        for cat in all_present_categories:
            if cat in direct_affected_targets:
                affected_set.add(cat)

        affected = [cat for cat in all_present_categories if cat in affected_set]
        unaffected = [cat for cat in all_present_categories if cat not in affected_set]

        return sorted(affected), sorted(unaffected)


dependency_graph = BathroomDependencyGraph()
