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
  door: { wall: string; offset_in: number; width_in: number; swing: string } | null;
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

export interface BathroomBrief {
  room_width_ft: number | null;
  room_length_ft: number | null;
  budget: number | null;
  currency: string;
  required_categories: string[];
  preferred_styles: string[];
  electrical_available: boolean | null;
  toilet_rough_in_in: number | null;
  door: { wall: string; offset_in: number; width_in: number; swing: string } | null;
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
  }[];
  ambiguous_objects: { candidate_types: string[]; reason: string }[];
  occlusions: { target_object: string; occluded_by: string }[];
  missing_information: string[];
  unverifiable_attributes: Record<string, { status: string; verification_required: boolean; reason: string }>;
}
