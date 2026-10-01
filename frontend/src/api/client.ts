import type { components } from "./schema";

export type HealthResponse = components["schemas"]["HealthResponse"];

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
  }
  return response.json();
}
