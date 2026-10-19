/**
 * Utility functions for date, string, and status formatting.
 * Enforces plain words, sentence case, and readable dates ("21 Oct 2026").
 */

const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

/**
 * Formats an ISO date string (e.g. "2026-10-21" or "2026-10-21T10:00:00Z") to "21 Oct 2026".
 * If invalid or empty, returns an empty string or the fallback.
 */
export function formatDate(dateStr: string | null | undefined, fallback = "—"): string {
  if (!dateStr) return fallback;
  try {
    const raw = dateStr.includes("T") ? dateStr.split("T")[0] : dateStr;
    const parts = raw.split("-");
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const monthIdx = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      if (!isNaN(year) && !isNaN(monthIdx) && !isNaN(day) && monthIdx >= 0 && monthIdx < 12) {
        return `${day} ${MONTH_NAMES[monthIdx]} ${year}`;
      }
    }
    const d = new Date(dateStr);
    if (!isNaN(d.getTime())) {
      return `${d.getDate()} ${MONTH_NAMES[d.getMonth()]} ${d.getFullYear()}`;
    }
  } catch {
    // fallback
  }
  return fallback;
}

/**
 * Formats an ISO time string or date string to readable time, e.g. "10:30 AM".
 */
export function formatTime(timeStr: string | null | undefined): string {
  if (!timeStr) return "";
  try {
    if (timeStr.includes("T")) {
      const d = new Date(timeStr);
      if (!isNaN(d.getTime())) {
        return d.toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit", hour12: true });
      }
    }
  } catch {
    // fallback
  }
  return timeStr;
}

/**
 * Converts internal codes and scream-case strings to clean sentence-case plain words.
 * E.g. NOT_REACHED -> "Not reached", PASS_OVER -> "Passed over", IN_PROGRESS -> "In progress"
 */
export function formatStatus(code: string | null | undefined): string {
  if (!code) return "—";
  const mapped: Record<string, string> = {
    NOT_REACHED: "Not reached",
    PASS_OVER: "Passed over",
    HEARD: "Heard",
    ADJOURNED: "Adjourned",
    LISTED: "Listed",
    DISPOSED: "Disposed",
    PRE_ADMISSION: "Pre-admission",
    PLEADINGS: "Pleadings",
    EVIDENCE: "Evidence",
    ARGUMENTS: "Arguments",
    RESERVED: "Reserved",
    SETTLED: "Settled",
    WITHDRAWN: "Withdrawn",
    CIRP: "CIRP",
    LIQUIDATION: "Liquidation",
    APPEAL: "Appeal",
    CIVIL_APPEAL: "Civil appeal",
    COMPANY_PETITION: "Company petition",
    COMMERCIAL_SUIT: "Commercial suit",
    OPEN: "Open",
    IN_PROGRESS: "In progress",
    DONE: "Done",
    CANCELLED: "Cancelled",
    OVERDUE: "Overdue",
    DUE_SOON: "Due soon",
    ACTIVE: "Active",
    CLOSED: "Closed",
    ARCHIVED: "Archived",
    PENDING: "Pending",
    MANUAL: "Manual",
    SOURCE_CAUSE_LIST: "Cause list",
    COMPANY: "Company",
    INDIVIDUAL: "Individual",
    LLP: "LLP",
    PARTNERSHIP: "Partnership",
    TRUST: "Trust",
    SOCIETY: "Society",
    STATUTORY_BODY: "Statutory body",
    ADMIN: "Admin",
    PARTNER: "Partner",
    ASSOCIATE: "Associate",
    LEAD: "Lead",
    MEMBER: "Member",
    VIEWER: "Viewer",
  };

  if (mapped[code]) {
    return mapped[code];
  }

  // Generic sentence case conversion for words separated by underscores
  const words = code.toLowerCase().split("_");
  if (words.length === 0) return code;
  const sentence = words.join(" ");
  return sentence.charAt(0).toUpperCase() + sentence.slice(1);
}

/**
 * Converts any string into sentence case (first letter capitalized, rest lowercase unless acronym).
 */
export function toSentenceCase(str: string): string {
  if (!str) return "";
  const trimmed = str.trim();
  return trimmed.charAt(0).toUpperCase() + trimmed.slice(1);
}
