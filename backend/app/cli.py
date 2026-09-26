"""
backend/app/cli.py
==================
Developer CLI and CI/CD Runner for VECTIS
IBM Bob 2.0 Hackathon -- Autonomous Release Safety

Standalone CLI using Python 3.11 standard library argparse with zero
external CLI dependencies (no Click/Typer).

Commands:
  vectis audit [--diff <base>...<head>] [--staged] [--json] [--sarif <path>]
  vectis hook install
  vectis passport verify --file <passport.json>

Exit codes:
  0: PASS (risk < 70.0, authentic passport, hook installed)
  1: BLOCK (risk >= 70.0, verification failed, error)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure app package is importable and Python stdlib 'ast' is not shadowed
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_CURRENT_DIR)
_REPO_ROOT = os.path.dirname(_BACKEND_DIR)

# Reconfigure standard streams to UTF-8 on Windows if needed
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# When invoked directly, Python inserts _CURRENT_DIR at sys.path[0].
# Filter it out so 'app/ast' does not shadow Python's standard library 'ast' module.
sys.path = [p for p in sys.path if os.path.abspath(p) != _CURRENT_DIR]

for path in (_BACKEND_DIR, _REPO_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)


try:
    from app.ast.analyzer import ASTChangeDetector, DependencyDAGEngine
    from app.compliance.pci_dss_engine import PCIDSSComplianceEngine
    from app.compliance.sarif_exporter import SARIFExporter
    from app.risk.scorer import BlastRiskCalculator
    from app.schemas.blast import verify_signed_passport
except ImportError:
    from .ast.analyzer import ASTChangeDetector, DependencyDAGEngine
    from .compliance.pci_dss_engine import PCIDSSComplianceEngine
    from .compliance.sarif_exporter import SARIFExporter
    from .risk.scorer import BlastRiskCalculator
    from .schemas.blast import verify_signed_passport


# ---------------------------------------------------------------------------
# Terminal ANSI Color & ASCII Formatting
# ---------------------------------------------------------------------------

class Term:
    """Rich terminal formatting using pure standard library ANSI escapes."""

    _USE_COLOR = (
        os.getenv("NO_COLOR") is None
        and (hasattr(sys.stdout, "isatty") and sys.stdout.isatty())
        or os.getenv("FORCE_COLOR") == "1"
    )

    RESET = "\033[0m" if _USE_COLOR else ""
    BOLD = "\033[1m" if _USE_COLOR else ""
    DIM = "\033[2m" if _USE_COLOR else ""

    RED = "\033[31m" if _USE_COLOR else ""
    GREEN = "\033[32m" if _USE_COLOR else ""
    YELLOW = "\033[33m" if _USE_COLOR else ""
    BLUE = "\033[34m" if _USE_COLOR else ""
    MAGENTA = "\033[35m" if _USE_COLOR else ""
    CYAN = "\033[36m" if _USE_COLOR else ""
    WHITE = "\033[37m" if _USE_COLOR else ""

    BG_RED = "\033[41m" if _USE_COLOR else ""
    BG_GREEN = "\033[42m" if _USE_COLOR else ""
    BG_YELLOW = "\033[43m" if _USE_COLOR else ""

    @classmethod
    def bold(cls, s: str) -> str:
        return f"{cls.BOLD}{s}{cls.RESET}"

    @classmethod
    def red(cls, s: str) -> str:
        return f"{cls.RED}{s}{cls.RESET}"

    @classmethod
    def green(cls, s: str) -> str:
        return f"{cls.GREEN}{s}{cls.RESET}"

    @classmethod
    def yellow(cls, s: str) -> str:
        return f"{cls.YELLOW}{s}{cls.RESET}"

    @classmethod
    def cyan(cls, s: str) -> str:
        return f"{cls.CYAN}{s}{cls.RESET}"

    @classmethod
    def dim(cls, s: str) -> str:
        return f"{cls.DIM}{s}{cls.RESET}"


# ---------------------------------------------------------------------------
# Git Diff & Discovery Utilities
# ---------------------------------------------------------------------------

def run_git_command(args: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Execute a git command safely and return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return -1, "", "Git executable not found in PATH"
    except Exception as e:
        return -1, "", str(e)


def discover_modified_files(
    repo_path: str, diff_spec: Optional[str] = None, staged_only: bool = False
) -> Tuple[List[str], str]:
    """
    Discovers modified TypeScript/JavaScript files and retrieves unified diff text.
    Returns (list_of_modified_ts_js_files, unified_diff_text).
    """
    ts_extensions = (".ts", ".tsx", ".js", ".jsx")
    unified_diff = ""
    modified_files: List[str] = []

    if staged_only:
        code, names_out, _ = run_git_command(["diff", "--cached", "--name-only"], cwd=repo_path)
        if code == 0 and names_out:
            modified_files = [line.strip() for line in names_out.splitlines() if line.strip()]
        code, diff_out, _ = run_git_command(["diff", "--cached"], cwd=repo_path)
        if code == 0:
            unified_diff = diff_out

    elif diff_spec:
        code, names_out, _ = run_git_command(["diff", "--name-only", diff_spec], cwd=repo_path)
        if code == 0 and names_out:
            modified_files = [line.strip() for line in names_out.splitlines() if line.strip()]
        code, diff_out, _ = run_git_command(["diff", diff_spec], cwd=repo_path)
        if code == 0:
            unified_diff = diff_out

    else:
        # Default: check working tree changes against HEAD
        code, names_out, _ = run_git_command(["diff", "--name-only", "HEAD"], cwd=repo_path)
        if code == 0 and names_out:
            modified_files = [line.strip() for line in names_out.splitlines() if line.strip()]
            code, diff_out, _ = run_git_command(["diff", "HEAD"], cwd=repo_path)
            if code == 0:
                unified_diff = diff_out
        else:
            # Fallback to unstaged diff
            code, names_out, _ = run_git_command(["diff", "--name-only"], cwd=repo_path)
            if code == 0 and names_out:
                modified_files = [line.strip() for line in names_out.splitlines() if line.strip()]
                code, diff_out, _ = run_git_command(["diff"], cwd=repo_path)
                if code == 0:
                    unified_diff = diff_out

    # Filter only TypeScript and JavaScript files
    relevant_files = [
        f for f in modified_files
        if f.endswith(ts_extensions) and not f.endswith(".d.ts")
    ]

    return relevant_files, unified_diff


# ---------------------------------------------------------------------------
# GitHub Actions Step Summary
# ---------------------------------------------------------------------------

def write_github_step_summary(
    verdict: str,
    risk: Dict[str, Any],
    breaking_changes: List[Dict[str, Any]],
    downstream_impact: List[Dict[str, Any]],
    compliance_violations: List[Any],
    sarif_path: Optional[str] = None,
) -> None:
    """
    Appends an enterprise Markdown report directly to $GITHUB_STEP_SUMMARY
    if running in GitHub Actions.
    """
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_file or os.getenv("GITHUB_ACTIONS") != "true":
        return

    verdict_badge = "❌ **BLOCKED**" if verdict == "BLOCK" else "✅ **PASSED**"
    score = risk.get("total_score", 0.0)

    lines = [
        "# 🛡️ VECTIS Sentinel -- Release Safety & Blast Radius Report",
        "",
        f"### Verdict: {verdict_badge} &nbsp;|&nbsp; Risk Score: **`{score:.1f} / 100.0`**",
        "",
        "> **Autonomous Release Safety Gate (IBM Bob 2.0 Hackathon)**",
        "> Scans Git contract drift, maps downstream dependency blast radius, and enforces PCI-DSS v4.0.1 compliance.",
        "",
        "### 📊 Key Metrics Summary",
        "| Metric | Value | Threshold | Status |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Overall Risk Score** | `{score:.1f}` | `< 70.0` | {'🔴 Critical' if score >= 70 else '🟢 Safe'} |",
        f"| **Blast Depth Penalty** | `{risk.get('blast_depth_score', 0.0):.1f}` | - | - |",
        f"| **Criticality Score** | `{risk.get('criticality_score', 0.0):.1f}` | - | - |",
        f"| **Compliance Penalty** | `{risk.get('compliance_penalty', 0.0):.1f}` | `< 50.0` | {'🔴 Blocking' if risk.get('compliance_penalty', 0.0) >= 50 else '🟢 Compliant'} |",
        f"| **Breaking Changes** | `{len(breaking_changes)}` | `0` | {'⚠️ Detected' if breaking_changes else '✅ None'} |",
        f"| **Downstream Nodes Impacted** | `{len(downstream_impact)}` | - | - |",
        "",
    ]

    # Breaking changes table
    if breaking_changes:
        lines.extend([
            "### 🚨 Detected Breaking Contract Changes",
            "| File | Symbol | Mutation Type | Severity | Description |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for bc in breaking_changes:
            lines.append(
                f"| `{bc.get('file_path')}` | `{bc.get('symbol_name')}` | `{bc.get('mutation_type')}` | "
                f"**{bc.get('severity', 'critical').upper()}** | {bc.get('description', '')} |"
            )
        lines.append("")

    # Downstream impact table
    if downstream_impact:
        lines.extend([
            "### 🌐 Blast Radius: Downstream Impacted Services",
            "| Service / Node | File Path | Depth | Criticality | Traffic Weight |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for node in downstream_impact:
            lines.append(
                f"| **{node.get('service', 'Service')}** | `{node.get('file_path')}` | "
                f"`{node.get('dependency_depth', 1)}` | `{node.get('criticality', 1.0):.2f}` | "
                f"`{node.get('traffic_weight', 1.0):.2f}` |"
            )
        lines.append("")

    # Compliance violations table
    if compliance_violations:
        lines.extend([
            "### ⚖️ PCI-DSS v4.0.1 & SOC2 Compliance Violations",
            "| Rule ID | Severity | File | Symbol | Remediation Guidance |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for cv in compliance_violations:
            rule_id = getattr(cv, "rule_id", str(cv))
            sev = getattr(cv, "severity", "HIGH")
            fpath = getattr(cv, "file_path", "")
            sym = getattr(cv, "symbol_name", "")
            guidance = getattr(cv, "remediation_guidance", "Apply IBM Granite 3.0 auto-heal shim.")
            lines.append(f"| `{rule_id}` | **{sev}** | `{fpath}` | `{sym}` | {guidance} |")
        lines.append("")

    if sarif_path and os.path.isfile(sarif_path):
        lines.append(f"📄 *SARIF v2.1.0 code scanning results uploaded to: `{sarif_path}`*")
        lines.append("")

    try:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        print(f"[VECTIS] Warning: Could not write GITHUB_STEP_SUMMARY: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------

def handle_audit(args: argparse.Namespace) -> int:
    """Executes the `vectis audit` release safety audit command."""
    repo_path = os.path.abspath(args.repo or os.getcwd())
    diff_spec = args.diff
    staged_only = args.staged
    is_json = args.json
    blocking_threshold = args.threshold
    sarif_output = args.sarif

    # 1. Discover modified files and diff
    changed_files, unified_diff = discover_modified_files(
        repo_path=repo_path,
        diff_spec=diff_spec,
        staged_only=staged_only,
    )

    # 2. Run AST Change Detector
    detector = ASTChangeDetector(repo_path=repo_path)
    breaking_changes: List[Dict[str, Any]] = []

    if not changed_files:
        # Check if session.ts exists in fixtures or target directory as demo fallback
        fixture_candidate = os.path.join(repo_path, "src", "auth", "session.ts")
        if not os.path.exists(fixture_candidate):
            fixture_candidate = os.path.join(repo_path, "main", "src", "auth", "session.ts")

        if os.path.exists(fixture_candidate):
            # Evaluate fixture file mutations
            mutations = detector.detect_contract_mutations("src/auth/session.ts", "main", "feature")
            breaking_changes.extend(mutations)
            changed_files = ["src/auth/session.ts"]
    else:
        for fp in changed_files:
            mutations = detector.detect_contract_mutations(fp, "main", "feature")
            breaking_changes.extend(mutations)

    # 3. Calculate downstream impact via DAG Engine
    dag_engine = DependencyDAGEngine()
    dag_engine.build_graph(repo_path)

    downstream_impact: List[Dict[str, Any]] = []
    for change in breaking_changes:
        affected = dag_engine.calculate_downstream_impact(
            file_path=change.get("file_path", ""),
            symbol_name=change.get("symbol_name", ""),
        )
        downstream_impact.extend(affected)

    # Deduplicate downstream impact by node_id
    seen_nodes = set()
    unique_impact: List[Dict[str, Any]] = []
    for node in downstream_impact:
        node_id = node.get("node_id")
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            unique_impact.append(node)

    # 4. Evaluate PCI-DSS Compliance
    compliance_engine = PCIDSSComplianceEngine()
    compliance_report = compliance_engine.audit_ast_diff(
        file_path=changed_files[0] if changed_files else "src/auth/session.ts",
        diff_text=unified_diff,
        detected_mutations=breaking_changes,
    )

    # 5. Compute Risk Score
    risk_calculator = BlastRiskCalculator()
    risk = risk_calculator.compute_risk_score(
        breaking_changes=breaking_changes,
        downstream_impact=unique_impact,
        total_repo_nodes=dag_engine.get_total_node_count(),
        compliance_violations=len(compliance_report.violations),
        raw_diff=unified_diff,
    )

    total_score = risk.get("total_score", 0.0)
    verdict = "BLOCK" if total_score >= blocking_threshold else "PASS"

    # 6. Optional SARIF export
    if sarif_output:
        exporter = SARIFExporter()
        exporter.write_sarif_file(compliance_report, sarif_output)

    # 7. Write GitHub Actions Step Summary if in CI
    write_github_step_summary(
        verdict=verdict,
        risk=risk,
        breaking_changes=breaking_changes,
        downstream_impact=unique_impact,
        compliance_violations=compliance_report.violations,
        sarif_path=sarif_output,
    )

    # 8. Output results
    if is_json:
        output_payload = {
            "status": "success",
            "verdict": verdict,
            "risk_assessment": risk,
            "breaking_changes_count": len(breaking_changes),
            "breaking_changes": breaking_changes,
            "downstream_impact_count": len(unique_impact),
            "downstream_impact": unique_impact,
            "compliance_report": {
                "total_penalty": compliance_report.total_penalty,
                "is_blocking": compliance_report.is_blocking,
                "violations_count": len(compliance_report.violations),
                "violations": [
                    {
                        "rule_id": v.rule_id,
                        "severity": v.severity,
                        "symbol": v.symbol_name,
                        "file": v.file_path,
                        "line": v.line_number,
                        "guidance": v.remediation_guidance,
                    }
                    for v in compliance_report.violations
                ],
            },
        }
        print(json.dumps(output_payload, indent=2))
        return 1 if verdict == "BLOCK" else 0

    # Rich Terminal ASCII Report
    print("")
    print(Term.bold(Term.cyan("+==============================================================================+")))
    print(Term.bold(Term.cyan("|            VECTIS SENTINEL -- AUTONOMOUS RELEASE SAFETY AUDIT                |")))
    print(Term.bold(Term.cyan("|            IBM Bob 2.0 Hackathon | Semantic Blast Radius Gate                |")))
    print(Term.bold(Term.cyan("+==============================================================================+")))
    print("")

    if verdict == "BLOCK":
        status_box = Term.bold(Term.red(" [ VERDICT: BLOCK ] [FAIL] RELEASE GATE CLOSED (Risk >= 70.0) "))
    else:
        status_box = Term.bold(Term.green(" [ VERDICT: PASS ] [PASS] RELEASE GATE OPEN (Risk < 70.0) "))

    print(f" Status: {status_box}")
    print(f" Total Risk Score:      {Term.bold(f'{total_score:.1f} / 100.0')}  (Threshold: {blocking_threshold})")
    print(f" Blast Depth Score:     {risk.get('blast_depth_score', 0.0):.1f}")
    print(f" Criticality Score:     {risk.get('criticality_score', 0.0):.1f}")
    print(f" Compliance Penalty:    {risk.get('compliance_penalty', 0.0):.1f}")
    print("")

    # Breaking changes section
    print(Term.bold("--- [!] Detected Breaking Contract Mutations ----------------------------------"))
    if breaking_changes:
        for idx, bc in enumerate(breaking_changes, start=1):
            sev = bc.get("severity", "critical").upper()
            sev_str = Term.red(f"[{sev}]") if sev == "CRITICAL" else Term.yellow(f"[{sev}]")
            print(f" {idx}. {sev_str} {Term.bold(bc.get('symbol_name', ''))} in {bc.get('file_path', '')}")
            print(f"    Type:        {bc.get('mutation_type', '')}")
            print(f"    Old:         {Term.dim(bc.get('old_signature', ''))}")
            print(f"    New:         {Term.cyan(bc.get('new_signature', ''))}")
            print(f"    Description: {bc.get('description', '')}")
    else:
        print(Term.green("  No contract-breaking changes detected."))
    print("")

    # Downstream impact section
    print(Term.bold("--- [*] Blast Radius: Downstream Impact ---------------------------------------"))
    if unique_impact:
        for idx, node in enumerate(unique_impact, start=1):
            service = node.get("service", "Microservice")
            depth = node.get("dependency_depth", 1)
            crit = node.get("criticality", 1.0)
            traffic = node.get("traffic_weight", 1.0)
            print(f" {idx}. {Term.bold(service)} ({Term.dim(node.get('file_path', ''))})")
            print(f"    Depth: {depth} | Criticality: {crit:.2f} | Traffic Weight: {traffic:.2f}")
    else:
        print(Term.green("  No downstream callers impacted."))
    print("")

    # Compliance section
    print(Term.bold("--- [~] PCI-DSS v4.0.1 & SOC2 Compliance Findings -----------------------------"))
    if compliance_report.violations:
        for idx, v in enumerate(compliance_report.violations, start=1):
            v_sev = Term.red(f"[{v.severity}]") if v.severity in ("CRITICAL", "HIGH") else Term.yellow(f"[{v.severity}]")
            print(f" {idx}. {v_sev} {Term.bold(v.rule_id)}: {v.symbol_name}")
            print(f"    File:        {v.file_path}:{v.line_number}")
            print(f"    Guidance:    {Term.cyan(v.remediation_guidance)}")
    else:
        print(Term.green("  All compliance rules passed."))
    print("")

    # Auto-heal recommendations
    if verdict == "BLOCK":
        print(Term.bold(Term.yellow("--- [?] IBM Granite 3.0 Auto-Heal Recommendation ------------------------------")))
        print("  Downstream runtime failures can be prevented automatically by generating an")
        print("  ES6 Proxy backward-compatibility shim. Run:")
        print(Term.cyan("    curl -X POST http://localhost:8000/api/auto-heal"))
        print("")

    if sarif_output:
        print(Term.dim(f" SARIF report written to: {sarif_output}"))
        print("")

    return 1 if verdict == "BLOCK" else 0


def handle_hook_install(args: argparse.Namespace) -> int:
    """Installs the pre-push git hook script."""
    repo_path = os.path.abspath(args.repo or os.getcwd())

    # Find .git directory
    git_dir = os.path.join(repo_path, ".git")
    if not os.path.isdir(git_dir):
        # Check upward
        curr = repo_path
        while curr and curr != os.path.dirname(curr):
            candidate = os.path.join(curr, ".git")
            if os.path.isdir(candidate):
                git_dir = candidate
                break
            curr = os.path.dirname(curr)

    if not os.path.isdir(git_dir):
        print(Term.red(f"[VECTIS] Error: No .git directory found at or above {repo_path}"), file=sys.stderr)
        return 1

    hooks_dir = os.path.join(git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    hook_file = os.path.join(hooks_dir, "pre-push")

    hook_content = """#!/usr/bin/env bash
# ==============================================================================
# VECTIS Sentinel -- Git Pre-Push Release Safety Hook
# IBM Bob 2.0 Hackathon -- Autonomous Release Safety
# ==============================================================================
# Executes AST change detection and blast radius analysis before any git push.
# Fails closed (exit code 1) on BLOCK (risk >= 70.0) to prevent broken deployments.

echo ""
echo "========================================================================="
echo "[VECTIS] Running pre-push semantic blast-radius and compliance audit..."
echo "========================================================================="

# Locate repository root and invoke VECTIS CLI
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

if [ -f "$REPO_ROOT/backend/app/cli.py" ]; then
    python "$REPO_ROOT/backend/app/cli.py" audit --repo "$REPO_ROOT"
elif [ -d "$REPO_ROOT/backend" ]; then
    (cd "$REPO_ROOT/backend" && python -m app.cli audit --repo "$REPO_ROOT")
else
    python -m app.cli audit
fi
AUDIT_EXIT=$?

if [ $AUDIT_EXIT -ne 0 ]; then
    echo ""
    echo "[VECTIS] ❌ PRE-PUSH BLOCKED: Release safety gate failed (risk >= 70.0)."
    echo "[VECTIS] A contract-breaking change was detected. Remediate or run auto-heal."
    echo ""
    exit 1
fi

echo "[VECTIS] ✅ Release safety audit passed. Proceeding with push."
echo ""
exit 0
"""

    try:
        with open(hook_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(hook_content)

        # Make executable on Unix-like environments
        try:
            os.chmod(hook_file, 0o755)
        except Exception:
            pass

        print("")
        print(Term.green("+==============================================================================+"))
        print(Term.green("|               [+] VECTIS SENTINEL PRE-PUSH HOOK INSTALLED                    |"))
        print(Term.green("+==============================================================================+"))
        print(f" Target Hook: {Term.bold(hook_file)}")
        print(" Protection:  Blocks dangerous pushes whenever risk >= 70.0 (FAIL-CLOSED)")
        print("")
        return 0

    except Exception as e:
        print(Term.red(f"[VECTIS] Failed to install pre-push hook: {e}"), file=sys.stderr)
        return 1


def handle_passport_verify(args: argparse.Namespace) -> int:
    """Verifies the cryptographic authenticity of an RFC 8785 release passport."""
    passport_file = os.path.abspath(args.file)
    secret = args.secret or os.getenv("VECTIS_PASSPORT_SECRET")

    if not os.path.isfile(passport_file):
        print(Term.red(f"[VECTIS] Error: Passport file not found: {passport_file}"), file=sys.stderr)
        return 1

    try:
        with open(passport_file, "r", encoding="utf-8") as f:
            passport_data = json.load(f)
    except json.JSONDecodeError as e:
        print(Term.red(f"[VECTIS] Error: Invalid JSON in passport file: {e}"), file=sys.stderr)
        return 1
    except Exception as e:
        print(Term.red(f"[VECTIS] Error reading passport file: {e}"), file=sys.stderr)
        return 1

    is_valid, message = verify_signed_passport(passport_data, secret=secret)

    print("")
    if is_valid:
        print(Term.bold(Term.green("+==============================================================================+")))
        print(Term.bold(Term.green("|            [+] VECTIS RELEASE PASSPORT: CRYPTOGRAPHICALLY VERIFIED           |")))
        print(Term.bold(Term.green("+==============================================================================+")))
        print(f" Status:        {Term.bold(Term.green('VALID & AUTHENTIC [PASS]'))}")
        print(f" PR Number:     #{passport_data.get('pr_number', 'N/A')}")
        print(f" Commit SHA:    {passport_data.get('commit_sha', 'N/A')}")
        print(f" Author:        {passport_data.get('author', 'N/A')}")
        print(f" Risk Score:    {passport_data.get('risk_score', 'N/A')} / 100.0")
        print(f" Verdict:       {passport_data.get('verdict', 'N/A')}")
        print(f" Shim Applied:  {passport_data.get('shim_applied', False)}")
        print(f" Issued At:     {passport_data.get('issued_at', 'N/A')}")
        print(f" Digest / Hash: {passport_data.get('passport_hash', 'N/A')}")
        print(f" Details:       {Term.cyan(message)}")
        print("")
        return 0
    else:
        print(Term.bold(Term.red("+==============================================================================+")))
        print(Term.bold(Term.red("|            [-] VECTIS RELEASE PASSPORT: VERIFICATION FAILED                  |")))
        print(Term.bold(Term.red("+==============================================================================+")))
        print(f" Status:        {Term.bold(Term.red('INVALID OR TAMPERED [FAIL]'))}")
        print(f" Reason:        {Term.red(message)}")
        print(f" Digest / Hash: {passport_data.get('passport_hash', 'N/A')}")
        print("")
        return 1


# ---------------------------------------------------------------------------
# CLI Argument Parser & Entrypoint
# ---------------------------------------------------------------------------

def create_parser() -> argparse.ArgumentParser:
    """Constructs the root argument parser for VECTIS CLI."""
    parser = argparse.ArgumentParser(
        prog="vectis",
        description="VECTIS Sentinel -- Autonomous Release Safety & CI/CD Runner (IBM Bob 2.0 Hackathon)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. audit
    audit_parser = subparsers.add_parser(
        "audit",
        help="Audit PR / branch diff for contract drift, blast radius, and PCI-DSS compliance",
    )
    audit_parser.add_argument(
        "--diff",
        default=None,
        help="Git diff specification, e.g., 'main...HEAD' or 'origin/main...HEAD'",
    )
    audit_parser.add_argument(
        "--staged",
        action="store_true",
        help="Audit staged changes only (git diff --cached)",
    )
    audit_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit output in machine-readable JSON format",
    )
    audit_parser.add_argument(
        "--sarif",
        default=None,
        help="File path to write OASIS SARIF v2.1.0 report (e.g. vectis-results.sarif)",
    )
    audit_parser.add_argument(
        "--repo",
        default=".",
        help="Path to repository root (defaults to current working directory)",
    )
    audit_parser.add_argument(
        "--threshold",
        type=float,
        default=70.0,
        help="Risk score threshold for BLOCK verdict (default: 70.0)",
    )

    # 2. hook
    hook_parser = subparsers.add_parser(
        "hook",
        help="Git hook management (install pre-push release gate)",
    )
    hook_subparsers = hook_parser.add_subparsers(dest="hook_command", required=True)
    hook_install_parser = hook_subparsers.add_parser(
        "install",
        help="Install pre-push release gate hook into .git/hooks/pre-push",
    )
    hook_install_parser.add_argument(
        "--repo",
        default=".",
        help="Path to repository root",
    )

    # 3. passport
    passport_parser = subparsers.add_parser(
        "passport",
        help="Release passport verification (RFC 8785)",
    )
    passport_subparsers = passport_parser.add_subparsers(dest="passport_command", required=True)
    passport_verify_parser = passport_subparsers.add_parser(
        "verify",
        help="Verify cryptographic authenticity of an RFC 8785 release passport",
    )
    passport_verify_parser.add_argument(
        "--file",
        required=True,
        help="Path to passport JSON file",
    )
    passport_verify_parser.add_argument(
        "--secret",
        default=None,
        help="HMAC verification secret (overrides VECTIS_PASSPORT_SECRET)",
    )

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.command == "audit":
        return handle_audit(parsed_args)
    elif parsed_args.command == "hook":
        if parsed_args.hook_command == "install":
            return handle_hook_install(parsed_args)
    elif parsed_args.command == "passport":
        if parsed_args.passport_command == "verify":
            return handle_passport_verify(parsed_args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
