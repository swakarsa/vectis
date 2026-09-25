"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  TerminalWindow,
  GitPullRequest,
  Check,
  Copy,
  Lightning,
  ShieldCheck,
  ShieldWarning,
} from "@phosphor-icons/react";

export function HeroSection() {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"cli" | "diff">("cli");

  const handleCopy = () => {
    navigator.clipboard.writeText("npx vectis-gate audit --pr 482");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="relative pt-12 pb-16 md:pt-16 md:pb-24 overflow-hidden">
      {/* Background Radial Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[850px] h-[450px] bg-gradient-to-b from-rose-500/[0.05] via-zinc-900/[0.03] to-transparent blur-3xl pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        {/* Top Status Hook: Two-Tone IBM Bob 2.0 Badge */}
        <div className="flex items-center justify-center mb-6">
          <a
            href="#architecture"
            className="inline-flex items-center gap-2.5 p-1 pr-3 rounded-[4px] border border-white/[0.08] hover:border-white/[0.18] bg-[#0f1013]/90 text-xs transition-colors cursor-pointer group shadow-sm"
          >
            <span className="bg-zinc-800 text-zinc-200 px-2 py-0.5 rounded-[3px] text-[11px] font-semibold border border-white/10 tracking-tight">
              IBM Bob 2.0
            </span>
            <span className="text-zinc-400 group-hover:text-zinc-200 transition-colors font-medium">
              Autonomous Agent Mode &amp; Granite 3.0 Code
            </span>
            <ArrowRight size={12} weight="bold" className="text-zinc-500 group-hover:text-zinc-200 group-hover:translate-x-0.5 transition-all" />
          </a>
        </div>

        {/* Main Typographic Headline */}
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white leading-[1.1]">
            Predictive Release Safety for Enterprise Monorepos.
          </h1>

          <p className="mt-4 text-sm sm:text-base text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            Stop silent breaking changes before production bleeds. Deterministic AST semantic analysis in 1.2ms with automated backward-compatibility shims.
          </p>

          {/* Dual Action CTAs (No pills: rounded-[4px], mb-10 for luxury whitespace) */}
          <div className="mt-6 mb-10 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/cockpit"
              className="w-full sm:w-auto h-9 px-4 rounded-[4px] bg-white text-black hover:bg-zinc-200 text-xs sm:text-sm font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-sm"
            >
              <TerminalWindow size={15} weight="bold" />
              <span>Launch Interactive Cockpit</span>
              <ArrowRight size={13} weight="bold" />
            </Link>

            <a
              href="#workflow"
              className="w-full sm:w-auto h-9 px-4 rounded-[4px] border border-white/[0.1] bg-[#14151a] hover:bg-[#1a1c23] text-zinc-200 text-xs sm:text-sm font-medium transition-colors flex items-center justify-center gap-2 cursor-pointer"
            >
              <GitPullRequest size={14} className="text-zinc-400" />
              <span>Inspect Sample PR #482</span>
            </a>
          </div>
        </div>

        {/* Interactive CLI Terminal Card (Subtle peek into the fold) */}
        <div className="max-w-4xl mx-auto">
          <div className="rounded-[6px] border border-white/[0.1] bg-[#0c0d10] shadow-2xl overflow-hidden">
            {/* Terminal Window Header */}
            <div className="h-10 px-4 bg-[#111216] border-b border-white/[0.08] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                  <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                  <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
                </div>
                <div className="h-3 w-[1px] bg-white/[0.08]" />
                <span className="text-xs text-zinc-400 font-medium">
                  vectis-gate-cli: Release Block Simulation
                </span>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex items-center border border-white/[0.08] rounded-[4px] p-0.5 bg-[#090a0d]">
                  <button
                    onClick={() => setActiveTab("cli")}
                    className={`px-2 py-0.5 text-[11px] rounded-[2px] transition-colors cursor-pointer ${
                      activeTab === "cli"
                        ? "bg-zinc-800 text-white font-medium"
                        : "text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    CLI Execution
                  </button>
                  <button
                    onClick={() => setActiveTab("diff")}
                    className={`px-2 py-0.5 text-[11px] rounded-[2px] transition-colors cursor-pointer ${
                      activeTab === "diff"
                        ? "bg-zinc-800 text-white font-medium"
                        : "text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    AST Signature Drift
                  </button>
                </div>

                <button
                  onClick={handleCopy}
                  className="h-5 px-2 rounded-[4px] border border-white/[0.08] hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 text-[11px] flex items-center gap-1 transition-colors cursor-pointer"
                  title="Copy Command"
                >
                  {copied ? (
                    <>
                      <Check size={12} className="text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy size={12} />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Terminal Body (Proportional sans typography with comfortable luxury spacing) */}
            <div className="p-4 sm:p-5 font-sans text-xs sm:text-[13px] leading-relaxed">
              {activeTab === "cli" ? (
                <div className="space-y-2 tabular-nums">
                  <div className="flex items-center gap-2 text-zinc-400">
                    <span className="text-zinc-600">$</span>
                    <span className="text-zinc-200 font-semibold">vectis gate audit --pr 482 --repo fintech-monorepo</span>
                  </div>

                  <div className="text-zinc-400 flex items-start gap-2">
                    <span className="text-emerald-400 font-medium">[ok]</span>
                    <span>AST Traversal complete in 1.2ms (Tree-sitter binary parser)</span>
                  </div>

                  <div className="text-rose-400 flex items-start gap-2">
                    <span className="font-semibold">[!]</span>
                    <span>BREAKING MUTATION: User.id renamed to sub in SessionUser contract (src/auth/session.ts:12)</span>
                  </div>

                  <div className="text-rose-400 flex items-start gap-2">
                    <span className="font-semibold">[!]</span>
                    <span>BREAKING MUTATION: User.tier relocated to SessionUser.metadata.tier (src/auth/session.ts:13)</span>
                  </div>

                  <div className="text-amber-400 flex items-start gap-2">
                    <span className="font-semibold">[!]</span>
                    <span>IMPACT DETECTED: 4 downstream callers orphaned (Billing, Settlement, Invoice, Profile)</span>
                  </div>

                  <div className="py-1 px-3 rounded-[4px] bg-rose-500/10 border border-rose-500/20 text-rose-300 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                      <span className="font-semibold tracking-wide text-xs">STATUS: RELEASE BLOCKED</span>
                    </div>
                    <span className="text-xs font-semibold tabular-nums text-rose-400">
                      Risk Index: 84.0 / 100
                    </span>
                  </div>

                  <div className="text-emerald-400 flex items-start gap-2">
                    <span className="font-semibold">[+]</span>
                    <span>SYNTHESIZING SHIM: IBM Granite 3.0 generating dual-contract proxy adapter... done</span>
                  </div>

                  <div className="text-zinc-400 flex items-start gap-2">
                    <span className="text-emerald-400 font-medium">[ok]</span>
                    <span>RE-EVALUATION: Backward compatibility restored for all 4 callers (Risk Index: 12.0 / 100)</span>
                  </div>

                  <div className="text-zinc-500 flex items-start gap-2 text-xs pt-1.5 border-t border-white/[0.06]">
                    <span className="text-zinc-400 font-medium">AUDIT PASSPORT:</span>
                    <span className="text-emerald-400">Cryptographic Proof Generated: SOC2 &amp; PCI-DSS Audit-Ready</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-3.5 tabular-nums">
                  <div className="text-zinc-400 text-xs">
                    Contract Signature Mutation in <span className="text-zinc-200 font-medium">SessionUser</span>:
                  </div>

                  <div className="p-3.5 rounded-[4px] bg-[#08090a] border border-white/[0.06] space-y-2">
                    <div className="text-rose-400/90 flex items-center gap-2">
                      <span className="text-rose-500 font-bold">-</span>
                      <span>export interface SessionUser &#123; id: string; tier: string; &#125;</span>
                    </div>
                    <div className="text-emerald-400/90 flex items-center gap-2">
                      <span className="text-emerald-500 font-bold">+</span>
                      <span>export interface SessionUser &#123; sub: string; metadata: &#123; tier: string &#125;; &#125;</span>
                    </div>
                  </div>

                  <div className="text-zinc-400 text-xs">
                    Synthesized ES6 Proxy Adapter (Zero downstream refactoring required):
                  </div>

                  <div className="p-3.5 rounded-[4px] bg-[#08090a] border border-white/[0.06] text-zinc-300 space-y-1.5 text-xs">
                    <div className="text-emerald-400">export function createSessionUserAdapter(target: any): any &#123;</div>
                    <div className="pl-4 text-zinc-400">return new Proxy(target, &#123;</div>
                    <div className="pl-8 text-zinc-300">get(obj, prop) &#123;</div>
                    <div className="pl-12 text-zinc-400">if (prop === &quot;id&quot;) return obj.sub;</div>
                    <div className="pl-12 text-zinc-400">if (prop === &quot;tier&quot;) return obj.metadata?.tier;</div>
                    <div className="pl-12 text-zinc-400">return Reflect.get(obj, prop);</div>
                    <div className="pl-8 text-zinc-300">&#125;</div>
                    <div className="pl-4 text-zinc-400">&#125;);</div>
                    <div className="text-emerald-400">&#125;</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
