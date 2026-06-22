import type { ApiResponse, AlertItem, SystemStats, DetectionResult } from "./types";

const BASE = "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  getStats: () => request<ApiResponse<SystemStats>>("/api/system/stats"),

  getTrends: () => request<ApiResponse<Array<{ hour: string; attacks: number; total: number }>>>("/api/system/trends"),

  getTopology: () => request<ApiResponse<{
    nodes: Array<{ id: string; traffic: number }>;
    links: Array<{ source: string; target: string; attack: string; count: number }>;
  }>>("/api/system/topology"),

  getAlerts: (page = 1, limit = 50, search?: string) => {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (search) params.set("search", search);
    return request<ApiResponse<AlertItem[]>>(`/api/alerts?${params}`);
  },

  getAlert: (id: string) => request<ApiResponse<AlertItem>>(`/api/alerts/${id}`),

  getModelInfo: () => request<ApiResponse<{ version: string; params_count: number; inference_time_ms: number }>>("/api/model/info"),

  getModelMetrics: () => request<ApiResponse<{
    accuracy: number;
    macro_f1: number;
    weighted_f1: number;
    confusion_matrix: number[][];
    class_names: string[];
  }>>("/api/model/metrics"),

  uploadPcap: async (file: File): Promise<ApiResponse<{ task_id: string; results: DetectionResult[] }>> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/api/detect/pcap`, { method: "POST", body: form });
    return res.json() as Promise<ApiResponse<{ task_id: string; results: DetectionResult[] }>>;
  },

  post: <T>(path: string, body?: unknown) =>
    request<ApiResponse<T>>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  explainAlert: (alertId: string) =>
    request<{
      shap_values: Array<{ feature: string; value: number; importance: number }>;
      attention: Array<{ layer: number; weights: number[][][] }>;
      prediction: string;
      confidence: number;
    }>(`/api/alerts/${alertId}/explain`),
};
