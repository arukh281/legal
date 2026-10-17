import React, { useState } from "react";
import {
  devLogin,
  executeResearchQuery,
  type ClaimItem,
  type DevLoginResponse,
  type ResearchQueryResponse,
} from "../api/client";
import { SourceViewer } from "../components/SourceViewer";

interface PreloadedQuery {
  id: string;
  title: string;
  tag: string;
  prompt: string;
  description: string;
}

const PRELOADED_QUERIES: PreloadedQuery[] = [
  {
    id: "s7",
    title: "Section 7 IBC: Debt & Default",
    tag: "NCLT / SC",
    prompt: "What is the scope of enquiry under Section 7 of the IBC for a financial debt and default?",
    description: "Scope of enquiry is strictly confined to verifying financial debt and default existence.",
  },
  {
    id: "s9_10a",
    title: "Section 9 & 10A IBC: Barred Period",
    tag: "NCLT Mumbai",
    prompt: "Can an operational creditor invoke Section 9 for default during the Section 10A period?",
    description: "Operational creditor applications barred for defaults within the Section 10A period.",
  },
  {
    id: "s14_ni",
    title: "Section 14 IBC: NI Act s.138",
    tag: "Supreme Court",
    prompt: "Does moratorium under Section 14 of IBC apply to Section 138 NI Act proceedings?",
    description: "Moratorium applies to corporate debtor quasi-criminal liability under s.138, not personal directors.",
  },
  {
    id: "out_of_corpus",
    title: "Admiralty Act 2017 (Out of Corpus)",
    tag: "Honest Negatives",
    prompt: "What are the rules for maritime salvage under the Admiralty Act 2017?",
    description: "Verifies platform honesty: returns 'not in MVP corpus' rather than hallucinating law.",
  },
];

export const ResearchPage: React.FC = () => {
  const [queryText, setQueryText] = useState<string>("");
  const [mode, setMode] = useState<string>("STANDARD");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResearchQueryResponse | null>(null);
  const [devAuthUser, setDevAuthUser] = useState<DevLoginResponse | null>(null);
  const [devLoggingIn, setDevLoggingIn] = useState<boolean>(false);

  // Source Viewer state
  const [activeViewer, setActiveViewer] = useState<{
    anchorId: string;
    workId: string;
    quote?: string;
  } | null>(null);

  const handleDevLogin = async () => {
    setDevLoggingIn(true);
    setError(null);
    try {
      const resp = await devLogin("partner.lawyer@firm.in");
      setDevAuthUser(resp);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Dev login failed";
      setError(msg);
    } finally {
      setDevLoggingIn(false);
    }
  };

  const handleRunQuery = async (textToRun: string) => {
    if (!textToRun.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await executeResearchQuery(textToRun.trim(), mode);
      setResult(resp);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to execute research query";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPreloaded = (pq: PreloadedQuery) => {
    setQueryText(pq.prompt);
    handleRunQuery(pq.prompt);
  };

  const extractWorkIdFromAnchor = (anchorId: string): string => {
    const parts = anchorId.split("/");
    return parts[0] || anchorId;
  };

  return (
    <div style={{ maxWidth: "1200px", margin: "0 auto", paddingBottom: "60px" }}>
      {/* Page Title & Subtitle */}
      <div style={{ marginBottom: "28px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h2 style={{ fontSize: "28px", fontWeight: "700", letterSpacing: "-0.02em" }}>
              Research Q&A & Citator Pinpoints
            </h2>
            <span
              style={{
                fontSize: "11px",
                padding: "3px 8px",
                borderRadius: "12px",
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                color: "#60a5fa",
                fontWeight: "600",
                border: "1px solid rgba(59, 130, 246, 0.3)",
              }}
            >
              Phase P5 / P6 / P8
            </span>
          </div>

          {/* Dev-only Login Button */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {devAuthUser && (
              <span
                id="dev-auth-status"
                style={{
                  fontSize: "12px",
                  color: "#34d399",
                  fontWeight: "600",
                  backgroundColor: "rgba(16, 185, 129, 0.12)",
                  padding: "4px 8px",
                  borderRadius: "6px",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                }}
              >
                ✓ {devAuthUser.email} ({devAuthUser.firm_role})
              </span>
            )}
            <button
              id="btn-dev-login"
              onClick={handleDevLogin}
              disabled={devLoggingIn}
              style={{
                padding: "8px 16px",
                fontSize: "13px",
                fontWeight: "600",
                borderRadius: "6px",
                backgroundColor: devAuthUser ? "rgba(59, 130, 246, 0.15)" : "var(--accent)",
                color: devAuthUser ? "#60a5fa" : "#ffffff",
                border: devAuthUser ? "1px solid rgba(59, 130, 246, 0.3)" : "none",
                cursor: devLoggingIn ? "not-allowed" : "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {devLoggingIn
                ? "Logging in..."
                : devAuthUser
                  ? "Dev login (Re-auth)"
                  : "Dev login (partner.lawyer@firm.in)"}
            </button>
          </div>
        </div>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px", lineHeight: "1.5" }}>
          Ground legal questions in statutory provisions and primary court orders. Every proposition resolves to a verified
          corpus anchor with exact quotes and click-to-source inspection.
        </p>
      </div>

      {/* Free-Text Question Box */}
      <div
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: "14px",
          padding: "20px",
          marginBottom: "16px",
          boxShadow: "0 4px 24px rgba(0, 0, 0, 0.25)",
        }}
      >
        <div style={{ marginBottom: "12px" }}>
          <textarea
            id="research-query-input"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            onKeyDown={(e) => {
              if ((e.key === "Enter" && (e.metaKey || e.ctrlKey)) || (e.key === "Enter" && !e.shiftKey)) {
                e.preventDefault();
                handleRunQuery(queryText);
              }
            }}
            placeholder="Ask a corporate-law question (e.g. What is the scope of enquiry under Section 7 of the IBC for a financial debt and default?)..."
            rows={3}
            style={{
              width: "100%",
              backgroundColor: "var(--bg-primary)",
              border: "1px solid var(--border)",
              borderRadius: "10px",
              padding: "14px 16px",
              color: "var(--text-primary)",
              fontSize: "15px",
              lineHeight: "1.5",
              fontFamily: "inherit",
              outline: "none",
              resize: "vertical",
              boxSizing: "border-box",
              transition: "border-color 0.15s ease",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "#3b82f6";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "var(--border)";
            }}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          {/* Depth Selector & Keyboard Hint */}
          <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "12px", color: "var(--text-secondary)" }}>
            <span style={{ fontWeight: "600" }}>Depth:</span>
            <div style={{ display: "inline-flex", backgroundColor: "var(--bg-primary)", padding: "2px", borderRadius: "8px", border: "1px solid var(--border)" }}>
              {(["QUICK", "STANDARD", "DEEP"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  style={{
                    padding: "4px 12px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    fontWeight: mode === m ? "600" : "400",
                    backgroundColor: mode === m ? "var(--accent)" : "transparent",
                    color: mode === m ? "#ffffff" : "var(--text-muted)",
                    border: "none",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  {m}
                </button>
              ))}
            </div>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              ↵ Enter to search, Shift+Enter for newline
            </span>
          </div>

          <button
            id="btn-run-research"
            onClick={() => handleRunQuery(queryText)}
            disabled={loading || !queryText.trim()}
            style={{
              backgroundColor: loading || !queryText.trim() ? "var(--bg-tertiary)" : "var(--accent)",
              color: "#ffffff",
              padding: "10px 24px",
              borderRadius: "8px",
              fontSize: "14px",
              fontWeight: "600",
              border: "none",
              cursor: loading || !queryText.trim() ? "not-allowed" : "pointer",
              transition: "all 0.15s ease",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>🔍</span>
            <span>{loading ? "Synthesizing..." : "Research"}</span>
          </button>
        </div>
      </div>

      {/* Suggestion Chips */}
      <div style={{ marginBottom: "28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <span style={{ fontSize: "12px", fontWeight: "600", color: "var(--text-muted)", marginRight: "4px" }}>
            Suggestions:
          </span>
          {PRELOADED_QUERIES.map((pq) => (
            <button
              key={pq.id}
              onClick={() => handleSelectPreloaded(pq)}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "20px",
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                color: "var(--text-secondary)",
                fontSize: "12px",
                fontWeight: "500",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "#3b82f6";
                e.currentTarget.style.color = "#60a5fa";
                e.currentTarget.style.backgroundColor = "rgba(59, 130, 246, 0.08)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.color = "var(--text-secondary)";
                e.currentTarget.style.backgroundColor = "var(--bg-secondary)";
              }}
              title={pq.description}
            >
              <span>⚡</span>
              <span>{pq.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div
          style={{
            padding: "16px",
            borderRadius: "8px",
            backgroundColor: "rgba(239, 68, 68, 0.15)",
            border: "1px solid var(--danger)",
            color: "#fca5a5",
            fontSize: "14px",
            marginBottom: "24px",
          }}
        >
          {error}
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div
          style={{
            padding: "40px",
            textAlign: "center",
            backgroundColor: "var(--bg-secondary)",
            borderRadius: "12px",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
          }}
        >
          <div style={{ fontSize: "16px", fontWeight: "600", marginBottom: "8px" }}>
            Scanning Corpus & Verifying Anchors...
          </div>
          <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
            Executing lexical search against g1 partitions, extracting claims, and enforcing C0–C2 warrant ladders.
          </div>
        </div>
      )}

      {/* Query Results */}
      {!loading && result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Out of corpus banner */}
          {!result.in_corpus && (
            <div
              style={{
                padding: "20px",
                borderRadius: "10px",
                backgroundColor: "rgba(245, 158, 11, 0.1)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
                color: "#fde68a",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: "700", marginBottom: "6px" }}>
                <span>⚠️ Topic Not Found in MVP Corpus</span>
              </div>
              <p style={{ fontSize: "14px", lineHeight: "1.5", color: "#fef3c7" }}>{result.summary}</p>
              <div style={{ marginTop: "10px", fontSize: "12px", color: "#fde68a" }}>
                Antigravity strictly adheres to Non-negotiable #3: we never invent statutes or citations from model weights.
              </div>
            </div>
          )}

          {/* Narrative Summary Card */}
          {result.in_corpus && (
            <div
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "12px",
                padding: "24px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: "700",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    color: "var(--text-muted)",
                  }}
                >
                  Executive Synthesis
                </span>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  {result.summary_status && (
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: "700",
                        padding: "3px 8px",
                        borderRadius: "6px",
                        backgroundColor: "rgba(245, 158, 11, 0.15)",
                        color: "#fbbf24",
                        textTransform: "uppercase",
                        letterSpacing: "0.03em",
                      }}
                    >
                      {result.summary_status}
                    </span>
                  )}
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: "700",
                      padding: "3px 8px",
                      borderRadius: "6px",
                      backgroundColor:
                        result.verification_gate === "PASS"
                          ? "rgba(16, 185, 129, 0.2)"
                          : result.verification_gate === "PARTIAL"
                            ? "rgba(245, 158, 11, 0.2)"
                            : "rgba(239, 68, 68, 0.2)",
                      color:
                        result.verification_gate === "PASS"
                          ? "#34d399"
                          : result.verification_gate === "PARTIAL"
                            ? "#fbbf24"
                            : "#f87171",
                    }}
                  >
                    GATE: {result.verification_gate}
                  </span>
                </div>
              </div>
              <p style={{ fontSize: "15px", lineHeight: "1.7", color: "var(--text-primary)" }}>{result.summary}</p>
            </div>
          )}

          {/* Verified Claims List */}
          {result.claims.length > 0 && (
            <div>
              <div
                style={{
                  fontSize: "14px",
                  fontWeight: "700",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: "var(--text-secondary)",
                  marginBottom: "12px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <span>Verified Legal Propositions</span>
                <span style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: "400" }}>
                  ({result.claims.length} claims pinned to primary anchors)
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {result.claims.map((claim: ClaimItem) => (
                  <div
                    key={claim.claim_id}
                    style={{
                      backgroundColor: "var(--bg-secondary)",
                      border: "1px solid var(--border)",
                      borderLeft:
                        claim.display_band.includes("WITHHELD")
                          ? "4px solid #ef4444"
                          : claim.display_band.includes("CHECK") || claim.display_band.includes("CAUTION")
                            ? "4px solid #f59e0b"
                            : "4px solid #10b981",
                      borderRadius: "10px",
                      padding: "18px 20px",
                      boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: "700",
                            padding: "2px 8px",
                            borderRadius: "4px",
                            backgroundColor: "rgba(99, 102, 241, 0.15)",
                            color: "#818cf8",
                            letterSpacing: "0.03em",
                          }}
                        >
                          {claim.claim_type}
                        </span>
                        {/* Display Band (Amendment #1) */}
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: "600",
                            padding: "2px 8px",
                            borderRadius: "4px",
                            backgroundColor:
                              claim.display_band.includes("VERIFIED") || claim.display_band.includes("verified")
                                ? "rgba(16, 185, 129, 0.15)"
                                : "rgba(245, 158, 11, 0.15)",
                            color:
                              claim.display_band.includes("VERIFIED") || claim.display_band.includes("verified")
                                ? "#34d399"
                                : "#fbbf24",
                            border:
                              claim.display_band.includes("VERIFIED") || claim.display_band.includes("verified")
                                ? "1px solid rgba(16, 185, 129, 0.3)"
                                : "1px solid rgba(245, 158, 11, 0.3)",
                          }}
                        >
                          {claim.display_band}
                        </span>
                      </div>
                      <span style={{ fontSize: "11px", fontFamily: "monospace", color: "var(--text-muted)" }}>
                        {claim.claim_id}
                      </span>
                    </div>

                    <p style={{ fontSize: "15px", color: "var(--text-primary)", lineHeight: "1.6", marginBottom: "14px", fontWeight: "500" }}>
                      {claim.text}
                    </p>

                    {/* Support & Citation Pinpoints (Clean Chips Pass) */}
                    {claim.support.map((supp, sIdx) => {
                      const workId = extractWorkIdFromAnchor(supp.anchor_id);
                      return (
                        <div
                          key={sIdx}
                          style={{
                            marginTop: "10px",
                            backgroundColor: "var(--bg-primary)",
                            border: "1px solid var(--border)",
                            borderRadius: "8px",
                            padding: "12px 14px",
                          }}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
                            {/* Citation Chip */}
                            <button
                              onClick={() =>
                                setActiveViewer({
                                  anchorId: supp.anchor_id,
                                  workId: workId,
                                  quote: supp.quote,
                                })
                              }
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "6px",
                                padding: "4px 10px",
                                borderRadius: "6px",
                                backgroundColor: "rgba(59, 130, 246, 0.12)",
                                border: "1px solid rgba(59, 130, 246, 0.3)",
                                color: "#60a5fa",
                                fontSize: "12px",
                                fontWeight: "600",
                                fontFamily: "monospace",
                                cursor: "pointer",
                                transition: "all 0.15s ease",
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor = "rgba(59, 130, 246, 0.25)";
                                e.currentTarget.style.borderColor = "#3b82f6";
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = "rgba(59, 130, 246, 0.12)";
                                e.currentTarget.style.borderColor = "rgba(59, 130, 246, 0.3)";
                              }}
                              title="Click to inspect pinpoint in primary source"
                            >
                              <span>📍</span>
                              <span>{supp.anchor_id}</span>
                              <span style={{ fontSize: "11px", opacity: 0.8 }}>↗</span>
                            </button>

                            <button
                              onClick={() =>
                                setActiveViewer({
                                  anchorId: supp.anchor_id,
                                  workId: workId,
                                  quote: supp.quote,
                                })
                              }
                              style={{
                                fontSize: "12px",
                                color: "var(--text-muted)",
                                backgroundColor: "transparent",
                                border: "none",
                                cursor: "pointer",
                                textDecoration: "underline",
                              }}
                            >
                              Inspect Source Document
                            </button>
                          </div>

                          {/* Quoted Excerpt */}
                          <blockquote
                            style={{
                              margin: "8px 0 0 0",
                              padding: "6px 12px",
                              borderLeft: "2px solid rgba(59, 130, 246, 0.4)",
                              backgroundColor: "rgba(0, 0, 0, 0.15)",
                              borderRadius: "0 6px 6px 0",
                              fontSize: "13px",
                              fontStyle: "italic",
                              color: "var(--text-secondary)",
                              lineHeight: "1.5",
                            }}
                          >
                            "{supp.quote}"
                          </blockquote>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Contrary Authority Sweep Card (Amendment #2) */}
          <div
            style={{
              backgroundColor: "var(--bg-secondary)",
              border: "1px solid var(--border)",
              borderRadius: "10px",
              padding: "16px 20px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: "700",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  color: "var(--text-muted)",
                }}
              >
                Contrary Authority Sweep
              </span>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "700",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(245, 158, 11, 0.15)",
                  color: "#fbbf24",
                  border: "1px solid rgba(245, 158, 11, 0.3)",
                }}
              >
                STATUS: {result.contrary_sweep.status}
              </span>
            </div>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.4" }}>
              {result.contrary_sweep.notes}
            </p>
            <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
              Comprehensive adverse citator treatment graphs and doctrine rules will be fully verified in Phase P3/P4 (Session S09).
            </p>
          </div>

          {/* Transparency & Lineage Footer (Amendment #7) */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px 16px",
              backgroundColor: "var(--bg-primary)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              fontSize: "12px",
              color: "var(--text-muted)",
            }}
          >
            <div>
              Law current to:{" "}
              <strong style={{ color: "var(--text-primary)" }}>{result.law_current_to}</strong> (dynamic corpus capture date)
            </div>
            <div>
              {result.degradations.length > 0 ? (
                <span style={{ color: "#fbbf24" }}>
                  ⚠️ Notice: {result.degradations[0].kind} ({result.degradations[0].detail})
                </span>
              ) : (
                <span style={{ color: "#34d399" }}>✓ Fully Operational (No degradations)</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Slide-over Source Viewer Modal */}
      {activeViewer && (
        <SourceViewer
          anchorId={activeViewer.anchorId}
          workId={activeViewer.workId}
          highlightQuote={activeViewer.quote}
          onClose={() => setActiveViewer(null)}
        />
      )}
    </div>
  );
};
