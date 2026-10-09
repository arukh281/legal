import type { components } from "./schema";

export type HealthResponse = components["schemas"]["HealthResponse"];

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

export interface ClaimSupport {
  anchor_id: string;
  quote: string;
  span?: [number, number];
  support_type?: string;
}

export interface ClaimItem {
  claim_id: string;
  text: string;
  claim_type: string;
  support: ClaimSupport[];
  verification_status: string;
  display_band: string;
  reason_codes: string[];
}

export interface ContrarySweep {
  status: string;
  notes: string;
}

export interface DegradationItem {
  kind: string;
  detail: string;
}

export interface ResearchQueryResponse {
  query_id: string;
  text: string;
  summary: string;
  in_corpus: boolean;
  claims: ClaimItem[];
  contrary_sweep: ContrarySweep;
  law_current_to: string;
  degradations: DegradationItem[];
  verification_gate: string;
  created_at: string;
}

export interface AnchorSourceResponse {
  anchor_id: string;
  work_id: string;
  fragment: string;
  number_as_printed: string | null;
  node_type: string;
  text: string;
  ocr_conf: number | null;
  title: string | null;
  court_id: string | null;
  decision_date: string | null;
}

export interface DocumentParagraphItem {
  anchor_id: string;
  fragment: string;
  number_as_printed: string | null;
  node_type: string;
  text: string;
  ocr_conf: number | null;
}

export interface DocumentSourceResponse {
  work_id: string;
  title: string | null;
  court_id: string | null;
  decision_date: string | null;
  status: string;
  paragraphs: DocumentParagraphItem[];
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function executeResearchQuery(
  text: string,
  mode: string = "STANDARD",
  asOfLegalDate?: string,
): Promise<ResearchQueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/research/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      text,
      mode,
      as_of_legal_date: asOfLegalDate,
    }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Research query failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchAnchorSource(anchorId: string): Promise<AnchorSourceResponse> {
  const url = `${API_BASE_URL}/api/research/documents/anchor?anchor_id=${encodeURIComponent(anchorId)}`;
  const response = await fetch(url, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch anchor source: ${response.status}`);
  }
  return response.json();
}

export async function fetchDocumentSource(workId: string): Promise<DocumentSourceResponse> {
  const response = await fetch(`${API_BASE_URL}/api/research/documents/${encodeURIComponent(workId)}/source`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch document source: ${response.status}`);
  }
  return response.json();
}
