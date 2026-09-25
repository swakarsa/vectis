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
  GitMerge
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
}: DetailPanelProps) {
  const [activeTab, setActiveTab] = useState<"breaking" | "impact" | "shim" | "compliance">("breaking");
  const [copied, setCopied] = useState(false);

  const copyShim = () => {
    navigator.clipboard.writeText(shimCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <aside className="w-[420px] border-l border-white/[0.08] bg-[#0c0d10] flex flex-col h-[calc(100vh-3.5rem)] select-none">
      {/* Risk Metrics Section */}
      <div className="p-4 border-b border-white/[0.08] bg-[#0f1014]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wider text-zinc-400 font-semibold">
            Telemetry & Blast Depth
          </span>
          <span className="text-xs text-zinc-500">Tree-sitter AST</span>
        </div>

        {/* Score & Hairline gauge */}
        <div className="flex items-baseline justify-between mb-2">
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-bold tracking-tight text-white tabular-nums">
              {riskScore.toFixed(1)}
            </span>
            <span className="text-xs text-zinc-500">/ 100 Risk Index</span>
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                verdict === "BLOCK"
                  ? "bg-rose-500"
                  : verdict === "PASS"
                  ? "bg-emerald-400"
                  : "bg-amber-400"
              }`}
            />
            <span
              className={`font-semibold ${
                verdict === "BLOCK"
                  ? "text-rose-400"
                  : verdict === "PASS"
                  ? "text-emerald-400"
                  : "text-amber-400"
              }`}
            >
              {verdict === "BLOCK"
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
              verdict === "BLOCK"
                ? "bg-rose-500"
                : verdict === "PASS"
                ? "bg-emerald-400"
                : "bg-amber-400"
            }`}
            style={{ width: `${Math.min(riskScore, 100)}%` }}
          />
        </div>

        {/* 4 Metric Key-Value Rows */}
        <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-white/[0.04]">
          <div className="flex items-center justify-between text-zinc-400">
            <span>Downstream Callers:</span>
            <span className="text-zinc-200 font-semibold">{downstreamImpact.length}</span>
          </div>
          <div className="flex items-center justify-between text-zinc-400">
            <span>Breaking Contracts:</span>
            <span className="text-zinc-200 font-semibold">{breakingChanges.length}</span>
          </div>
          <div className="flex items-center justify-between text-zinc-400">
            <span>PCI-DSS Status:</span>
            <span className={shimApplied ? "text-emerald-400 font-semibold" : "text-rose-400 font-semibold"}>
              {shimApplied ? "Compliant" : "Violation"}
            </span>
          </div>
          <div className="flex items-center justify-between text-zinc-400">
            <span>AST Traversal:</span>
            <span className="text-zinc-200 font-semibold">1.2ms</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation (Linear style, clean borders) */}
      <div className="flex border-b border-white/[0.08] bg-[#090a0d] px-2 text-xs">
        <button
          onClick={() => setActiveTab("breaking")}
          className={`px-3 py-2.5 font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === "breaking"
              ? "border-rose-500 text-white"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <WarningCircle size={14} className={activeTab === "breaking" ? "text-rose-400" : ""} />
          <span>Breaking ({breakingChanges.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("impact")}
          className={`px-3 py-2.5 font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === "impact"
              ? "border-amber-400 text-white"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <TreeStructure size={14} className={activeTab === "impact" ? "text-amber-400" : ""} />
          <span>Impact ({downstreamImpact.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("shim")}
          className={`px-3 py-2.5 font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === "shim"
              ? "border-emerald-400 text-white"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Cpu size={14} className={activeTab === "shim" ? "text-emerald-400" : ""} />
          <span>Auto-Heal</span>
        </button>

        <button
          onClick={() => setActiveTab("compliance")}
          className={`px-3 py-2.5 font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === "compliance"
              ? "border-indigo-400 text-white"
              : "border-transparent text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Scales size={14} className={activeTab === "compliance" ? "text-indigo-400" : ""} />
          <span>Docling</span>
        </button>
      </div>

      {/* Tab Contents */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* TAB 1: BREAKING CHANGES */}
        {activeTab === "breaking" && (
          <div className="space-y-2.5">
            {breakingChanges.length === 0 ? (
              <div className="text-center py-10 text-zinc-500 text-xs">
                Run pre-merge gate audit to inspect contract mutations.
              </div>
            ) : (
              breakingChanges.map((change, idx) => (
                <div
                  key={idx}
                  className="rounded-[6px] border border-white/[0.07] bg-[#121318] p-3 text-xs hover:border-white/[0.14] transition-all"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-1.5 font-semibold text-rose-400">
                      <WarningCircle size={14} weight="bold" />
                      <span>{change.symbol_name}</span>
                    </div>
                    <span className="text-[11px] text-zinc-500">
                      L{change.line_number || 12}
                    </span>
                  </div>

                  <div className="text-zinc-400 text-[11px] mb-2 leading-relaxed">
                    {change.description || "Contract signature dropped legacy property."}
                  </div>

                  <div className="border border-white/[0.05] rounded-[4px] p-2 bg-[#090a0d] space-y-1">
                    <div className="flex items-center gap-2 text-[11px]">
                      <span className="text-rose-400 shrink-0 font-medium">OLD:</span>
                      <span className="text-zinc-300 truncate">{change.old_signature}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[11px]">
                      <span className="text-emerald-400 shrink-0 font-medium">NEW:</span>
                      <span className="text-zinc-300 truncate">{change.new_signature}</span>
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
              <div className="text-center py-10 text-zinc-500 text-xs">
                No downstream impacts detected.
              </div>
            ) : (
              downstreamImpact.map((item, idx) => (
                <div
                  key={idx}
                  className="rounded-[6px] border border-white/[0.07] bg-[#121318] p-3 text-xs flex items-center justify-between"
                >
                  <div>
                    <div className="flex items-center gap-1.5 font-medium text-zinc-200">
                      <FileCode size={14} className="text-amber-400" />
                      <span>{item.file_path}</span>
                    </div>
                    <div className="text-[11px] text-zinc-500 mt-0.5">
                      {item.service || "Dependent Service"} · Depth {item.dependency_depth}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[11px] text-zinc-400">
                      Crit: {item.criticality}
                    </div>
                    <div className="text-[11px] text-rose-400 font-medium">
                      Call site broken
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB 3: AUTO-HEAL SHIM (IBM BOB 2.0 / GRANITE 3.0) */}
        {activeTab === "shim" && (
          <div className="space-y-3">
            <div className="rounded-[6px] border border-emerald-500/20 bg-emerald-950/10 p-3 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-emerald-400 mb-1">
                <GitMerge size={15} weight="bold" />
                <span>IBM Bob 2.0 · Autonomous Shim Synthesis</span>
              </div>
              <p className="text-zinc-300 text-[11px] leading-relaxed">
                IBM Granite 3.0 Code analyzes AST deltas and synthesizes an ES6 Proxy adapter
                to bridge legacy <span className="font-sans font-medium text-emerald-300">.id</span> and <span className="font-sans font-medium text-emerald-300">.tier</span> properties with zero downstream code rewrites.
              </p>
            </div>

            {/* Apply Action Button */}
            {!shimApplied ? (
              <button
                onClick={onApplyShim}
                disabled={shimLoading || breakingChanges.length === 0}
                className="w-full py-2.5 px-4 rounded-[4px] bg-emerald-500 hover:bg-emerald-400 text-zinc-950 text-xs font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {shimLoading ? (
                  <span>Synthesizing Shim via Bob 2.0...</span>
                ) : (
                  <>
                    <GitMerge size={15} weight="bold" />
                    <span>Apply Compatibility Shim</span>
                  </>
                )}
              </button>
            ) : (
              <div className="flex items-center justify-between p-2.5 rounded-[4px] bg-emerald-950/20 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
                <div className="flex items-center gap-1.5">
                  <Check size={16} weight="bold" />
                  <span>Shim Active · Risk Dropped to 12.0</span>
                </div>
                <button
                  onClick={copyShim}
                  className="text-zinc-400 hover:text-white text-[11px] underline cursor-pointer"
                >
                  {copied ? "Copied" : "Copy Code"}
                </button>
              </div>
            )}

            {/* Code Box */}
            <div className="rounded-[6px] border border-white/[0.08] bg-[#090a0d] p-3 text-[11px] font-sans tabular-nums text-zinc-300 overflow-x-auto leading-relaxed">
              <pre className="whitespace-pre-wrap font-sans tabular-nums">{shimCode}</pre>
            </div>
          </div>
        )}

        {/* TAB 4: COMPLIANCE / IBM DOCLING */}
        {activeTab === "compliance" && (
          <div className="space-y-3">
            <div className="rounded-[6px] border border-white/[0.07] bg-[#121318] p-3 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-zinc-200 mb-1">
                <Scales size={15} className="text-indigo-400" />
                <span>IBM Docling · PCI-DSS v4.0.1 Ingestion</span>
              </div>
              <p className="text-zinc-400 text-[11px] leading-relaxed mb-3">
                Extracted from <span className="text-zinc-200 font-medium">PCI-DSS-v4-Auth-Clause.pdf</span>: Requirement 10.2.1 mandates strict audit log identity continuity.
              </p>

              <div className="p-2.5 rounded-[4px] border border-white/[0.06] bg-[#090a0d] text-[11px] space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-zinc-500">Requirement:</span>
                  <span className="text-zinc-300 font-medium">PCI-DSS Req 10.2.1</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-500">Audit Field:</span>
                  <span className="text-rose-400 font-medium">user.id (Mandatory)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-500">Current Status:</span>
                  <span className={shimApplied ? "text-emerald-400 font-medium" : "text-rose-400 font-medium"}>
                    {shimApplied ? "Continuity Preserved" : "Breached by PR #482"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
