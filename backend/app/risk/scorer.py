import math
import re
from typing import List, Dict, Any

class BlastRiskCalculator:
    """
    Deterministic Continuous Asymptotic Risk Scorer for Monorepo API changes:
    RawScore = (BlastDepthScore × DensityMultiplier) + CriticalityScore + CompliancePenalty
    RiskScore = 100.0 × (1 - exp(-RawScore / 55.0))
    Eliminates 100-point ceiling saturation and preserves ordinal hazard differentiation.
    Anti-Injection: CWE-94 check in diff / comments.
    """

    CWE94_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?rules",
        r"(?i)approve\s+this\s+pr",
        r"(?i)skip\s+check",
        r"(?i)override\s+gate",
        r"(?i)vectis\s+bypass",
        r"(?i)<\|endoftext\|>",
        r"(?i)system\s*:\s*you\s+are",
    ]

    TAU: float = 55.0  # Asymptotic saturation scale factor

    def compute_risk_score(
        self,
        breaking_changes: List[Dict[str, Any]],
        downstream_impact: List[Dict[str, Any]],
        total_repo_nodes: int,
        compliance_violations: int = 1,
        raw_diff: str = "",
    ) -> Dict[str, Any]:
        # Anti-injection check
        injection_detected = self._scan_for_injection(raw_diff)
        if injection_detected:
            return {
                "total_score": 100.0,
                "blast_depth_score": 0.0,
                "criticality_score": 0.0,
                "compliance_penalty": 0.0,
                "injection_flag": True,
                "breakdown": {"CWE-94": "Prompt injection detected in code comments"},
            }

        # Blast depth score calculation with depth attenuation
        blast_score = 0.0
        for node in downstream_impact:
            depth = max(node.get("dependency_depth", 1), 1)
            crit = node.get("criticality", 1.0)
            traffic = node.get("traffic_weight", 1.0)
            blast_score += (depth ** -0.5) * crit * traffic

        blast_score *= 10.5

        # Critical severity of breaking changes
        crit_count = len([c for c in breaking_changes if c.get("severity") == "critical"])
        warn_count = len([c for c in breaking_changes if c.get("severity") == "warning"])
        crit_score = (crit_count * 18.0) + (warn_count * 6.0)

        # Compliance penalty (e.g. PCI-DSS 10.2.1 identity continuity)
        comp_penalty = compliance_violations * 15.0

        # Monorepo graph blast density factor: ratio of affected nodes over total monorepo nodes
        repo_ratio = (len(downstream_impact) / max(total_repo_nodes, 1)) if total_repo_nodes > 0 else 0.5
        density_multiplier = 1.0 + min(repo_ratio * 1.5, 1.25)

        raw_total = (blast_score * density_multiplier) + crit_score + comp_penalty
        
        # Smooth continuous asymptotic saturation curve
        if raw_total <= 0.0:
            total = 0.0
        else:
            total = 100.0 * (1.0 - math.exp(-raw_total / self.TAU))

        return {
            "total_score": round(total, 1),
            "blast_depth_score": round(blast_score, 1),
            "criticality_score": round(crit_score, 1),
            "compliance_penalty": round(comp_penalty, 1),
            "injection_flag": False,
            "breakdown": {
                "raw_total_risk": round(raw_total, 2),
                "asymptotic_tau": self.TAU,
                "downstream_nodes_affected": len(downstream_impact),
                "breaking_changes_critical": crit_count,
                "breaking_changes_warning": warn_count,
                "compliance_violations": compliance_violations,
                "compliance_rule": "PCI-DSS v4.0.1 Req 10.2.1 Audit Continuity" if compliance_violations > 0 else "None"
            },
        }

    def _scan_for_injection(self, raw_diff: str) -> bool:
        if not raw_diff:
            return False
        for pattern in self.CWE94_PATTERNS:
            if re.search(pattern, raw_diff):
                return True
        return False
