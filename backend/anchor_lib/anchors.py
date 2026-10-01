"""Anchor Grammar v1.1 parser, canonicalizer, and validator for lawyer_brain.

Normative sources:
- docs/01_master_architecture.md §5.3 (formal EBNF grammar v1.0, examples, constraints A1-A8)
- docs/01a_spine_decision_record.md (D8, D16, D21.8, D21.17, D22.2)
- docs/mvp/03_data_model_and_contracts.md §1 item 3 (Postgres check regexes)

Anchor reference kinds:
1. public_anchor: wrk_<ulid>/<expression_key>#<fragment>
2. provision_ref: wrk_<ulid>#<statute_frag> (expression-independent)
3. pit_ref: wrk_<ulid>#<statute_frag>@<date>[~<territory>] (resolves to public_anchor)
4. private_anchor: pdoc_<ulid>/v<pver>[.<rendition>]#[att<att_no>/]<private_frag>
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date as dt_date

from anchor_lib.ids import ULID_REGEX

# ==============================================================================
# Lexical & Regex Definitions (verbatim EBNF 01 §5.3 & D22.2)
# ==============================================================================

# ISO 639-1 / 639-2 subtag: 2 or 3 lowercase letters.
# docs/01_master_architecture.md §5.3 line 563:
#   lang = lower, lower, [ lower ] ; (* ISO 639 primary subtag; "-x-mt" forbidden *)
LANG_REGEX = re.compile(r"^[a-z]{2,3}$")

# Territory: ISO 3166-2:IN
#   territory = "IN", [ "-", upper, upper, [ upper ] ]
TERRITORY_REGEX = re.compile(r"^IN(-[A-Z]{2,3})?$")

# Date: YYYY-MM-DD
DATE_REGEX = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

# Posint: non-zero digit followed by digits (>= 1, never 0)
POSINT_REGEX = re.compile(r"^[1-9][0-9]*$")

# Unit number: posint followed by optional uppercase letters (e.g. 302, 21A, 498A)
UNIT_NO_REGEX = re.compile(r"^[1-9][0-9]*[A-Z]*$")

# Judgment expression: lang, [ ".r", posint ]
JUDGMENT_EXPR_REGEX = re.compile(r"^([a-z]{2,3})(\.r([1-9][0-9]*))?$")

# Statute expression: lang, "@", date, [ "~", territory ]
STATUTE_EXPR_REGEX = re.compile(
    r"^([a-z]{2,3})@([0-9]{4}-[0-9]{2}-[0-9]{2})(~(IN(-[A-Z]{2,3})?))?$"
)

# Private rendition: (mt- | ht-) , lang
RENDITION_REGEX = re.compile(r"^(mt|ht)-([a-z]{2,3})$")

# Private version: v<posint>
PVER_REGEX = re.compile(r"^v([1-9][0-9]*)$")

# Fallback fragment: pg<N>[.l<M>]
FALLBACK_FRAG_REGEX = re.compile(r"^pg([1-9][0-9]*)(\.l([1-9][0-9]*))?$")

# Private region: pg<N>.rg<M>
REGION_REGEX = re.compile(r"^pg([1-9][0-9]*)\.rg([1-9][0-9]*)$")

# Private message: m<N>[.att<M>]
MESSAGE_REGEX = re.compile(r"^m([1-9][0-9]*)(\.att([1-9][0-9]*))?$")

# Private email header: hdr.(from|to|cc|date|subject)
EMAIL_HDR_REGEX = re.compile(r"^hdr\.(from|to|cc|date|subject)$")

# Private spreadsheet cell: [sheet<N>.]r<R>.c<C>
CELL_REGEX = re.compile(r"^(sheet([1-9][0-9]*)\.)?r([1-9][0-9]*)\.c([1-9][0-9]*)$")

# Private timerange: tHH:MM:SS-HH:MM:SS
TIMERANGE_REGEX = re.compile(r"^t([0-9]{2}:[0-9]{2}:[0-9]{2})-([0-9]{2}:[0-9]{2}:[0-9]{2})$")

# Sentence fragment: s<N>
SENTENCE_REGEX = re.compile(r"^s([1-9][0-9]*)$")

# Paragraph fragment: (p|u)<N>
PARA_REGEX = re.compile(r"^(p|u)([1-9][0-9]*)$")

# Sub-segment: posint | lower+ | u<posint> | x<posint>
SUB_SEG_REGEX = re.compile(r"^([1-9][0-9]*|[a-z]+|u[1-9][0-9]*|x[1-9][0-9]*)$")


# ==============================================================================
# Exceptions
# ==============================================================================


class AnchorError(ValueError):
    """Base exception for anchor errors."""


class InvalidAnchorError(AnchorError):
    """Raised when an anchor string violates EBNF grammar syntax."""


class SemanticConstraintError(AnchorError):
    """Raised when an anchor violates semantic constraints A1–A8."""


class NoExpressionError(SemanticConstraintError):
    """Raised under A3 when no expression covers the target date."""


# ==============================================================================
# Typed AST for Fragments & Expressions
# ==============================================================================


@dataclass(frozen=True, slots=True)
class JudgmentExpression:
    lang: str
    corrigendum_rev: int | None = None

    def __str__(self) -> str:
        if self.corrigendum_rev is not None:
            return f"{self.lang}.r{self.corrigendum_rev}"
        return self.lang


@dataclass(frozen=True, slots=True)
class StatuteExpression:
    lang: str
    date: str
    territory: str | None = None

    def __str__(self) -> str:
        res = f"{self.lang}@{self.date}"
        if self.territory:
            res += f"~{self.territory}"
        return res


@dataclass(frozen=True, slots=True)
class JudgmentFragment:
    """Judgment fragment AST.

    judgment_frag = [ opinion_prefix ] , jnode ;
    opinion_prefix = "o" , posint , "." ; (* absent = o1 *)
    jnode = "hdr" | "ord" | footnote | para_path ;
    """

    node_type: str  # "hdr" | "ord" | "fn" | "para"
    opinion: int = 1
    has_explicit_opinion: bool = False
    footnote_no: int | None = None
    para_kind: str | None = None  # "p" | "u"
    para_no: int | None = None
    sub_segs: tuple[str, ...] = ()
    sentence_no: int | None = None

    def __str__(self) -> str:
        prefix = f"o{self.opinion}." if self.has_explicit_opinion else ""
        if self.node_type == "hdr":
            return f"{prefix}hdr"
        if self.node_type == "ord":
            return f"{prefix}ord"
        if self.node_type == "fn":
            return f"{prefix}fn{self.footnote_no}"
        # para_path
        parts = [f"{self.para_kind}{self.para_no}"]
        for seg in self.sub_segs:
            parts.append(str(seg))
        if self.sentence_no is not None:
            parts.append(f"s{self.sentence_no}")
        return prefix + ".".join(parts)


@dataclass(frozen=True, slots=True)
class StatuteSegment:
    kind: str  # "subsec" | "clause" | "proviso" | "explanation" | "illustration"
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class StatuteFragment:
    """Statute fragment AST.

    unit = sec-N | art-N | rule-N | sch-N[.item-N | .ord-N[.rule-N]] (v1.1 D22.2)
    stat_seg = subsec | clause | proviso | explanation | illustration
    """

    unit_type: str  # "sec" | "art" | "rule" | "sch"
    unit_no: str
    sch_item: str | None = None
    sch_ord: str | None = None
    sch_rule: str | None = None
    segments: tuple[StatuteSegment, ...] = ()

    def __str__(self) -> str:
        if self.unit_type == "sch":
            base = f"sch-{self.unit_no}"
            if self.sch_item is not None:
                base += f".item-{self.sch_item}"
            elif self.sch_ord is not None:
                base += f".ord-{self.sch_ord}"
                if self.sch_rule is not None:
                    base += f".rule-{self.sch_rule}"
        else:
            base = f"{self.unit_type}-{self.unit_no}"

        if self.segments:
            return base + "." + ".".join(str(seg) for seg in self.segments)
        return base


@dataclass(frozen=True, slots=True)
class FallbackFragment:
    """Fallback locator fragment for QUARANTINED documents.

    fallback_frag = "pg" , posint , [ ".l" , posint ]
    """

    page: int
    line: int | None = None

    def __str__(self) -> str:
        if self.line is not None:
            return f"pg{self.page}.l{self.line}"
        return f"pg{self.page}"


# ==============================================================================
# Top-level Typed Anchor Objects
# ==============================================================================


class AnchorRef(ABC):
    """Abstract base class for all legal anchor references."""

    @abstractmethod
    def format(self) -> str:
        """Format the anchor to exact canonical representation."""
        ...

    @abstractmethod
    def canonical_key(self) -> str:
        """A6: work_id (or pdoc_id) '#' fragment, stripping expr_key and o1. prefix."""
        ...

    @property
    @abstractmethod
    def is_public(self) -> bool: ...

    @property
    @abstractmethod
    def is_private(self) -> bool: ...

    def __str__(self) -> str:
        return self.format()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.format()}')"


@dataclass(frozen=True, slots=True)
class PublicAnchor(AnchorRef):
    """Public anchor: wrk_<ulid>/<expression_key>#<fragment>"""

    work_id: str
    expression: JudgmentExpression | StatuteExpression
    fragment: JudgmentFragment | StatuteFragment | FallbackFragment
    _raw_str: str | None = None

    @property
    def is_public(self) -> bool:
        return True

    @property
    def is_private(self) -> bool:
        return False

    def format(self) -> str:
        if self._raw_str is not None:
            return self._raw_str
        return f"{self.work_id}/{self.expression}#{self.fragment}"

    def canonical_key(self) -> str:
        # A6: strip expression key and default o1. prefix
        frag_str = str(self.fragment)
        if isinstance(self.fragment, JudgmentFragment) and self.fragment.opinion == 1:
            if frag_str.startswith("o1."):
                frag_str = frag_str[3:]
        return f"{self.work_id}#{frag_str}"


@dataclass(frozen=True, slots=True)
class ProvisionRef(AnchorRef):
    """Expression-independent provision reference: wrk_<ulid>#<statute_frag>"""

    work_id: str
    fragment: StatuteFragment
    _raw_str: str | None = None

    @property
    def is_public(self) -> bool:
        return True

    @property
    def is_private(self) -> bool:
        return False

    def format(self) -> str:
        if self._raw_str is not None:
            return self._raw_str
        return f"{self.work_id}#{self.fragment}"

    def canonical_key(self) -> str:
        return f"{self.work_id}#{self.fragment}"


@dataclass(frozen=True, slots=True)
class PITRef(AnchorRef):
    """Point-in-time statute reference: wrk_<ulid>#<statute_frag>@<date>[~<territory>]"""

    work_id: str
    fragment: StatuteFragment
    date: str
    territory: str | None = None
    _raw_str: str | None = None

    @property
    def is_public(self) -> bool:
        return True

    @property
    def is_private(self) -> bool:
        return False

    def format(self) -> str:
        if self._raw_str is not None:
            return self._raw_str
        res = f"{self.work_id}#{self.fragment}@{self.date}"
        if self.territory:
            res += f"~{self.territory}"
        return res

    def canonical_key(self) -> str:
        # A6: canonical key for provision across versions / PIT drops PIT date/territory
        return f"{self.work_id}#{self.fragment}"


@dataclass(frozen=True, slots=True)
class PrivateAnchor(AnchorRef):
    """Private document anchor: pdoc_<ulid>/v<ver>[.<rendition>]#[att<att_no>/]<frag>"""

    pdoc_id: str
    version: int
    fragment: JudgmentFragment | StatuteFragment | FallbackFragment | str
    rendition: str | None = None  # e.g. "mt-en", "ht-en"
    attachment: int | None = None
    _raw_str: str | None = None

    @property
    def is_public(self) -> bool:
        return False

    @property
    def is_private(self) -> bool:
        return True

    @property
    def is_mt_rendition(self) -> bool:
        return self.rendition is not None and self.rendition.startswith("mt-")

    @property
    def is_ht_rendition(self) -> bool:
        return self.rendition is not None and self.rendition.startswith("ht-")

    def format(self) -> str:
        if self._raw_str is not None:
            return self._raw_str
        rend = f".{self.rendition}" if self.rendition else ""
        att = f"att{self.attachment}/" if self.attachment else ""
        return f"{self.pdoc_id}/v{self.version}{rend}#{att}{self.fragment}"

    def canonical_key(self) -> str:
        raise SemanticConstraintError(
            f"Constraint A6: canonical_key is defined only for public legal anchors "
            f"(canonical_key = work_id '#' fragment per 01 §5.3 A6). "
            f"Private document anchor '{self.format()}' carries tenant versioning "
            f"and cannot be canonicalized to a public match key."
        )


# ==============================================================================
# Parsers
# ==============================================================================


def _parse_posint(val: str, name: str) -> int:
    if not POSINT_REGEX.match(val):
        raise InvalidAnchorError(f"Expected positive integer for {name}, got '{val}'")
    return int(val)


def _parse_judgment_fragment(frag_str: str) -> JudgmentFragment:
    opinion = 1
    has_explicit_opinion = False
    rest = frag_str

    if rest.startswith("o") and "." in rest:
        op_part, after_op = rest.split(".", 1)
        if op_part[1:].isdigit():
            opinion = _parse_posint(op_part[1:], "opinion number")
            has_explicit_opinion = True
            rest = after_op

    if rest == "hdr":
        return JudgmentFragment(
            node_type="hdr",
            opinion=opinion,
            has_explicit_opinion=has_explicit_opinion,
        )
    if rest == "ord":
        return JudgmentFragment(
            node_type="ord",
            opinion=opinion,
            has_explicit_opinion=has_explicit_opinion,
        )
    if rest.startswith("fn") and rest[2:].isdigit():
        fn_no = _parse_posint(rest[2:], "footnote number")
        return JudgmentFragment(
            node_type="fn",
            opinion=opinion,
            has_explicit_opinion=has_explicit_opinion,
            footnote_no=fn_no,
        )

    # para_path = para , { "." , sub_seg } , [ "." , sentence ]
    tokens = rest.split(".")
    para_token = tokens[0]
    if (para_token.startswith("p") or para_token.startswith("u")) and para_token[1:] == "0":
        raise InvalidAnchorError(
            f"Constraint A1 violation: Paragraph number cannot be zero in '{frag_str}' (posint required)"
        )
    m_para = PARA_REGEX.match(para_token)
    if not m_para:
        raise InvalidAnchorError(f"Invalid judgment fragment node: '{frag_str}'")

    para_kind = m_para.group(1)
    para_no = int(m_para.group(2))

    sub_segs: list[str] = []
    sentence_no: int | None = None

    for idx, tok in enumerate(tokens[1:]):
        m_sent = SENTENCE_REGEX.match(tok)
        if m_sent:
            if idx != len(tokens) - 2:
                raise InvalidAnchorError(
                    f"Sentence '{tok}' must be terminal in paragraph path '{frag_str}'"
                )
            sentence_no = int(m_sent.group(1))
        else:
            if not SUB_SEG_REGEX.match(tok):
                raise InvalidAnchorError(
                    f"Invalid sub-segment '{tok}' in judgment fragment '{frag_str}'"
                )
            sub_segs.append(tok)

    return JudgmentFragment(
        node_type="para",
        opinion=opinion,
        has_explicit_opinion=has_explicit_opinion,
        para_kind=para_kind,
        para_no=para_no,
        sub_segs=tuple(sub_segs),
        sentence_no=sentence_no,
    )


def _parse_statute_fragment(frag_str: str) -> StatuteFragment:
    tokens = frag_str.split(".")
    unit_token = tokens[0]

    unit_type: str
    unit_no: str
    sch_item: str | None = None
    sch_ord: str | None = None
    sch_rule: str | None = None
    curr_idx = 1

    if unit_token.startswith("sec-"):
        unit_type = "sec"
        unit_no = unit_token[4:]
    elif unit_token.startswith("art-"):
        unit_type = "art"
        unit_no = unit_token[4:]
    elif unit_token.startswith("rule-"):
        unit_type = "rule"
        unit_no = unit_token[5:]
    elif unit_token.startswith("sch-"):
        unit_type = "sch"
        unit_no = unit_token[4:]
        # Check grammar v1.1 D22.2 schedule sub-units:
        # [ ".item-", unit_no | ".ord-", unit_no, [ ".rule-", unit_no ] ]
        if curr_idx < len(tokens):
            next_tok = tokens[curr_idx]
            if next_tok.startswith("item-"):
                sch_item = next_tok[5:]
                if not UNIT_NO_REGEX.match(sch_item):
                    raise InvalidAnchorError(f"Invalid schedule item number: '{sch_item}'")
                curr_idx += 1
            elif next_tok.startswith("ord-"):
                sch_ord = next_tok[4:]
                if not UNIT_NO_REGEX.match(sch_ord):
                    raise InvalidAnchorError(f"Invalid schedule order number: '{sch_ord}'")
                curr_idx += 1
                if curr_idx < len(tokens) and tokens[curr_idx].startswith("rule-"):
                    sch_rule = tokens[curr_idx][5:]
                    if not UNIT_NO_REGEX.match(sch_rule):
                        raise InvalidAnchorError(f"Invalid schedule rule number: '{sch_rule}'")
                    curr_idx += 1
    else:
        raise InvalidAnchorError(f"Invalid statute unit prefix in '{frag_str}'")

    if not UNIT_NO_REGEX.match(unit_no):
        raise InvalidAnchorError(f"Invalid statute unit number '{unit_no}' in '{frag_str}'")

    segments: list[StatuteSegment] = []
    for tok in tokens[curr_idx:]:
        # stat_seg = subsec | clause | proviso | explanation | illustration
        if tok.startswith("p") and tok[1:].isdigit():
            p_no = _parse_posint(tok[1:], "proviso number")
            segments.append(StatuteSegment("proviso", f"p{p_no}"))
        elif tok.startswith("e") and tok[1:].isdigit():
            e_no = _parse_posint(tok[1:], "explanation number")
            segments.append(StatuteSegment("explanation", f"e{e_no}"))
        elif tok.startswith("ill-"):
            ill_val = tok[4:]
            if not (ill_val.islower() or (ill_val.isdigit() and int(ill_val) > 0)):
                raise InvalidAnchorError(f"Invalid illustration segment: '{tok}'")
            segments.append(StatuteSegment("illustration", tok))
        elif UNIT_NO_REGEX.match(tok) and any(c.isdigit() for c in tok):
            # subsec: posint , { upper } (e.g. 1, 1A)
            segments.append(StatuteSegment("subsec", tok))
        elif tok.isalpha() and tok.islower():
            # clause: lower , { lower } (e.g. a, aa, ba, i, iv)
            segments.append(StatuteSegment("clause", tok))
        else:
            raise InvalidAnchorError(f"Invalid statute segment '{tok}' in '{frag_str}'")

    return StatuteFragment(
        unit_type=unit_type,
        unit_no=unit_no,
        sch_item=sch_item,
        sch_ord=sch_ord,
        sch_rule=sch_rule,
        segments=tuple(segments),
    )


def _parse_public_fragment(
    frag_str: str,
) -> JudgmentFragment | StatuteFragment | FallbackFragment:
    # 1. Fallback locator: pg<N>[.l<M>]
    m_fb = FALLBACK_FRAG_REGEX.match(frag_str)
    if m_fb:
        pg = int(m_fb.group(1))
        line = int(m_fb.group(3)) if m_fb.group(3) else None
        return FallbackFragment(page=pg, line=line)

    # 2. Statute fragment
    if any(frag_str.startswith(p) for p in ("sec-", "art-", "rule-", "sch-")):
        return _parse_statute_fragment(frag_str)

    # 3. Judgment fragment
    return _parse_judgment_fragment(frag_str)


def _parse_private_fragment(
    frag_str: str,
) -> JudgmentFragment | StatuteFragment | FallbackFragment | str:
    # Region: pgN.rgM
    if REGION_REGEX.match(frag_str):
        return frag_str
    # Message: mN[.attM]
    if MESSAGE_REGEX.match(frag_str):
        return frag_str
    # Email header: hdr.subject ...
    if EMAIL_HDR_REGEX.match(frag_str):
        return frag_str
    # Cell: [sheetN.]rR.cC
    if CELL_REGEX.match(frag_str):
        return frag_str
    # Timerange: tHH:MM:SS-HH:MM:SS
    if TIMERANGE_REGEX.match(frag_str):
        return frag_str

    # Fallback or Judgment fragment
    return _parse_public_fragment(frag_str)


def _parse_expression(expr_str: str) -> JudgmentExpression | StatuteExpression:
    # docs/01_master_architecture.md §5.3 line 563: lang = lower, lower, [ lower ] ; (* "-x-mt" forbidden *)
    if "-x-mt" in expr_str or expr_str.startswith("mt-") or expr_str.endswith(".mt"):
        raise InvalidAnchorError(
            f"Machine translation is forbidden as an Expression (01 §5.3 line 563): '{expr_str}'"
        )

    # Check statute expression: lang@date[~territory]
    m_stat = STATUTE_EXPR_REGEX.match(expr_str)
    if m_stat:
        lang = m_stat.group(1)
        date_str = m_stat.group(2)
        # Validate date
        try:
            dt_date.fromisoformat(date_str)
        except ValueError as err:
            raise InvalidAnchorError(f"Invalid date in expression '{expr_str}'") from err
        terr = m_stat.group(4)
        return StatuteExpression(lang=lang, date=date_str, territory=terr)

    # Check judgment expression: lang[.rN]
    m_jdg = JUDGMENT_EXPR_REGEX.match(expr_str)
    if m_jdg:
        lang = m_jdg.group(1)
        rev = int(m_jdg.group(3)) if m_jdg.group(3) else None
        return JudgmentExpression(lang=lang, corrigendum_rev=rev)

    raise InvalidAnchorError(f"Invalid expression key: '{expr_str}'")


# ==============================================================================
# Public API: parse(), format(), validate(), canonical_key()
# ==============================================================================


def parse(anchor_str: str) -> AnchorRef:
    """Parse an anchor string into a typed AnchorRef.

    Args:
        anchor_str: The anchor string to parse.

    Returns:
        One of PublicAnchor, ProvisionRef, PITRef, PrivateAnchor.

    Raises:
        InvalidAnchorError: If the string violates Anchor Grammar v1.1.
    """
    if not isinstance(anchor_str, str) or not anchor_str.isascii():
        raise InvalidAnchorError("Anchor must be an ASCII string")

    if "#" not in anchor_str:
        raise InvalidAnchorError(f"Missing '#' in anchor: '{anchor_str}'")

    prefix_part, frag_part = anchor_str.split("#", 1)
    if not frag_part:
        raise InvalidAnchorError(f"Empty fragment in anchor: '{anchor_str}'")

    # 1. Private anchor: pdoc_<ulid>/v<N>[.<rendition>]#[att<M>/]<pnode>
    if prefix_part.startswith("pdoc_"):
        if "/" not in prefix_part:
            raise InvalidAnchorError(f"Private anchor missing version: '{anchor_str}'")
        pdoc_id, ver_part = prefix_part.split("/", 1)
        ulid = pdoc_id[5:]
        if not ULID_REGEX.match(ulid):
            raise InvalidAnchorError(f"Invalid ULID in private anchor: '{pdoc_id}'")

        # Parse ver_part: vN[.rendition]
        rendition: str | None = None
        if "." in ver_part:
            v_token, rend_token = ver_part.split(".", 1)
            m_rend = RENDITION_REGEX.match(rend_token)
            if not m_rend:
                raise InvalidAnchorError(f"Invalid rendition '{rend_token}' in '{anchor_str}'")
            rendition = rend_token
        else:
            v_token = ver_part

        m_v = PVER_REGEX.match(v_token)
        if not m_v:
            raise InvalidAnchorError(f"Invalid private version '{v_token}' in '{anchor_str}'")
        pver = int(m_v.group(1))

        # Parse attachment: [attN/]
        attachment: int | None = None
        pnode_str = frag_part
        if frag_part.startswith("att") and "/" in frag_part:
            att_token, rest_pnode = frag_part.split("/", 1)
            if att_token[3:].isdigit() and int(att_token[3:]) > 0:
                attachment = int(att_token[3:])
                pnode_str = rest_pnode
            else:
                raise InvalidAnchorError(f"Invalid attachment prefix '{att_token}'")

        parsed_pnode = _parse_private_fragment(pnode_str)
        return PrivateAnchor(
            pdoc_id=pdoc_id,
            version=pver,
            rendition=rendition,
            attachment=attachment,
            fragment=parsed_pnode,
            _raw_str=anchor_str,
        )

    # 2. Public anchor, provision ref, or pit ref
    if not prefix_part.startswith("wrk_"):
        raise InvalidAnchorError(f"Public anchor must start with 'wrk_': '{anchor_str}'")

    # Check if there is an expression part: wrk_<ulid>/<expr>
    if "/" in prefix_part:
        work_id, expr_part = prefix_part.split("/", 1)
        ulid = work_id[4:]
        if not ULID_REGEX.match(ulid):
            raise InvalidAnchorError(f"Invalid ULID in work_id: '{work_id}'")
        expr = _parse_expression(expr_part)
        frag = _parse_public_fragment(frag_part)
        return PublicAnchor(
            work_id=work_id,
            expression=expr,
            fragment=frag,
            _raw_str=anchor_str,
        )

    # No expression part: provision_ref or pit_ref
    work_id = prefix_part
    ulid = work_id[4:]
    if not ULID_REGEX.match(ulid):
        raise InvalidAnchorError(f"Invalid ULID in work_id: '{work_id}'")

    # Check for pit_ref: work_id # statute_frag @ date [~ territory]
    if "@" in frag_part:
        stat_frag_str, pit_part = frag_part.split("@", 1)
        date_str: str
        territory: str | None = None
        if "~" in pit_part:
            date_str, territory = pit_part.split("~", 1)
            if not TERRITORY_REGEX.match(territory):
                raise InvalidAnchorError(f"Invalid territory in PIT ref: '{territory}'")
        else:
            date_str = pit_part

        if not DATE_REGEX.match(date_str):
            raise InvalidAnchorError(f"Invalid date in PIT ref: '{date_str}'")
        try:
            dt_date.fromisoformat(date_str)
        except ValueError as err:
            raise InvalidAnchorError(f"Invalid date in PIT ref: '{date_str}'") from err

        stat_frag = _parse_statute_fragment(stat_frag_str)
        return PITRef(
            work_id=work_id,
            fragment=stat_frag,
            date=date_str,
            territory=territory,
            _raw_str=anchor_str,
        )

    # Expression-independent provision ref: wrk_<ulid>#<statute_frag>
    stat_frag = _parse_statute_fragment(frag_part)
    return ProvisionRef(
        work_id=work_id,
        fragment=stat_frag,
        _raw_str=anchor_str,
    )


def format(anchor: AnchorRef) -> str:
    """Format an AnchorRef to its exact string representation.

    Guarantees: format(parse(x)) == x.
    Note on default spelling: When constructed from scratch, opinion 1 is omitted
    by default (e.g. '#p45' rather than '#o1.p45'), matching Akoma Ntoso convention.
    If explicitly parsed from a string containing 'o1.', it is preserved exactly.
    """
    return anchor.format()


def canonical_key(anchor: AnchorRef | str) -> str:
    """Compute the canonical match key for a public legal anchor (01 §5.3 constraint A6).

    Stripping the expression key and the default 'o1.' prefix gives:
      canonical_key(anchor) = work_id "#" fragment
    Used in matter_dependency.match_key and all language-agnostic joins.
    Raises SemanticConstraintError on private document anchors.
    """
    if isinstance(anchor, str):
        anchor = parse(anchor)
    return anchor.canonical_key()


def is_public(anchor: AnchorRef | str) -> bool:
    """Return True if anchor is a public legal anchor (public_anchor, provision_ref, pit_ref)."""
    if isinstance(anchor, str):
        anchor = parse(anchor)
    return anchor.is_public


def is_private(anchor: AnchorRef | str) -> bool:
    """Return True if anchor is a private document anchor."""
    if isinstance(anchor, str):
        anchor = parse(anchor)
    return anchor.is_private


def is_fallback_locator(anchor: AnchorRef | str) -> bool:
    """Check if anchor contains a fallback page/line locator (pgN / pgN.lM)."""
    if isinstance(anchor, str):
        anchor = parse(anchor)
    if isinstance(anchor, PublicAnchor) and isinstance(anchor.fragment, FallbackFragment):
        return True
    if isinstance(anchor, PrivateAnchor) and isinstance(anchor.fragment, FallbackFragment):
        return True
    return False


# ==============================================================================
# Semantic Constraints A1–A8 (Pure Functions, No Database Access)
# ==============================================================================


def validate(
    anchor: AnchorRef | str,
    *,
    is_quarantined: bool = False,
    is_claim_support: bool = False,
    claim_role: str = "PUBLIC_LAW",
) -> None:
    """Validate an anchor against structural grammar and semantic constraints A1-A8.

    Args:
        anchor: AnchorRef or anchor string.
        is_quarantined: Flag indicating whether source document has quality.gate=QUARANTINED.
        is_claim_support: Whether the anchor is being evaluated as legal claim support.
        claim_role: Role of the claim ("PUBLIC_LAW", "RECORD_FACT", etc.).

    Raises:
        InvalidAnchorError: On grammar syntax failure.
        SemanticConstraintError: On A1-A8 constraint violation.
    """
    if isinstance(anchor, str):
        anchor = parse(anchor)

    # A2: Fallback locators (pg / pg.l) exist only for quality.gate=QUARANTINED documents.
    if is_fallback_locator(anchor) and not is_quarantined:
        raise SemanticConstraintError(
            f"Constraint A2 violation: Fallback locator '{anchor}' is only valid for "
            "QUARANTINED documents (docs/01_master_architecture.md §5.3 A2)."
        )

    # A5: Machine translation never has a public anchor.
    # Private mt- rendition is never legal claim support.
    if is_claim_support:
        if isinstance(anchor, PrivateAnchor):
            if anchor.is_mt_rendition:
                raise SemanticConstraintError(
                    f"Constraint A5 violation: Private MT rendition '{anchor}' can never "
                    "support a claim (docs/01a_spine_decision_record.md D8, D21.8: MT_ANCHOR)."
                )
            if anchor.is_ht_rendition and claim_role != "RECORD_FACT":
                raise SemanticConstraintError(
                    f"Constraint A5 violation: Private certified translation '{anchor}' "
                    f"may support RECORD_FACT claims only, not '{claim_role}' (D21.17)."
                )


@dataclass(frozen=True, slots=True)
class ExpressionInfo:
    """Metadata for candidate statute expression for PIT resolution (A3)."""

    expression_key: str
    lang: str
    valid_from: str  # YYYY-MM-DD
    valid_to: str | None = None  # YYYY-MM-DD or None if current
    territory: str | None = None


def resolve_pit(
    pit_ref: PITRef | str,
    expressions: Sequence[ExpressionInfo],
) -> PublicAnchor:
    """Resolve a point-in-time ref to a public_anchor per constraint A3 (pure function).

    docs/01_master_architecture.md §5.3 A3:
    "A pit_ref resolves by (date D, territory T) to the statute_expr with valid_from <= D < valid_to.
     A territorial expression ~T takes precedence over the national one.
     If no expression covers D, the result is NO_EXPRESSION, never the nearest one."
    """
    if isinstance(pit_ref, str):
        parsed = parse(pit_ref)
        if not isinstance(parsed, PITRef):
            raise InvalidAnchorError(f"Expected PITRef, got {type(parsed).__name__}")
        pit_ref = parsed

    target_date = dt_date.fromisoformat(pit_ref.date)

    # Filter candidate expressions covering target_date: valid_from <= target_date < valid_to
    valid_candidates: list[ExpressionInfo] = []
    for expr in expressions:
        v_from = dt_date.fromisoformat(expr.valid_from)
        v_to = dt_date.fromisoformat(expr.valid_to) if expr.valid_to else None
        if v_from <= target_date and (v_to is None or target_date < v_to):
            valid_candidates.append(expr)

    if not valid_candidates:
        raise NoExpressionError(
            f"NO_EXPRESSION: No statute expression covers date {pit_ref.date} "
            f"for work '{pit_ref.work_id}' (01 §5.3 constraint A3)."
        )

    # Territory precedence: if pit_ref has territory T, matching ~T takes precedence over national
    selected_expr: ExpressionInfo | None = None
    if pit_ref.territory:
        for c in valid_candidates:
            if c.territory == pit_ref.territory:
                selected_expr = c
                break

    if selected_expr is None:
        # Fallback to national expression (territory is None or "IN")
        for c in valid_candidates:
            if c.territory is None or c.territory == "IN":
                selected_expr = c
                break

    if selected_expr is None:
        # If still None, take first valid candidate
        selected_expr = valid_candidates[0]

    parsed_expr = _parse_expression(selected_expr.expression_key)
    return PublicAnchor(
        work_id=pit_ref.work_id,
        expression=parsed_expr,
        fragment=pit_ref.fragment,
    )


def check_reconstructed_text(
    anchor: AnchorRef | str,
    *,
    derived: bool,
    verification: str,
    impact_tier: int,
) -> bool:
    """Enforce constraint A4: Reconstructed text backing tier-1 claims.

    docs/01_master_architecture.md §5.3 A4:
    "Reconstructed expressions (derived=true) back tier-1 claims only if verification=ROUNDTRIP_OK."
    """
    if derived and impact_tier == 1 and verification != "ROUNDTRIP_OK":
        return False
    return True


def check_translation_support(
    anchor: AnchorRef | str,
    *,
    claim_role: str = "PUBLIC_LAW",
) -> bool:
    """Enforce constraint A5: Translation support rules.

    docs/01_master_architecture.md §5.3 A5 & decisions D8, D16, D21.8, D21.17:
    - MT renditions are NEVER support.
    - Private certified translations (ht-) support RECORD_FACT claims only.
    """
    if isinstance(anchor, str):
        anchor = parse(anchor)

    if isinstance(anchor, PrivateAnchor):
        if anchor.is_mt_rendition:
            return False
        if anchor.is_ht_rendition and claim_role != "RECORD_FACT":
            return False
    return True


def rewrite_statute_expression(
    anchor: AnchorRef | str,
    target_expression_key: str,
) -> PublicAnchor:
    """Enforce constraint A7: IAL anchor rewriting.

    The IAL rewrites anchors of coalesced statute chunks to the expression valid
    on the query's valid_at (04_P2 §2.6-8).
    """
    if isinstance(anchor, str):
        anchor = parse(anchor)

    if not isinstance(anchor, PublicAnchor) or not isinstance(anchor.fragment, StatuteFragment):
        raise SemanticConstraintError(
            f"Constraint A7: Only statute anchors can be rewritten by IAL: '{anchor}'"
        )

    target_expr = _parse_expression(target_expression_key)
    if not isinstance(target_expr, StatuteExpression):
        raise SemanticConstraintError(
            f"Target expression '{target_expression_key}' must be a StatuteExpression"
        )

    return PublicAnchor(
        work_id=anchor.work_id,
        expression=target_expr,
        fragment=anchor.fragment,
    )


def get_clause_hierarchy(
    statute_frag: StatuteFragment | str,
) -> tuple[StatuteSegment, ...]:
    """Enforce constraint A8: Positional clause level hierarchy.

    docs/01_master_architecture.md §5.3 A8:
    "Clause level is positional (tree depth), not lexical. 'i' may be a clause or a sub-clause.
     Resolution uses the provision tree of the expression."
    """
    if isinstance(statute_frag, str):
        parsed = _parse_statute_fragment(statute_frag)
    else:
        parsed = statute_frag

    return parsed.segments
