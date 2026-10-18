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
  summary_status: string;
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

export interface DevLoginResponse {
  status: string;
  user_id: string;
  email: string;
  tenant_id: string;
  firm_role: string;
}

export async function devLogin(email: string = "partner.lawyer@firm.in"): Promise<DevLoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/dev-login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Dev login failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

// ==============================================================================
// Workspace Types (from OpenAPI schema)
// ==============================================================================

export type ClientResponse = components["schemas"]["ClientResponse"];
export type ClientCreateRequest = components["schemas"]["ClientCreateRequest"];
export type ClientUpdateRequest = components["schemas"]["ClientUpdateRequest"];
export type ClientDetailResponse = components["schemas"]["ClientDetailResponse"];
export type MatterSummaryResponse = components["schemas"]["MatterSummaryResponse"];
export type MatterCreateRequest = components["schemas"]["MatterCreateRequest"];
export type MatterDetailResponse = components["schemas"]["MatterDetailResponse"];
export type MatterUpdateRequest = components["schemas"]["MatterUpdateRequest"];
export type CaseLinkResponse = components["schemas"]["CaseLinkResponse"];
export type CaseLinkCreateRequest = components["schemas"]["CaseLinkCreateRequest"];
export type PdocResponse = components["schemas"]["PdocResponse"];
export type PdocVersionResponse = components["schemas"]["PdocVersionResponse"];
export type ParagraphViewResponse = components["schemas"]["ParagraphViewResponse"];
export type PrivateAnchorItem = components["schemas"]["PrivateAnchorItem"];

// ==============================================================================
// Clients & Matters API
// ==============================================================================

export async function fetchClients(): Promise<ClientResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/clients`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch clients (${response.status})`);
  }
  return response.json();
}

export async function createClient(data: ClientCreateRequest): Promise<ClientResponse> {
  const response = await fetch(`${API_BASE_URL}/api/clients`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create client (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchClient(clientId: string): Promise<ClientDetailResponse> {
  const response = await fetch(`${API_BASE_URL}/api/clients/${encodeURIComponent(clientId)}`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch client (${response.status})`);
  }
  return response.json();
}

export async function updateClient(clientId: string, data: ClientUpdateRequest): Promise<ClientResponse> {
  const response = await fetch(`${API_BASE_URL}/api/clients/${encodeURIComponent(clientId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update client (${response.status})`);
  }
  return response.json();
}

export async function archiveClient(clientId: string): Promise<ClientResponse> {
  const response = await fetch(`${API_BASE_URL}/api/clients/${encodeURIComponent(clientId)}/archive`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to archive client (${response.status})`);
  }
  return response.json();
}

export async function fetchAllMatters(): Promise<MatterSummaryResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/matters`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch matters (${response.status})`);
  }
  return response.json();
}

export async function fetchClientMatters(clientId: string): Promise<MatterSummaryResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/clients/${encodeURIComponent(clientId)}/matters`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch client matters (${response.status})`);
  }
  return response.json();
}

export async function createMatter(data: MatterCreateRequest): Promise<MatterSummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/matters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create matter (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchMatter(matterId: string): Promise<MatterDetailResponse> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch matter (${response.status})`);
  }
  return response.json();
}

export async function updateMatter(matterId: string, data: MatterUpdateRequest): Promise<MatterSummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update matter (${response.status})`);
  }
  return response.json();
}

export async function closeMatter(matterId: string): Promise<MatterSummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/close`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to close matter (${response.status})`);
  }
  return response.json();
}

export async function fetchCaseLinks(matterId: string): Promise<CaseLinkResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/case-links`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch case links (${response.status})`);
  }
  return response.json();
}

export async function addCaseLink(matterId: string, data: CaseLinkCreateRequest): Promise<CaseLinkResponse> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/case-links`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to add case link (${response.status})`);
  }
  return response.json();
}

export async function removeCaseLink(matterId: string, scheme: string, valueNormalized: string): Promise<void> {
  const url = `${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/case-links?scheme=${encodeURIComponent(scheme)}&value_normalized=${encodeURIComponent(valueNormalized)}`;
  const response = await fetch(url, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to remove case link (${response.status})`);
  }
}

// ==============================================================================
// Document Vault API
// ==============================================================================

export async function uploadDocument(matterId: string, formData: FormData): Promise<PdocResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/documents/upload`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Upload failed (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchMatterDocuments(matterId: string): Promise<PdocResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/documents`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch documents (${response.status})`);
  }
  return response.json();
}

export async function fetchDocumentVersions(pdocId: string): Promise<PdocVersionResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${encodeURIComponent(pdocId)}/versions`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch document versions (${response.status})`);
  }
  return response.json();
}

export async function fetchDocumentParagraphs(pdocId: string, pver?: string): Promise<ParagraphViewResponse> {
  const url = pver
    ? `${API_BASE_URL}/api/documents/${encodeURIComponent(pdocId)}/paragraphs?pver=${encodeURIComponent(pver)}`
    : `${API_BASE_URL}/api/documents/${encodeURIComponent(pdocId)}/paragraphs`;
  const response = await fetch(url, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch document paragraphs (${response.status})`);
  }
  return response.json();
}

export function getDocumentDownloadUrl(pdocId: string, pver?: string): string {
  return pver
    ? `${API_BASE_URL}/api/documents/${encodeURIComponent(pdocId)}/download?pver=${encodeURIComponent(pver)}`
    : `${API_BASE_URL}/api/documents/${encodeURIComponent(pdocId)}/download`;
}

// ==============================================================================
// R2: Hearings, Dates, Candidates, Timeline & Today API
// ==============================================================================

export interface HearingResponse {
  hearing_id: string;
  matter_id: string;
  date: string;
  court_no: string | null;
  item_no: string | null;
  bench: string | null;
  purpose: string | null;
  source: string;
  source_ref: string | null;
  status: string;
  outcome: string | null;
  entered_by: string;
  observed_at: string | null;
  court_or_forum: string | null;
}

export interface HearingCreateRequest {
  date: string;
  court_no?: string | null;
  item_no?: string | null;
  bench?: string | null;
  purpose?: string | null;
}

export interface HearingOutcomeRequest {
  outcome: string;
  status?: string;
  next_date?: string | null;
  next_purpose?: string | null;
}

export interface DeadlineResponse {
  deadline_id: string;
  matter_id: string;
  rule_id: string | null;
  label: string;
  kind: string;
  due_on: string;
  lifecycle: string;
  owner: string | null;
  source_note: string;
  created_at: string;
}

export interface DeadlineCreateRequest {
  label: string;
  due_on: string;
  owner?: string | null;
  rule_id?: string | null;
}

export interface CaseCandidateResponse {
  candidate_id: string;
  matter_id: string;
  kind: string;
  source: string;
  source_ref: string;
  case_number_raw: string;
  list_date: string | null;
  bench: string | null;
  normalized_case_no: string | null;
  details: Record<string, any>;
  status: string;
  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
}

export interface CourtOrderResponse {
  matter_id: string;
  public_id: string;
  match_key: string;
  decision_date: string | null;
  bench: string | null;
  kind: string;
  source_ref: string;
  uncertified_badge: boolean;
  source_viewer_url: string;
}

export interface TimelineItemResponse {
  id: string;
  date: string;
  item_type: string;
  title: string;
  subtitle: string | null;
  status: string | null;
  metadata: Record<string, any>;
}

export interface TodayHearingItem {
  hearing_id: string;
  matter_id: string;
  matter_title: string;
  client_id: string | null;
  court_or_forum: string | null;
  court_no: string | null;
  item_no: string | null;
  bench: string | null;
  purpose: string | null;
  status: string;
  date: string;
}

export interface TodayDeadlineItem {
  deadline_id: string;
  matter_id: string;
  matter_title: string;
  label: string;
  due_on: string;
  lifecycle: string;
  source_note: string;
  is_overdue: boolean;
}

export interface TodayResponse {
  today_date: string;
  today_hearings: TodayHearingItem[];
  tomorrow_hearings: TodayHearingItem[];
  this_week_hearings: TodayHearingItem[];
  this_week_deadlines: TodayDeadlineItem[];
  pending_candidates: CaseCandidateResponse[];
  recent_orders: CourtOrderResponse[];
  total_active_matters: number;
}

export async function fetchToday(): Promise<TodayResponse> {
  const response = await fetch(`${API_BASE_URL}/api/today`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch Today dashboard (${response.status})`);
  }
  return response.json();
}

export async function fetchMatterHearings(matterId: string): Promise<HearingResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/hearings`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch hearings (${response.status})`);
  }
  return response.json();
}

export async function createMatterHearing(matterId: string, data: HearingCreateRequest): Promise<HearingResponse> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/hearings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Failed to create hearing (${response.status}): ${err}`);
  }
  return response.json();
}

export async function recordHearingOutcome(hearingId: string, data: HearingOutcomeRequest): Promise<HearingResponse> {
  const response = await fetch(`${API_BASE_URL}/api/hearings/${encodeURIComponent(hearingId)}/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Failed to record outcome (${response.status}): ${err}`);
  }
  return response.json();
}

export async function fetchMatterDeadlines(matterId: string): Promise<DeadlineResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/deadlines`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch deadlines (${response.status})`);
  }
  return response.json();
}

export async function createMatterDeadline(matterId: string, data: DeadlineCreateRequest): Promise<DeadlineResponse> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/deadlines`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Failed to create deadline (${response.status}): ${err}`);
  }
  return response.json();
}

export async function updateDeadlineLifecycle(deadlineId: string, lifecycle: string): Promise<DeadlineResponse> {
  const response = await fetch(`${API_BASE_URL}/api/deadlines/${encodeURIComponent(deadlineId)}/lifecycle`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ lifecycle }),
  });
  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Failed to update deadline lifecycle (${response.status}): ${err}`);
  }
  return response.json();
}

export async function fetchCandidates(matterId?: string): Promise<CaseCandidateResponse[]> {
  const url = matterId
    ? `${API_BASE_URL}/api/candidates?matter_id=${encodeURIComponent(matterId)}`
    : `${API_BASE_URL}/api/candidates`;
  const response = await fetch(url, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch candidates (${response.status})`);
  }
  return response.json();
}

export async function confirmCandidate(candidateId: string): Promise<{ status: string; candidate_id: string; resolved: string }> {
  const response = await fetch(`${API_BASE_URL}/api/candidates/${encodeURIComponent(candidateId)}/confirm`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to confirm candidate (${response.status})`);
  }
  return response.json();
}

export async function dismissCandidate(candidateId: string): Promise<{ status: string; candidate_id: string; resolved: string }> {
  const response = await fetch(`${API_BASE_URL}/api/candidates/${encodeURIComponent(candidateId)}/dismiss`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to dismiss candidate (${response.status})`);
  }
  return response.json();
}

export async function fetchMatterOrders(matterId: string): Promise<CourtOrderResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/orders`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch court orders (${response.status})`);
  }
  return response.json();
}

export async function fetchMatterTimeline(matterId: string): Promise<TimelineItemResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/timeline`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch matter timeline (${response.status})`);
  }
  return response.json();
}

export function getMatterCalendarExportUrl(matterId: string): string {
  return `${API_BASE_URL}/api/matters/${encodeURIComponent(matterId)}/calendar/export`;
}

export function getFirmCalendarExportUrl(): string {
  return `${API_BASE_URL}/api/calendar/export`;
}

