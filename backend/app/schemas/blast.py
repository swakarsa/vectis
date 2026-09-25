import hashlib
import json
import datetime
from typing import List, Dict, Any, Optional
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
    """RFC 8785 JCS Canonical JSON + SHA-256 Release Passport."""
    def create_signed_passport(
        self,
        pr_number: int,
        commit_sha: str,
        author: str,
        risk_score: float,
        verdict: str,
        shim_applied: bool
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
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        payload["passport_hash"] = f"sha256:{digest}"
        return payload
