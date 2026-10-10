import React, { useState } from "react";
import { executeResearchQuery, type ClaimItem, type ResearchQueryResponse } from "../api/client";
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

  // Source Viewer state
  const [activeViewer, setActiveViewer] = useState<{
    anchorId: string;
    workId: string;
    quote?: string;
  } | null>(null);

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
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
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
        <p style={{ color: "var(--text-secondary)", fontSize: "14px", lineHeight: "1.5" }}>
          Ground legal questions in statutory provisions and primary court orders. Every proposition resolves to a verified
          corpus anchor with exact quotes and click-to-source inspection.
        </p>
      </div>

      {/* Demo Queries Selection Cards */}
      <div style={{ marginBottom: "24px" }}>
        <div
          style={{
            fontSize: "12px",
            fontWeight: "600",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "var(--text-muted)",
            marginBottom: "10px",
          }}
        >
          Curated Demo Questions (Exit Check Golden Test Suite)
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "12px",
          }}
        >
          {PRELOADED_QUERIES.map((pq) => (
            <div
              key={pq.id}
              onClick={() => handleSelectPreloaded(pq)}
              style={{
                backgroundColor: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "10px",
                padding: "14px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "#3b82f6";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-primary)" }}>{pq.title}</span>
                <span
                  style={{
                    fontSize: "10px",
                    fontWeight: "600",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    backgroundColor: pq.id === "out_of_corpus" ? "rgba(239, 68, 68, 0.2)" : "rgba(16, 185, 129, 0.2)",
                    color: pq.id === "out_of_corpus" ? "#f87171" : "#34d399",
                  }}
                >
                  {pq.tag}
                </span>
              </div>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.4" }}>{pq.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Query Search Bar */}
      <div
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "16px",
          marginBottom: "32px",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.2)",
        }}
      >
        <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "12px" }}>
          <input
            type="text"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleRunQuery(queryText);
            }}
            placeholder="Ask a corporate-law question (e.g. scope of enquiry under Section 7 IBC...)"
            style={{
              flex: 1,
              backgroundColor: "var(--bg-primary)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "12px 16px",
              color: "var(--text-primary)",
              fontSize: "14px",
              outline: "none",
            }}
          />
          <button
            onClick={() => handleRunQuery(queryText)}
            disabled={loading || !queryText.trim()}
            style={{
              backgroundColor: loading || !queryText.trim() ? "var(--bg-tertiary)" : "var(--accent)",
              color: "#ffffff",
              padding: "12px 24px",
              borderRadius: "8px",
              fontSize: "14px",
              fontWeight: "600",
              cursor: loading || !queryText.trim() ? "not-allowed" : "pointer",
              transition: "all 0.15s ease",
            }}
          >
            {loading ? "Searching..." : "Research"}
          </button>
        </div>

        {/* Mode Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "12px", color: "var(--text-secondary)" }}>
          <span>Search Depth:</span>
          {(["QUICK", "STANDARD", "DEEP"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              style={{
                padding: "4px 10px",
                borderRadius: "6px",
                fontSize: "12px",
                fontWeight: mode === m ? "600" : "400",
                backgroundColor: mode === m ? "rgba(59, 130, 246, 0.2)" : "transparent",
                color: mode === m ? "#60a5fa" : "var(--text-muted)",
                border: mode === m ? "1px solid rgba(59, 130, 246, 0.4)" : "1px solid transparent",
              }}
            >
              {m}
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
                      borderRadius: "10px",
                      padding: "18px 20px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: "700",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor: "rgba(99, 102, 241, 0.15)",
                            color: "#818cf8",
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
                            backgroundColor: "rgba(16, 185, 129, 0.15)",
                            color: "#34d399",
                            border: "1px solid rgba(16, 185, 129, 0.3)",
                          }}
                        >
                          {claim.display_band}
                        </span>
                      </div>
                      <span style={{ fontSize: "11px", fontFamily: "monospace", color: "var(--text-muted)" }}>
                        {claim.claim_id}
                      </span>
                    </div>

                    <p style={{ fontSize: "14px", color: "var(--text-primary)", lineHeight: "1.5", marginBottom: "12px" }}>
                      {claim.text}
                    </p>

                    {/* Support & Citation Pinpoint */}
                    {claim.support.map((supp, sIdx) => {
                      const workId = extractWorkIdFromAnchor(supp.anchor_id);
                      return (
                        <div
                          key={sIdx}
                          style={{
                            backgroundColor: "var(--bg-primary)",
                            border: "1px solid var(--border)",
                            borderRadius: "8px",
                            padding: "12px 14px",
                            marginTop: "8px",
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            gap: "16px",
                          }}
                        >
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: "12px", fontFamily: "monospace", color: "#60a5fa", marginBottom: "4px" }}>
                              📌 {supp.anchor_id}
                            </div>
                            <div
                              style={{
                                fontSize: "13px",
                                fontStyle: "italic",
                                color: "var(--text-secondary)",
                                lineHeight: "1.4",
                              }}
                            >
                              "{supp.quote}"
                            </div>
                          </div>
                          <button
                            onClick={() =>
                              setActiveViewer({
                                anchorId: supp.anchor_id,
                                workId: workId,
                                quote: supp.quote,
                              })
                            }
                            style={{
                              padding: "6px 12px",
                              borderRadius: "6px",
                              backgroundColor: "rgba(59, 130, 246, 0.15)",
                              color: "#60a5fa",
                              fontSize: "12px",
                              fontWeight: "600",
                              border: "1px solid rgba(59, 130, 246, 0.3)",
                              cursor: "pointer",
                              whiteSpace: "nowrap",
                              transition: "all 0.15s ease",
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.backgroundColor = "rgba(59, 130, 246, 0.3)";
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.backgroundColor = "rgba(59, 130, 246, 0.15)";
                            }}
                          >
                            Inspect in Source →
                          </button>
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
