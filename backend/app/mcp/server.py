import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure the backend directory is in sys.path when running this script directly
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from mcp.server.fastmcp import FastMCP, Context
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

from app.ast.analyzer import ASTChangeDetector, DependencyDAGEngine
from app.risk.scorer import BlastRiskCalculator
from app.schemas.blast import PassportSigner
from app.granite.synthesizer import IBMGraniteSynthesizer
from app.compliance.pci_dss_engine import PCIDSSComplianceEngine

dag_engine = DependencyDAGEngine()
risk_calculator = BlastRiskCalculator()
passport_signer = PassportSigner()
granite_synthesizer = IBMGraniteSynthesizer()
compliance_engine = PCIDSSComplianceEngine()

def run_blast_analysis(
    repo_path: str,
    base_ref: str,
    head_ref: str,
    changed_files: List[str]
) -> Dict[str, Any]:
    detector = ASTChangeDetector(repo_path=repo_path)
    breaking_changes = []

    for file_path in changed_files:
        if file_path.endswith((".ts", ".tsx", ".js", ".jsx", ".py")):
            changes = detector.detect_contract_mutations(file_path, base_ref, head_ref)
            breaking_changes.extend(changes)

    dag_engine.build_graph(repo_path)
    downstream_impact = []
    for change in breaking_changes:
        affected = dag_engine.calculate_downstream_impact(change["file_path"], change["symbol_name"])
        downstream_impact.extend(affected)

    unique_impact = list({node["node_id"]: node for node in downstream_impact}.values())
    risk_assessment = risk_calculator.compute_risk_score(
        breaking_changes, unique_impact, dag_engine.get_total_node_count()
    )

    verdict = "BLOCK" if risk_assessment["total_score"] >= 70.0 else (
        "WARN" if risk_assessment["total_score"] >= 30.0 else "PASS"
    )
    return {
        "status": "success",
        "verdict": verdict,
        "risk_assessment": risk_assessment,
        "breaking_changes": breaking_changes,
        "downstream_impact": unique_impact
    }

if HAS_MCP:
    mcp = FastMCP(
        name="vectis-sentinel",
        instructions="FastMCP Server for Autonomous Monorepo Blast Radius, IBM Granite 3.0 Shims & PCI-DSS Governance"
    )

    @mcp.tool()
    async def analyze_blast_radius(
        repo_path: str,
        base_ref: str,
        head_ref: str,
        changed_files: List[str],
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """Analyzes PR contract mutations and multi-hop downstream blast radius using AST & NetworkX DAG."""
        return run_blast_analysis(repo_path, base_ref, head_ref, changed_files)

    @mcp.tool()
    async def synthesize_granite_shim(
        symbol: str,
        old_sig: str,
        new_sig: str,
        callers: Optional[List[str]] = None,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """Synthesizes an ES6 Proxy compatibility adapter via IBM Granite 3.0 on watsonx.ai."""
        res = granite_synthesizer.synthesize_adapter(
            symbol=symbol,
            old_sig=old_sig,
            new_sig=new_sig,
            callers=callers or []
        )
        return {
            "status": "success",
            "symbol": symbol,
            "shim_code": res.shim_code,
            "remappings": res.remappings,
            "source": res.source,
            "pci_dss_continuous": res.pci_dss_continuous,
        }

    @mcp.tool()
    async def audit_pci_compliance(
        diff_text: str,
        file_path: str = "src/auth/session.ts",
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """Audits pull request diff against PCI-DSS v4.0.1 rules (Req 10.2.1, 3.4.2, 8.2.8)."""
        report = compliance_engine.audit_diff(diff_text=diff_text, file_path=file_path)
        return {
            "status": "success",
            "is_blocking": report.is_blocking,
            "total_penalty": report.total_penalty,
            "evaluated_symbols_count": report.evaluated_symbols_count,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "symbol_name": v.symbol_name,
                    "severity": v.severity,
                    "penalty_score": v.penalty_score,
                    "remediation_guidance": v.remediation_guidance,
                }
                for v in report.violations
            ],
            "engine_fingerprint": report.engine_fingerprint,
        }

    @mcp.tool()
    async def generate_release_passport(
        pr_number: int,
        commit_sha: str,
        author: str,
        risk_score: float,
        verdict: str,
        shim_applied: bool,
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """Issues an RFC 8785 canonical JSON signed Cryptographic Release Passport."""
        if verdict == "BLOCK" and not shim_applied:
            raise ValueError("Cannot issue Release Passport: PR is BLOCKED due to critical contract drift!")
        return passport_signer.create_signed_passport(
            pr_number, commit_sha, author, risk_score, verdict, shim_applied
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vectis FastMCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transport protocol (stdio or sse)")
    parser.add_argument("--port", type=int, default=8001, help="Port for SSE transport")
    args = parser.parse_args()

    if HAS_MCP:
        if args.transport == "sse":
            mcp.run(transport="sse", port=args.port)
        else:
            mcp.run(transport="stdio")
    else:
        print("FastMCP module not installed. Standalone mode ready.")
