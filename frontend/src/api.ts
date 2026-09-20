import type {
  BathroomBrief,
  CatalogResponse,
  DesignState,
  DesignStateDiff,
  ExportPackageResponse,
  ImpactReport,
  ImpactRequest,
  InspirationApplyResponse,
  InspirationPresetsResponse,
  InspirationRequest,
  ModifyResponse,
  PlanResponse,
  ProjectHistoryResponse,
  TradeoffApplyResponse,
  TradeoffOption,
  VisionEvidence,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(
      "Could not reach the planning service. Is the backend running on port 8000?",
      0,
    );
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body.detail)) {
        // FastAPI validation errors arrive as a list of field problems.
        detail = body.detail
          .map((item: { loc?: unknown[]; msg?: string }) =>
            `${(item.loc ?? []).slice(1).join(".")}: ${item.msg ?? "invalid"}`,
          )
          .join("; ");
      }
    } catch {
      /* response had no JSON body; keep the status-based message */
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

export interface PlanRequest extends Partial<BathroomBrief> {
  preferences?: Record<string, unknown>;
  weights?: Record<string, number>;
  max_candidates?: number;
}

export const api = {
  health: () =>
    request<{
      status: string;
      catalog_size: number;
      vision_available: boolean;
      llm_available: boolean;
    }>("/api/v1/health"),

  getCatalog: () => request<CatalogResponse>("/api/v1/catalog"),


  createPlan: (brief: PlanRequest) =>
    request<PlanResponse>("/api/v1/plan", {
      method: "POST",
      body: JSON.stringify(brief),
    }),

  getPlan: (projectId: string) => request<PlanResponse>(`/api/v1/plan/${projectId}`),

  getDesignState: (projectId: string, versionId?: string) =>
    request<DesignState>(
      `/api/v1/plan/${projectId}/state${versionId ? `?version_id=${versionId}` : ""}`,
    ),

  resolve: (projectId: string, body: Record<string, unknown>) =>
    request<PlanResponse>(`/api/v1/plan/${projectId}/resolve`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  modify: (projectId: string, message: string) =>
    request<ModifyResponse>(`/api/v1/plan/${projectId}/modify`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  impact: (projectId: string, req: ImpactRequest) =>
    request<ImpactReport>(`/api/v1/plan/${projectId}/impact`, {
      method: "POST",
      body: JSON.stringify(req),
    }),

  applyTradeoff: (projectId: string, tradeoffId: string, tradeoff?: TradeoffOption) =>
    request<TradeoffApplyResponse>(`/api/v1/plan/${projectId}/tradeoff`, {
      method: "POST",
      body: JSON.stringify({ tradeoff_id: tradeoffId, tradeoff }),
    }),

  getHistory: (projectId: string) =>
    request<ProjectHistoryResponse>(`/api/v1/plan/${projectId}/history`),

  getDiff: (projectId: string, fromVersion = "v1", toVersion = "v2") =>
    request<DesignStateDiff>(
      `/api/v1/plan/${projectId}/diff?from_version=${fromVersion}&to_version=${toVersion}`,
    ),

  getInspirationPresets: () =>
    request<InspirationPresetsResponse>("/api/v1/inspiration/presets"),

  applyInspiration: (projectId: string, req: InspirationRequest) =>
    request<InspirationApplyResponse>(`/api/v1/plan/${projectId}/inspiration`, {
      method: "POST",
      body: JSON.stringify(req),
    }),

  getExportPackage: (
    projectId: string,
    role: "client" | "designer" | "dealer" = "client",
    versionId?: string,
  ) =>
    request<ExportPackageResponse>(
      `/api/v1/plan/${projectId}/export?role=${role}${versionId ? `&version_id=${versionId}` : ""}`,
    ),

  getExportDocumentUrl: (
    projectId: string,
    role: "client" | "designer" | "dealer" = "client",
    versionId?: string,
  ) =>
    `${BASE}/api/v1/plan/${projectId}/export/document?role=${role}${versionId ? `&version_id=${versionId}` : ""}`,

  analyseImage: async (projectId: string, file: File): Promise<VisionEvidence> => {
    const form = new FormData();
    form.append("image", file);
    const response = await fetch(`${BASE}/api/v1/project/${projectId}/vision`, {
      method: "POST",
      body: form,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new ApiError(body.detail ?? "Image analysis is unavailable", response.status);
    }
    return response.json();
  },
};

export const formatMoney = (value: number, currency = "INR") =>
  `${currency === "INR" ? "₹" : currency + " "}${Math.round(value).toLocaleString("en-IN")}`;

export const formatLitres = (value: number) =>
  `${Math.round(value).toLocaleString("en-IN")} L`;
