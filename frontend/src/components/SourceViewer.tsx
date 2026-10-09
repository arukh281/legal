import React, { useEffect, useRef, useState } from "react";
import { fetchDocumentSource, type DocumentSourceResponse } from "../api/client";

interface SourceViewerProps {
  anchorId: string;
  workId: string;
  highlightQuote?: string;
  onClose: () => void;
}

export const SourceViewer: React.FC<SourceViewerProps> = ({
  anchorId,
  workId,
  highlightQuote,
  onClose,
}) => {
  const [data, setData] = useState<DocumentSourceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const targetRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchDocumentSource(workId)
      .then((doc) => {
        if (isMounted) {
          setData(doc);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load document source.");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [workId]);

  // Auto-scroll to target anchor paragraph once loaded
  useEffect(() => {
    if (!loading && targetRef.current) {
      setTimeout(() => {
        targetRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 100);
    }
  }, [loading, anchorId]);

  // Handle ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Helper to render text with quote highlighted
  const renderParagraphContent = (text: string, isTarget: boolean) => {
    if (!isTarget || !highlightQuote) {
      return <span>{text}</span>;
    }

    const cleanQuote = highlightQuote.trim();
    const idx = text.toLowerCase().indexOf(cleanQuote.toLowerCase());
    if (idx === -1) {
      return <span>{text}</span>;
    }

    const before = text.slice(0, idx);
    const matched = text.slice(idx, idx + cleanQuote.length);
    const after = text.slice(idx + cleanQuote.length);

    return (
      <span>
        {before}
        <mark
          style={{
            backgroundColor: "#fef08a",
            color: "#854d0e",
            fontWeight: "600",
            padding: "2px 4px",
            borderRadius: "3px",
          }}
        >
          {matched}
        </mark>
        {after}
      </span>
    );
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(4px)",
        zIndex: 50,
        display: "flex",
        justifyContent: "flex-end",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "800px",
          height: "100%",
          backgroundColor: "var(--bg-primary)",
          borderLeft: "1px solid var(--border)",
          boxShadow: "-10px 0 25px rgba(0, 0, 0, 0.5)",
          display: "flex",
          flexDirection: "column",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid var(--border)",
            backgroundColor: "var(--bg-secondary)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div style={{ flex: 1, paddingRight: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "700",
                  textTransform: "uppercase",
                  padding: "2px 8px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(59, 130, 246, 0.2)",
                  color: "#60a5fa",
                  letterSpacing: "0.05em",
                }}
              >
                Primary Authority
              </span>
              {data?.court_id && (
                <span
                  style={{
                    fontSize: "12px",
                    color: "var(--text-secondary)",
                    fontFamily: "monospace",
                  }}
                >
                  {data.court_id}
                </span>
              )}
              {data?.decision_date && (
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  • {data.decision_date}
                </span>
              )}
            </div>
            <h3
              style={{
                fontSize: "16px",
                fontWeight: "600",
                color: "var(--text-primary)",
                lineHeight: "1.4",
              }}
            >
              {data?.title || workId}
            </h3>
            <div style={{ marginTop: "6px", fontSize: "12px", color: "var(--text-muted)" }}>
              Pinpoint Anchor: <span style={{ fontFamily: "monospace", color: "#93c5fd" }}>{anchorId}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              backgroundColor: "var(--bg-tertiary)",
              color: "var(--text-secondary)",
              fontSize: "14px",
              fontWeight: "500",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            ✕ Close
          </button>
        </div>

        {/* Content Body */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
          }}
        >
          {loading && (
            <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-secondary)" }}>
              <p style={{ fontSize: "14px" }}>Loading verified primary text...</p>
            </div>
          )}

          {error && (
            <div
              style={{
                padding: "16px",
                borderRadius: "8px",
                backgroundColor: "rgba(239, 68, 68, 0.15)",
                border: "1px solid var(--danger)",
                color: "#fca5a5",
                fontSize: "14px",
              }}
            >
              {error}
            </div>
          )}

          {!loading && data && data.paragraphs.length === 0 && (
            <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-muted)" }}>
              No text nodes recorded for this work.
            </div>
          )}

          {!loading &&
            data &&
            data.paragraphs.map((p) => {
              const isTarget = p.anchor_id === anchorId;
              return (
                <div
                  key={p.anchor_id}
                  ref={isTarget ? targetRef : undefined}
                  style={{
                    padding: "16px",
                    borderRadius: "8px",
                    border: isTarget ? "2px solid #3b82f6" : "1px solid var(--border)",
                    backgroundColor: isTarget ? "rgba(30, 41, 59, 0.8)" : "var(--bg-secondary)",
                    boxShadow: isTarget ? "0 0 20px rgba(59, 130, 246, 0.25)" : "none",
                    transition: "all 0.2s ease",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "8px",
                      fontSize: "12px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span
                        style={{
                          fontWeight: "700",
                          color: isTarget ? "#60a5fa" : "var(--text-secondary)",
                          fontFamily: "monospace",
                        }}
                      >
                        {p.number_as_printed ? `¶ ${p.number_as_printed}` : `#${p.fragment}`}
                      </span>
                      {isTarget && (
                        <span
                          style={{
                            fontSize: "10px",
                            backgroundColor: "#3b82f6",
                            color: "#ffffff",
                            padding: "1px 6px",
                            borderRadius: "10px",
                            fontWeight: "600",
                          }}
                        >
                          CITED PINPOINT
                        </span>
                      )}
                    </div>
                    {p.ocr_conf !== null && (
                      <span
                        style={{
                          fontSize: "11px",
                          color: p.ocr_conf >= 0.9 ? "#34d399" : "#fbbf24",
                        }}
                      >
                        OCR {(p.ocr_conf * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <p
                    style={{
                      fontSize: "14px",
                      lineHeight: "1.65",
                      color: "var(--text-primary)",
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {renderParagraphContent(p.text, isTarget)}
                  </p>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
};
