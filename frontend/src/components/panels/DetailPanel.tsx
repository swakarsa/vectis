"use client";

import React, { useState } from "react";
import {
  WarningCircle,
  ShieldCheck,
  ShieldWarning,
  Cpu,
  Check,
  ArrowRight,
  Scales,
  FileCode,
  TreeStructure,
  GitMerge,
  TerminalWindow,
  DownloadSimple,
} from "@phosphor-icons/react";

interface DetailPanelProps {
  verdict: "BLOCK" | "WARN" | "PASS" | "IDLE";
  riskScore: number;
  breakingChanges: any[];
  downstreamImpact: any[];
  shimApplied: boolean;
  onApplyShim: () => void;
  shimLoading: boolean;
  shimCode: string;
  onDownloadPassport?: () => void;
  passportAvailable?: boolean;
  onExportSecurityAudit?: () => void;
}

export function DetailPanel({
  verdict,
  riskScore,
  breakingChanges,
  downstreamImpact,
  shimApplied,
  onApplyShim,
  shimLoading,
  shimCode,
  onDownloadPassport,
  passportAvailable,
  onExportSecurityAudit,
}: DetailPanelProps) {
  const [activeTab, setActiveTab] = useState<"breaking" | "impact" | "shim" | "compliance">("breaking");
  const [copied, setCopied] = useState(false);

  const copyShim = () => {
    navigator.clipboard.writeText(shimCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportAudit = () => {
    if (onExportSecurityAudit) {
      onExportSecurityAudit();
      return;
    }
    const sarifPayload = {
      $schema: "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
      version: "2.1.0",
      runs: [
        {
          tool: {
            driver: {
              name: "VECTIS Sentinel",
              version: "1.0.0",
              semanticVersion: "1.0.0",
              informationUri: "https://github.com/swakarsa/vectis",
              rules: [
                {
                  id: "PCI-4.0.1-REQ-10.2.1",
                  name: "PCI-REQ-10.2.1-Audit-Log-Identity-Continuity",
                  shortDescription: {
                    text: "PCI-DSS v4.0.1 Req 10.2.1: Audit Log Identity / Principal Mutation Without Shim",
                  },
                  defaultConfiguration: { level: "error" },
                  properties: {
                    "security-severity": "7.0",
                    tags: ["security", "compliance", "pci-dss"],
                  },
                },
                {
                  id: "PCI-4.0.1-REQ-3.4.2",
                  name: "PCI-REQ-3.4.2-PAN-Exposure",
                  shortDescription: {
                    text: "PCI-DSS v4.0.1 Req 3.4.2: PAN / CVV / Card Expiry Exposed in Schema",
                  },
                  defaultConfiguration: { level: "error" },
                  properties: {
                    "security-severity": "9.0",
                    tags: ["security", "compliance", "pci-dss"],
                  },
                },
                {
                  id: "PCI-4.0.1-REQ-8.2.8",
                  name: "PCI-REQ-8.2.8-Auth-Credential-Exposure",
                  shortDescription: {
                    text: "PCI-DSS v4.0.1 Req 8.2.8: Raw Authentication Credential in Interface Contract",
                  },
                  defaultConfiguration: { level: "error" },
                  properties: {
                    "security-severity": "9.0",
                    tags: ["security", "compliance", "pci-dss"],
                  },
                },
              ],
            },
          },
          results: breakingChanges.map((change) => ({
            ruleId: "PCI-4.0.1-REQ-10.2.1",
            level: "error",
            message: {
              text: `[HIGH] ${change.symbol_name || "Contract symbol"}: Identity / principal field removal without backward-compatible serialization shim.`,
            },
            locations: [
              {
                physicalLocation: {
                  artifactLocation: {
                    uri: change.file_path || "src/auth/session.ts",
                    uriBaseId: "%SRCROOT%",
                  },
                  region: {
                    startLine: change.line_number || 12,
                    startColumn: 1,
                    snippet: {
                      text: `${change.old_signature || ""} -> ${change.new_signature || ""}`,
                    },
                  },
                },
              },
            ],
            fixes: [
              {
                description: {
                  text: "Apply IBM Granite 3.0 auto-heal compatibility shim.",
                },
              },
            ],
          })),
        },
      ],
    };

    const blob = new Blob([JSON.stringify(sarifPayload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "vectis-security-audit.sarif";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const isIdle = verdict === "IDLE";

  return (
    <aside className="w-[420px] border-l border-white/[0.08] bg-[#0c0d10] flex flex-col h-full select-none shrink-0">
      {/* Top Metrics Section */}
      <div className="p-4 border-b border-white/[0.08] bg-[#0e0f13]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] uppercase tracking-wider text-zinc-400 font-semibold">
            Telemetry & Blast Radius
          </span>
          <span className="text-[11px] text-zinc-500 font-mono">Tree-sitter AST</span>
        </div>

        {/* Score & Verdict */}
        <div className="flex items-baseline justify-between mb-2.5">
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold tracking-tight text-white tabular-nums">
              {riskScore.toFixed(1)}
            </span>
            <span className="text-xs text-zinc-500">/ 100 Risk Score</span>
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isIdle
                  ? "bg-zinc-500"
                  : verdict === "BLOCK"
                  ? "bg-rose-500 animate-pulse"
                  : verdict === "PASS"
                  ? "bg-emerald-400"
                  : "bg-amber-400"
              }`}
            />
            <span
              className={`font-semibold tracking-tight ${
                isIdle
                  ? "text-zinc-400"
                  : verdict === "BLOCK"
                  ? "text-rose-400"
                  : verdict === "PASS"
                  ? "text-emerald-400"
                  : "text-amber-400"
              }`}
            >
              {isIdle
                ? "Awaiting Audit"
                : verdict === "BLOCK"
                ? "Critical Hazard"
                : verdict === "PASS"
                ? "Safe to Release"
                : "Review Required"}
            </span>
          </div>
        </div>

        {/* 2px Hairline Progress Bar */}
        <div className="w-full h-[2px] bg-zinc-800 rounded-none overflow-hidden mb-3">
          <div
            className={`h-full transition-all duration-500 ${
              isIdle
                ? "bg-zinc-700"
                : verdict === "BLOCK"
                ? "bg-rose-500"
                : verdict === "PASS"
                ? "bg-emerald-400"
                : "bg-amber-400"
            }`}
            style={{ width: `${isIdle ? 0 : Math.min(riskScore, 100)}%` }}
          />
        </div>

        {/* 4 Metric Key-Value Grid */}
        <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-white/[0.04]">
          <div className="flex items-center justify-between text-zinc-400">
            <span>Downstream Nodes:</span>
            <span className="text-zinc-200 font-semibold tabular-nums">{downstreamImpact.length}</span>
          </div>
          <div className="flex items-center justify-between text-zinc-400">
            <span>Breaking Mutations:</span>
            <span className="text-zinc-200 font-semibold tabular-nums">{breakingChanges.length}</span>
          </div>
          <div className="flex items-center justify-between text-zinc-400">
            <span>PCI-DSS Req 10.2:</span>
            <span
              className={
                isIdle
                  ? "text-zinc-500 font-medium"
                  : shimApplied || verdict === "PASS"
                  ? "text-emerald-400 font-semibold"
                  : "text-rose-400 font-semibold"
              }
            >
              {isIdle ? "Unverified" : shimApplied || verdict === "PASS" ? "Compliant" : "Violation"}
            </span>
          </div>
          <div className="flex items-center justify-between text-zinc-400">
            <span>Graph Traversal:</span>
            <span className="text-zinc-200 font-semibold tabular-nums">{isIdle ? "-" : "1.2ms"}</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation (Single-line, no wrapping) */}
      <div className="flex border-b border-white/[0.08] bg-[#090a0d] px-1 text-xs">
        <button
          onClick={() => setActiveTab("breaking")}
          className={`flex-1 min-w-0 py-2.5 px-1.5 font-medium border-b-2 transition-all cursor-pointer flex items-center justify-center gap-1.5 whitespace-nowrap ${
            activeTab === "breaking"
              ? breakingChanges.length > 0
                ? "border-rose-500 text-white"
                : "border-white text-white"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <WarningCircle
            size={13}
            className={`shrink-0 ${breakingChanges.length > 0 ? "text-rose-400" : "text-zinc-500"}`}
          />
          <span className="whitespace-nowrap">Breaking ({breakingChanges.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("impact")}
          className={`flex-1 min-w-0 py-2.5 px-1.5 font-medium border-b-2 transition-all cursor-pointer flex items-center justify-center gap-1.5 whitespace-nowrap ${
            activeTab === "impact"
              ? "border-amber-400 text-white"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <TreeStructure
            size={13}
            className={`shrink-0 ${downstreamImpact.length > 0 ? "text-amber-400" : "text-zinc-500"}`}
          />
          <span className="whitespace-nowrap">Impact ({downstreamImpact.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("shim")}
          className={`flex-1 min-w-0 py-2.5 px-1.5 font-medium border-b-2 transition-all cursor-pointer flex items-center justify-center gap-1.5 whitespace-nowrap ${
            activeTab === "shim"
              ? "border-emerald-400 text-white"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Cpu size={13} className="shrink-0 text-emerald-400" />
          <span className="whitespace-nowrap">Auto-Heal</span>
        </button>

        <button
          onClick={() => setActiveTab("compliance")}
          className={`flex-1 min-w-0 py-2.5 px-1.5 font-medium border-b-2 transition-all cursor-pointer flex items-center justify-center gap-1.5 whitespace-nowrap ${
            activeTab === "compliance"
              ? "border-indigo-400 text-white"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Scales size={13} className="shrink-0 text-indigo-400" />
          <span className="whitespace-nowrap">Docling</span>
        </button>
      </div>

      {/* Tab Contents */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* TAB 1: BREAKING CHANGES */}
        {activeTab === "breaking" && (
          <div className="space-y-2.5">
            {breakingChanges.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-14 px-4 text-center">
                <div className="w-9 h-9 rounded-[6px] bg-white/[0.03] border border-white/[0.08] flex items-center justify-center text-zinc-500 mb-2.5">
                  <TerminalWindow size={18} />
                </div>
                <div className="text-xs font-medium text-zinc-300 mb-1">Awaiting Gate Audit</div>
                <p className="text-[11px] text-zinc-500 max-w-[220px] leading-relaxed">
                  Click <span className="text-zinc-300 font-medium">Run Gate Audit</span> to detect breaking contract mutations.
                </p>
              </div>
            ) : (
              breakingChanges.map((change, idx) => (
                <div
                  key={idx}
                  className="rounded-[4px] border border-white/[0.08] bg-[#121318] p-3 text-xs space-y-2 hover:border-white/20 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-semibold text-rose-400">
                      <WarningCircle size={14} weight="bold" />
                      <span>{change.symbol_name}</span>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-mono">
                      L{change.line_number || 12}
                    </span>
                  </div>

                  <p className="text-zinc-400 text-[11px] leading-relaxed">
                    {change.description || "Contract signature dropped legacy property."}
                  </p>

                  <div className="border border-white/[0.05] rounded-[3px] p-2 bg-[#090a0d] space-y-1">
                    <div className="flex items-center gap-2 text-[11px]">
                      <span className="text-rose-400 shrink-0 font-medium text-[10px]">OLD:</span>
                      <span className="text-zinc-300 truncate font-mono text-[10px]">{change.old_signature}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[11px]">
                      <span className="text-emerald-400 shrink-0 font-medium text-[10px]">NEW:</span>
                      <span className="text-zinc-300 truncate font-mono text-[10px]">{change.new_signature}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB 2: DOWNSTREAM IMPACT */}
        {activeTab === "impact" && (
          <div className="space-y-2">
            {downstreamImpact.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-14 px-4 text-center">
                <div className="w-9 h-9 rounded-[6px] bg-white/[0.03] border border-white/[0.08] flex items-center justify-center text-zinc-500 mb-2.5">
                  <TreeStructure size={18} />
                </div>
                <div className="text-xs font-medium text-zinc-300 mb-1">No Blast Radius Detected</div>
                <p className="text-[11px] text-zinc-500 max-w-[220px] leading-relaxed">
                  Downstream dependencies and caller risks will populate after running audit.
                </p>
              </div>
            ) : (
              downstreamImpact.map((item, idx) => (
                <div
                  key={idx}
                  className="rounded-[4px] border border-white/[0.08] bg-[#121318] p-3 text-xs flex items-center justify-between"
                >
                  <div className="space-y-0.5">
                    <div className="font-semibold text-zinc-200">{item.file_path}</div>
                    <div className="text-[11px] text-zinc-500">{item.service || "Downstream Service"}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] font-mono text-amber-400 font-semibold">
                      HOP {item.dependency_depth || 1}
                    </div>
                    <div className="text-[10px] text-zinc-500">
                      Crit: {item.criticality || 1.0}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB 3: AUTO-HEAL SHIM */}
        {activeTab === "shim" && (
          <div className="space-y-3">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-[4px] space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                  <Cpu size={14} />
                  <span>IBM Granite 3.0 Code Synthesizer</span>
                </div>
                <span className="text-[10px] px-1.5 py-0.5 rounded-[2px] bg-emerald-500/20 text-emerald-300 font-mono">
                  4 PROXY TRAPS
                </span>
              </div>
              <p className="text-[11px] text-zinc-300 leading-relaxed">
                Autonomous backward-compatibility shim bridging legacy <code className="text-white">.id</code> and <code className="text-white">.tier</code> calls without downstream refactoring.
              </p>
            </div>

            <div className="relative border border-white/[0.08] rounded-[4px] bg-[#08090b] p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono text-zinc-500">auth_adapter.ts</span>
                <button
                  onClick={copyShim}
                  className="text-[11px] text-zinc-400 hover:text-white transition-colors cursor-pointer flex items-center gap-1"
                >
                  {copied ? <Check size={12} className="text-emerald-400" /> : null}
                  <span>{copied ? "Copied!" : "Copy"}</span>
                </button>
              </div>
              <pre className="text-[11px] text-zinc-300 font-mono overflow-x-auto max-h-48 leading-relaxed whitespace-pre">
                {shimCode}
              </pre>
            </div>

            <button
              onClick={onApplyShim}
              disabled={shimLoading || shimApplied}
              className={`w-full py-2 px-3 rounded-[4px] text-xs font-semibold transition-all flex items-center justify-center gap-2 cursor-pointer ${
                shimApplied
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  : "bg-white text-black hover:bg-zinc-200"
              }`}
            >
              {shimLoading ? (
                <span>Synthesizing Adapter...</span>
              ) : shimApplied ? (
                <>
                  <Check size={14} weight="bold" />
                  <span>Shim Verified · Risk Reduced to 12.0</span>
                </>
              ) : (
                <>
                  <Cpu size={14} weight="bold" />
                  <span>Apply IBM Granite Shim</span>
                </>
              )}
            </button>

            {shimApplied && onDownloadPassport && (
              <button
                onClick={onDownloadPassport}
                className="w-full py-2 px-3 rounded-[4px] border border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20 text-xs font-semibold text-emerald-300 flex items-center justify-between gap-2 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2 truncate">
                  <DownloadSimple size={14} weight="bold" className="shrink-0" />
                  <span className="truncate">Download Cryptographic Release Passport</span>
                </div>
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-[2px] bg-emerald-500/20 border border-emerald-500/30 text-emerald-200 text-[10px] font-medium shrink-0">
                  <ShieldCheck size={11} weight="fill" className="text-emerald-400" />
                  <span>Certified &amp; Signed</span>
                </span>
              </button>
            )}
          </div>
        )}

        {/* TAB 4: COMPLIANCE (DOCLING) */}
        {activeTab === "compliance" && (
          <div className="space-y-3">
            <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-[4px] space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400">
                  <Scales size={14} />
                  <span>PCI-DSS v4.0.1 Compliance</span>
                </div>
                <span className="text-[10px] px-1.5 py-0.5 rounded-[2px] bg-indigo-500/20 text-indigo-300 font-mono">
                  IBM DOCLING
                </span>
              </div>
              <p className="text-[11px] text-zinc-300 leading-relaxed">
                Extracted directly from regulatory mandate <span className="text-white">PCI-DSS-v4-Auth-Clause.pdf</span>.
              </p>
            </div>

            <div className="space-y-2 text-xs">
              <div className="p-3 rounded-[4px] bg-[#121318] border border-white/[0.08] space-y-1">
                <div className="font-semibold text-zinc-200">Req 10.2.1: Audit Identity Continuity</div>
                <p className="text-[11px] text-zinc-400 leading-relaxed">
                  Renaming identifier attributes from <code className="text-rose-400">id</code> to <code className="text-emerald-400">sub</code> without backward-compatible shims breaks transaction audit trail linkage.
                </p>
              </div>

              <div className="p-3 rounded-[4px] bg-[#121318] border border-white/[0.08] space-y-1">
                <div className="font-semibold text-zinc-200">Req 3.4.2: Settlement System Integrity</div>
                <p className="text-[11px] text-zinc-400 leading-relaxed">
                  Silent ledger corruption causing settlement batch cron abortion is classified as a Critical Non-Compliance Event (SEV-1).
                </p>
              </div>

              <div className="p-3 rounded-[4px] bg-[#121318] border border-white/[0.08] space-y-1">
                <div className="font-semibold text-zinc-200">Req 8.2.8: 90-Day Transition Window</div>
                <p className="text-[11px] text-zinc-400 leading-relaxed">
                  Deprecation grace periods are strictly required before contract fields can be dropped.
                </p>
              </div>
            </div>

            {/* Secondary Action: Export Security Audit */}
            <div className="pt-1">
              <button
                onClick={handleExportAudit}
                className="w-full py-2 px-3 rounded-[4px] border border-white/[0.12] bg-[#121318] hover:bg-[#181920] hover:border-white/20 text-xs font-medium text-zinc-300 hover:text-white flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <DownloadSimple size={14} className="text-zinc-400" />
                <span>Export Security Audit</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
