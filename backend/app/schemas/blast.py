import os
import hmac
import hashlib
import json
import datetime
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

class BreakingChange(BaseModel):
    file_path: str
    symbol_name: str
    mutation_type: str  # "type_change" | "field_removed" | "field_renamed" | "interface_removed"
    old_signature: str
    new_signature: str
    severity: str = "critical"  # "critical" | "warning" | "info"
    line_number: Optional[int] = None
    description: Optional[str] = None

class DownstreamNode(BaseModel):
    node_id: str
    file_path: str
    symbol_name: str
    dependency_depth: int
    criticality: float = 1.0
    traffic_weight: float = 1.0

class RiskAssessment(BaseModel):
    total_score: float = Field(ge=0, le=100)
    blast_depth_score: float
    criticality_score: float
    compliance_penalty: float = 0.0
    injection_flag: bool = False
    breakdown: Dict[str, Any] = {}

class AnalysisRequest(BaseModel):
    repo_path: Optional[str] = ""
    base_ref: str = "main"
    head_ref: str = "feature/refactor-auth"
    changed_files: List[str] = ["src/auth/session.ts"]

class AnalysisResponse(BaseModel):
    status: str
    verdict: str  # "PASS" | "WARN" | "BLOCK"
    risk_assessment: RiskAssessment
    breaking_changes: List[BreakingChange]
    downstream_impact: List[DownstreamNode]
    dag_metrics: Dict[str, Any]

class ComplianceRequest(BaseModel):
    standard_id: str = "PCI-DSS-v4.0.1"
    diff_payload: str
    parsed_entities: List[Dict[str, Any]]
    pdf_path: Optional[str] = None

class RemediationRequest(BaseModel):
    broken_symbol: str
    old_signature: str
    new_signature: str
    affected_callers: List[str]
    language: str = "typescript"

class PassportSigner:
    """RFC 8785 JCS Canonical JSON + HMAC-SHA256 / SHA-256 Release Passport."""

    def __init__(self, secret: Optional[str] = None):
        self.secret = secret

    def create_signed_passport(
        self,
        pr_number: int,
        commit_sha: str,
        author: str,
        risk_score: float,
        verdict: str,
        shim_applied: bool,
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "pr_number": pr_number,
            "commit_sha": commit_sha,
            "author": author,
            "risk_score": round(risk_score, 2),
            "verdict": verdict,
            "shim_applied": shim_applied,
            "issued_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "engine": "vectis-sentinel-v1.0"
        }
        # RFC 8785: Canonical JSON (sorted keys, no whitespace)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signing_secret = secret if secret is not None else (self.secret or os.getenv("VECTIS_PASSPORT_SECRET"))

        if signing_secret:
            sig = hmac.new(
                signing_secret.encode("utf-8"),
                canonical.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            payload["passport_hash"] = f"hmac-sha256:{sig}"
        else:
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            payload["passport_hash"] = f"sha256:{digest}"

        return payload

    def verify(
        self, passport: Dict[str, Any], secret: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Verify release passport using verify_signed_passport."""
        return verify_signed_passport(passport, secret=secret or self.secret)


def verify_signed_passport(
    passport: Dict[str, Any], secret: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Verifies cryptographic authenticity of an RFC 8785 release passport.
    Supports HMAC-SHA256 (keyed) and SHA-256 (unkeyed) digests.

    Returns:
        tuple[bool, str]: (is_valid, status_or_reason_message)
    """
    if not isinstance(passport, dict):
        return False, "Invalid passport format: expected JSON dictionary"

    passport_hash = passport.get("passport_hash")
    if not passport_hash or not isinstance(passport_hash, str):
        return False, "Missing or invalid 'passport_hash' in release passport"

    # Reconstruct canonical payload by omitting the signature / hash field and transport envelope metadata
    ignored_keys = {"passport_hash", "signature_algorithm", "canonical_standard", "attestation", "signature"}
    payload = {k: v for k, v in passport.items() if k not in ignored_keys}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    active_secret = secret if secret is not None else os.getenv("VECTIS_PASSPORT_SECRET")

    if passport_hash.startswith("hmac-sha256:"):
        expected_sig = passport_hash.split("hmac-sha256:", 1)[1]
        if not active_secret:
            return (
                False,
                "Passport signed with HMAC-SHA256 but VECTIS_PASSPORT_SECRET is not configured or provided",
            )
        computed_sig = hmac.new(
            active_secret.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(computed_sig, expected_sig):
            return True, "Valid HMAC-SHA256 cryptographic release passport signature"
        return False, "Cryptographic verification failed: HMAC-SHA256 signature mismatch"

    elif passport_hash.startswith("sha256:"):
        expected_digest = passport_hash.split("sha256:", 1)[1]
        computed_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if hmac.compare_digest(computed_digest, expected_digest):
            return True, "Valid canonical SHA-256 release passport digest (unkeyed)"
        return False, "Cryptographic verification failed: SHA-256 digest mismatch"

    elif len(passport_hash) == 64 and all(c in "0123456789abcdefABCDEF" for c in passport_hash):
        computed_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if hmac.compare_digest(computed_digest.lower(), passport_hash.lower()):
            return True, "Valid canonical SHA-256 release passport digest"
        return False, "Cryptographic verification failed: SHA-256 digest mismatch"

    return False, f"Unsupported passport_hash algorithm: {passport_hash}"

