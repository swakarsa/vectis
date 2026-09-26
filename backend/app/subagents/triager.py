"""
backend/app/subagents/triager.py
==================================
Autonomous PR Risk Triage Engine
VECTIS Autonomous Release Safety -- IBM Bob 2.0 Hackathon

This module is the orchestration brain of the VECTIS Sentinel.  It accepts
raw pull-request metadata and drives a five-phase triage pipeline that
coordinates every specialist subsystem:

Phase 1 -- Syntactic AST change extraction
    :class:`~app.ast.analyzer.ASTChangeDetector` parses TypeScript interfaces
    and emits structured mutation dicts for each breaking field change.

Phase 2 -- Topological impact traversal
    :class:`~app.ast.analyzer.DependencyDAGEngine` computes the directed
    reachability set from changed nodes and classifies each downstream
    consumer by criticality and traffic weight.

Phase 3 -- Security and regulatory compliance scoring
    :class:`~app.compliance.pci_dss_engine.PCIDSSComplianceEngine` evaluates
    the diff against PCI-DSS v4.0.1 and SOC2 CC6.1 rules and accumulates a
    penalty score.
    :class:`~app.risk.scorer.BlastRiskCalculator` combines the blast radius
    with the compliance penalty into a single 0-100 aggregate risk score.

Phase 4 -- IBM Granite 3.0 remediation dispatch
    When the verdict is BLOCK or WARN, :class:`~app.granite.synthesizer.IBMGraniteSynthesizer`
    synthesises a TypeScript ES6 Proxy backward-compatibility adapter that
    repairs the contract drift without requiring callers to change.

Phase 5 -- Release passport issuance decision
    A :class:`TriageVerdict` is returned.  When the verdict is PASS, the
    :class:`~app.schemas.blast.PassportSigner` issues an RFC 8785 cryptographic
    release passport authorising the merge.

Usage::

    from app.subagents.triager import AutonomousPRTriager, TriageVerdict

    triager = AutonomousPRTriager()
    verdict = triager.triage(
        pr_number=482,
        changed_files=["src/auth/session.ts"],
        raw_diff=git_patch_text,
        author="alex-dev",
        base_ref="main",
        head_ref="feature/refactor-auth",
        repo_path="/workspace/fixtures/sample-repo",
    )
    print(verdict.decision)          # "BLOCK" | "WARN" | "PASS"
    print(verdict.summary_markdown)  # GitHub PR comment body
"""

from __future__ import annotations

import datetime
import logging
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any, Optional

from ..ast.analyzer import ASTChangeDetector, DependencyDAGEngine
from ..compliance.pci_dss_engine import (
    ComplianceAuditReport,
    ComplianceViolation,
    PCIDSSComplianceEngine,
)
from ..granite.synthesizer import IBMGraniteSynthesizer, SynthesisResult
from ..risk.scorer import BlastRiskCalculator
from ..schemas.blast import PassportSigner

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Decision constants
# ---------------------------------------------------------------------------

BLOCK_THRESHOLD: float = 70.0
WARN_THRESHOLD: float = 30.0

# Aggregate risk ceilings that force human review regardless of score
HUMAN_OVERRIDE_RISK_FLOOR: float = 85.0

# ---------------------------------------------------------------------------
# Triage verdict data class
# ---------------------------------------------------------------------------


@dataclass
class TriageVerdict:
    """Complete output of one autonomous PR triage run.

    Attributes
    ----------
    decision:
        One of ``"BLOCK"``, ``"WARN"``, or ``"PASS"``.
    aggregate_risk_score:
        Normalised 0.0 - 100.0 composite score derived from blast radius,
        compliance penalties, and injection detection.
    summary_markdown:
        GitHub PR comment body in Markdown format.  Includes risk breakdown
        table, compliance violation matrix, downstream service impact list,
        and (when applicable) the synthesised remediation patch preview.
    remediation_patch:
        Complete TypeScript adapter source code synthesised by IBM Granite
        3.0 when ``decision`` is ``"BLOCK"`` or ``"WARN"``.  ``None`` when
        no remediation is necessary.
    affected_downstream_services:
        Human-readable names of the services downstream of the changed node.
    requires_human_override:
        ``True`` when ``aggregate_risk_score >= HUMAN_OVERRIDE_RISK_FLOOR``
        and even the synthesised patch cannot fully de-risk the change.
    release_passport:
        RFC 8785 signed passport dict when ``decision == "PASS"``,
        otherwise ``None``.
    phase_timings_ms:
        Per-phase wall-clock durations in milliseconds for telemetry.
    """

    decision: str
    aggregate_risk_score: float
    summary_markdown: str
    remediation_patch: Optional[str]
    affected_downstream_services: list[str]
    requires_human_override: bool
    release_passport: Optional[dict]
    phase_timings_ms: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Internal per-phase result containers
# ---------------------------------------------------------------------------


@dataclass
class _Phase1Result:
    breaking_changes: list[dict]
    mutation_count: int


@dataclass
class _Phase2Result:
    downstream_nodes: list[dict]
    impacted_services: list[str]
    max_depth: int


@dataclass
class _Phase3Result:
    risk_score: float
    risk_breakdown: dict
    compliance_report: ComplianceAuditReport


@dataclass
class _Phase4Result:
    synthesis: Optional[SynthesisResult]
    patch_available: bool


# ---------------------------------------------------------------------------
# Autonomous triage engine
# ---------------------------------------------------------------------------


class AutonomousPRTriager:
    """Five-phase autonomous pull-request triage orchestrator.

    Coordinates AST analysis, blast-radius graph traversal, PCI-DSS
    compliance scoring, IBM Granite 3.0 remediation synthesis, and release
    passport issuance into a single deterministic pipeline.

    Parameters
    ----------
    repo_path:
        Absolute or relative path to the repository root.  Required for
        the AST detector to read fixture files.  Defaults to ``"."``
        (current working directory).
    dag_engine:
        Optional pre-built :class:`~app.ast.analyzer.DependencyDAGEngine`.
        When ``None`` a fresh instance is created and the DAG is built from
        *repo_path*.
    compliance_engine:
        Optional pre-built :class:`~app.compliance.pci_dss_engine.PCIDSSComplianceEngine`.
        When ``None`` a default instance is used.
    synthesizer:
        Optional pre-built :class:`~app.granite.synthesizer.IBMGraniteSynthesizer`.
        When ``None`` an offline-mode synthesiser is created.
    """

    def __init__(
        self,
        repo_path: str = ".",
        dag_engine: Optional[DependencyDAGEngine] = None,
        compliance_engine: Optional[PCIDSSComplianceEngine] = None,
        synthesizer: Optional[IBMGraniteSynthesizer] = None,
    ) -> None:
        self._repo_path = repo_path
        self._dag = dag_engine or DependencyDAGEngine()
        self._compliance = compliance_engine or PCIDSSComplianceEngine()
        self._synth = synthesizer or IBMGraniteSynthesizer()
        self._risk_calc = BlastRiskCalculator()
        self._passport = PassportSigner()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def triage(
        self,
        pr_number: int,
        changed_files: list[str],
        raw_diff: str,
        author: str = "unknown",
        base_ref: str = "main",
        head_ref: str = "feature/unknown",
        repo_path: Optional[str] = None,
    ) -> TriageVerdict:
        """Execute the full five-phase triage pipeline for a pull request.

        Parameters
        ----------
        pr_number:
            GitHub pull-request number (used in passport and markdown report).
        changed_files:
            Repository-relative paths of all files touched by the PR.
        raw_diff:
            Full unified diff text (``git diff base..head``).
        author:
            GitHub username of the PR author.
        base_ref:
            Base branch or commit ref (e.g. ``"main"``).
        head_ref:
            Head branch or commit ref (e.g. ``"feature/refactor-auth"``).
        repo_path:
            Override the instance-level ``repo_path`` for this call.

        Returns
        -------
        TriageVerdict
            Complete verdict with markdown report, optional remediation patch,
            and (on PASS) a cryptographic release passport.
        """
        effective_repo = repo_path or self._repo_path
        timings: dict[str, float] = {}

        logger.info(
            "AutonomousPRTriager: starting triage for PR #%d by %s "
            "(%d files changed)",
            pr_number,
            author,
            len(changed_files),
        )

        # ---- Phase 1: AST mutation extraction ----
        t0 = _now_ms()
        phase1 = self._phase1_ast_extraction(
            changed_files=changed_files,
            base_ref=base_ref,
            head_ref=head_ref,
            repo_path=effective_repo,
        )
        timings["phase1_ast_ms"] = _now_ms() - t0
        logger.info(
            "Phase 1 complete: %d breaking change(s) detected",
            phase1.mutation_count,
        )

        # ---- Phase 2: Topological impact traversal ----
        t0 = _now_ms()
        phase2 = self._phase2_dag_traversal(
            breaking_changes=phase1.breaking_changes,
            repo_path=effective_repo,
        )
        timings["phase2_dag_ms"] = _now_ms() - t0
        logger.info(
            "Phase 2 complete: %d downstream node(s), max depth %d",
            len(phase2.downstream_nodes),
            phase2.max_depth,
        )

        # ---- Phase 3: Compliance and risk scoring ----
        t0 = _now_ms()
        phase3 = self._phase3_compliance_scoring(
            changed_files=changed_files,
            raw_diff=raw_diff,
            breaking_changes=phase1.breaking_changes,
            downstream_nodes=phase2.downstream_nodes,
        )
        timings["phase3_compliance_ms"] = _now_ms() - t0
        logger.info(
            "Phase 3 complete: risk_score=%.1f compliance_penalty=%.1f blocking=%s",
            phase3.risk_score,
            phase3.compliance_report.total_penalty,
            phase3.compliance_report.is_blocking,
        )

        # ---- Phase 4: Granite remediation dispatch ----
        t0 = _now_ms()
        phase4 = self._phase4_remediation(
            breaking_changes=phase1.breaking_changes,
            changed_files=changed_files,
            risk_score=phase3.risk_score,
        )
        timings["phase4_synthesis_ms"] = _now_ms() - t0

        # ---- Phase 5: Verdict and passport ----
        t0 = _now_ms()
        verdict = self._phase5_verdict(
            pr_number=pr_number,
            author=author,
            base_ref=base_ref,
            head_ref=head_ref,
            changed_files=changed_files,
            phase1=phase1,
            phase2=phase2,
            phase3=phase3,
            phase4=phase4,
            timings=timings,
        )
        timings["phase5_passport_ms"] = _now_ms() - t0
        verdict.phase_timings_ms = timings

        logger.info(
            "AutonomousPRTriager: triage complete -- decision=%s score=%.1f "
            "human_override=%s",
            verdict.decision,
            verdict.aggregate_risk_score,
            verdict.requires_human_override,
        )
        return verdict

    # ------------------------------------------------------------------
    # Phase implementations
    # ------------------------------------------------------------------

    def _phase1_ast_extraction(
        self,
        changed_files: list[str],
        base_ref: str,
        head_ref: str,
        repo_path: str,
    ) -> _Phase1Result:
        """Phase 1: Extract AST contract mutations from changed TypeScript files."""
        detector = ASTChangeDetector(repo_path=repo_path)
        all_mutations: list[dict] = []

        for file_path in changed_files:
            if not file_path.endswith((".ts", ".tsx", ".js", ".jsx")):
                continue
            try:
                mutations = detector.detect_contract_mutations(
                    file_path, base_ref, head_ref
                )
                all_mutations.extend(mutations)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Phase 1: failed to analyse %s: %s", file_path, exc
                )

        return _Phase1Result(
            breaking_changes=all_mutations,
            mutation_count=len(all_mutations),
        )

    def _phase2_dag_traversal(
        self,
        breaking_changes: list[dict],
        repo_path: str,
    ) -> _Phase2Result:
        """Phase 2: Traverse the dependency DAG to find downstream blast radius."""
        self._dag.build_graph(repo_path)
        all_downstream: list[dict] = []

        for change in breaking_changes:
            fp = change.get("file_path", "")
            sym = change.get("symbol_name", "")
            try:
                nodes = self._dag.calculate_downstream_impact(fp, sym)
                all_downstream.extend(nodes)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Phase 2: DAG traversal failed for %s/%s: %s", fp, sym, exc
                )

        # Deduplicate by node_id
        seen: set[str] = set()
        unique_nodes: list[dict] = []
        for n in all_downstream:
            nid = n.get("node_id", "")
            if nid and nid not in seen:
                seen.add(nid)
                unique_nodes.append(n)

        services = sorted({
            n.get("service", n.get("node_id", "unknown"))
            for n in unique_nodes
        })
        max_depth = self._dag.get_max_depth(unique_nodes)

        return _Phase2Result(
            downstream_nodes=unique_nodes,
            impacted_services=services,
            max_depth=max_depth,
        )

    def _phase3_compliance_scoring(
        self,
        changed_files: list[str],
        raw_diff: str,
        breaking_changes: list[dict],
        downstream_nodes: list[dict],
    ) -> _Phase3Result:
        """Phase 3: PCI-DSS compliance audit and composite risk scoring."""
        # Compliance check on the primary changed file(s)
        primary_file = changed_files[0] if changed_files else "unknown"
        compliance_report = self._compliance.audit_ast_diff(
            file_path=primary_file,
            diff_text=raw_diff,
            detected_mutations=breaking_changes,
        )

        # Blast-radius risk calculation
        num_compliance_violations = len(compliance_report.violations)
        risk = self._risk_calc.compute_risk_score(
            breaking_changes=breaking_changes,
            downstream_impact=downstream_nodes,
            total_repo_nodes=self._dag.get_total_node_count(),
            compliance_violations=num_compliance_violations,
            raw_diff=raw_diff,
        )

        return _Phase3Result(
            risk_score=risk["total_score"],
            risk_breakdown=risk,
            compliance_report=compliance_report,
        )

    def _phase4_remediation(
        self,
        breaking_changes: list[dict],
        changed_files: list[str],
        risk_score: float,
    ) -> _Phase4Result:
        """Phase 4: Dispatch IBM Granite 3.0 to synthesise a remediation shim.

        Synthesis is only triggered when breaking changes are present and the
        risk score is above the WARN threshold.
        """
        if not breaking_changes or risk_score < WARN_THRESHOLD:
            return _Phase4Result(synthesis=None, patch_available=False)

        try:
            result = self._synth.synthesize(
                breaking_changes=breaking_changes,
                changed_files=changed_files,
                target_symbol=_infer_target_symbol(breaking_changes),
            )
            logger.info(
                "Phase 4: IBM Granite 3.0 synthesised adapter (%s, %d chars)",
                result.model_used,
                len(result.adapter_code),
            )
            return _Phase4Result(synthesis=result, patch_available=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Phase 4: Granite synthesis failed: %s", exc
            )
            return _Phase4Result(synthesis=None, patch_available=False)

    def _phase5_verdict(
        self,
        pr_number: int,
        author: str,
        base_ref: str,
        head_ref: str,
        changed_files: list[str],
        phase1: _Phase1Result,
        phase2: _Phase2Result,
        phase3: _Phase3Result,
        phase4: _Phase4Result,
        timings: dict[str, float],
    ) -> TriageVerdict:
        """Phase 5: Compose final verdict, markdown report, and passport."""
        risk_score = phase3.risk_score

        # Decision logic
        if risk_score >= BLOCK_THRESHOLD or phase3.compliance_report.is_blocking:
            decision = "BLOCK"
        elif risk_score >= WARN_THRESHOLD:
            decision = "WARN"
        else:
            decision = "PASS"

        requires_human = risk_score >= HUMAN_OVERRIDE_RISK_FLOOR

        # Release passport: issued only for PASS
        passport: Optional[dict] = None
        if decision == "PASS":
            passport = self._passport.create_signed_passport(
                pr_number=pr_number,
                commit_sha=head_ref,
                author=author,
                risk_score=risk_score,
                verdict="PASS",
                shim_applied=phase4.patch_available,
            )

        # Remediation patch
        patch_code: Optional[str] = (
            phase4.synthesis.adapter_code
            if phase4.synthesis is not None
            else None
        )

        # Build markdown report
        md = _build_markdown_report(
            pr_number=pr_number,
            author=author,
            base_ref=base_ref,
            head_ref=head_ref,
            changed_files=changed_files,
            decision=decision,
            risk_score=risk_score,
            risk_breakdown=phase3.risk_breakdown,
            breaking_changes=phase1.breaking_changes,
            downstream_nodes=phase2.downstream_nodes,
            impacted_services=phase2.impacted_services,
            compliance_report=phase3.compliance_report,
            synthesis=phase4.synthesis,
            passport=passport,
            requires_human=requires_human,
            timings=timings,
        )

        return TriageVerdict(
            decision=decision,
            aggregate_risk_score=risk_score,
            summary_markdown=md,
            remediation_patch=patch_code,
            affected_downstream_services=phase2.impacted_services,
            requires_human_override=requires_human,
            release_passport=passport,
        )


# ---------------------------------------------------------------------------
# Markdown report builder
# ---------------------------------------------------------------------------


def _build_markdown_report(
    pr_number: int,
    author: str,
    base_ref: str,
    head_ref: str,
    changed_files: list[str],
    decision: str,
    risk_score: float,
    risk_breakdown: dict,
    breaking_changes: list[dict],
    downstream_nodes: list[dict],
    impacted_services: list[str],
    compliance_report: ComplianceAuditReport,
    synthesis: Optional[SynthesisResult],
    passport: Optional[dict],
    requires_human: bool,
    timings: dict[str, float],
) -> str:
    """Compose the full GitHub PR comment in Markdown.

    Sections
    --------
    1. Header with verdict badge
    2. Risk score breakdown table
    3. Breaking changes list
    4. Downstream service impact matrix
    5. Compliance violations table
    6. IBM Granite 3.0 remediation patch (collapsed)
    7. Release passport (on PASS)
    8. Triage pipeline timings
    """
    parts: list[str] = []

    # ---- 1. Header ----
    badge_map = {
        "BLOCK": "![BLOCK](https://img.shields.io/badge/Vectis%20Gate-BLOCK-red)",
        "WARN": "![WARN](https://img.shields.io/badge/Vectis%20Gate-WARN-orange)",
        "PASS": "![PASS](https://img.shields.io/badge/Vectis%20Gate-PASS-brightgreen)",
    }
    icon_map = {"BLOCK": "🚫", "WARN": "⚠️", "PASS": "✅"}
    badge = badge_map.get(decision, "")
    icon = icon_map.get(decision, "")

    parts.append(f"## {icon} Vectis Sentinel Release Gate — {decision}")
    parts.append("")
    parts.append(badge)
    parts.append("")
    parts.append(
        f"**PR #{pr_number}** | author: `{author}` | "
        f"`{base_ref}` &rarr; `{head_ref}`"
    )
    parts.append("")

    if requires_human:
        parts.append(
            "> **Human override required.** "
            "Risk score exceeds the autonomous triage ceiling. "
            "A senior engineer must review before merge."
        )
        parts.append("")

    # ---- 2. Risk score breakdown ----
    bd = risk_breakdown.get("breakdown", {})
    parts.append("### Risk Score Breakdown")
    parts.append("")
    parts.append("| Dimension | Score |")
    parts.append("|-----------|-------|")
    parts.append(
        f"| **Aggregate Risk Score** | **{risk_score:.1f} / 100** |"
    )
    parts.append(
        f"| Blast Depth Score | {risk_breakdown.get('blast_depth_score', 0):.1f} |"
    )
    parts.append(
        f"| Breaking Change Criticality | {risk_breakdown.get('criticality_score', 0):.1f} |"
    )
    parts.append(
        f"| Compliance Penalty | {risk_breakdown.get('compliance_penalty', 0):.1f} |"
    )
    parts.append(
        f"| Downstream Nodes Affected | {bd.get('downstream_nodes_affected', len(downstream_nodes))} |"
    )
    if risk_breakdown.get("injection_flag"):
        parts.append("| **CWE-94 Injection Detected** | **100.0** |")
    parts.append("")

    # ---- 3. Breaking changes ----
    if breaking_changes:
        parts.append(f"### Breaking Contract Mutations ({len(breaking_changes)})")
        parts.append("")
        parts.append("| Symbol | Type | Severity | Change Summary |")
        parts.append("|--------|------|----------|----------------|")
        for bc in breaking_changes:
            sym = bc.get("symbol_name", "-")
            mtype = bc.get("mutation_type", "-")
            sev = bc.get("severity", "unknown").upper()
            old_s = bc.get("old_signature", "")
            new_s = bc.get("new_signature", "")
            summary = f"`{old_s}` &rarr; `{new_s}`"
            if len(summary) > 80:
                summary = summary[:77] + "..."
            parts.append(f"| `{sym}` | `{mtype}` | {sev} | {summary} |")
        parts.append("")
    else:
        parts.append("### Breaking Contract Mutations")
        parts.append("")
        parts.append("_No breaking changes detected._")
        parts.append("")

    # ---- 4. Downstream service impact ----
    if downstream_nodes:
        parts.append(f"### Downstream Service Impact ({len(downstream_nodes)} nodes)")
        parts.append("")
        parts.append("| Service | File | Depth | Criticality | Traffic |")
        parts.append("|---------|------|-------|-------------|---------|")
        for node in downstream_nodes[:10]:  # cap table rows
            svc = node.get("service", node.get("node_id", "-"))
            fp = node.get("file_path", "-")
            depth = node.get("dependency_depth", "-")
            crit = node.get("criticality", 1.0)
            traffic = node.get("traffic_weight", 1.0)
            parts.append(
                f"| {svc} | `{fp}` | {depth} | {crit:.2f} | {traffic:.2f} |"
            )
        if len(downstream_nodes) > 10:
            parts.append(
                f"| _... {len(downstream_nodes) - 10} more_ | | | | |"
            )
        parts.append("")
    else:
        parts.append("### Downstream Service Impact")
        parts.append("")
        parts.append("_No downstream services affected._")
        parts.append("")

    # ---- 5. Compliance violations ----
    if compliance_report.violations:
        parts.append(
            f"### Compliance Violations ({len(compliance_report.violations)} found)"
        )
        parts.append("")
        parts.append("| Rule ID | Severity | Symbol | Penalty |")
        parts.append("|---------|----------|--------|---------|")
        for v in compliance_report.violations:
            parts.append(
                f"| `{v.rule_id}` | **{v.severity}** | `{v.symbol_name}` | {v.penalty_score:.1f} |"
            )
        parts.append("")
        parts.append(
            f"**Total compliance penalty: {compliance_report.total_penalty:.1f}** "
            f"(blocking threshold: 50.0)"
        )
        parts.append("")

        # Show remediation guidance for CRITICAL violations
        critical = [
            v for v in compliance_report.violations
            if v.severity == "CRITICAL"
        ]
        if critical:
            parts.append("<details>")
            parts.append(
                "<summary>Remediation guidance for CRITICAL violations</summary>"
            )
            parts.append("")
            for v in critical:
                parts.append(f"**{v.rule_id} -- `{v.symbol_name}`**")
                parts.append("")
                parts.append(f"> {v.remediation_guidance}")
                parts.append("")
            parts.append("</details>")
            parts.append("")
    else:
        parts.append("### Compliance Check")
        parts.append("")
        parts.append(
            "_All compliance rules passed._  "
            f"(Evaluated {compliance_report.evaluated_symbols_count} symbol(s))"
        )
        parts.append("")

    # ---- 6. Granite remediation patch ----
    if synthesis is not None:
        engine_label = (
            "IBM Granite 3.0 (live)"
            if synthesis.model_used != "deterministic-offline"
            else "Offline Deterministic Engine"
        )
        parts.append("### IBM Granite 3.0 Remediation Patch")
        parts.append("")
        parts.append(
            f"Auto-synthesised by **{engine_label}** "
            "to restore backward-compatibility for all downstream callers."
        )
        parts.append("")
        parts.append("<details>")
        parts.append(
            "<summary>View synthesised TypeScript adapter "
            "(<code>src/auth/auth_adapter.ts</code>)</summary>"
        )
        parts.append("")
        parts.append("```typescript")
        parts.append(synthesis.adapter_code)
        parts.append("```")
        parts.append("")
        parts.append(
            "_Apply via: `vectis auto-heal --pr "
            f"{pr_number} --commit`_"
        )
        parts.append("</details>")
        parts.append("")

    # ---- 7. Release passport (PASS only) ----
    if passport is not None:
        ph = passport.get("passport_hash", "")
        issued = passport.get("issued_at", "")
        parts.append("### Cryptographic Release Passport (RFC 8785)")
        parts.append("")
        parts.append(
            "This PR has been certified for production release by "
            "the Vectis Sentinel engine."
        )
        parts.append("")
        parts.append("```json")
        import json as _json
        parts.append(
            _json.dumps(
                {
                    "passport_hash": ph,
                    "verdict": "PASS",
                    "engine": "vectis-sentinel-v1.0",
                    "shim_applied": passport.get("shim_applied", False),
                    "issued_at": issued,
                },
                indent=2,
            )
        )
        parts.append("```")
        parts.append("")

    # ---- 8. Triage pipeline timings ----
    total_ms = sum(timings.values())
    parts.append("<details>")
    parts.append("<summary>Triage pipeline timings</summary>")
    parts.append("")
    parts.append("| Phase | Duration |")
    parts.append("|-------|----------|")
    phase_labels = {
        "phase1_ast_ms": "Phase 1 - AST extraction",
        "phase2_dag_ms": "Phase 2 - DAG traversal",
        "phase3_compliance_ms": "Phase 3 - Compliance scoring",
        "phase4_synthesis_ms": "Phase 4 - Granite synthesis",
        "phase5_passport_ms": "Phase 5 - Verdict & passport",
    }
    for key, label in phase_labels.items():
        ms = timings.get(key, 0.0)
        parts.append(f"| {label} | {ms:.1f} ms |")
    parts.append(f"| **Total** | **{total_ms:.1f} ms** |")
    parts.append("")
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    parts.append(
        f"_Audit timestamp: {ts} | "
        f"Engine fingerprint: `{compliance_report.engine_fingerprint[:16]}...`_"
    )
    parts.append("")
    parts.append("</details>")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_ms() -> float:
    """Return current time in milliseconds."""
    import time
    return time.perf_counter() * 1000.0


def _infer_target_symbol(breaking_changes: list[dict]) -> str:
    """Infer the primary TypeScript interface name from mutation dicts.

    Takes the interface portion of the first ``symbol_name`` that contains a
    dot (e.g. ``"User.id"`` -> ``"User"``).  Falls back to ``"SessionUser"``
    when no qualified name is found.
    """
    for change in breaking_changes:
        sym = change.get("symbol_name", "")
        if "." in sym:
            return sym.split(".")[0]
    return "SessionUser"
