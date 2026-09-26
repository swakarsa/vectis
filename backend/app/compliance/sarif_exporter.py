"""
backend/app/compliance/sarif_exporter.py
========================================
OASIS SARIF v2.1.0 Standard Exporter for GitHub Advanced Security
VECTIS Autonomous Release Safety -- IBM Bob 2.0 Hackathon

Converts PCI-DSS v4.0.1 and SOC2 Type II compliance audit reports into
valid OASIS SARIF v2.1.0 JSON payloads for GitHub Code Scanning ingestion.
Includes rich rule definitions, security severity scores (9.0 critical, 7.0 high),
physical artifact URI locations, code snippets, and IBM Granite 3.0 auto-heal guidance.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .pci_dss_engine import (
    RULE_PCI_3_4_2,
    RULE_PCI_8_2_8,
    RULE_PCI_10_2_1,
    RULE_PCI_6_2_4,
    RULE_SOC2_CC6_1,
    ComplianceAuditReport,
    ComplianceViolation,
)

SARIF_SCHEMA_URI = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
)
SARIF_VERSION = "2.1.0"

# Canonical metadata for all supported VECTIS compliance rules
RULE_METADATA_CATALOGUE: Dict[str, Dict[str, Any]] = {
    RULE_PCI_3_4_2: {
        "id": RULE_PCI_3_4_2,
        "name": "PCI-REQ-3.4.2-PAN-Exposure",
        "shortDescription": {
            "text": "PCI-DSS v4.0.1 Req 3.4.2: PAN / CVV / Card Expiry Exposed in Schema"
        },
        "fullDescription": {
            "text": (
                "PCI-DSS v4.0.1 Req 3.4.2 mandates that Primary Account Numbers (PAN), "
                "CVVs, and card expiry dates must never be exposed as unencrypted or "
                "un-tokenized plaintext fields in exported TypeScript schemas or API payloads."
            )
        },
        "helpUri": "https://docs.pcisecuritystandards.org/PCI%20DSS/Standard/PCI-DSS-v4_0_1.pdf#page=45",
        "help": {
            "text": (
                "Tokenize or redact cardholder data before contract serialization. "
                "Apply an IBM Granite 3.0 auto-heal shim to replace raw properties with tokenized accessors."
            ),
            "markdown": (
                "### Remediation Guidance\n"
                "1. Tokenize or redact all cardholder data before exporting schema fields.\n"
                "2. Apply an **IBM Granite 3.0 auto-heal shim** to wrap property accessors in cryptographic token references.\n"
                "3. Reference: *PCI-DSS v4.0.1 Requirement 3.4.2*."
            ),
        },
        "defaultConfiguration": {"level": "error"},
        "properties": {
            "tags": ["security", "compliance", "pci-dss", "cwe-312", "financial-data"],
            "security-severity": "9.0",
            "precision": "very-high",
            "problem.severity": "error",
        },
    },
    RULE_PCI_8_2_8: {
        "id": RULE_PCI_8_2_8,
        "name": "PCI-REQ-8.2.8-Auth-Credential-Exposure",
        "shortDescription": {
            "text": "PCI-DSS v4.0.1 Req 8.2.8: Raw Authentication Credential in Interface Contract"
        },
        "fullDescription": {
            "text": (
                "PCI-DSS v4.0.1 Req 8.2.8 strictly prohibits hardcoded passwords, API keys, "
                "bearer tokens, or cryptographic private keys in serializable interface contracts."
            )
        },
        "helpUri": "https://docs.pcisecuritystandards.org/PCI%20DSS/Standard/PCI-DSS-v4_0_1.pdf#page=82",
        "help": {
            "text": (
                "Remove credential literals and secrets from interface definitions. "
                "Inject secret resolution dynamically via IBM Secrets Manager or an auto-heal shim."
            ),
            "markdown": (
                "### Remediation Guidance\n"
                "1. Remove raw credential fields and literals from public interface contracts.\n"
                "2. Inject dynamic credential resolution via an enterprise secrets manager.\n"
                "3. Use **IBM Granite 3.0 auto-heal shims** to insulate downstream callers."
            ),
        },
        "defaultConfiguration": {"level": "error"},
        "properties": {
            "tags": ["security", "compliance", "pci-dss", "cwe-798", "secrets"],
            "security-severity": "9.0",
            "precision": "very-high",
            "problem.severity": "error",
        },
    },
    RULE_PCI_10_2_1: {
        "id": RULE_PCI_10_2_1,
        "name": "PCI-REQ-10.2.1-Audit-Log-Identity-Continuity",
        "shortDescription": {
            "text": "PCI-DSS v4.0.1 Req 10.2.1: Audit Log Identity / Principal Mutation Without Shim"
        },
        "fullDescription": {
            "text": (
                "PCI-DSS v4.0.1 Req 10.2.1 requires an unbroken, auditable link to individual "
                "user identities for all system actions. Renaming or removing user identification "
                "properties without a backward-compatible serialization shim (toJSON / Proxy traps) "
                "breaks downstream audit event correlation."
            )
        },
        "helpUri": "https://docs.pcisecuritystandards.org/PCI%20DSS/Standard/PCI-DSS-v4_0_1.pdf#page=102",
        "help": {
            "text": (
                "Apply an IBM Granite 3.0 ES6 Proxy backward-compatibility adapter with a toJSON trap "
                "and bidirectional property mappings to maintain audit trail continuity."
            ),
            "markdown": (
                "### Remediation Guidance\n"
                "1. Generate an **IBM Granite 3.0 ES6 Proxy adapter** containing `get`, `set`, and `toJSON` traps.\n"
                "2. Ensure legacy properties like `.id` transparently bridge to modern `.sub` in serialized audit records.\n"
                "3. Reference: *PCI-DSS v4.0.1 Requirement 10.2.1*."
            ),
        },
        "defaultConfiguration": {"level": "error"},
        "properties": {
            "tags": ["security", "compliance", "pci-dss", "audit-trail", "identity-continuity"],
            "security-severity": "7.0",
            "precision": "very-high",
            "problem.severity": "error",
        },
    },
    RULE_PCI_6_2_4: {
        "id": RULE_PCI_6_2_4,
        "name": "PCI-REQ-6.2.4-Injection-Surface",
        "shortDescription": {
            "text": "PCI-DSS v4.0.1 Req 6.2.4: Code / Prompt Injection Surface (CWE-94)"
        },
        "fullDescription": {
            "text": (
                "PCI-DSS v4.0.1 Req 6.2.4 mandates protections against code injection and adversarial "
                "prompt-injection instructions (CWE-94) embedded in code, comments, or diffs that attempt "
                "to override automated release safety gates."
            )
        },
        "helpUri": "https://docs.pcisecuritystandards.org/PCI%20DSS/Standard/PCI-DSS-v4_0_1.pdf#page=62",
        "help": {
            "text": (
                "Remove adversarial prompt-injection patterns and gate-bypass directives from the diff."
            ),
            "markdown": (
                "### Remediation Guidance\n"
                "1. Strip any prompt injection instructions (e.g. `ignore all rules`, `skip gate`).\n"
                "2. Maintain strict deterministic code review integrity."
            ),
        },
        "defaultConfiguration": {"level": "error"},
        "properties": {
            "tags": ["security", "compliance", "pci-dss", "cwe-94", "prompt-injection", "ai-safety"],
            "security-severity": "9.0",
            "precision": "very-high",
            "problem.severity": "error",
        },
    },
    RULE_SOC2_CC6_1: {
        "id": RULE_SOC2_CC6_1,
        "name": "SOC2-CC6.1-Tenant-Isolation-Removal",
        "shortDescription": {
            "text": "SOC2 Type II CC6.1: Tenant Isolation Identifier Dropped from Contract"
        },
        "fullDescription": {
            "text": (
                "SOC2 Trust Services Criteria CC6.1 requires logical tenant boundary enforcement. "
                "Removing tenant identifiers (e.g., organizationId, tenantId) without replacement "
                "introduces severe risk of cross-tenant data leakage in multi-tenant cloud services."
            )
        },
        "helpUri": "https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services",
        "help": {
            "text": (
                "Restore tenant partition identifiers or apply an IBM Granite 3.0 shim to bridge multi-tenant context."
            ),
            "markdown": (
                "### Remediation Guidance\n"
                "1. Retain tenant partition identifiers on all public request and response contracts.\n"
                "2. Use **IBM Granite 3.0 auto-heal shims** to synthesize backward-compatible tenant metadata."
            ),
        },
        "defaultConfiguration": {"level": "error"},
        "properties": {
            "tags": ["security", "compliance", "soc2", "tenant-isolation", "data-protection"],
            "security-severity": "7.0",
            "precision": "very-high",
            "problem.severity": "error",
        },
    },
}


class SARIFExporter:
    """
    Exports VECTIS compliance violations and release safety audit reports
    into the OASIS SARIF v2.1.0 standard schema for GitHub Advanced Security.
    """

    def __init__(self, tool_name: str = "VECTIS Sentinel", tool_version: str = "1.0.0"):
        self.tool_name = tool_name
        self.tool_version = tool_version

    def export_sarif(self, report: ComplianceAuditReport) -> Dict[str, Any]:
        """
        Converts a ComplianceAuditReport into a valid OASIS SARIF v2.1.0 dictionary payload.
        """
        rules_list: List[Dict[str, Any]] = list(RULE_METADATA_CATALOGUE.values())
        rule_id_to_index: Dict[str, int] = {
            r["id"]: idx for idx, r in enumerate(rules_list)
        }

        results: List[Dict[str, Any]] = []

        for v in report.violations:
            rule_id = v.rule_id
            rule_idx = rule_id_to_index.get(rule_id, -1)

            # Determine SARIF result level
            level = "error" if v.severity in ("CRITICAL", "HIGH") else (
                "warning" if v.severity == "MEDIUM" else "note"
            )

            # Clean and normalize file URI
            normalized_path = v.file_path.replace("\\", "/").strip()
            if normalized_path.startswith("./"):
                normalized_path = normalized_path[2:]

            start_line = max(v.line_number, 1)
            snippet_text = v.raw_snippet.strip() if v.raw_snippet else f"Violation: {v.symbol_name}"

            result_entry: Dict[str, Any] = {
                "ruleId": rule_id,
                "level": level,
                "message": {
                    "text": (
                        f"[{v.severity}] {v.symbol_name}: {v.remediation_guidance}"
                    )
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": normalized_path,
                                "uriBaseId": "%SRCROOT%",
                            },
                            "region": {
                                "startLine": start_line,
                                "startColumn": 1,
                                "snippet": {
                                    "text": snippet_text,
                                },
                            },
                        }
                    }
                ],
                "fixes": [
                    {
                        "description": {
                            "text": (
                                f"Apply IBM Granite 3.0 auto-heal shim: {v.remediation_guidance}"
                            )
                        },
                        "artifactChanges": [
                            {
                                "artifactLocation": {
                                    "uri": normalized_path,
                                    "uriBaseId": "%SRCROOT%",
                                },
                                "replacements": [
                                    {
                                        "deletedRegion": {
                                            "startLine": start_line,
                                            "startColumn": 1,
                                        },
                                        "insertedContent": {
                                            "text": f"// Vectis Auto-Heal Shim: {v.remediation_guidance}\n",
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ],
                "properties": {
                    "violationId": v.violation_id,
                    "symbolName": v.symbol_name,
                    "severity": v.severity,
                    "penaltyScore": v.penalty_score,
                    "remediationGuidance": v.remediation_guidance,
                    "autoHealShimAvailable": True,
                },
            }

            if rule_idx >= 0:
                result_entry["ruleIndex"] = rule_idx

            results.append(result_entry)

        sarif_payload: Dict[str, Any] = {
            "$schema": SARIF_SCHEMA_URI,
            "version": SARIF_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.tool_name,
                            "version": self.tool_version,
                            "semanticVersion": self.tool_version,
                            "informationUri": "https://github.com/swakarsa/vectis",
                            "rules": rules_list,
                        }
                    },
                    "results": results,
                    "invocations": [
                        {
                            "executionSuccessful": not report.is_blocking,
                            "endTimeUtc": report.audit_timestamp,
                            "properties": {
                                "totalPenalty": report.total_penalty,
                                "isBlocking": report.is_blocking,
                                "evaluatedSymbols": report.evaluated_symbols_count,
                                "engineFingerprint": report.engine_fingerprint,
                            },
                        }
                    ],
                }
            ],
        }

        return sarif_payload

    def write_sarif_file(
        self, report: ComplianceAuditReport, output_path: str = "vectis-results.sarif"
    ) -> str:
        """
        Serializes and writes the SARIF v2.1.0 payload to disk.
        Creates parent directories if necessary.
        """
        payload = self.export_sarif(report)
        abs_output = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)

        with open(abs_output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return abs_output
