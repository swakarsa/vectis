"use client";

import React from "react";
import {
  TreeStructure,
  Cpu,
  Scales,
  ShieldCheck,
  CheckCircle,
} from "@phosphor-icons/react";

export function BentoGridSection() {
  return (
    <section id="architecture" className="py-20 border-t border-white/[0.08] bg-[#090a0d]">
      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <div className="inline-flex items-center gap-2 text-xs text-zinc-400 font-medium mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Built with IBM Bob 2.0 Agent Mode &amp; IBM Granite 3.0 Code API</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
            Four Enterprise Technologies. Zero Hallucinations.
          </h2>
          <p className="mt-4 text-sm sm:text-base text-zinc-400 leading-relaxed">
            Deterministic AST parsing, autonomous code synthesis, regulatory document ingestion, and instant compliance certification.
          </p>
        </div>

        {/* Bento Grid (Asymmetric Layout, Zero Pills, Zero Em-Dash) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {/* Card 1 (Col Span 2): Deterministic Core Engine */}
          <div className="md:col-span-2 rounded-[6px] border border-white/[0.08] bg-[#0c0d10] p-6 sm:p-8 flex flex-col justify-between group hover:border-white/[0.18] transition-colors">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-8 h-8 rounded-[4px] bg-[#14151a] border border-white/[0.08] flex items-center justify-center text-emerald-400">
                  <TreeStructure size={18} weight="bold" />
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-zinc-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>100% Deterministic Engine</span>
                </div>
              </div>

              <h3 className="text-xl font-bold text-white tracking-tight">
                Deterministic AST Traversal &amp; NetworkX Blast DAG
              </h3>

              <p className="mt-4 text-xs sm:text-sm text-zinc-300 leading-relaxed">
                Native Tree-sitter binary parsers map syntax diffs in 1.2ms while NetworkX computes multi-hop dependency DAGs with zero LLM hallucination, eliminating breaking changes before code touches production.
              </p>

              {/* Engine Metrics Bar */}
              <div className="mt-6 grid grid-cols-3 gap-4 border-t border-white/[0.06] pt-5">
                <div>
                  <div className="text-xs text-zinc-500 font-medium">AST Parse Speed</div>
                  <div className="text-lg font-bold text-white tabular-nums mt-0.5">1.2ms</div>
                </div>
                <div>
                  <div className="text-xs text-zinc-500 font-medium">Decision Hallucination</div>
                  <div className="text-lg font-bold text-emerald-400 tabular-nums mt-0.5">0.0%</div>
                </div>
                <div>
                  <div className="text-xs text-zinc-500 font-medium">Dependency Traversal</div>
                  <div className="text-lg font-bold text-white tabular-nums mt-0.5">Multi-Hop</div>
                </div>
              </div>
            </div>

            {/* Path visualization */}
            <div className="mt-6 p-3 rounded-[4px] bg-[#111216] border border-white/[0.06] flex items-center justify-between text-xs text-zinc-400">
              <span className="text-zinc-300 font-medium">Identity Core (models/user.ts)</span>
              <span className="text-zinc-600">-&gt;</span>
              <span className="text-zinc-300 font-medium">Auth Gateway (auth/session.ts)</span>
              <span className="text-zinc-600">-&gt;</span>
              <span className="text-rose-400 font-medium">Billing &amp; Settlement (Protected)</span>
            </div>
          </div>

          {/* Card 2: Autonomous Auto-Heal (IBM Granite 3.0) */}
          <div className="rounded-[6px] border border-white/[0.08] bg-[#0c0d10] p-6 sm:p-8 flex flex-col justify-between group hover:border-white/[0.18] transition-colors">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-8 h-8 rounded-[4px] bg-[#14151a] border border-white/[0.08] flex items-center justify-center text-zinc-200">
                  <Cpu size={18} weight="bold" />
                </div>
                <span className="text-[11px] text-zinc-400">IBM Granite 3.0 Code API</span>
              </div>

              <h3 className="text-base font-bold text-white tracking-tight">
                Autonomous Auto-Heal Shims
              </h3>

              <p className="mt-4 text-xs text-zinc-300 leading-relaxed">
                IBM Granite 3.0 Code API synthesizes dual-contract ES6 Proxy shims directly in the pull request, keeping legacy and modern services operating without breaking delivery.
              </p>
            </div>

            <div className="mt-6 p-3 rounded-[4px] bg-[#111216] border border-white/[0.06] text-[11px] space-y-1">
              <div className="text-zinc-500">Compatibility Adapter:</div>
              <div className="text-emerald-400 font-medium">
                Dual-Contract Proxy Shim Synthesized
              </div>
              <div className="text-zinc-400 text-[10px]">
                Risk score reduced from 84.0 to 12.0
              </div>
            </div>
          </div>

          {/* Card 3: Regulatory Compliance (IBM Docling) */}
          <div id="compliance" className="rounded-[6px] border border-white/[0.08] bg-[#0c0d10] p-6 sm:p-8 flex flex-col justify-between group hover:border-white/[0.18] transition-colors">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-8 h-8 rounded-[4px] bg-[#14151a] border border-white/[0.08] flex items-center justify-center text-amber-400">
                  <Scales size={18} weight="bold" />
                </div>
                <span className="text-[11px] text-zinc-400">IBM Docling Engine</span>
              </div>

              <h3 className="text-base font-bold text-white tracking-tight">
                PCI-DSS v4.0.1 Req 10.2.1
              </h3>

              <p className="mt-4 text-xs text-zinc-300 leading-relaxed">
                IBM Docling ingests complex PCI-DSS regulatory audit documentation and compiles active AST verification policies, ensuring continuous fintech compliance without manual overhead.
              </p>
            </div>

            <div className="mt-6 p-3 rounded-[4px] bg-[#111216] border border-white/[0.06] text-[11px] space-y-1">
              <div className="text-zinc-500">Audit Rule Enforced:</div>
              <div className="text-amber-400 font-medium">
                Mandatory User Identifier Audit Trail
              </div>
              <div className="text-zinc-400 text-[10px]">
                Pre-merge compliance verification passed
              </div>
            </div>
          </div>

          {/* Card 4 (Col Span 2): Instant Audit Compliance for CISO & Regulators */}
          <div className="md:col-span-2 rounded-[6px] border border-white/[0.08] bg-[#0c0d10] p-6 sm:p-8 flex flex-col justify-between group hover:border-white/[0.18] transition-colors">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-8 h-8 rounded-[4px] bg-[#14151a] border border-white/[0.08] flex items-center justify-center text-zinc-200">
                  <ShieldCheck size={18} weight="bold" className="text-emerald-400" />
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span>Audit-Ready Release Trail</span>
                </div>
              </div>

              <h3 className="text-xl font-bold text-white tracking-tight">
                Instant Audit Compliance for CISO &amp; Regulators
              </h3>

              <p className="mt-4 text-xs sm:text-sm text-zinc-300 leading-relaxed">
                Every release generates a tamper-proof cryptographic audit trail, providing engineering and compliance teams with instant mathematical proof that code is safe before touching production.
              </p>

              {/* Status element (Crisp rectangular style, no pill) */}
              <div className="mt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-[4px] bg-[#111216] border border-white/[0.06]">
                <div className="flex items-center gap-2.5">
                  <div className="px-2.5 py-1 rounded-[4px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-semibold text-xs flex items-center gap-1.5">
                    <CheckCircle size={14} weight="fill" />
                    <span>Status: SOC2 &amp; PCI-DSS Audit-Ready</span>
                  </div>
                </div>

                <div className="text-xs text-zinc-400">
                  Instant mathematical proof that your release is safe before touching production.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
