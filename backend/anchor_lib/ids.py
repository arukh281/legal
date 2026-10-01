"""Identifier minting, prefix registry, and validation for lawyer_brain.

Normative sources:
- docs/01_master_architecture.md §5.2 (ID prefix registry, form rules)
- docs/01a_spine_decision_record.md (D12, D16, D19.3, D20.5, D21.5, D21.16, D22.1)
- docs/mvp/03_data_model_and_contracts.md §1 item 2

Rules:
1. Entity IDs are prefix_ + 26-character Crockford ULID (monotonic within a millisecond).
2. Curated reference registries may use stable upper-snake mnemonics after the prefix.
   These are strictly crt_, ent_, rul_, and ter_ (01 §5.2 line 482).
3. Works are NEVER mnemonic (wrk_ACT_NI is invalid; 01 §5.2 line 483).
4. IDs are ASCII-only.
5. Content addresses use sha256:<64-char-lowercase-hex>.
"""

from __future__ import annotations

import re
import secrets
import threading
import time
from dataclasses import dataclass

# Crockford's Base32 character set (excludes I, L, O, U)
CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CROCKFORD_DECODE_MAP = {char: idx for idx, char in enumerate(CROCKFORD_ALPHABET)}

# Mnemonic allowed prefixes per docs/01_master_architecture.md §5.2 line 482:
# "Curated reference registries may use stable upper-snake mnemonics after the prefix.
#  These are crt_, ent_, rul_ and ter_, e.g. crt_IN_HC_ALL_LKO, ent_GOV_IN_UP, rul_IN_PREC_07."
MNEMONIC_PREFIXES: frozenset[str] = frozenset({"crt", "ent", "rul", "ter"})

# Prefix registry as specified in docs/01_master_architecture.md §5.2
# and updated by decisions D12, D16, D19.3, D20.5, D21.5, D21.16, D22.1.
DOC_PREFIX_REGISTRY: frozenset[str] = frozenset(
    {
        # Public Legal Corpus (PLC)
        "wrk",  # Work (P1)
        "cas",  # Case / proceeding (P1)
        "man",  # Manifestation (P1)
        "par",  # Parse run (P1, D20.5 replaces prs_)
        "cap",  # Capture (P0)
        "crun",  # Crawl run (P0)
        "acq",  # Acquisition request (P0)
        "lp",  # Legal profile (P0)
        "cal",  # Court calendar (P0)
        "jex",  # Judgment-expected record (P0, D20.5)
        "cm",  # Citation mention (P1)
        "sm",  # Statute mention (P1)
        "em",  # Entity mention (P1)
        "ai",  # Amendment instruction (P1)
        "cc",  # Citation cluster (P1)
        "asr",  # Assertion (P3)
        "prp",  # Proposition (P3)
        "lga",  # Legislative action (P3)
        "crt",  # Court / bench seat registry (P3)
        "bnc",  # Bench / coram instance (P3)
        "jdg",  # Judge person (P1 -> P3)
        "ent",  # Recurring institutional party (P1)
        "itp",  # Public issue-topic taxonomy node (P3, D12)
        "rvw",  # HITL review task (P1, P3)
        "rul",  # Doctrine rule (P3)
        "prs",  # Procedural RuleSpec (P6)
        "ter",  # Territory node (P3)
        "xrn",  # Crosswalk row (P3)
        "xwg",  # Crosswalk group (P3, D22.1)
        "xtr",  # Extraction run (P3, D20.5)
        "gdl",  # Graph delta (P3)
        "imp",  # Impact (P4)
        "camp",  # Reprocess campaign (P4)
        "rpq",  # Reprocess request (P4)
        "kgp",  # KG proposal (P9)
        "dig",  # Digest edition (P10)
        "dgi",  # Digest item (P10)
        "ovl",  # Redaction overlay (P0, P1, ops/legal, D19.3, D20.5)
        # Shared / Dual plane
        "sum",  # Summary (P2)
        "chk",  # Chunk (P2)
        "gld",  # Gold set (P8)
        "evc",  # Eval case (P8)
        "evr",  # Eval run (P8)
        # Tenant Private Layer (TPL)
        "aud",  # Citation audit report (P8, D12)
        "vr",  # Verification report (P8)
        "ten",  # Tenant (P7)
        "usr",  # User (P7)
        "grp",  # Team / group (P7)
        "mat",  # Matter (P7)
        "pdoc",  # Private document (P7)
        "fct",  # Fact (P7)
        "iss",  # Private matter issue (P7)
        "opc",  # Opponent claim (P7)
        "hrg",  # Hearing (P7)
        "hold",  # Legal hold (P7)
        "pasr",  # Private assertion (P7)
        "adt",  # Audit event (P7)
        "tec",  # Tenant Execution Context (P7)
        "alr",  # Matter alert (P7)
        "qry",  # Research query (P5)
        "evb",  # Evidence bundle (P5)
        "job",  # Strategy job (P6)
        "clm",  # Claim (P6)
        "mem",  # Strategy memo (P6)
        "drf",  # Draft artifact (P6)
        "ddl",  # Deadline (P6)
        "mck",  # Maintainability check (P6, D21.5)
        "fb",  # Feedback event (P9)
        "act",  # Actor pseudonym (P9)
        "cns",  # ConsentRecord snapshot (P7, D21.16)
        "uim",  # UI impression (P10)
        "wl",  # Watchlist (P10)
        "wr",  # Watch rule (P10)
        "wh",  # Watch hit (P10)
        "ntf",  # Notification (P10)
        "chb",  # Channel binding (P10)
        "udg",  # User digest (P10)
        "cck",  # Cite-check run (P10)
    }
)

# MVP additions to the ID prefix registry, each citing its DECISIONS.md record.
MVP_PREFIX_ADDITIONS: dict[str, str] = {
    "ewl": "DECISIONS.md 2026-10-01: Ethical wall identifier prefix (Session S03)",
}

# The active prefix registry is the union of normative blueprint prefixes and MVP additions.
PREFIX_REGISTRY: frozenset[str] = DOC_PREFIX_REGISTRY | frozenset(MVP_PREFIX_ADDITIONS.keys())


ULID_REGEX = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
MNEMONIC_REGEX = re.compile(r"^[A-Z0-9_]+$")
SHA256_REGEX = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ParsedID:
    raw: str
    prefix: str
    ulid: str | None = None
    timestamp_ms: int | None = None
    entropy: int | None = None
    mnemonic: str | None = None
    is_mnemonic: bool = False
    is_content_address: bool = False


class _MonotonicULIDGenerator:
    """Thread-safe monotonic Crockford ULID generator.

    Generates 128-bit values (48-bit timestamp + 80-bit randomness).
    Within the same millisecond, the 80-bit entropy is incremented monotonically.
    Guarantees strict sorting order matching creation order.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_time_ms: int = -1
        self._last_entropy: int = 0

    def generate(self) -> str:
        now_ms = time.time_ns() // 1_000_000
        with self._lock:
            if now_ms > self._last_time_ms:
                self._last_time_ms = now_ms
                self._last_entropy = secrets.randbits(80)
            else:
                # Same millisecond or clock moved backwards: monotonically increment entropy
                self._last_entropy += 1
                if self._last_entropy > 0xFFFFFFFFFFFFFFFFFFFF:
                    # Entropy overflowed 80 bits, increment timestamp
                    self._last_time_ms += 1
                    self._last_entropy = 0

            time_ms = self._last_time_ms
            entropy = self._last_entropy

        value_128 = (time_ms << 80) | entropy
        # Encode 128 bits into 26 Crockford base32 characters
        chars = [""] * 26
        for i in range(25, -1, -1):
            chars[i] = CROCKFORD_ALPHABET[value_128 & 0x1F]
            value_128 >>= 5
        return "".join(chars)


_GENERATOR: _MonotonicULIDGenerator = _MonotonicULIDGenerator()


def mint_ulid() -> str:
    """Mint a raw, unprefixed 26-character Crockford ULID.

    Used where contracts specify raw Crockford ULIDs without prefix
    (e.g., ops.llm_call_record.call_id per 03 §3.15).
    """
    return _GENERATOR.generate()


def mint_id(prefix: str) -> str:
    """Mint a new prefixed ULID.

    Args:
        prefix: The entity prefix (e.g. 'wrk', 'cas', 'ten'). Must be registered.
                May be provided with or without trailing underscore.

    Returns:
        String of form '{prefix}_{ulid_26}'.

    Raises:
        ValueError: If prefix is not in PREFIX_REGISTRY.
    """
    clean_prefix = prefix.rstrip("_")
    if clean_prefix not in PREFIX_REGISTRY:
        raise ValueError(
            f"Unknown prefix '{clean_prefix}'. Must be in 01 §5.2 registry: "
            f"{sorted(PREFIX_REGISTRY)}"
        )
    ulid = _GENERATOR.generate()
    return f"{clean_prefix}_{ulid}"


def is_valid_sha256(content_address: str) -> bool:
    """Validate a sha256: content address (lowercase hex, 64 characters)."""
    return bool(SHA256_REGEX.match(content_address))


def parse_id(id_str: str) -> ParsedID:
    """Parse an entity identifier, registry mnemonic, or sha256 content address.

    Args:
        id_str: The identifier string.

    Returns:
        ParsedID with extracted components.

    Raises:
        ValueError: If id_str is malformed or has an unknown prefix.
    """
    if not isinstance(id_str, str) or not id_str.isascii():
        raise ValueError("ID must be an ASCII string")

    if id_str.startswith("sha256:"):
        if not is_valid_sha256(id_str):
            raise ValueError(f"Invalid sha256 content address: {id_str}")
        return ParsedID(
            raw=id_str,
            prefix="sha256",
            is_content_address=True,
        )

    if "_" not in id_str:
        raise ValueError(f"ID missing prefix delimiter '_': {id_str}")

    prefix, suffix = id_str.split("_", 1)
    if prefix not in PREFIX_REGISTRY:
        raise ValueError(f"Unknown prefix '{prefix}' in ID '{id_str}'")

    # Check for ULID form (exactly 26 Crockford base32 characters)
    if len(suffix) == 26 and ULID_REGEX.match(suffix):
        # Decode Crockford ULID
        val = 0
        for ch in suffix:
            val = (val << 5) | CROCKFORD_DECODE_MAP[ch]
        time_ms = val >> 80
        entropy = val & 0xFFFFFFFFFFFFFFFFFFFF
        return ParsedID(
            raw=id_str,
            prefix=prefix,
            ulid=suffix,
            timestamp_ms=time_ms,
            entropy=entropy,
            is_mnemonic=False,
        )

    # Check for curated reference registry mnemonic form
    if prefix in MNEMONIC_PREFIXES:
        if MNEMONIC_REGEX.match(suffix):
            return ParsedID(
                raw=id_str,
                prefix=prefix,
                mnemonic=suffix,
                is_mnemonic=True,
            )
        raise ValueError(f"Invalid mnemonic suffix '{suffix}' for prefix '{prefix}'")

    if prefix == "wrk":
        raise ValueError(
            f"Works are never mnemonic (wrk_ACT_NI is invalid; 01 §5.2 line 483): '{id_str}'"
        )

    raise ValueError(f"Invalid ULID suffix '{suffix}' for prefix '{prefix}'")


def is_valid_id(
    id_str: str,
    prefix: str | None = None,
    allow_mnemonic: bool = True,
) -> bool:
    """Validate an ID string.

    Args:
        id_str: ID string to validate.
        prefix: If given, the ID must have this specific prefix.
        allow_mnemonic: If False, reject mnemonic IDs even for crt/ent/rul/ter.

    Returns:
        True if valid, False otherwise.
    """
    try:
        parsed = parse_id(id_str)
    except ValueError:
        return False

    if prefix is not None and parsed.prefix != prefix.rstrip("_"):
        return False

    if parsed.is_mnemonic and not allow_mnemonic:
        return False

    return True
