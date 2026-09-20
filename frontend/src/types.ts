// Mirrors backend/api/schemas.py. Kept narrow: only the fields the UI reads.

export type CheckStatus = "pass" | "fail" | "verification_required" | "warning";
export type ReportStatus = "feasible" | "feasible_pending_verification" | "infeasible";

export interface CheckResult {
  constraint: string;
  passed: boolean;
  status: CheckStatus;
  reason: string;
  blocking: boolean;
  details: Record<string, unknown>;
}

export interface ConfigurationReport {
  status: ReportStatus;
  feasible: boolean;
  offerable: boolean;
  checks: CheckResult[];
  blocking_failures: string[];
  verification_requirements: string[];
}

export interface Product {
  id: string;
  name: string;
  category: string;
  tier: string;
  price: number | null;
  currency: string;
  price_status: string;
  verification_status: string;
  kohler_reference_family: string | null;
  dimensions: { width_in: number | null; depth_in: number | null; height_in: number | null };
  electrical_required: boolean | null;
  smart: { features: string[]; konnect_compatible: boolean | null };
  water: {
    flow_rate_gpm: number | null;
    flush_volume_gal: number | null;
    watersense_eligible: boolean | null;
    manufacturer_claim: ManufacturerClaim | null;
  };
  style: string[];
}

export interface ManufacturerClaim {
  claim_type: string;
  value: number;
  unit: string;
  comparison_baseline: string;
  assumptions: string;
  source_url: string;
}

export interface Rect {
  x_in: number;
  y_in: number;
  width_in: number;
  depth_in: number;
}

export interface PlacedFixture {
  product_id: string;
  product_name: string;
  category: string;
  wall: string;
  footprint: Rect;
  clearance: Rect;
  clearance_source: string;
}

export interface UnplacedFixture {
  product_id: string;
  product_name: string;
  category: string;
  reason: string;
  status: string;
}

export interface RoomLayout {
  room_width_in: number;
  room_length_in: number;
  door: DoorSpec | null;
  door_swing: Rect | null;
  placed: PlacedFixture[];
  unplaced: UnplacedFixture[];
  circulation_ok: boolean;
  circulation_notes: string[];
  notes: string[];
}

export interface FixtureWaterEstimate {
  product_name: string;
  category: string;
  status: "calculated" | "insufficient_data" | "not_a_water_fixture";
  recorded_spec: string | null;
  baseline_spec: string | null;
  annual_litres: number | null;
  formula: string | null;
  note: string | null;
}

export interface WaterImpactEstimate {
  status: "calculated" | "insufficient_data";
  assumptions: string[];
  baseline_description: string;
  fixtures: FixtureWaterEstimate[];
  configuration_annual_litres: number | null;
  baseline_annual_litres: number | null;
  annual_litres_saved: number | null;
  percent_saved: number | null;
  manufacturer_claims: ManufacturerClaim[];
  unquantified_products: string[];
  disclaimer: string;
}

export interface ScoreBreakdown {
  spatial: number;
  budget: number;
  preference: number;
  water_efficiency: number;
  style: number;
  smart_feature: number;
  total: number;
}

export interface CandidatePlan {
  label: string | null;
  products: Product[];
  total_price: number;
  currency: string;
  remaining_budget: number | null;
  constraint_report: ConfigurationReport;
  score: ScoreBreakdown;
  layout: RoomLayout;
  water_impact: WaterImpactEstimate;
  strengths: string[];
  trade_offs: string[];
  installation_warnings: string[];
  verification_requirements: string[];
  explanation: string | null;
  explanation_source: string;
}

export interface RelaxationSuggestion {
  constraint: string;
  description: string;
  product_ids: string[];
}

export interface ConstraintViolationSummary {
  constraint: string;
  status: string;
  occurrences: number;
  example_reasons: string[];
}

export interface ClosestAlternative {
  products: Product[];
  total_price: number;
  currency: string;
  violations: CheckResult[];
}

export interface ConflictResult {
  status: string;
  violated_constraints: ConstraintViolationSummary[];
  closest_alternatives: ClosestAlternative[];
  possible_relaxations: RelaxationSuggestion[];
}

export interface DoorSpec {
  wall: string;
  offset_in: number;
  width_in: number;
  swing: string;
}

export interface BathroomBrief {
  room_width_ft: number | null;
  room_length_ft: number | null;
  /** Present in the API contract; the header and 3D view both read it. */
  ceiling_height_ft: number | null;
  budget: number | null;
  currency: string;
  required_categories: string[];
  preferred_styles: string[];
  electrical_available: boolean | null;
  toilet_rough_in_in: number | null;
  door: DoorSpec | null;
  usage: {
    household_size: number;
    flushes_per_person_per_day: number;
    shower_minutes_per_person_per_day: number;
    faucet_minutes_per_person_per_day: number;
  };
}

export interface PlanMeta {
  computed_by: string[];
  catalog_size: number;
  configurations_evaluated: number;
  llm_available: boolean;
  vision_available: boolean;
  notes: string[];
}

export interface PlanResponse {
  project_id: string;
  status: "ok" | "no_fully_compliant_configuration";
  brief: BathroomBrief;
  candidates: CandidatePlan[];
  conflict: ConflictResult | null;
  meta: PlanMeta;
}

export interface ModifyResponse {
  project_id: string;
  understood_as: string;
  interpretation_source: "llm" | "deterministic_keywords";
  applied_changes: string[];
  plan: PlanResponse;
}

export interface VisionEvidence {
  authoritative: false;
  overall_confidence: number;
  detected_objects: {
    type: string;
    confidence: number;
    bounding_box: { x: number; y: number; width: number; height: number };
    observation_status?: "observed" | "estimated" | "unknown" | "requires_verification";
    approximate_wall_region?: "north" | "south" | "east" | "west" | "center" | "unknown";
    dimension_status?: "unknown" | "estimated" | "measured";
  }[];
  ambiguous_objects: { candidate_types: string[]; reason: string }[];
  occlusions: { target_object: string; occluded_by: string; estimated_occlusion_pct?: number }[];
  missing_information: string[];
  unverifiable_attributes: Record<string, { status: string; verification_required: boolean; reason: string }>;
}

// --- DesignPulse Types --------------------------------------------------------

export type LedgerStatus = "pass" | "warning" | "fail";

export interface ConstraintLedgerEntry {
  domain: string;
  status: LedgerStatus;
  summary: string;
  blocking_count: number;
  warning_count: number;
  verification_count: number;
  checks: CheckResult[];
}

export interface ConstraintLedger {
  domains: Record<string, ConstraintLedgerEntry>;
  is_feasible: boolean;
  requires_verification: boolean;
  overall_status: "feasible" | "feasible_pending_verification" | "infeasible";
}

export interface DecisionRecord {
  category: string;
  action: string;
  product_id?: string;
  product_name?: string;
  client_requirement_ref?: string | null;
  rationale: string;
  timestamp: string;
}

export interface DesignState {
  project_id: string;
  version_id: string;
  version_number: number;
  parent_version_id: string | null;
  created_at: string;
  room_width_ft: number | null;
  room_length_ft: number | null;
  ceiling_height_ft: number | null;
  door: DoorSpec | null;
  electrical_available: boolean | null;
  toilet_rough_in_in: number | null;
  selected_products: Product[];
  total_price: number;
  budget_limit: number | null;
  currency: string;
  remaining_budget: number | null;
  layout: RoomLayout;
  constraint_report: ConfigurationReport;
  water_impact: WaterImpactEstimate;
  ledger: ConstraintLedger;
  decision_records: DecisionRecord[];
  vision_analysis?: VisionEvidence | null;
  metadata: Record<string, unknown>;
}

export interface DependencyEvaluation {
  target: string;
  relation_class:
    | "hard_constraint"
    | "model_specific_requirement"
    | "design_heuristic"
    | "unknown_verification"
    | "unaffected";
  status: "pass" | "warning" | "violation" | "unaffected";
  title: string;
  description: string;
  delta: string | null;
}

export interface TradeoffOption {
  id: string;
  title: string;
  description: string;
  strategy:
    | "compensate_budget"
    | "stretch_budget"
    | "compact_alternative"
    | "interface_repair"
    | "preserve_selection";
  substitutions: Array<{ category: string; add_id: string; remove_id: string }>;
  price_delta: number;
  resulting_total_price: number;
  resulting_is_feasible: boolean;
  spatial_summary: string;
  decision_rationale: string;
  suggested_budget_limit?: number | null;
}

export interface ImpactReport {
  changed_category: string;
  previous_product: Product;
  new_product: Product;
  dimensional_delta: Record<string, number>;
  price_delta: number;
  new_total_price: number;
  budget_limit: number | null;
  budget_delta: number;
  spatial_status: "pass" | "warning" | "fail";
  compatibility_status: "pass" | "warning" | "fail";
  budget_status: "pass" | "warning" | "fail";
  installation_status: "pass" | "warning" | "fail";
  affected_categories: string[];
  unaffected_categories: string[];
  dependency_evaluations: DependencyEvaluation[];
  candidate_tradeoffs: TradeoffOption[];
  trial_layout: RoomLayout;
  trial_report: ConfigurationReport;
  trial_ledger: ConstraintLedger;
}

export interface DesignStateDiff {
  from_version: string;
  to_version: string;
  added_products: Product[];
  removed_products: Product[];
  modified_categories: string[];
  price_delta: number;
  remaining_budget_delta: number | null;
  water_annual_litres_saved_delta: number | null;
  ledger_changes: Record<string, [LedgerStatus, LedgerStatus]>;
  new_verification_items: string[];
  resolved_verification_items: string[];
  summary: string;
}

export interface ImpactRequest {
  category?: string;
  action?: "replace_product" | "change_dimension" | "add_category" | "remove_category";
  target_product_id?: string | null;
  target_dimension?: Record<string, number> | null;
  message?: string;
}

export interface TradeoffApplyResponse {
  project_id: string;
  version_id: string;
  version_number: number;
  v2: DesignState;
  diff: DesignStateDiff;
}

export interface VersionSummary {
  version_id: string;
  version_number: number;
  parent_version_id: string | null;
  timestamp: string;
  total_price: number;
  currency: string;
  is_active: boolean;
  metadata: Record<string, unknown>;
}

export interface ProjectHistoryResponse {
  project_id: string;
  active_version_id: string;
  versions: VersionSummary[];
}

// --- Phase 5: Inspiration & Professional Export Types ------------------------

export interface InspirationStylePreset {
  id: string;
  title: string;
  tagline: string;
  description: string;
  primary_materials: string[];
  hardware_finishes: string[];
  palette_tones: string[];
  recommended_families: string[];
  style_keywords: string[];
  mood_imagery_keywords: string[];
}

export interface InspirationPresetsResponse {
  presets: InspirationStylePreset[];
}

export interface InspirationRequest {
  preset_id?: string | null;
  query?: string | null;
}

export interface InspirationApplyResponse {
  project_id: string;
  preset: InspirationStylePreset;
  applied_styles: string[];
  plan: PlanResponse;
  state: DesignState;
}

export interface ClientProductItem {
  category: string;
  name: string;
  price: number;
  currency: string;
  tier: string;
  dimensions: string;
  style: string[];
}

export interface ClientExportData {
  project_id: string;
  version_id: string;
  created_at: string;
  room_dimensions: string;
  total_investment: number;
  currency: string;
  products: ClientProductItem[];
  water_litres_saved_annually: number | null;
  summary: string;
}

export interface DesignerClearanceItem {
  product_name: string;
  category: string;
  wall: string;
  footprint: string;
  required_clearance: string;
  clearance_source: string;
}

export interface DesignerExportData {
  project_id: string;
  version_id: string;
  room_dimensions: string;
  ledger: ConstraintLedger;
  clearances: DesignerClearanceItem[];
  decision_records: DecisionRecord[];
  unresolved_verifications: string[];
  circulation_notes: string[];
}

export interface DealerBOMItem {
  item_number: number;
  category: string;
  kohler_family: string;
  sku: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  currency: string;
  rough_in_in: number | null;
  electrical_required: boolean;
}

export interface DealerExportData {
  project_id: string;
  version_id: string;
  date_generated: string;
  line_items: DealerBOMItem[];
  total_net_price: number;
  currency: string;
  rough_in_summary: string[];
  electrical_summary: string[];
}

export interface ExportPackageResponse {
  role: "client" | "designer" | "dealer";
  project_id: string;
  version_id: string;
  data: ClientExportData | DesignerExportData | DealerExportData | Record<string, unknown>;
}

export interface CatalogResponse {
  count: number;
  categories: string[];
  products: Product[];
  data_disclaimer: string;
}



