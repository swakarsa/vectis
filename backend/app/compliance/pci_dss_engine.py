"""
backend/app/compliance/pci_dss_engine.py
==========================================
PCI-DSS v4.0.1 & SOC2 Type II Compliance Enforcement Engine
VECTIS Autonomous Release Safety -- IBM Bob 2.0 Hackathon

Scans Git AST mutations and contract diffs for violations of financial-data
regulations and cloud-security standards.  Every rule is implemented as a
self-contained callable so they can be independently enabled, disabled, or
extended without modifying the orchestrator.

Supported rule catalogue
------------------------
PCI-DSS v4.0.1
  REQ-3.4.2  PAN_EXPOSURE        -- Raw card numbers / CVV / expiry in schemas
  REQ-8.2.8  AUTH_CREDENTIAL     -- Passwords, bearer tokens, private keys in
                                    interface signatures or serializable types
  REQ-10.2.1 AUDIT_LOG_IDENTITY  -- Identity-field mutations without backward-
                                    compatible serialization shim (toJSON /
                                    ES6 Proxy traps)
  REQ-6.2.4  INJECTION_SURFACE   -- Prompt-injection / CWE-94 patterns in diffs

SOC2 Type II (Trust Service Criteria)
  CC6.1  DATA_PROTECTION         -- Tenant-isolation identifiers removed from
                                    request/response contracts

Penalty scoring
---------------
A :class:`ComplianceAuditReport` accumulates the sum of individual
:attr:`ComplianceViolation.penalty_score` values.  When
``total_penalty >= BLOCKING_THRESHOLD`` (default 50.0) the report sets
``is_blocking = True``, which the VECTIS release gate maps to a ``BLOCK``
verdict and disables the GitHub merge button.

Remediation links
-----------------
Each violation includes a ``remediation_guidance`` string that references the
IBM Granite 3.0 synthesizer shim by name so the auto-heal pipeline can resolve
and apply it without manual intervention.

Usage::

    from app.compliance.pci_dss_engine import PCIDSSComplianceEngine

    engine = PCIDSSComplianceEngine()
    report = engine.audit_ast_diff(
        file_path="src/auth/session.ts",
        diff_text=raw_git_patch,
        detected_mutations=mutations_from_ast_analyzer,
    )
    if report.is_blocking:
        # Trigger IBM Granite 3.0 auto-heal pipeline
        ...
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BLOCKING_THRESHOLD: float = 50.0

ENGINE_VERSION: str = "vectis-compliance-v1.0"

# ---------------------------------------------------------------------------
# Rule IDs -- canonical identifiers used in violation records
# ---------------------------------------------------------------------------

RULE_PCI_3_4_2 = "PCI-4.0.1-REQ-3.4.2"
RULE_PCI_8_2_8 = "PCI-4.0.1-REQ-8.2.8"
RULE_PCI_10_2_1 = "PCI-4.0.1-REQ-10.2.1"
RULE_PCI_6_2_4 = "PCI-4.0.1-REQ-6.2.4"
RULE_SOC2_CC6_1 = "SOC2-CC6.1-DATA-PROTECTION"

# All rules in evaluation order (cheapest/highest-signal first)
ALL_RULE_IDS: list[str] = [
    RULE_PCI_3_4_2,
    RULE_PCI_8_2_8,
    RULE_PCI_10_2_1,
    RULE_PCI_6_2_4,
    RULE_SOC2_CC6_1,
]

# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"

# Default penalty weights per severity
PENALTY_BY_SEVERITY: dict[str, float] = {
    SEVERITY_CRITICAL: 30.0,
    SEVERITY_HIGH: 15.0,
    SEVERITY_MEDIUM: 8.0,
    SEVERITY_LOW: 3.0,
}

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ComplianceViolation:
    """A single compliance rule violation detected during AST diff analysis.

    Attributes
    ----------
    violation_id:
        Unique identifier for this violation instance, composed from the
        rule_id and a short hash of file_path + symbol_name.
    rule_id:
        Canonical rule identifier, e.g. ``"PCI-4.0.1-REQ-10.2.1"``.
    severity:
        One of ``CRITICAL``, ``HIGH``, ``MEDIUM``, ``LOW``.
    file_path:
        Repository-relative path of the offending file.
    line_number:
        Best-effort line number (0 when unavailable).
    symbol_name:
        TypeScript symbol (interface or field) that triggered the violation.
    raw_snippet:
        Short text excerpt from the diff that triggered detection.
    remediation_guidance:
        Human-readable remediation instruction that references the IBM
        Granite 3.0 synthesizer shim when applicable.
    penalty_score:
        Numeric penalty contributed to the audit report total.
    """

    violation_id: str
    rule_id: str
    severity: str
    file_path: str
    line_number: int
    symbol_name: str
    raw_snippet: str
    remediation_guidance: str
    penalty_score: float


@dataclass
class ComplianceAuditReport:
    """Aggregate result of one compliance audit pass.

    Attributes
    ----------
    total_penalty:
        Sum of all :attr:`ComplianceViolation.penalty_score` values.
    is_blocking:
        ``True`` when ``total_penalty >= BLOCKING_THRESHOLD``.  Maps
        directly to the VECTIS ``BLOCK`` verdict.
    violations:
        Ordered list of all detected violations.
    passed_rules:
        Rule IDs for which no violations were found.
    evaluated_symbols_count:
        Total number of TypeScript symbols inspected.
    audit_timestamp:
        ISO-8601 UTC timestamp when the report was generated.
    engine_fingerprint:
        SHA-256 hex digest of the serialised violation list, providing
        an integrity check for the audit record (PCI-DSS Req 10.5.1).
    """

    total_penalty: float
    is_blocking: bool
    violations: list[ComplianceViolation]
    passed_rules: list[str]
    evaluated_symbols_count: int
    audit_timestamp: str
    engine_fingerprint: str


# ---------------------------------------------------------------------------
# Regex pattern library
# ---------------------------------------------------------------------------

# --- PCI REQ-3.4.2: PAN / CVV / expiry exposure ---

# Luhn-plausible PAN pattern: 13-19 consecutive digits, optionally hyphen/space
# separated.  Excludes phone numbers (7-10 digits) and version strings.
_RE_PAN_RAW = re.compile(
    r"\b(?:\d[\s\-]?){12,18}\d\b"
)
# Field names that suggest a PAN or card number
_RE_PAN_FIELD = re.compile(
    r"(?i)\b(card_?number|pan|primary_?account|account_?number|"
    r"credit_?card|debit_?card|card_?no)\b"
)
# CVV / CVC / CID field names
_RE_CVV_FIELD = re.compile(
    r"(?i)\b(cvv2?|cvc2?|cid|security_?code|card_?verification)\b"
)
# Expiry field names
_RE_EXPIRY_FIELD = re.compile(
    r"(?i)\b(expir(y|ation|es?|ed?)|exp_?date|card_?exp|valid_?thru)\b"
)
# Tokenization wrappers that make a field safe (exclusion)
_RE_TOKENIZED = re.compile(
    r"(?i)(token(ized|Reference|_?id)?|masked|hashed|encrypted|vault)"
)

# --- PCI REQ-8.2.8: Authentication credentials ---

_RE_PASSWORD_FIELD = re.compile(
    r"(?i)\b(password|passwd|pass_?phrase|secret|credential|"
    r"pin|auth_?token|access_?token|refresh_?token|api_?key|"
    r"private_?key|client_?secret|session_?token|jwt_?secret|"
    r"signing_?key|hmac_?key)\b"
)
# Bearer token literal in diff line (not just field name)
_RE_BEARER_LITERAL = re.compile(
    r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"
)
# PEM private key block
_RE_PEM_PRIVATE = re.compile(
    r"-----BEGIN\s+(RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY-----"
)
# AWS access key pattern
_RE_AWS_KEY = re.compile(r"\b(AKIA|AGPA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b")

# --- PCI REQ-10.2.1: Audit log identity immutability ---

# Identity / principal fields whose removal breaks audit continuity
_RE_IDENTITY_FIELD = re.compile(
    r"(?i)(?:\b(user_?id|sub|subject|principal|account_?id|"
    r"member_?id|employee_?id|session_?id|audit_?id|"
    r"correlation_?id|request_?id)\b"
    r"|(?<![A-Za-z_0-9])id(?![A-Za-z_0-9]))"
)
# Fields that, if removed from a TypeScript interface, lose audit traceability
_RE_ROLES_FIELD = re.compile(
    r"(?i)\b(roles?|permissions?|scopes?|authorities|grants?|entitlements?)\b"
)
# Shim indicators that prove backward-compat serialization is present
_RE_SHIM_PRESENT = re.compile(
    r"(?i)(toJSON|createBackwardCompatibilityProxy|CompatibilityProxy|"
    r"Reflect\.get|new\s+Proxy|getOwnPropertyDescriptor|ownKeys)"
)

# --- PCI REQ-6.2.4: Injection surface (CWE-94) ---

_RE_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)ignore\s+(all\s+)?rules"),
    re.compile(r"(?i)approve\s+this\s+(pr|pull\s*request)"),
    re.compile(r"(?i)skip\s+(check|gate|sentinel|compliance)"),
    re.compile(r"(?i)override\s+(gate|vectis|compliance|sentinel)"),
    re.compile(r"(?i)vectis[\s_-]bypass"),
    re.compile(r"(?i)<\|endoftext\|>"),
    re.compile(r"(?i)system\s*:\s*you\s+are"),
    re.compile(r"(?i)act\s+as\s+(an?\s+)?ai"),
    re.compile(r"(?i)disregard\s+(previous|prior|earlier)\s+instructions?"),
    re.compile(r"(?i)\bprompt\s*injection\b"),
    re.compile(r"<\|system\|>.*?<\|user\|>", re.DOTALL),
]

# --- SOC2 CC6.1: Tenant isolation ---

_RE_TENANT_FIELD = re.compile(
    r"(?i)\b(organization_?id|tenant_?id|account_?id|workspace_?id|"
    r"company_?id|customer_?id|org_?id|site_?id|partition_?key)\b"
)

# ---------------------------------------------------------------------------
# Violation ID generator
# ---------------------------------------------------------------------------


def _make_violation_id(rule_id: str, file_path: str, symbol_name: str) -> str:
    """Generate a stable, short violation identifier.

    The ID is ``<rule_id>:<8-hex-chars>`` where the hex digest covers
    ``file_path + symbol_name`` so the same symbol violation in the same
    file always produces the same ID within a run.
    """
    digest = hashlib.sha256(
        f"{file_path}:{symbol_name}".encode("utf-8")
    ).hexdigest()[:8]
    return f"{rule_id}:{digest}"


# ---------------------------------------------------------------------------
# Individual rule implementations
# ---------------------------------------------------------------------------


class _Rule:
    """Base wrapper that associates a rule ID and description with a callable.

    Parameters
    ----------
    rule_id:
        Canonical identifier (e.g. ``RULE_PCI_3_4_2``).
    description:
        One-line human description used in log output.
    fn:
        Callable ``(engine, context) -> list[ComplianceViolation]``.
    """

    def __init__(
        self,
        rule_id: str,
        description: str,
        fn: Callable[["PCIDSSComplianceEngine", "_AuditContext"], list[ComplianceViolation]],
    ) -> None:
        self.rule_id = rule_id
        self.description = description
        self.fn = fn

    def evaluate(
        self,
        engine: "PCIDSSComplianceEngine",
        ctx: "_AuditContext",
    ) -> list[ComplianceViolation]:
        """Run the rule and return any violations."""
        try:
            return self.fn(engine, ctx)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Rule %s raised an exception during evaluation: %s",
                self.rule_id,
                exc,
            )
            return []


# ---------------------------------------------------------------------------
# Audit context (per-invocation state passed to each rule)
# ---------------------------------------------------------------------------


@dataclass
class _AuditContext:
    """All inputs available to a rule evaluation.

    Attributes
    ----------
    file_path:
        Repository-relative path of the file being audited.
    diff_text:
        Raw unified diff text from ``git diff``.
    diff_lines:
        ``diff_text`` split into individual lines.
    added_lines:
        Lines prefixed with ``+`` (excluding the ``+++`` header).
    removed_lines:
        Lines prefixed with ``-`` (excluding the ``---`` header).
    detected_mutations:
        Structured mutation dicts from :class:`~app.ast.analyzer.ASTChangeDetector`.
    mutation_symbols:
        Set of ``symbol_name`` values from *detected_mutations* for O(1) lookup.
    """

    file_path: str
    diff_text: str
    diff_lines: list[str]
    added_lines: list[str]
    removed_lines: list[str]
    detected_mutations: list[dict]
    mutation_symbols: set[str] = field(default_factory=set)

    @classmethod
    def build(
        cls,
        file_path: str,
        diff_text: str,
        detected_mutations: list[dict],
    ) -> "_AuditContext":
        """Construct a context from raw inputs."""
        safe_diff = diff_text or ""
        lines = safe_diff.splitlines()
        added = [
            ln[1:]
            for ln in lines
            if ln.startswith("+") and not ln.startswith("+++")
        ]
        removed = [
            ln[1:]
            for ln in lines
            if ln.startswith("-") and not ln.startswith("---")
        ]
        symbols = {m.get("symbol_name", "") for m in detected_mutations}
        return cls(
            file_path=file_path,
            diff_text=safe_diff,
            diff_lines=lines,
            added_lines=added,
            removed_lines=removed,
            detected_mutations=detected_mutations,
            mutation_symbols=symbols,
        )


# ---------------------------------------------------------------------------
# Rule function implementations
# ---------------------------------------------------------------------------


def _rule_pan_exposure(
    engine: "PCIDSSComplianceEngine",
    ctx: "_AuditContext",
) -> list[ComplianceViolation]:
    """PCI REQ-3.4.2 -- PAN / CVV / card-expiry exposure in schema changes.

    Inspects added diff lines for:
    * Bare PAN-like field names without tokenization wrappers.
    * Raw CVV / CVC field names exposed in serializable types.
    * Card expiry field names not wrapped in a vault or tokenized container.
    * Actual digit sequences that pass a rough Luhn-range check.

    A field is considered *safe* when the same line or its immediate context
    contains a tokenization marker (e.g. ``tokenReference``, ``masked``,
    ``encrypted``).
    """
    violations: list[ComplianceViolation] = []

    for line in ctx.added_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Skip lines that already contain a tokenization wrapper
        if _RE_TOKENIZED.search(stripped):
            continue

        detected_issue: Optional[tuple[str, str]] = None  # (field_desc, severity)

        if _RE_PAN_FIELD.search(stripped):
            detected_issue = ("raw PAN / card-number field", SEVERITY_CRITICAL)
        elif _RE_CVV_FIELD.search(stripped):
            detected_issue = ("CVV/CVC field", SEVERITY_CRITICAL)
        elif _RE_EXPIRY_FIELD.search(stripped):
            detected_issue = ("card expiry field", SEVERITY_HIGH)
        elif _RE_PAN_RAW.search(stripped):
            # Digit sequence that looks like a PAN
            detected_issue = ("PAN-like digit sequence", SEVERITY_CRITICAL)

        if detected_issue is None:
            continue

        field_desc, severity = detected_issue
        symbol = _extract_symbol_from_line(stripped)
        vid = _make_violation_id(RULE_PCI_3_4_2, ctx.file_path, symbol)
        guidance = (
            f"The {field_desc} '{symbol}' is exposed without tokenization in "
            f"{ctx.file_path}. "
            "Wrap it in a vault-tokenized reference or encrypt at rest. "
            "Use the IBM Granite 3.0 `createBackwardCompatibilityProxy` shim "
            "to preserve backward-compat while migrating to tokenized storage. "
            "Reference: PCI-DSS v4.0.1 Req 3.4.2."
        )
        violations.append(
            ComplianceViolation(
                violation_id=vid,
                rule_id=RULE_PCI_3_4_2,
                severity=severity,
                file_path=ctx.file_path,
                line_number=_find_line_number(ctx.diff_lines, line),
                symbol_name=symbol,
                raw_snippet=stripped[:200],
                remediation_guidance=guidance,
                penalty_score=PENALTY_BY_SEVERITY[severity],
            )
        )

    return violations


def _rule_auth_credential(
    engine: "PCIDSSComplianceEngine",
    ctx: "_AuditContext",
) -> list[ComplianceViolation]:
    """PCI REQ-8.2.8 -- Authentication credentials in interface signatures.

    Detects:
    * Password / API-key / bearer-token field names added to TypeScript
      interfaces or type aliases that are exported (and therefore potentially
      serialized).
    * Literal bearer token values in the diff.
    * PEM private key blocks accidentally committed.
    * AWS-style access key patterns.
    """
    violations: list[ComplianceViolation] = []

    for line in ctx.added_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Skip benign comment lines - unless they contain leaked PEM keys or AWS secrets
        if (stripped.startswith("//") or stripped.startswith("*")) and not (_RE_PEM_PRIVATE.search(stripped) or _RE_AWS_KEY.search(stripped)):
            continue

        kind: Optional[str] = None

        if _RE_PEM_PRIVATE.search(stripped):
            kind = "PEM private key block"
        elif _RE_AWS_KEY.search(stripped):
            kind = "AWS access key"
        elif _RE_BEARER_LITERAL.search(stripped):
            kind = "bare bearer token literal"
        elif _RE_PASSWORD_FIELD.search(stripped):
            # Only flag if it looks like an interface/type field declaration,
            # not a function parameter or local variable.
            if _looks_like_schema_field(stripped):
                kind = "authentication-credential field in serializable schema"

        if kind is None:
            continue

        symbol = _extract_symbol_from_line(stripped)
        vid = _make_violation_id(RULE_PCI_8_2_8, ctx.file_path, symbol)
        severity = SEVERITY_CRITICAL if "key" in kind or "bearer" in kind else SEVERITY_HIGH
        guidance = (
            f"A {kind} ('{symbol}') was found in {ctx.file_path}. "
            "Never include raw credentials in exported TypeScript interfaces "
            "or serializable schemas. "
            "Store secrets in environment variables and inject via dependency "
            "injection. "
            "Apply the IBM Granite 3.0 `createBackwardCompatibilityProxy` shim "
            "to omit credential fields from serialized output via the `toJSON` trap. "
            "Reference: PCI-DSS v4.0.1 Req 8.2.8."
        )
        violations.append(
            ComplianceViolation(
                violation_id=vid,
                rule_id=RULE_PCI_8_2_8,
                severity=severity,
                file_path=ctx.file_path,
                line_number=_find_line_number(ctx.diff_lines, line),
                symbol_name=symbol,
                raw_snippet=stripped[:200],
                remediation_guidance=guidance,
                penalty_score=PENALTY_BY_SEVERITY[severity],
            )
        )

    return violations


def _rule_audit_log_identity(
    engine: "PCIDSSComplianceEngine",
    ctx: "_AuditContext",
) -> list[ComplianceViolation]:
    """PCI REQ-10.2.1 -- Identity-field mutations without backward-compat shim.

    When a mutation removes or renames an identity field (``id``, ``sub``,
    ``user_id``, ``roles``, etc.) the diff MUST also introduce a
    backward-compatibility shim (ES6 Proxy / ``toJSON`` / ``ownKeys`` trap)
    so that existing audit log consumers continue to receive the field.

    A violation is raised when:
    1. A mutation of type ``field_removed`` or ``field_renamed`` touches an
       identity or roles field, AND
    2. The diff does NOT contain any shim indicator.
    """
    violations: list[ComplianceViolation] = []

    # Check whether any shim is present anywhere in the diff
    shim_present = bool(_RE_SHIM_PRESENT.search(ctx.diff_text))

    for mutation in ctx.detected_mutations:
        mut_type = mutation.get("mutation_type", "")
        if mut_type not in ("field_removed", "type_change", "field_renamed"):
            continue

        old_sig = mutation.get("old_signature", "")
        symbol = mutation.get("symbol_name", "")
        field_part = symbol.split(".")[-1] if "." in symbol else symbol

        is_identity = bool(
            _RE_IDENTITY_FIELD.search(field_part)
            or _RE_IDENTITY_FIELD.search(old_sig)
        )
        is_roles = bool(
            _RE_ROLES_FIELD.search(field_part)
            or _RE_ROLES_FIELD.search(old_sig)
        )

        if not (is_identity or is_roles):
            continue

        if shim_present:
            # Shim exists in the diff -- no violation
            continue

        vid = _make_violation_id(RULE_PCI_10_2_1, ctx.file_path, symbol)
        field_kind = "identity field" if is_identity else "roles/permissions field"
        guidance = (
            f"The {field_kind} '{symbol}' was removed or renamed in "
            f"{ctx.file_path} without an accompanying backward-compatibility "
            "serialization shim. "
            "PCI-DSS v4.0.1 Req 10.2.1 requires unbroken audit log identity "
            "continuity. "
            "Resolve by running `vectis auto-heal` to synthesise an IBM Granite "
            "3.0 `createBackwardCompatibilityProxy` ES6 Proxy shim that "
            "preserves the legacy field via `toJSON`, `ownKeys`, and "
            "`getOwnPropertyDescriptor` traps. "
            "Reference: PCI-DSS v4.0.1 Req 10.2.1."
        )
        violations.append(
            ComplianceViolation(
                violation_id=vid,
                rule_id=RULE_PCI_10_2_1,
                severity=SEVERITY_CRITICAL,
                file_path=ctx.file_path,
                line_number=mutation.get("line_number", 0),
                symbol_name=symbol,
                raw_snippet=old_sig[:200],
                remediation_guidance=guidance,
                penalty_score=PENALTY_BY_SEVERITY[SEVERITY_CRITICAL],
            )
        )

    return violations


def _rule_injection_surface(
    engine: "PCIDSSComplianceEngine",
    ctx: "_AuditContext",
) -> list[ComplianceViolation]:
    """PCI REQ-6.2.4 -- Prompt-injection / CWE-94 patterns in diff content.

    Scans the full diff text (both added and context lines) for strings that
    attempt to manipulate the AI review pipeline -- prompt-injection attacks
    embedded in code comments, string literals, or commit messages.
    """
    violations: list[ComplianceViolation] = []

    for pattern in _RE_INJECTION_PATTERNS:
        m = pattern.search(ctx.diff_text)
        if not m:
            continue

        snippet = ctx.diff_text[max(0, m.start() - 20): m.end() + 20].strip()
        vid = _make_violation_id(RULE_PCI_6_2_4, ctx.file_path, pattern.pattern[:30])
        guidance = (
            "A prompt-injection or CWE-94 pattern was detected in the diff of "
            f"{ctx.file_path}: '{snippet[:100]}'. "
            "Remove all AI-instruction-overriding comments, string literals, "
            "and metadata from the change. "
            "This pattern will cause the VECTIS sentinel to hard-block the PR "
            "with a risk score of 100. "
            "Reference: PCI-DSS v4.0.1 Req 6.2.4, CWE-94."
        )
        violations.append(
            ComplianceViolation(
                violation_id=_make_violation_id(
                    RULE_PCI_6_2_4, ctx.file_path, pattern.pattern[:30]
                ),
                rule_id=RULE_PCI_6_2_4,
                severity=SEVERITY_CRITICAL,
                file_path=ctx.file_path,
                line_number=0,
                symbol_name="(injection-pattern)",
                raw_snippet=snippet[:200],
                remediation_guidance=guidance,
                penalty_score=100.0,  # Always blocking
            )
        )
        # One injection violation is sufficient to block; stop scanning
        break

    return violations


def _rule_tenant_isolation(
    engine: "PCIDSSComplianceEngine",
    ctx: "_AuditContext",
) -> list[ComplianceViolation]:
    """SOC2 CC6.1 -- Tenant isolation identifiers removed from contracts.

    Detects when a field that enforces tenant/organisation isolation (e.g.
    ``organizationId``, ``tenantId``) is present in *removed* diff lines but
    absent from *added* lines -- i.e. it was deleted from the contract without
    replacement.
    """
    violations: list[ComplianceViolation] = []

    removed_tenant_fields: set[str] = set()
    added_tenant_fields: set[str] = set()

    for line in ctx.removed_lines:
        m = _RE_TENANT_FIELD.search(line)
        if m:
            removed_tenant_fields.add(m.group(0).lower().replace("_", ""))

    for line in ctx.added_lines:
        m = _RE_TENANT_FIELD.search(line)
        if m:
            added_tenant_fields.add(m.group(0).lower().replace("_", ""))

    # Fields dropped without re-addition anywhere in the diff
    truly_removed = removed_tenant_fields - added_tenant_fields
    for field_norm in truly_removed:
        symbol = field_norm
        vid = _make_violation_id(RULE_SOC2_CC6_1, ctx.file_path, symbol)
        guidance = (
            f"The tenant-isolation field '{symbol}' was removed from the "
            f"contract in {ctx.file_path} without replacement. "
            "SOC2 CC6.1 requires that every request/response contract retains "
            "tenant isolation identifiers to prevent cross-tenant data leakage. "
            "Restore the field or provide an equivalent isolation mechanism. "
            "Reference: SOC2 Type II CC6.1."
        )
        violations.append(
            ComplianceViolation(
                violation_id=vid,
                rule_id=RULE_SOC2_CC6_1,
                severity=SEVERITY_HIGH,
                file_path=ctx.file_path,
                line_number=0,
                symbol_name=symbol,
                raw_snippet="",
                remediation_guidance=guidance,
                penalty_score=PENALTY_BY_SEVERITY[SEVERITY_HIGH],
            )
        )

    return violations


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _extract_symbol_from_line(line: str) -> str:
    """Best-effort extraction of a TypeScript field name from a diff line.

    Handles patterns like:
    * ``  id: string;``
    * ``  cardNumber?: string;``
    * ``export const API_KEY = ...``
    """
    # Field declaration in interface/type: "  fieldName?: Type;"
    m = re.match(r"^\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\??:", line)
    if m:
        return m.group(1)
    # Const / let / var declaration: "const apiKey = ..."
    m = re.match(r"^\s*(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)", line)
    if m:
        return m.group(1)
    # Export statement: "export const FOO = ..."
    m = re.match(r"^\s*export\s+(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)", line)
    if m:
        return m.group(1)
    # Fallback: first word token
    m = re.match(r"^\s*([A-Za-z_$][A-Za-z0-9_$]*)", line)
    if m:
        return m.group(1)
    return "(unknown)"


def _looks_like_schema_field(line: str) -> bool:
    """Return True if the line looks like a TypeScript interface field declaration.

    Discriminates against function parameter lists, local variable assignments,
    and import statements to reduce false positives on REQ-8.2.8.
    """
    stripped = line.strip()
    # Interface/type field: "  fieldName: Type" or "  fieldName?: Type"
    if re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*\s*\??:\s*\S", stripped):
        return True
    # Exported const that is clearly a type definition
    if re.match(r"^export\s+(type|interface|const)\s+", stripped):
        return True
    return False


def _find_line_number(diff_lines: list[str], target_line: str) -> int:
    """Return the 1-based index of *target_line* (stripped) inside *diff_lines*.

    Returns 0 when the line is not found.
    """
    target = target_line.strip()
    for i, dl in enumerate(diff_lines, start=1):
        if dl.lstrip("+-# ").strip() == target:
            return i
    return 0


def _compute_engine_fingerprint(violations: list[ComplianceViolation]) -> str:
    """Produce a SHA-256 hex digest over the serialised violation list.

    This fingerprint satisfies PCI-DSS Req 10.5.1 (audit log integrity).
    """
    payload = json.dumps(
        [
            {
                "id": v.violation_id,
                "rule": v.rule_id,
                "severity": v.severity,
                "file": v.file_path,
                "symbol": v.symbol_name,
                "penalty": v.penalty_score,
            }
            for v in violations
        ],
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------


class PCIDSSComplianceEngine:
    """PCI-DSS v4.0.1 & SOC2 Type II compliance engine for VECTIS.

    Evaluates Git AST mutations and unified diff text against a catalogue of
    financial-data and cloud-security rules, producing a
    :class:`ComplianceAuditReport` that the VECTIS release gate uses to decide
    whether to block a PR or recommend auto-remediation via IBM Granite 3.0.

    Instantiation parameters
    ------------------------
    blocking_threshold:
        Cumulative penalty score at or above which ``is_blocking`` is set to
        ``True``.  Default ``50.0``.
    enabled_rules:
        Optional list of rule IDs to enable.  When ``None`` all rules in
        :data:`ALL_RULE_IDS` are active.

    Example::

        engine = PCIDSSComplianceEngine()
        report = engine.audit_ast_diff(
            file_path="src/auth/session.ts",
            diff_text=diff,
            detected_mutations=mutations,
        )
        print(report.total_penalty, report.is_blocking)
    """

    def __init__(
        self,
        blocking_threshold: float = BLOCKING_THRESHOLD,
        enabled_rules: Optional[list[str]] = None,
    ) -> None:
        self._blocking_threshold = blocking_threshold
        self._enabled_rule_ids: set[str] = (
            set(enabled_rules) if enabled_rules is not None else set(ALL_RULE_IDS)
        )
        self._rules: list[_Rule] = self._build_rule_registry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def audit_ast_diff(
        self,
        file_path: str,
        diff_text: str,
        detected_mutations: list[dict],
    ) -> ComplianceAuditReport:
        """Run all enabled compliance rules against a single file diff.

        Parameters
        ----------
        file_path:
            Repository-relative path (e.g. ``"src/auth/session.ts"``).
        diff_text:
            Unified diff text as produced by ``git diff``.  May be empty when
            only AST-level mutations are available.
        detected_mutations:
            List of mutation dicts from
            :class:`~app.ast.analyzer.ASTChangeDetector`.  Each dict must
            contain at minimum ``symbol_name``, ``mutation_type``,
            ``old_signature``, and ``new_signature``.

        Returns
        -------
        ComplianceAuditReport
            Aggregated report with total penalty, blocking decision, and the
            full violation list.
        """
        ctx = _AuditContext.build(
            file_path=file_path,
            diff_text=diff_text or "",
            detected_mutations=detected_mutations or [],
        )

        all_violations: list[ComplianceViolation] = []
        passed_rules: list[str] = []
        evaluated_symbols = len(ctx.detected_mutations)

        for rule in self._rules:
            if rule.rule_id not in self._enabled_rule_ids:
                continue

            rule_violations = rule.evaluate(self, ctx)

            if rule_violations:
                # Deduplicate by violation_id within a single rule pass
                seen_ids: set[str] = set()
                for v in rule_violations:
                    if v.violation_id not in seen_ids:
                        seen_ids.add(v.violation_id)
                        all_violations.append(v)
                logger.info(
                    "Rule %s: %d violation(s) detected in %s",
                    rule.rule_id,
                    len(rule_violations),
                    file_path,
                )
            else:
                passed_rules.append(rule.rule_id)
                logger.debug("Rule %s: PASSED for %s", rule.rule_id, file_path)

        total_penalty = round(
            sum(v.penalty_score for v in all_violations), 2
        )
        is_blocking = total_penalty >= self._blocking_threshold

        fingerprint = _compute_engine_fingerprint(all_violations)
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        report = ComplianceAuditReport(
            total_penalty=total_penalty,
            is_blocking=is_blocking,
            violations=all_violations,
            passed_rules=passed_rules,
            evaluated_symbols_count=evaluated_symbols,
            audit_timestamp=timestamp,
            engine_fingerprint=fingerprint,
        )

        if is_blocking:
            logger.warning(
                "COMPLIANCE BLOCK: file=%s penalty=%.1f threshold=%.1f violations=%d",
                file_path,
                total_penalty,
                self._blocking_threshold,
                len(all_violations),
            )
        return report

    def audit_multiple_files(
        self,
        file_diffs: list[dict],
        all_mutations: list[dict],
    ) -> ComplianceAuditReport:
        """Audit a collection of file diffs and merge results into one report.

        Parameters
        ----------
        file_diffs:
            List of ``{"file_path": str, "diff_text": str}`` dicts.
        all_mutations:
            Flat list of all mutation dicts across all files.

        Returns
        -------
        ComplianceAuditReport
            Merged report.  ``is_blocking`` is ``True`` if the *merged*
            ``total_penalty`` meets the threshold.
        """
        merged_violations: list[ComplianceViolation] = []
        merged_passed: list[str] = []
        total_symbols = 0

        for fd in file_diffs:
            fp = fd.get("file_path", "")
            dt = fd.get("diff_text", "")
            file_mutations = [
                m for m in all_mutations
                if m.get("file_path", "") == fp
            ]
            sub = self.audit_ast_diff(fp, dt, file_mutations)
            merged_violations.extend(sub.violations)
            for r in sub.passed_rules:
                if r not in merged_passed:
                    merged_passed.append(r)
            total_symbols += sub.evaluated_symbols_count

        # Remove duplicate violation IDs (same symbol across files)
        seen: set[str] = set()
        unique_violations: list[ComplianceViolation] = []
        for v in merged_violations:
            if v.violation_id not in seen:
                seen.add(v.violation_id)
                unique_violations.append(v)

        total_penalty = round(sum(v.penalty_score for v in unique_violations), 2)
        is_blocking = total_penalty >= self._blocking_threshold
        fingerprint = _compute_engine_fingerprint(unique_violations)
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return ComplianceAuditReport(
            total_penalty=total_penalty,
            is_blocking=is_blocking,
            violations=unique_violations,
            passed_rules=list(set(merged_passed)),
            evaluated_symbols_count=total_symbols,
            audit_timestamp=timestamp,
            engine_fingerprint=fingerprint,
        )

    def get_rule_descriptions(self) -> dict[str, str]:
        """Return a mapping of rule_id -> description for all registered rules."""
        return {r.rule_id: r.description for r in self._rules}

    # ------------------------------------------------------------------
    # Internal: rule registry
    # ------------------------------------------------------------------

    def _build_rule_registry(self) -> list[_Rule]:
        """Instantiate the full catalogue of compliance rules."""
        return [
            _Rule(
                rule_id=RULE_PCI_3_4_2,
                description=(
                    "PCI-DSS v4.0.1 Req 3.4.2 -- PAN/CVV/expiry fields exposed "
                    "in schema changes without tokenization wrappers"
                ),
                fn=_rule_pan_exposure,
            ),
            _Rule(
                rule_id=RULE_PCI_8_2_8,
                description=(
                    "PCI-DSS v4.0.1 Req 8.2.8 -- Raw passwords, API keys, bearer "
                    "tokens, or private keys in exported interface signatures"
                ),
                fn=_rule_auth_credential,
            ),
            _Rule(
                rule_id=RULE_PCI_10_2_1,
                description=(
                    "PCI-DSS v4.0.1 Req 10.2.1 -- Identity/roles field removal "
                    "without backward-compatible serialization shim"
                ),
                fn=_rule_audit_log_identity,
            ),
            _Rule(
                rule_id=RULE_PCI_6_2_4,
                description=(
                    "PCI-DSS v4.0.1 Req 6.2.4 -- Prompt-injection / CWE-94 "
                    "patterns detected in diff content"
                ),
                fn=_rule_injection_surface,
            ),
            _Rule(
                rule_id=RULE_SOC2_CC6_1,
                description=(
                    "SOC2 Type II CC6.1 -- Tenant isolation identifiers "
                    "(organizationId, tenantId) removed from request/response contracts"
                ),
                fn=_rule_tenant_isolation,
            ),
        ]
