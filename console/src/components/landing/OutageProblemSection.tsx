"use client";

import React from "react";
import {
  XCircle,
  CheckCircle,
  ShieldCheck,
  Warning,
} from "@phosphor-icons/react";

export function OutageProblemSection() {
  return (
    <section id="problem" className="py-20 border-t border-white/[0.08] bg-[#090a0d]">
      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <div className="inline-flex items-center gap-2 text-xs text-zinc-400 font-medium mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
            <span>Root Cause Analysis</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
            Why 100% Passing Tests Still Crash in Production
          </h2>
          <p className="mt-4 text-sm sm:text-base text-zinc-400 leading-relaxed">
            Unit tests run isolated components. Linters check formatting syntax. Neither validates whether downstream microservices or async workers still match the upstream contract.
          </p>
        </div>

        {/* Side-by-Side Comparison (Hairline borders, no pills, no circular decor) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          {/* Column Left: Standard CI (False sense of security ending in red disaster) */}
          <div className="rounded-[6px] border border-white/[0.08] bg-[#0c0d10] p-6 sm:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-5 border-b border-white/[0.08]">
                <div className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-[4px] bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
                    <XCircle size={15} weight="bold" />
                  </div>
                  <h3 className="text-sm font-semibold text-white">
                    Standard CI Pipeline
                  </h3>
                </div>
                <span className="text-[11px] text-zinc-500 font-medium">
                  Isolated Validation
                </span>
              </div>

              {/* Status List (All green checkmarks eliminated - muted gray false passes) */}
              <div className="mt-6 space-y-3 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-[4px] bg-[#111216] border border-white/[0.04]">
                  <span className="text-zinc-400">Local Unit Tests</span>
                  <span className="text-zinc-500 font-medium">
                    142 / 142 Passed (Isolated only)
                  </span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-[4px] bg-[#111216] border border-white/[0.04]">
                  <span className="text-zinc-400">Linter &amp; TypeScript</span>
                  <span className="text-zinc-500 font-medium">
                    0 Errors (Syntax only)
                  </span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-[4px] bg-rose-500/10 border border-rose-500/25">
                  <span className="text-zinc-400 font-medium">PR Release Status</span>
                  <span className="text-rose-400 font-semibold flex items-center gap-1.5">
                    <Warning size={14} weight="fill" className="text-rose-500 shrink-0" />
                    <span>Blindly Merged -&gt; 02:00 AM Outage</span>
                  </span>
                </div>
              </div>
            </div>

            {/* Direct Contrast Result Box */}
            <div className="mt-8 p-3.5 rounded-[4px] border border-rose-500/20 bg-rose-500/[0.06] text-xs">
              <div className="text-rose-400 font-semibold mb-1 text-[12px]">
                Standard CI: Tests Pass, Linter Clean -&gt; Result: 02:00 AM Payment Crash
              </div>
              <p className="text-zinc-300 leading-relaxed text-[11px]">
                A renamed user identifier bypassed mocks and triggered runtime null errors in billing. Downstream checkout workers crashed, causing an emergency midnight rollback and lost transactions.
              </p>
            </div>
          </div>

          {/* Column Right: Vectis Gate (Total emerald protective fortress) */}
          <div className="rounded-[6px] border border-emerald-500/30 bg-[#0c0d10] p-6 sm:p-8 flex flex-col justify-between shadow-lg shadow-emerald-500/[0.02]">
            <div>
              <div className="flex items-center justify-between pb-5 border-b border-white/[0.08]">
                <div className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-[4px] bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                    <ShieldCheck size={15} weight="bold" />
                  </div>
                  <h3 className="text-sm font-semibold text-white">
                    Vectis Gatekeeper
                  </h3>
                </div>
                <span className="text-[11px] text-emerald-400 font-medium">
                  Semantic Monorepo Gate
                </span>
              </div>

              {/* Status List (All green/emerald defensive shield indicators) */}
              <div className="mt-6 space-y-3 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-[4px] bg-[#111216] border border-white/[0.04]">
                  <span className="text-zinc-400">Tree-sitter AST Diff</span>
                  <span className="text-emerald-400 font-medium flex items-center gap-1.5">
                    <ShieldCheck size={14} weight="fill" className="text-emerald-400 shrink-0" />
                    <span>2 Contract Drifts Intercepted (1.2ms)</span>
                  </span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-[4px] bg-[#111216] border border-white/[0.04]">
                  <span className="text-zinc-400">NetworkX Dependency DAG</span>
                  <span className="text-emerald-400 font-medium flex items-center gap-1.5">
                    <ShieldCheck size={14} weight="fill" className="text-emerald-400 shrink-0" />
                    <span>4 Downstream Services Shielded</span>
                  </span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-[4px] bg-emerald-500/10 border border-emerald-500/25">
                  <span className="text-zinc-300 font-medium">Pre-Merge Gate Decision</span>
                  <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                    <CheckCircle size={14} weight="fill" className="text-emerald-400 shrink-0" />
                    <span>Auto-Healed in PR (Safe to Deploy)</span>
                  </span>
                </div>
              </div>
            </div>

            {/* Direct Contrast Result Box */}
            <div className="mt-8 p-3.5 rounded-[4px] border border-emerald-500/20 bg-emerald-500/[0.06] text-xs">
              <div className="text-emerald-400 font-semibold mb-1 text-[12px]">
                Vectis Gate: Contract Drift Blocked -&gt; Result: Zero Outage, Auto-Healed in PR
              </div>
              <p className="text-zinc-300 leading-relaxed text-[11px]">
                IBM Granite 3.0 synthesized an ES6 Proxy adapter directly inside the PR review. Both legacy callers and new schemas ran concurrently without touching downstream code.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
