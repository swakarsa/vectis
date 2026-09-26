"""
backend/tests/test_cli_and_sarif_and_crawler.py
===============================================
Comprehensive test suite for:
  1. IBMGraniteSynthesizer bidirectional Proxy `set` trap
  2. RFC 8785 HMAC-SHA256 PassportSigner and verify_signed_passport
  3. DynamicWorkspaceCrawler NetworkX monorepo dependency graph
  4. OASIS SARIF v2.1.0 compliance exporter
  5. Developer CLI runner (backend/app/cli.py)
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import networkx as nx

from app.granite.synthesizer import IBMGraniteSynthesizer
from app.schemas.blast import PassportSigner, verify_signed_passport
from app.ast.dag_crawler import DynamicWorkspaceCrawler, normalize_posix_path
from app.ast.analyzer import DependencyDAGEngine, ASTChangeDetector
from app.compliance.pci_dss_engine import (
    PCIDSSComplianceEngine,
    ComplianceAuditReport,
    ComplianceViolation,
    RULE_PCI_3_4_2,
    RULE_PCI_8_2_8,
    RULE_PCI_10_2_1,
    RULE_PCI_6_2_4,
    RULE_SOC2_CC6_1,
)
from app.compliance.sarif_exporter import SARIFExporter, SARIF_SCHEMA_URI, SARIF_VERSION
from app.cli import (
    main,
    create_parser,
    discover_modified_files,
    write_github_step_summary,
    handle_passport_verify,
    handle_hook_install,
    handle_audit,
)


# ===========================================================================
# 1. IBMGraniteSynthesizer Bidirectional `set` Trap Tests
# ===========================================================================

class TestGraniteSynthesizerSetTrap:
    """Validates the bidirectional `set` trap in IBMGraniteSynthesizer."""

    @pytest.fixture(autouse=True)
    def setup_synth(self):
        self.synth = IBMGraniteSynthesizer(force_offline=True)
        self.mutations = [
            {
                "file_path": "src/auth/session.ts",
                "symbol_name": "User.id",
                "mutation_type": "field_removed",
                "old_signature": "id: string",
                "new_signature": "sub: string (renamed to sub)",
                "severity": "critical",
                "line_number": 12,
            },
            {
                "file_path": "src/auth/session.ts",
                "symbol_name": "User.tier",
                "mutation_type": "field_removed",
                "old_signature": "tier: 'free' | 'pro' | 'enterprise'",
                "new_signature": "metadata: { tier: ... } (moved to nested object)",
                "severity": "critical",
                "line_number": 13,
            },
        ]

    def test_adapter_contains_set_trap(self):
        result = self.synth.synthesize(
            breaking_changes=self.mutations,
            changed_files=["src/auth/session.ts"],
        )
        code = result.adapter_code
        assert "set(target, prop, value, receiver)" in code
        assert "Reflect.set(target, prop, value, receiver)" in code

    def test_set_trap_intercepts_flat_legacy_key(self):
        result = self.synth.synthesize(
            breaking_changes=self.mutations,
            changed_files=["src/auth/session.ts"],
        )
        code = result.adapter_code
        assert 'if (prop === "id")' in code
        assert "target.sub = value;" in code
        assert "return true;" in code

    def test_set_trap_intercepts_nested_legacy_key(self):
        result = self.synth.synthesize(
            breaking_changes=self.mutations,
            changed_files=["src/auth/session.ts"],
        )
        code = result.adapter_code
        assert 'if (prop === "tier")' in code
        assert "if (!target.metadata) target.metadata = {};" in code
        assert "target.metadata.tier = value;" in code
        assert "return true;" in code

    def test_all_five_traps_present(self):
        result = self.synth.synthesize(
            breaking_changes=self.mutations,
            changed_files=["src/auth/session.ts"],
        )
        code = result.adapter_code
        assert "get(target, prop, receiver)" in code
        assert "set(target, prop, value, receiver)" in code
        assert "ownKeys(target)" in code
        assert "getOwnPropertyDescriptor(target, prop)" in code
        assert "has(target, prop)" in code


# ===========================================================================
# 2. RFC 8785 HMAC-SHA256 Passport Signer & Verification Tests
# ===========================================================================

class TestPassportSigningAndVerification:
    """Validates HMAC-SHA256 and SHA-256 release passport generation and verification."""

    def test_unkeyed_sha256_passport(self):
        signer = PassportSigner()
        passport = signer.create_signed_passport(
            pr_number=482,
            commit_sha="c8a9f24e9b",
            author="alex-dev",
            risk_score=12.0,
            verdict="PASS",
            shim_applied=True,
        )
        assert passport["passport_hash"].startswith("sha256:")
        assert passport["pr_number"] == 482
        assert passport["verdict"] == "PASS"

        is_valid, msg = verify_signed_passport(passport)
        assert is_valid is True
        assert "SHA-256" in msg

    def test_hmac_sha256_passport_with_explicit_secret(self):
        signer = PassportSigner(secret="repo-master-key-xyz")
        passport = signer.create_signed_passport(
            pr_number=501,
            commit_sha="9bf81a021",
            author="security-lead",
            risk_score=5.5,
            verdict="PASS",
            shim_applied=True,
        )
        assert passport["passport_hash"].startswith("hmac-sha256:")

        # Verify with matching secret
        is_valid, msg = verify_signed_passport(passport, secret="repo-master-key-xyz")
        assert is_valid is True
        assert "HMAC-SHA256" in msg

        # Verify with wrong secret
        is_valid, msg = verify_signed_passport(passport, secret="incorrect-key")
        assert is_valid is False
        assert "mismatch" in msg

    def test_hmac_sha256_passport_with_env_secret(self, monkeypatch):
        monkeypatch.setenv("VECTIS_PASSPORT_SECRET", "env-secret-42")
        signer = PassportSigner()
        passport = signer.create_signed_passport(
            pr_number=100,
            commit_sha="aabbcc",
            author="ci-bot",
            risk_score=0.0,
            verdict="PASS",
            shim_applied=False,
        )
        assert passport["passport_hash"].startswith("hmac-sha256:")

        is_valid, msg = verify_signed_passport(passport)
        assert is_valid is True

    def test_tampered_passport_fails_verification(self):
        signer = PassportSigner(secret="secret-key")
        passport = signer.create_signed_passport(
            pr_number=482,
            commit_sha="c8a9f24",
            author="alex-dev",
            risk_score=12.0,
            verdict="PASS",
            shim_applied=True,
        )
        # Malicious actor changes verdict to PASS and risk to 0
        tampered = dict(passport)
        tampered["risk_score"] = 0.0

        is_valid, msg = verify_signed_passport(tampered, secret="secret-key")
        assert is_valid is False
        assert "mismatch" in msg

    def test_verify_missing_hash(self):
        is_valid, msg = verify_signed_passport({"pr_number": 482})
        assert is_valid is False
        assert "Missing" in msg

    def test_signer_verify_instance_method(self):
        signer = PassportSigner(secret="instance-secret")
        passport = signer.create_signed_passport(
            pr_number=202,
            commit_sha="112233",
            author="tester",
            risk_score=15.0,
            verdict="PASS",
            shim_applied=True,
        )
        is_valid, _ = signer.verify(passport)
        assert is_valid is True


# ===========================================================================
# 3. DynamicWorkspaceCrawler Monorepo Dependency Graph Tests
# ===========================================================================

class TestDynamicWorkspaceCrawler:
    """Validates directory walking, ES import parsing, alias resolution, and fallback."""

    def test_crawl_real_temp_monorepo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock monorepo structure
            src = Path(tmpdir) / "src"
            models = src / "models"
            auth = src / "auth"
            payments = src / "payments"
            utils = src / "utils"

            for d in (models, auth, payments, utils):
                d.mkdir(parents=True)

            # models/user.ts
            (models / "user.ts").write_text("export interface User { id: string; }", encoding="utf-8")

            # utils/format.ts
            (utils / "format.ts").write_text("export const formatUser = (u: any) => u.id;", encoding="utf-8")

            # auth/session.ts imports models/user and utils/format
            (auth / "session.ts").write_text("""
import { User } from '../models/user';
import { formatUser } from '@/utils/format';
export class SessionManager {}
""", encoding="utf-8")

            # payments/checkout.ts imports auth/session
            (payments / "checkout.ts").write_text("""
import { SessionManager } from '../auth/session';
export const checkout = () => {};
""", encoding="utf-8")

            # Add an ignored directory with ts file
            node_modules = Path(tmpdir) / "node_modules" / "pkg"
            node_modules.mkdir(parents=True)
            (node_modules / "index.ts").write_text("export const ignoreMe = 1;", encoding="utf-8")

            crawler = DynamicWorkspaceCrawler(workspace_root=tmpdir)
            graph = crawler.crawl_workspace()

            # node_modules should not be present
            nodes = list(graph.nodes())
            assert not any("node_modules" in n for n in nodes)

            # Check nodes
            assert "src/models/user.ts" in graph
            assert "src/auth/session.ts" in graph
            assert "src/payments/checkout.ts" in graph
            assert "src/utils/format.ts" in graph

            # Check edges: producer -> consumer
            assert graph.has_edge("src/models/user.ts", "src/auth/session.ts")
            assert graph.has_edge("src/utils/format.ts", "src/auth/session.ts")
            assert graph.has_edge("src/auth/session.ts", "src/payments/checkout.ts")

            # Check heuristics
            auth_meta = graph.nodes["src/auth/session.ts"]
            assert auth_meta["criticality"] == 0.9
            assert auth_meta["traffic"] == 0.85

            util_meta = graph.nodes["src/utils/format.ts"]
            assert util_meta["criticality"] == 0.4
            assert util_meta["traffic"] == 0.5

    def test_merge_with_fallback_empty_workspace(self):
        crawler = DynamicWorkspaceCrawler()
        empty_graph = nx.DiGraph()
        merged = crawler.merge_with_fallback(empty_graph)
        assert merged.number_of_nodes() == 7
        assert "models/user.ts" in merged
        assert "auth/session.ts" in merged
        assert merged.has_edge("models/user.ts", "auth/session.ts")

    def test_merge_with_fallback_preserves_multi_node_graph(self):
        crawler = DynamicWorkspaceCrawler()
        graph = nx.DiGraph()
        graph.add_edge("a.ts", "b.ts")
        graph.add_edge("b.ts", "c.ts")
        merged = crawler.merge_with_fallback(graph)
        assert merged.number_of_nodes() == 3
        assert "a.ts" in merged

    def test_dependency_dag_engine_build_graph_integration(self):
        engine = DependencyDAGEngine()
        # Empty repo_path falls back to 7-node topology
        engine.build_graph("")
        assert engine.get_total_node_count() == 7
        assert engine.graph.has_edge("auth/session.ts", "payments/checkout.ts")

        # Downstream impact calculation
        impact = engine.calculate_downstream_impact("models/user.ts", "User")
        assert len(impact) > 0
        nodes = [i["node_id"] for i in impact]
        assert "auth/session.ts" in nodes


# ===========================================================================
# 4. OASIS SARIF v2.1.0 Exporter Tests
# ===========================================================================

class TestSARIFExporter:
    """Validates OASIS SARIF v2.1.0 schema compliance and rule definitions."""

    @pytest.fixture
    def sample_report(self) -> ComplianceAuditReport:
        violation1 = ComplianceViolation(
            violation_id="PCI-4.0.1-REQ-3.4.2:a1b2c3d4",
            rule_id=RULE_PCI_3_4_2,
            severity="CRITICAL",
            file_path="src/payments/card.ts",
            line_number=24,
            symbol_name="cardNumber",
            raw_snippet="cardNumber: string;",
            remediation_guidance="Apply IBM Granite 3.0 auto-heal tokenization shim.",
            penalty_score=30.0,
        )
        violation2 = ComplianceViolation(
            violation_id="PCI-4.0.1-REQ-10.2.1:e5f6g7h8",
            rule_id=RULE_PCI_10_2_1,
            severity="HIGH",
            file_path="src/auth/session.ts",
            line_number=12,
            symbol_name="User.id",
            raw_snippet="id: string -> sub: string",
            remediation_guidance="Apply IBM Granite 3.0 ES6 Proxy adapter with toJSON trap.",
            penalty_score=15.0,
        )
        return ComplianceAuditReport(
            total_penalty=45.0,
            is_blocking=False,
            violations=[violation1, violation2],
            passed_rules=[RULE_PCI_8_2_8, RULE_PCI_6_2_4, RULE_SOC2_CC6_1],
            evaluated_symbols_count=10,
            audit_timestamp="2026-09-26T18:00:00Z",
            engine_fingerprint="abc123def456",
        )

    def test_export_sarif_structure(self, sample_report):
        exporter = SARIFExporter()
        sarif = exporter.export_sarif(sample_report)

        assert sarif["$schema"] == SARIF_SCHEMA_URI
        assert sarif["version"] == SARIF_VERSION
        assert len(sarif["runs"]) == 1

        run = sarif["runs"][0]
        driver = run["tool"]["driver"]
        assert driver["name"] == "VECTIS Sentinel"
        assert driver["version"] == "1.0.0"

        # Check all 5 rules are registered in driver.rules
        rule_ids = {r["id"] for r in driver["rules"]}
        assert RULE_PCI_3_4_2 in rule_ids
        assert RULE_PCI_8_2_8 in rule_ids
        assert RULE_PCI_10_2_1 in rule_ids
        assert RULE_PCI_6_2_4 in rule_ids
        assert RULE_SOC2_CC6_1 in rule_ids

        # Check security severity on rules
        pci_342_rule = next(r for r in driver["rules"] if r["id"] == RULE_PCI_3_4_2)
        assert pci_342_rule["properties"]["security-severity"] == "9.0"

        pci_1021_rule = next(r for r in driver["rules"] if r["id"] == RULE_PCI_10_2_1)
        assert pci_1021_rule["properties"]["security-severity"] == "7.0"

    def test_export_sarif_results(self, sample_report):
        exporter = SARIFExporter()
        sarif = exporter.export_sarif(sample_report)
        results = sarif["runs"][0]["results"]

        assert len(results) == 2

        r1 = results[0]
        assert r1["ruleId"] == RULE_PCI_3_4_2
        assert r1["level"] == "error"
        assert r1["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "src/payments/card.ts"
        assert r1["locations"][0]["physicalLocation"]["region"]["startLine"] == 24
        assert "Granite 3.0" in r1["fixes"][0]["description"]["text"]

        r2 = results[1]
        assert r2["ruleId"] == RULE_PCI_10_2_1
        assert r2["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "src/auth/session.ts"

    def test_write_sarif_file(self, sample_report):
        exporter = SARIFExporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "audit-results.sarif")
            res_path = exporter.write_sarif_file(sample_report, output_path=out_file)
            assert os.path.isfile(res_path)

            with open(res_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            assert loaded["version"] == "2.1.0"
            assert len(loaded["runs"][0]["results"]) == 2


# ===========================================================================
# 5. Developer CLI & CI/CD Runner Tests
# ===========================================================================

class TestVectisCLI:
    """Validates the CLI commands: audit, hook install, and passport verify."""

    def test_parser_configuration(self):
        parser = create_parser()
        args = parser.parse_args(["audit", "--json", "--threshold", "80.0"])
        assert args.command == "audit"
        assert args.json is True
        assert args.threshold == 80.0

        args = parser.parse_args(["hook", "install"])
        assert args.command == "hook"
        assert args.hook_command == "install"

        args = parser.parse_args(["passport", "verify", "--file", "passport.json"])
        assert args.command == "passport"
        assert args.passport_command == "verify"
        assert args.file == "passport.json"

    def test_audit_json_output(self, capsys):
        parser = create_parser()
        args = parser.parse_args(["audit", "--json"])
        exit_code = handle_audit(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "success"
        assert "verdict" in data
        assert "risk_assessment" in data
        assert exit_code in (0, 1)

    def test_passport_verify_cli_success(self, capsys):
        signer = PassportSigner()
        passport = signer.create_signed_passport(
            pr_number=777,
            commit_sha="fedcba98",
            author="release-eng",
            risk_score=10.0,
            verdict="PASS",
            shim_applied=True,
        )

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            json.dump(passport, f)
            temp_path = f.name

        try:
            parser = create_parser()
            args = parser.parse_args(["passport", "verify", "--file", temp_path])
            exit_code = handle_passport_verify(args)
            assert exit_code == 0

            captured = capsys.readouterr()
            assert "CRYPTOGRAPHICALLY VERIFIED" in captured.out
            assert "VALID & AUTHENTIC" in captured.out
        finally:
            os.remove(temp_path)

    def test_passport_verify_cli_failure(self, capsys):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            json.dump({"pr_number": 1, "passport_hash": "sha256:0000000000"}, f)
            temp_path = f.name

        try:
            parser = create_parser()
            args = parser.parse_args(["passport", "verify", "--file", temp_path])
            exit_code = handle_passport_verify(args)
            assert exit_code == 1

            captured = capsys.readouterr()
            assert "VERIFICATION FAILED" in captured.out
        finally:
            os.remove(temp_path)

    def test_hook_install_cli(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock .git directory
            os.makedirs(os.path.join(tmpdir, ".git"))

            parser = create_parser()
            args = parser.parse_args(["hook", "install", "--repo", tmpdir])
            exit_code = handle_hook_install(args)
            assert exit_code == 0

            hook_file = os.path.join(tmpdir, ".git", "hooks", "pre-push")
            assert os.path.isfile(hook_file)
            with open(hook_file, "r", encoding="utf-8") as f:
                content = f.read()
            assert "python -m app.cli audit" in content

    def test_github_step_summary_generation(self, monkeypatch):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            summary_path = f.name

        try:
            monkeypatch.setenv("GITHUB_ACTIONS", "true")
            monkeypatch.setenv("GITHUB_STEP_SUMMARY", summary_path)

            write_github_step_summary(
                verdict="BLOCK",
                risk={"total_score": 88.5, "blast_depth_score": 25.0, "criticality_score": 36.0, "compliance_penalty": 30.0},
                breaking_changes=[{
                    "file_path": "src/auth/session.ts",
                    "symbol_name": "User.id",
                    "mutation_type": "field_removed",
                    "severity": "critical",
                    "description": "Property id renamed to sub",
                }],
                downstream_impact=[{
                    "service": "Billing Gateway",
                    "file_path": "src/payments/checkout.ts",
                    "dependency_depth": 1,
                    "criticality": 1.0,
                    "traffic_weight": 0.9,
                }],
                compliance_violations=[],
            )

            with open(summary_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "VECTIS Sentinel -- Release Safety & Blast Radius Report" in content
            assert "BLOCKED" in content
            assert "88.5 / 100.0" in content
            assert "User.id" in content
            assert "Billing Gateway" in content
        finally:
            if os.path.exists(summary_path):
                os.remove(summary_path)
