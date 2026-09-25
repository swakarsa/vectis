import json
import logging
from typing import List, Dict, Any, Optional

try:
    from mcp.server.fastmcp import FastMCP, Context
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

from app.ast.analyzer import ASTChangeDetector, DependencyDAGEngine
from app.risk.scorer import BlastRiskCalculator
from app.schemas.blast import PassportSigner

dag_engine = DependencyDAGEngine()
risk_calculator = BlastRiskCalculator()
passport_signer = PassportSigner()

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
        title="Vectis Sentinel Engine",
        description="FastMCP Server for Monorepo Blast Radius and Shim Synthesis"
    )

    @mcp.tool()
    async def analyze_blast_radius(
        repo_path: str,
        base_ref: str,
        head_ref: str,
        changed_files: List[str],
        ctx: Optional[Context] = None
    ) -> Dict[str, Any]:
        """Analyzes PR diff using Tree-sitter AST & NetworkX DAG."""
        return run_blast_analysis(repo_path, base_ref, head_ref, changed_files)

    @mcp.tool()
    async def generate_release_passport(
        pr_number: int,
        commit_sha: str,
        author: str,
        risk_score: float,
        verdict: str,
        shim_applied: bool
    ) -> Dict[str, Any]:
        """Issues SHA-256 Cryptographic Release Passport."""
        if verdict == "BLOCK" and not shim_applied:
            raise ValueError("Cannot issue Release Passport: PR is BLOCKED!")
        return passport_signer.create_signed_passport(
            pr_number, commit_sha, author, risk_score, verdict, shim_applied
        )

if __name__ == "__main__":
    if HAS_MCP:
        mcp.run(transport="stdio")
    else:
        print("FastMCP module not installed. Standalone mode ready.")
