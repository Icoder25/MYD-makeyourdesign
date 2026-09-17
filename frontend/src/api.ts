import type {
  BathroomBrief,
  ModifyResponse,
  PlanResponse,
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

  createPlan: (brief: PlanRequest) =>
    request<PlanResponse>("/api/v1/plan", {
      method: "POST",
      body: JSON.stringify(brief),
    }),

  getPlan: (projectId: string) => request<PlanResponse>(`/api/v1/plan/${projectId}`),

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
