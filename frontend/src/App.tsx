import { useEffect, useState } from "react";
import { ApiError, api, formatMoney, type PlanRequest } from "./api";
import { BriefDrawerModal } from "./components/BriefDrawerModal";
import { GOLDEN_PATH, buildRequest } from "./components/BriefForm";
import { CatalogModal } from "./components/CatalogModal";
import { ConflictPanel } from "./components/ConflictPanel";
import { DesignPulseChangeConsole } from "./components/DesignPulseChangeConsole";
import { ExportModal } from "./components/ExportModal";
import { FinalizeModal } from "./components/FinalizeModal";
import { HelpModal } from "./components/HelpModal";
import { InspirationModal } from "./components/InspirationModal";
import { MyDesignsDrawer, type SavedProjectRecord } from "./components/MyDesignsDrawer";
import { PersistentLedgerDock } from "./components/PersistentLedgerDock";
import { PlanCanvas } from "./components/PlanCanvas";
import { ProductInspectorDrawer } from "./components/ProductInspectorDrawer";
import { ProductSpecificationSheet } from "./components/ProductSpecificationSheet";
import { NavRoute, Sidebar, UserRole } from "./components/Sidebar";
import { SustainabilityModal } from "./components/SustainabilityModal";
import { AppTheme, WorkspaceHeader } from "./components/WorkspaceHeader";
import type {
  CandidatePlan,
  ConstraintLedger,
  ConstraintLedgerEntry,
  DesignState,
  DesignStateDiff,
  ImpactReport,
  InspirationApplyResponse,
  PlanResponse,
  Product,
  TradeoffOption,
  VisionEvidence,
} from "./types";

const LEDGER_DOMAIN_KEYS = [
  "space",
  "budget",
  "compatibility",
  "installation",
  "style",
  "water",
  "verification",
] as const;

/** Domains where a warning means someone still has to go and check something.
 *  Budget and water can warn without anything being verifiable. */
const VERIFIABLE_DOMAIN_KEYS = [
  "space",
  "compatibility",
  "installation",
  "verification",
] as const;

function normalizeDesignStateLedger(state: DesignState): DesignState {
  const ledger = state.ledger as ConstraintLedger & Record<string, unknown>;
  if (ledger.domains) return state;

  const domains: Record<string, ConstraintLedgerEntry> = {};
  for (const key of LEDGER_DOMAIN_KEYS) {
    const entry = (ledger as Record<string, unknown>)[key];
    if (entry && typeof entry === "object") {
      domains[key] = entry as ConstraintLedgerEntry;
    }
  }

  const hasFail = LEDGER_DOMAIN_KEYS.some((k) => domains[k]?.status === "fail");
  const hasVerification = VERIFIABLE_DOMAIN_KEYS.some(
    (k) => (domains[k]?.verification_count ?? 0) > 0 || domains[k]?.status === "warning"
  );

  const overall_status: ConstraintLedger["overall_status"] = hasFail
    ? "infeasible"
    : hasVerification
    ? "feasible_pending_verification"
    : "feasible";

  return {
    ...state,
    ledger: {
      domains,
      is_feasible: !hasFail,
      requires_verification: hasVerification,
      overall_status,
    },
  };
}

function buildInitialDesignState(plan: PlanResponse, candidate: CandidatePlan): DesignState {
  const isBudgetOk =
    plan.brief.budget !== null ? candidate.total_price <= plan.brief.budget : true;

  return {
    project_id: plan.project_id,
    version_id: "v1",
    version_number: 1,
    parent_version_id: null,
    created_at: new Date().toISOString(),
    room_width_ft: plan.brief.room_width_ft,
    room_length_ft: plan.brief.room_length_ft,
    ceiling_height_ft: plan.brief.ceiling_height_ft ?? 8.0,
    door: plan.brief.door,
    electrical_available: plan.brief.electrical_available,
    toilet_rough_in_in: plan.brief.toilet_rough_in_in,
    selected_products: candidate.products,
    total_price: candidate.total_price,
    budget_limit: plan.brief.budget,
    currency: candidate.currency,
    remaining_budget: candidate.remaining_budget,
    layout: candidate.layout,
    constraint_report: candidate.constraint_report,
    water_impact: candidate.water_impact,
    ledger: {
      domains: {
        space: {
          domain: "space",
          status: candidate.constraint_report.feasible ? "pass" : "fail",
          summary: candidate.constraint_report.feasible
            ? "Spatial clearances and door swings satisfied"
            : "Clearance overlap detected",
          blocking_count: candidate.constraint_report.blocking_failures.length,
          warning_count: 0,
          verification_count: 0,
          checks: candidate.constraint_report.checks.filter(
            (c) =>
              c.constraint.includes("clearance") ||
              c.constraint.includes("door") ||
              c.constraint.includes("circulation")
          ),
        },
        budget: {
          domain: "budget",
          status: isBudgetOk ? "pass" : "fail",
          summary: `${formatMoney(candidate.total_price, candidate.currency)}${
            plan.brief.budget !== null
              ? ` / ${formatMoney(plan.brief.budget, candidate.currency)} limit`
              : ""
          }`,
          blocking_count: isBudgetOk ? 0 : 1,
          warning_count: 0,
          verification_count: 0,
          checks: candidate.constraint_report.checks.filter((c) =>
            c.constraint.includes("budget")
          ),
        },
        compatibility: {
          domain: "compatibility",
          status: "pass",
          summary: "All plumbing and fixture interfaces compatible",
          blocking_count: 0,
          warning_count: 0,
          verification_count: 0,
          checks: candidate.constraint_report.checks.filter(
            (c) => c.constraint.includes("interface") || c.constraint.includes("compatibility")
          ),
        },
        installation: {
          domain: "installation",
          status: candidate.installation_warnings.length > 0 ? "warning" : "pass",
          summary:
            candidate.installation_warnings.length > 0
              ? candidate.installation_warnings[0]
              : "Standard floor/wall mounting verified",
          blocking_count: 0,
          warning_count: candidate.installation_warnings.length,
          verification_count: 0,
          checks: candidate.constraint_report.checks.filter(
            (c) => c.constraint.includes("rough_in") || c.constraint.includes("electrical")
          ),
        },
        style: {
          domain: "style",
          status: "pass",
          summary: "Aesthetic finish and form-language aligned",
          blocking_count: 0,
          warning_count: 0,
          verification_count: 0,
          checks: [],
        },
        water: {
          domain: "water",
          status: candidate.water_impact.status === "calculated" ? "pass" : "warning",
          summary: candidate.water_impact.annual_litres_saved
            ? `${candidate.water_impact.annual_litres_saved.toLocaleString()} L saved annually`
            : "Baseline consumption recorded",
          blocking_count: 0,
          warning_count: 0,
          verification_count: 0,
          checks: [],
        },
        verification: {
          domain: "verification",
          status: candidate.verification_requirements.length > 0 ? "warning" : "pass",
          summary:
            candidate.verification_requirements.length > 0
              ? candidate.verification_requirements[0]
              : "All field dimensions verified",
          blocking_count: 0,
          warning_count: 0,
          verification_count: candidate.verification_requirements.length,
          checks: [],
        },
      },
      is_feasible: candidate.constraint_report.feasible,
      requires_verification: candidate.verification_requirements.length > 0,
      overall_status: candidate.constraint_report.status,
    },
    decision_records: [
      {
        category: "overall",
        action: "initial_selection",
        product_id: "init",
        product_name: "Initial Candidate Plan",
        client_requirement_ref: null,
        rationale: "Initial plan generated from stated brief requirements.",
        timestamp: new Date().toISOString(),
      },
    ],
    metadata: {},
  };
}

export default function App() {
  // Navigation & Role State
  const [activeRoute, setActiveRoute] = useState<NavRoute>("new_project");
  const [userRole, setUserRole] = useState<UserRole>(() => {
    return (localStorage.getItem("kohler_user_mode") as UserRole) || "homeowner";
  });

  // Appearance Theme State (Light / Dark / System)
  const [theme, setTheme] = useState<AppTheme>(() => {
    return (localStorage.getItem("kohler_theme") as AppTheme) || "system";
  });

  // Core Planning State
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [selected, setSelected] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<{
    catalog_size: number;
    vision_available: boolean;
    llm_available: boolean;
  } | null>(null);

  // Vision State
  const [pendingImage, setPendingImage] = useState<File | null>(null);
  const [vision, setVision] = useState<VisionEvidence | null>(null);
  const [visionError, setVisionError] = useState<string | null>(null);
  const [uploadedSitePhotoUrl, setUploadedSitePhotoUrl] = useState<string | null>(null);

  // DesignPulse & Versioning State
  const [activeDesignState, setActiveDesignState] = useState<DesignState | null>(null);
  const [v1DesignState, setV1DesignState] = useState<DesignState | null>(null);
  const [impactReport, setImpactReport] = useState<ImpactReport | null>(null);
  const [activeDiff, setActiveDiff] = useState<DesignStateDiff | null>(null);
  const [viewingVersion, setViewingVersion] = useState<"v1" | "v2">("v1");

  // Interaction: Highlighted & Inspected Fixture
  const [highlightedProductId, setHighlightedProductId] = useState<string | null>(null);
  const [inspectedProduct, setInspectedProduct] = useState<Product | null>(null);
  const [catalogInitialCategory, setCatalogInitialCategory] = useState<string | null>(null);

  // Modals & Drawers
  const [isBriefOpen, setIsBriefOpen] = useState<boolean>(false);
  const [isInspirationOpen, setIsInspirationOpen] = useState<boolean>(false);
  const [isFinalizeOpen, setIsFinalizeOpen] = useState<boolean>(false);
  const [isExportOpen, setIsExportOpen] = useState<boolean>(false);
  const [isCatalogOpen, setIsCatalogOpen] = useState<boolean>(false);
  const [isSustainabilityOpen, setIsSustainabilityOpen] = useState<boolean>(false);
  const [isMyDesignsOpen, setIsMyDesignsOpen] = useState<boolean>(false);
  const [isHelpOpen, setIsHelpOpen] = useState<boolean>(false);
  const [isFinalized, setIsFinalized] = useState<boolean>(false);

  // Saved Projects Persistence
  const [savedProjects, setSavedProjects] = useState<SavedProjectRecord[]>(() => {
    try {
      const stored = localStorage.getItem("kohler_saved_projects");
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });
  const [saveStatusText, setSaveStatusText] = useState<string>("✓ Ready");

  // Apply & Listen Theme Changes
  useEffect(() => {
    localStorage.setItem("kohler_theme", theme);

    const applyTheme = () => {
      let resolved = theme;
      if (theme === "system") {
        resolved = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      }
      document.documentElement.setAttribute("data-theme", resolved);
    };

    applyTheme();

    if (theme === "system") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      const handler = () => applyTheme();
      mediaQuery.addEventListener("change", handler);
      return () => mediaQuery.removeEventListener("change", handler);
    }
  }, [theme]);

  // Persist User Role
  const handleToggleUserRole = (role: UserRole) => {
    setUserRole(role);
    localStorage.setItem("kohler_user_mode", role);
  };

  // Check Backend Health on Mount
  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() =>
        setError(
          "The planning service is not reachable. Start the backend with: uvicorn backend.main:app --reload"
        )
      );
  }, []);

  const run = async <T,>(work: () => Promise<T>): Promise<T | null> => {
    setBusy(true);
    setError(null);
    try {
      return await work();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Something went wrong.");
      return null;
    } finally {
      setBusy(false);
    }
  };

  /** The server's DesignState if it can be fetched, else the local rebuild.
   *
   * The browser can reconstruct a v1 from the plan response, and does, because
   * the design has to appear even when a later call fails. But the ledger and
   * the diffs are computed server-side, so when the authoritative copy is
   * reachable it wins — otherwise v1 on screen and v1 in the diff are two
   * different objects.
   */
  const loadDesignState = async (
    projectId: string,
    plan: PlanResponse,
    candidate: CandidatePlan,
  ): Promise<DesignState> => {
    try {
      return normalizeDesignStateLedger(await api.getDesignState(projectId));
    } catch {
      return buildInitialDesignState(plan, candidate);
    }
  };

  const handlePlan = async (request: PlanRequest) => {
    const result = await run(() => api.createPlan(request));
    if (!result) return;
    setPlan(result);
    setSelected(0);
    setImpactReport(null);
    setActiveDiff(null);
    setViewingVersion("v1");
    setIsFinalized(false);
    setActiveRoute("new_project");
    setSaveStatusText("Design ready · not saved yet");

    if (result.candidates.length > 0) {
      const v1 = await loadDesignState(result.project_id, result, result.candidates[0]);
      setActiveDesignState(v1);
      setV1DesignState(v1);
    } else {
      setActiveDesignState(null);
      setV1DesignState(null);
    }

    if (pendingImage) {
      setUploadedSitePhotoUrl(URL.createObjectURL(pendingImage));
      if (result.meta.vision_available) {
        analyseImage(result.project_id, pendingImage);
      }
    }
  };

  const analyseImage = async (projectId: string, file: File) => {
    setVisionError(null);
    try {
      const evidence = await api.analyseImage(projectId, file);
      setVision(evidence);
      setActiveDesignState((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          vision_analysis: evidence,
          ledger: {
            ...prev.ledger,
            requires_verification: true,
            overall_status:
              prev.ledger.overall_status === "feasible"
                ? "feasible_pending_verification"
                : prev.ledger.overall_status,
          },
        };
      });
    } catch (caught) {
      setVision(null);
      setVisionError(
        caught instanceof ApiError
          ? caught.message
          : "Vision analysis unavailable. You can continue using manual project inputs."
      );
    }
  };

  const handleResolve = async (body: Record<string, unknown>) => {
    if (!plan) return;
    const result = await run(() => api.resolve(plan.project_id, body));
    if (result) {
      setPlan(result);
      setSelected(0);
      setImpactReport(null);
      setActiveDiff(null);
      setViewingVersion("v1");
      setIsFinalized(false);
      setSaveStatusText("✓ Recomputed");
      if (result.candidates.length > 0) {
        const v1 = await loadDesignState(result.project_id, result, result.candidates[0]);
        setActiveDesignState(v1);
        setV1DesignState(v1);
      }
    }
  };

  const handleAnalyzeImpact = async (message: string) => {
    if (!plan) return;
    const report = await run(() => api.impact(plan.project_id, { message }));
    if (report) {
      setImpactReport(report);
    }
  };

  const handleApplyTradeoff = async (tradeoff: TradeoffOption) => {
    if (!plan) return;
    const response = await run(() =>
      api.applyTradeoff(plan.project_id, tradeoff.id, tradeoff)
    );
    if (response) {
      if (activeDesignState && activeDesignState.version_id === "v1") {
        setV1DesignState(activeDesignState);
      }
      setActiveDesignState(normalizeDesignStateLedger(response.v2));
      setActiveDiff(response.diff);
      setImpactReport(null);
      setViewingVersion("v2");
      setIsFinalized(false);
      setSaveStatusText("✓ V2 Created & Saved");
    }
  };

  const handlePresetApplied = (res: InspirationApplyResponse) => {
    setPlan(res.plan);
    setSelected(0);
    setActiveDesignState(normalizeDesignStateLedger(res.state));
    setSaveStatusText("✓ Style Applied");
    if (res.state.version_number > 1) {
      setViewingVersion("v2");
      api
        .getDiff(res.project_id, "v1", res.state.version_id)
        .then(setActiveDiff)
        .catch(() => {});
    }
  };

  const handleSaveCurrentProject = (name: string) => {
    if (!plan || !activeDesignState) return;

    const newRecord: SavedProjectRecord = {
      id: plan.project_id,
      name,
      timestamp: new Date().toISOString(),
      dimensions: `${activeDesignState.room_width_ft}′ × ${activeDesignState.room_length_ft}′`,
      totalPrice: activeDesignState.total_price,
      currency: activeDesignState.currency,
      productsCount: activeDesignState.selected_products.length,
      plan,
      activeDesignState,
      v1DesignState,
    };

    const updated = [newRecord, ...savedProjects.filter((p) => p.id !== plan.project_id)];
    setSavedProjects(updated);
    try {
      localStorage.setItem("kohler_saved_projects", JSON.stringify(updated));
      setSaveStatusText("✓ Saved to Projects");
    } catch {
      /* ignore storage quota */
    }
  };

  const handleLoadSavedProject = async (record: SavedProjectRecord) => {
    // Saved designs live in this browser; the planning session that answers
    // DesignPulse, versioning and export lives in the backend and does not
    // survive a restart. Restoring only the browser half looks like it worked
    // and then fails on the next click, so re-establish the server session
    // from the saved brief when it has gone.
    setPlan(record.plan);
    setActiveDesignState(record.activeDesignState);
    setV1DesignState(record.v1DesignState ?? record.activeDesignState);
    setViewingVersion(record.activeDesignState.version_id === "v2" ? "v2" : "v1");
    setIsFinalized(false);
    setImpactReport(null);
    setActiveDiff(null);
    setError(null);
    setSaveStatusText("Opening…");

    try {
      await api.getPlan(record.id);
      setSaveStatusText("✓ Opened");
      return;
    } catch (caught) {
      if (!(caught instanceof ApiError) || (caught.status !== 404 && caught.status !== 0)) {
        throw caught;
      }
    }

    try {
      const revived = await api.createPlan(record.plan.brief as PlanRequest);
      setPlan(revived);
      setSelected(0);
      if (revived.candidates.length > 0) {
        const v1 = await loadDesignState(revived.project_id, revived, revived.candidates[0]);
        setActiveDesignState(v1);
        setV1DesignState(v1);
        setViewingVersion("v1");
      }
      setSaveStatusText("✓ Opened · session rebuilt");
      setError(
        "This design was reopened from your browser and the planning session had to be rebuilt, " +
          "so it starts again at V1 — any later versions you had made are not on the server. " +
          "The room, budget and requirements are exactly as you saved them.",
      );
    } catch {
      setSaveStatusText("Offline copy");
      setError(
        "This design was reopened from your browser, but the planning service is not reachable, " +
          "so changes, versioning and export are unavailable. Start the backend and open it again.",
      );
    }
  };

  const handleDeleteSavedProject = (id: string) => {
    const updated = savedProjects.filter((p) => p.id !== id);
    setSavedProjects(updated);
    localStorage.setItem("kohler_saved_projects", JSON.stringify(updated));
  };

  // Sidebar Route Navigation Dispatcher
  const handleSidebarNavigate = (route: NavRoute) => {
    setActiveRoute(route);
    switch (route) {
      case "new_project":
        if (!plan) setIsBriefOpen(true);
        break;
      case "my_designs":
        setIsMyDesignsOpen(true);
        break;
      case "inspiration":
        setIsInspirationOpen(true);
        break;
      case "catalog":
        setCatalogInitialCategory(null);
        setIsCatalogOpen(true);
        break;
      case "designpulse":
        // Focus column 3
        break;
      case "sustainability":
        setIsSustainabilityOpen(true);
        break;
      case "export":
        setIsExportOpen(true);
        break;
    }
  };

  const candidate = plan?.candidates[selected] ?? null;

  const projectName = plan
    ? savedProjects.find((p) => p.id === plan.project_id)?.name ?? "Untitled design"
    : "New Project";

  // Active view layout & ledger
  const currentDisplayState =
    viewingVersion === "v2" && activeDesignState?.version_id === "v2"
      ? activeDesignState
      : v1DesignState ?? activeDesignState;

  const currentLayout = currentDisplayState?.layout ?? candidate?.layout ?? null;
  const currentLedger = currentDisplayState?.ledger ?? null;

  // Derive workflow current step
  const currentWorkflowStep = isFinalized
    ? "finalize"
    : viewingVersion === "v2" || impactReport
    ? "refine"
    : plan
    ? "design"
    : "brief";

  return (
    <div className="kohler-app-shell">
      {/* Left Sidebar Navigation */}
      <Sidebar
        activeRoute={activeRoute}
        onNavigate={handleSidebarNavigate}
        userRole={userRole}
        onToggleUserRole={handleToggleUserRole}
        savedDesignsCount={savedProjects.length}
        catalogCount={health?.catalog_size ?? 0}
        hasActivePlan={Boolean(plan)}
      />

      {/* Main Studio Frame */}
      <div className="studio-main-frame">
        {/* Workspace Top Header & Project Context Bar */}
        <WorkspaceHeader
          projectId={plan?.project_id || "New Project"}
          projectName={projectName}
          roomWidthFt={currentDisplayState?.room_width_ft ?? plan?.brief.room_width_ft ?? null}
          roomLengthFt={currentDisplayState?.room_length_ft ?? plan?.brief.room_length_ft ?? null}
          budget={currentDisplayState?.budget_limit ?? plan?.brief.budget ?? null}
          currency={currentDisplayState?.currency || "INR"}
          styles={plan?.brief.preferred_styles ?? []}
          door={currentDisplayState?.door ?? plan?.brief.door ?? null}
          hasPlan={Boolean(plan)}
          activeVersion={viewingVersion}
          hasV2={Boolean(activeDiff || (activeDesignState && activeDesignState.version_id === "v2"))}
          onSelectVersion={(ver) => setViewingVersion(ver)}
          isFinalized={isFinalized}
          requiresVerification={currentLedger?.requires_verification ?? false}
          catalogSize={health?.catalog_size ?? 0}
          llmAvailable={health?.llm_available || false}
          visionAvailable={health?.vision_available || false}
          currentStep={currentWorkflowStep}
          theme={theme}
          onSelectTheme={setTheme}
          saveStatusText={saveStatusText}
          onSaveProject={() => {
            const suggested = currentDisplayState
              ? `${currentDisplayState.room_width_ft ?? "?"}′ × ${
                  currentDisplayState.room_length_ft ?? "?"
                }′ bathroom`
              : "Bathroom design";
            const name = window.prompt("Name this design", suggested);
            if (name && name.trim()) handleSaveCurrentProject(name.trim());
          }}
          onOpenInspiration={() => setIsInspirationOpen(true)}
          onOpenBrief={() => setIsBriefOpen(true)}
          onOpenFinalize={() => setIsFinalizeOpen(true)}
          onOpenExport={() => setIsExportOpen(true)}
          onOpenHelp={() => setIsHelpOpen(true)}
          onCompareVersions={() => {
            if (activeDiff) setViewingVersion(viewingVersion === "v1" ? "v2" : "v1");
          }}
        />

        {error && (
          <div className="banner banner-error" role="alert">
            {error}
          </div>
        )}

        {/* Compact Hero Block (Shown when no plan or when starting) */}
        {!plan && !busy && (
          <main className="hero-studio-landing">
            <div className="hero-landing-card">
              <span className="hero-badge">KOHLER AI BATHPLAN</span>
              <h2 className="hero-heading">Your Dream Bathroom, Designed with Intelligence</h2>
              <p className="hero-subtext">
                Explore a feasible layout, products, and visual options — then understand what changes
                before you commit. Powered by verified architectural rules and the DesignPulse™
                consequence engine.
              </p>

              <div className="hero-cta-cluster">
                <button
                  type="button"
                  className="btn-hero-primary"
                  onClick={() => handlePlan(buildRequest(GOLDEN_PATH as any))}
                >
                  <span>🏛</span> Launch Golden Demo Project (6′ × 8′ Master Bath)
                </button>
                <button
                  type="button"
                  className="btn-hero-secondary"
                  onClick={() => setIsBriefOpen(true)}
                >
                  <span>📐</span> Enter Custom Room Dimensions
                </button>
              </div>

              <div className="hero-features-strip">
                <div className="feature-item">
                  <span className="feature-icon">✓</span>
                  <span>Strict NKBA &amp; IRC Clearances</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">⚡</span>
                  <span>DesignPulse™ Consequence Tracking</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">💧</span>
                  <span>WaterSense Conservation Intelligence</span>
                </div>
              </div>
            </div>
          </main>
        )}

        {/* Conflict Resolution Banner */}
        {plan?.status === "no_fully_compliant_configuration" && plan.conflict && (
          <div style={{ marginTop: "1rem" }}>
            <ConflictPanel
              conflict={plan.conflict}
              brief={plan.brief}
              onResolve={handleResolve}
              busy={busy}
            />
          </div>
        )}

        {/* 3-COLUMN ARCHITECTURAL WORKSPACE GRID */}
        {plan && currentDisplayState && (
          <main className="studio-grid">
            {/* Column 1: Centerpiece Architectural Canvas */}
            <PlanCanvas
              state={currentDisplayState}
              layout={currentLayout}
              activeVersion={viewingVersion}
              diff={activeDiff}
              v1State={v1DesignState}
              meta={plan.meta}
              vision={vision}
              visionError={visionError}
              uploadedPhotoUrl={uploadedSitePhotoUrl}
              onUploadPhoto={(file) => {
                setUploadedSitePhotoUrl(URL.createObjectURL(file));
                if (plan.meta.vision_available) {
                  analyseImage(plan.project_id, file);
                }
              }}
              highlightedProductId={highlightedProductId}
              selectedProductId={inspectedProduct?.id}
              onSelectProduct={(productId) => {
                const found = currentDisplayState.selected_products.find(
                  (p) => p.id === productId
                );
                if (found) setInspectedProduct(found);
              }}
            />

            {/* Column 2: Products in this Design */}
            <ProductSpecificationSheet
              state={currentDisplayState}
              candidate={candidate}
              onOpenInspiration={() => setIsInspirationOpen(true)}
              onOpenCatalog={(category) => {
                setCatalogInitialCategory(category || null);
                setIsCatalogOpen(true);
              }}
              onHoverProduct={setHighlightedProductId}
              onSelectProduct={setInspectedProduct}
              userRole={userRole}
            />

            {/* Column 3: DesignPulse™ Consequence Console */}
            <DesignPulseChangeConsole
              activeState={currentDisplayState}
              impactReport={impactReport}
              onAnalyze={handleAnalyzeImpact}
              onApplyTradeoff={handleApplyTradeoff}
              onKeepCurrent={() => setImpactReport(null)}
              onCompareVersions={() => {
                if (activeDiff) setViewingVersion(viewingVersion === "v1" ? "v2" : "v1");
              }}
              busy={busy}
              llmAvailable={health?.llm_available ?? false}
              userRole={userRole}
            />
          </main>
        )}

        {/* Persistent Bottom 7-Domain Constraint & Trust Ledger */}
        {currentLedger && (
          <PersistentLedgerDock
            ledger={currentLedger}
            totalPrice={currentDisplayState?.total_price}
            currency={currentDisplayState?.currency}
            onOpenFinalize={() => setIsFinalizeOpen(true)}
            isFinalized={isFinalized}
            userRole={userRole}
          />
        )}
      </div>

      {/* Contextual Product Inspector Drawer */}
      <ProductInspectorDrawer
        product={inspectedProduct}
        currency={currentDisplayState?.currency || "INR"}
        isOpen={Boolean(inspectedProduct)}
        onClose={() => setInspectedProduct(null)}
        onReplace={(p) => {
          setCatalogInitialCategory(p.category);
          setIsCatalogOpen(true);
        }}
        onOpenCatalog={(cat) => {
          setCatalogInitialCategory(cat);
          setIsCatalogOpen(true);
        }}
        userRole={userRole}
      />

      {/* Catalog Explorer Modal */}
      <CatalogModal
        isOpen={isCatalogOpen}
        onClose={() => setIsCatalogOpen(false)}
        initialCategory={catalogInitialCategory}
        hasActivePlan={Boolean(plan)}
        onSwapProduct={(product) => {
          if (!plan) return;
          // Trigger real DesignPulse impact evaluation for swapping this product!
          api
            .impact(plan.project_id, {
              category: product.category,
              action: "replace_product",
              target_product_id: product.id,
            })
            .then((report) => {
              setImpactReport(report);
              setActiveRoute("designpulse");
            })
            .catch((err) => setError(err.message || "Could not evaluate fixture swap"));
        }}
      />

      {/* Sustainability Intelligence Modal */}
      <SustainabilityModal
        isOpen={isSustainabilityOpen}
        onClose={() => setIsSustainabilityOpen(false)}
        state={currentDisplayState}
        candidate={candidate}
      />

      {/* My Designs Drawer */}
      <MyDesignsDrawer
        isOpen={isMyDesignsOpen}
        onClose={() => setIsMyDesignsOpen(false)}
        savedProjects={savedProjects}
        currentProjectId={plan?.project_id ?? null}
        onLoadProject={handleLoadSavedProject}
        onSaveCurrentProject={handleSaveCurrentProject}
        onDeleteProject={handleDeleteSavedProject}
        hasActivePlan={Boolean(plan)}
      />

      {/* Architecture & Help Modal */}
      <HelpModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />

      {/* Brief Drawer Modal */}
      <BriefDrawerModal
        isOpen={isBriefOpen}
        onClose={() => setIsBriefOpen(false)}
        onSubmit={handlePlan}
        onImageSelected={(file) => {
          setPendingImage(file);
          setUploadedSitePhotoUrl(URL.createObjectURL(file));
          if (plan) analyseImage(plan.project_id, file);
        }}
        busy={busy}
        visionAvailable={health?.vision_available ?? false}
        imageName={pendingImage?.name ?? null}
      />

      {/* Inspiration Modal */}
      {plan && (
        <InspirationModal
          projectId={plan.project_id}
          isOpen={isInspirationOpen}
          onClose={() => setIsInspirationOpen(false)}
          onPresetApplied={handlePresetApplied}
        />
      )}

      {/* Finalize Modal */}
      {plan && (
        <FinalizeModal
          isOpen={isFinalizeOpen}
          onClose={() => setIsFinalizeOpen(false)}
          state={currentDisplayState}
          ledger={currentLedger}
          isFinalized={isFinalized}
          onFinalizeConfirm={() => {
            setIsFinalized(true);
            setSaveStatusText("🔒 Finalized & Locked");
          }}
          onOpenExport={() => setIsExportOpen(true)}
        />
      )}

      {/* Export & BOM Modal */}
      {plan && (
        <ExportModal
          projectId={plan.project_id}
          versionId={currentDisplayState?.version_id}
          isOpen={isExportOpen}
          onClose={() => setIsExportOpen(false)}
        />
      )}
    </div>
  );
}
