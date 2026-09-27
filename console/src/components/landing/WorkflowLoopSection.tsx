"use client";

import React from "react";
import Link from "next/link";
import {
  TreeStructure,
  Cpu,
  Sparkle,
  ArrowRight,
  ShieldWarning,
  FileCode,
} from "@phosphor-icons/react";

export function WorkflowLoopSection() {
  const steps = [
    {
      num: "01",
      title: "Detect Contract Drift",
      subtitle: "Deterministic AST Traversal in 1.2ms",
      desc: "Tree-sitter executes grammar-level AST diffs in 1.2ms, flagging breaking signature mutations before flawed types ever reach downstream microservices.",
      icon: FileCode,
      metrics: "Sub-2ms AST diff | Zero hallucination",
    },
    {
      num: "02",
      title: "Calculate Blast Radius",
      subtitle: "NetworkX Dependency DAG",
      desc: "NetworkX builds a multi-hop dependency DAG across monorepo boundaries, calculating exact caller blast radius and service criticality before merge.",
      icon: TreeStructure,
      metrics: "4 downstream services mapped | Risk: 84.0/100",
    },
    {
      num: "03",
      title: "Autonomous Auto-Heal",
      subtitle: "IBM Granite 3.0 Proxy Shim",
      desc: "IBM Granite 3.0 Code synthesizes backward-compatible ES6 Proxy adapters directly in the PR, eliminating downtime without requiring emergency caller refactoring.",
      icon: Cpu,
      metrics: "Risk drops 84.0 -> 12.0 | Gate Cleared",
    },
  ];

  return (
    <section id="workflow" className="py-20 border-t border-white/[0.08] bg-[#08090a]">
      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <div className="inline-flex items-center gap-2 text-xs text-zinc-400 font-medium mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Native GitHub PR Gatekeeper</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
            From Pull Request to Guaranteed Production Safety
          </h2>
          <p className="mt-4 text-sm sm:text-base text-zinc-400 leading-relaxed">
            Vectis stops broken code directly where developers collaborate: no new tools to learn, no context switching.
          </p>
        </div>

        {/* 3-Step Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                className="rounded-[6px] border border-white/[0.08] bg-[#0c0d10] p-6 flex flex-col justify-between hover:border-white/[0.18] transition-colors relative"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-semibold text-zinc-500 tabular-nums">
                      {step.num}
                    </span>
                    <div className="w-7 h-7 rounded-[4px] bg-[#14151a] border border-white/[0.08] flex items-center justify-center text-zinc-300">
                      <Icon size={15} />
                    </div>
                  </div>

                  <h3 className="text-base font-semibold text-white tracking-tight">
                    {step.title}
                  </h3>

                  <div className="text-xs text-zinc-400 font-medium mt-1 mb-3">
                    {step.subtitle}
                  </div>

                  <p className="text-xs text-zinc-300 leading-relaxed">
                    {step.desc}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-white/[0.06] text-[11px] text-zinc-500 font-normal">
                  {step.metrics}
                </div>
              </div>
            );
          })}
        </div>

        {/* GitHub Native PR Gatekeeper Mockup */}
        <div className="mt-20 max-w-3xl mx-auto">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 text-xs text-zinc-400 font-medium mb-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>GitHub Native</span>
            </div>
            <h3 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Right where you already review code.
            </h3>
            <p className="mt-2 text-xs sm:text-sm text-zinc-400 max-w-xl mx-auto leading-relaxed">
              Vectis audits every commit and suggests the fix directly inside your Pull Request - no context switching, no new tools to learn.
            </p>
          </div>

          <div className="rounded-[6px] border border-white/[0.1] bg-[#0c0d10] overflow-hidden shadow-2xl">
            {/* PR Comment Top Bar */}
            <div className="h-10 px-4 bg-[#111216] border-b border-white/[0.08] flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <div className="w-5 h-5 rounded-[4px] bg-rose-500/20 text-rose-400 border border-rose-500/30 flex items-center justify-center font-bold text-[10px]">
                  V
                </div>
                <span className="font-semibold text-zinc-200">vectis-gate[bot]</span>
                <span className="text-zinc-500 text-[11px]">commented 3 minutes ago</span>
              </div>

              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                <span className="text-rose-400 font-semibold text-[11px]">
                  RELEASE BLOCKED
                </span>
              </div>
            </div>

            {/* PR Comment Content */}
            <div className="p-5 text-xs space-y-4">
              <div className="flex items-start gap-2.5 text-zinc-300">
                <ShieldWarning size={16} className="text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-white">
                    Pull Request #482 contains 2 breaking interface mutations
                  </div>
                  <div className="text-zinc-400 text-[11px] mt-0.5">
                    Target: <span className="font-sans font-medium text-zinc-300">src/auth/session.ts</span> | Monorepo risk index: 84.0 / 100
                  </div>
                </div>
              </div>

              {/* Mutations Table (Non-monospaced tabular) */}
              <div className="border border-white/[0.08] rounded-[4px] overflow-hidden">
                <div className="grid grid-cols-12 bg-[#14151a] px-3 py-2 text-[11px] font-semibold text-zinc-400 border-b border-white/[0.06]">
                  <span className="col-span-4">Mutated Symbol</span>
                  <span className="col-span-4">Old Contract</span>
                  <span className="col-span-4">New Contract</span>
                </div>
                <div className="grid grid-cols-12 px-3 py-2 text-[11px] border-b border-white/[0.04] bg-[#0c0d10] text-zinc-300">
                  <span className="col-span-4 text-rose-400 font-medium">User.id</span>
                  <span className="col-span-4 text-zinc-400">id: string</span>
                  <span className="col-span-4 text-zinc-400">sub: string (renamed)</span>
                </div>
                <div className="grid grid-cols-12 px-3 py-2 text-[11px] bg-[#0c0d10] text-zinc-300">
                  <span className="col-span-4 text-rose-400 font-medium">User.tier</span>
                  <span className="col-span-4 text-zinc-400">tier: enum</span>
                  <span className="col-span-4 text-zinc-400">metadata.tier (nested)</span>
                </div>
              </div>

              {/* Downstream Callers List */}
              <div className="p-3 rounded-[4px] bg-[#111216] border border-white/[0.06]">
                <div className="text-[11px] text-zinc-400 mb-2 font-medium">
                  Impacted Downstream Services (Depth 1-2):
                </div>
                <div className="flex flex-wrap gap-2 text-[11px]">
                  <span className="px-2 py-1 rounded-[4px] bg-zinc-800 text-zinc-300 border border-white/[0.06]">
                    payments/checkout.ts (Billing)
                  </span>
                  <span className="px-2 py-1 rounded-[4px] bg-zinc-800 text-zinc-300 border border-white/[0.06]">
                    workers/settlement_worker.ts (Cron)
                  </span>
                  <span className="px-2 py-1 rounded-[4px] bg-zinc-800 text-zinc-300 border border-white/[0.06]">
                    reporting/invoice_generator.ts (Invoicing)
                  </span>
                </div>
              </div>

              {/* Action Bar */}
              <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <span className="text-[11px] text-zinc-400">
                  Automated shim synthesized by IBM Granite 3.0 Code API
                </span>

                <Link
                  href="/cockpit"
                  className="h-8 px-3.5 rounded-[4px] bg-white text-black hover:bg-zinc-200 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Sparkle size={13} weight="bold" />
                  <span>Apply 1-Click Fix in PR -&gt;</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
