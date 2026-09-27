"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  ArrowLeft,
  Check,
  WarningCircle,
  ShieldCheck,
  ShieldWarning,
  TerminalWindow,
  Sparkle,
  TreeStructure,
  GitPullRequest,
  Cpu,
  FileCode,
  Scales,
  ArrowUpRight,
} from "@phosphor-icons/react";

export default function KeynoteSlidesPage() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [hazardTab, setHazardTab] = useState<"illusion" | "reality" | "contract">("illusion");
  const [isHealed, setIsHealed] = useState(false);
  const [isCodemod, setIsCodemod] = useState(false);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
        e.preventDefault();
        setCurrentSlide((prev) => Math.min(prev + 1, 3));
      } else if (e.key === "ArrowLeft" || e.key === "Backspace" || e.key === "PageUp") {
        e.preventDefault();
        setCurrentSlide((prev) => Math.max(prev - 1, 0));
      } else if (["1", "2", "3", "4"].includes(e.key)) {
        setCurrentSlide(parseInt(e.key, 10) - 1);
      } else if (e.key.toLowerCase() === "f") {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleToggleHeal = () => {
    setIsHealed((prev) => !prev);
    setIsCodemod(false);
  };

  const handleToggleCodemod = () => {
    setIsCodemod((prev) => {
      const next = !prev;
      setIsHealed(next);
      return next;
    });
  };

  return (
    <div className="relative w-screen h-screen h-[100dvh] bg-[#08090a] text-zinc-100 flex flex-col overflow-hidden select-none font-sans">
      {/* Background Grids & Radial Glow */}
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-40"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "36px 36px",
          maskImage: "radial-gradient(circle at 50% 35%, black 25%, transparent 80%)",
        }}
      />
      <div className="fixed top-[-10%] left-1/2 -translate-x-1/2 w-[75vw] h-[50vh] bg-gradient-to-b from-rose-500/[0.04] via-zinc-800/[0.02] to-transparent blur-3xl pointer-events-none z-0" />

      {/* Global Slide Header */}
      <header className="relative z-50 w-full h-14 px-6 md:px-10 border-b border-white/[0.08] bg-[#08090a]/90 backdrop-blur-md flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="relative w-6 h-6 rounded-[3px] overflow-hidden border border-white/10">
              <Image
                src="/assets/slides/titanium-v-logo-3d.jpg"
                alt="Vectis"
                fill
                className="object-cover"
                priority
              />
            </div>
            <span className="text-sm font-semibold tracking-tight text-white group-hover:text-zinc-200">
              VECTIS
            </span>
            <span className="text-xs text-zinc-500 font-normal">/</span>
            <span className="text-xs text-zinc-400">
              Keynote Deck · IBM Bob 2.0 Hackathon
            </span>
          </Link>
        </div>

        {/* Center Segments */}
        <nav className="flex items-center gap-1 bg-[#0f1013] border border-white/[0.08] p-1 rounded-[4px]">
          {[
            { id: 0, label: "01. Genesis" },
            { id: 1, label: "02. The Hazard" },
            { id: 2, label: "03. Architecture" },
            { id: 3, label: "04. Impact & Demo" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentSlide(item.id)}
              className={`px-3 py-1 text-xs font-medium rounded-[3px] transition-colors flex items-center gap-2 cursor-pointer ${
                currentSlide === item.id
                  ? "bg-[#14151a] text-white shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-[#1a1c22]"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  currentSlide === item.id ? "bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.6)]" : "bg-zinc-600"
                }`}
              />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
            🏆 95.8 / 100 · Grand Prize Grade
          </span>
          <Link
            href="/cockpit"
            className="h-8 px-3.5 rounded-[4px] bg-white text-black hover:bg-zinc-200 text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <TerminalWindow size={14} weight="bold" />
            <span>Launch Cockpit</span>
            <ArrowUpRight size={13} weight="bold" />
          </Link>
        </div>
      </header>

      {/* Main Slide Stage */}
      <main className="relative z-10 flex-1 w-full overflow-hidden p-6 md:p-10 flex flex-col justify-between">
        {/* ==================================================================
            SLIDE 0: GENESIS & ARCHIMEDEAN THESIS
            ================================================================== */}
        {currentSlide === 0 && (
          <div className="flex-1 flex flex-col justify-center max-w-7xl mx-auto w-full animate-in fade-in zoom-in-95 duration-200">
            <div className="grid grid-cols-1 lg:grid-cols-[1.3fr_0.7fr] gap-8 items-center mb-6">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="px-2 py-0.5 rounded-[3px] bg-[#14151a] border border-white/20 text-[11px] font-semibold text-zinc-200">
                    Official Entry · IBM Bob 2.0 AI Hackathon 2026
                  </span>
                  <span className="px-2 py-0.5 rounded-[3px] bg-emerald-500/10 border border-emerald-500/30 text-[11px] font-semibold text-emerald-400">
                    40/40 Audits Concluded · 140/140 Tests Green
                  </span>
                </div>

                <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-white leading-[1.08] mb-3">
                  Merge with mathematical <span className="italic font-serif text-zinc-100">certainty.</span>
                </h1>

                <p className="text-sm sm:text-base text-zinc-400 max-w-2xl leading-relaxed">
                  Autonomous Pre-Merge Release Sentinel &amp; Semantic Blast-Radius Intelligence for Enterprise Monorepos.
                </p>

                <p className="text-xs sm:text-sm text-zinc-500 mt-2.5 max-w-2xl leading-relaxed">
                  The Archimedean Principle for Enterprise Software: Give us a 1.2ms deterministic AST fulcrum, and{" "}
                  <span className="text-zinc-300 italic font-serif">
                    IBM Bob 2.0 moves entire releases without breaking a single downstream microservice
                  </span>
                  .
                </p>
              </div>

              {/* 3D Titanium Logo Display Card */}
              <div className="relative h-56 sm:h-64 rounded-[6px] border border-white/20 bg-black overflow-hidden shadow-2xl flex items-center justify-center group">
                <Image
                  src="/assets/slides/titanium-v-logo-3d.jpg"
                  alt="Vectis Titanium Origami V Logo"
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                  priority
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                <div className="absolute bottom-2.5 left-3 text-[10px] tracking-wider uppercase text-zinc-400 font-medium">
                  Vectis Titanium Origami V · Deterministic Fulcrum
                </div>
              </div>
            </div>

            {/* 3 Bento Pillar Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
              <div className="rounded-[5px] border border-white/[0.08] bg-[#0f1013] p-4 flex flex-col justify-between hover:border-white/20 transition-colors">
                <div>
                  <div className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <TreeStructure size={13} className="text-zinc-400" />
                    <span>01 · Deterministic Core</span>
                  </div>
                  <div className="text-sm font-semibold text-white tracking-tight mb-1">
                    1.2ms Polyglot AST Engine
                  </div>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Sub-second Tree-sitter diffing with generalized alias clustering, enum narrowing, and Python Pydantic contract diffing. 0% token waste, 0% hallucination.
                  </p>
                </div>
              </div>

              <div className="rounded-[5px] border border-white/[0.18] bg-[#0f1013] p-4 flex flex-col justify-between hover:border-white/30 transition-colors border-t-2 border-t-zinc-300">
                <div>
                  <div className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <Sparkle size={13} className="text-emerald-400" />
                    <span>02 · Master Orchestrator</span>
                  </div>
                  <div className="text-sm font-semibold text-white tracking-tight mb-1">
                    IBM Bob 2.0 &amp; Granite 3.0
                  </div>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Bob Agent Mode dispatches FastMCP stdio subagents. Two-Tier Remediation: Layer 1 ephemeral proxy membrane + Layer 2 clean AST codemod PR generator.
                  </p>
                </div>
              </div>

              <div className="rounded-[5px] border border-white/[0.08] bg-[#0f1013] p-4 flex flex-col justify-between hover:border-white/20 transition-colors">
                <div>
                  <div className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <ShieldCheck size={13} className="text-zinc-400" />
                    <span>03 · Zero-Trust Governance</span>
                  </div>
                  <div className="text-sm font-semibold text-white tracking-tight mb-1">
                    Ed25519 Dual-Control Passport
                  </div>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    IBM Docling regulatory extraction (PCI-DSS v4.0.1 Req 10.2.1, 3.4.2). RFC 8785 canonical JSON digest + human sign-off for Kubernetes cluster gates.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================================================================
            SLIDE 1: THE HAZARD - 18,400 TESTS PASSED (PR #482)
            ================================================================== */}
        {currentSlide === 1 && (
          <div className="flex-1 flex flex-col justify-center max-w-7xl mx-auto w-full animate-in fade-in zoom-in-95 duration-200">
            <div>
              <span className="px-2 py-0.5 rounded-[3px] bg-rose-500/10 border border-rose-500/25 text-[11px] font-semibold text-rose-400 uppercase tracking-wider">
                01 · Root Cause Analysis · PR #482 Silent Bleed
              </span>
              <h2 className="text-2xl sm:text-4xl font-bold tracking-tight text-white leading-tight mt-2 mb-1.5">
                18,400 Tests Passed. Production Still Burned at Midnight.
              </h2>
              <p className="text-xs sm:text-sm text-zinc-400 max-w-3xl leading-relaxed">
                Compilers check syntax. Linters check style. Unit tests test local mocks.{" "}
                <span className="italic font-serif text-zinc-200">
                  Zero existing CI tools test cross-service semantic contract drift.
                </span>
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-4 mt-3.5">
              {/* Left Column: Interactive State Tabs + Glass AST Plate */}
              <div className="rounded-[5px] border border-white/[0.08] bg-[#0f1013] p-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <button
                      onClick={() => setHazardTab("illusion")}
                      className={`px-3 py-1 rounded-[3px] text-xs font-semibold cursor-pointer transition-colors ${
                        hazardTab === "illusion"
                          ? "bg-emerald-500/15 border border-emerald-500/30 text-emerald-400"
                          : "border border-white/10 text-zinc-400 hover:bg-zinc-800"
                      }`}
                    >
                      ✓ The Local Illusion (PR #482 Green)
                    </button>
                    <button
                      onClick={() => setHazardTab("reality")}
                      className={`px-3 py-1 rounded-[3px] text-xs font-semibold cursor-pointer transition-colors ${
                        hazardTab === "reality"
                          ? "bg-rose-500/15 border border-rose-500/30 text-rose-400"
                          : "border border-white/10 text-zinc-400 hover:bg-zinc-800"
                      }`}
                    >
                      ⚠ The Midnight Reality (SEV-1 Crash)
                    </button>
                    <button
                      onClick={() => setHazardTab("contract")}
                      className={`px-3 py-1 rounded-[3px] text-xs font-semibold cursor-pointer transition-colors ${
                        hazardTab === "contract"
                          ? "bg-amber-500/15 border border-amber-500/30 text-amber-400"
                          : "border border-white/10 text-zinc-400 hover:bg-zinc-800"
                      }`}
                    >
                      🔍 AST Contract Drift
                    </button>
                  </div>

                  {hazardTab === "illusion" && (
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-emerald-400">
                        Developer refactors `src/auth/session.ts` to OIDC 2.0 standards:
                      </div>
                      <p className="text-xs text-zinc-400 leading-relaxed">
                        The developer renames <code>User.id</code> to <code>SessionUser.sub</code> and nests <code>User.tier</code> under <code>metadata.tier</code>.
                      </p>
                      <ul className="text-xs text-zinc-300 space-y-1 pt-1">
                        <li className="flex items-start gap-1.5">
                          <Check size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                          <span><b>18,400 / 18,400</b> unit tests pass (local package mocks updated)</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <Check size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                          <span>TypeScript compiler passes via internal <code>(user as any)</code> casts</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <Check size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                          <span>CI/CD turns green. PR #482 approved by human reviewers in 4 minutes.</span>
                        </li>
                      </ul>
                    </div>
                  )}

                  {hazardTab === "reality" && (
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-rose-400">
                        Forty-five minutes post-deployment at 00:15 WIB:
                      </div>
                      <p className="text-xs text-zinc-400 leading-relaxed">
                        Downstream consumers evaluate renamed properties as <code>undefined</code>, triggering cascading runtime outages:
                      </p>
                      <ul className="text-xs text-zinc-300 space-y-1 pt-1">
                        <li className="flex items-start gap-1.5">
                          <WarningCircle size={14} className="text-rose-400 mt-0.5 shrink-0" />
                          <span><b>payments/checkout.ts:</b> Stripe 400 Bad Request (Customer ID undefined)</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <WarningCircle size={14} className="text-rose-400 mt-0.5 shrink-0" />
                          <span><b>cron/settlement_worker.ts:</b> Fatal crash on key <code>ledger_undefined</code> (SEV-1)</span>
                        </li>
                        <li className="flex items-start gap-1.5">
                          <WarningCircle size={14} className="text-rose-400 mt-0.5 shrink-0" />
                          <span><b>PCI-DSS v4.0.1 Req 10.2.1 Breach:</b> Identity continuity severed in audit logs</span>
                        </li>
                      </ul>
                    </div>
                  )}

                  {hazardTab === "contract" && (
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-amber-400">
                        AST Mutation Extraction via Tree-sitter:
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="p-2.5 rounded-[4px] bg-rose-500/10 border border-rose-500/20">
                          <span className="text-[10px] font-semibold text-rose-400">BASE (MAIN)</span>
                          <div className="text-zinc-300 mt-1">
                            - id: string<br />- tier: &apos;free&apos; | &apos;pro&apos;
                          </div>
                        </div>
                        <div className="p-2.5 rounded-[4px] bg-emerald-500/10 border border-emerald-500/20">
                          <span className="text-[10px] font-semibold text-emerald-400">HEAD (PR #482)</span>
                          <div className="text-zinc-300 mt-1">
                            + sub: string<br />+ metadata: &#123; tier: ... &#125;
                          </div>
                        </div>
                      </div>
                      <div className="text-[11px] text-zinc-500">
                        Orphaned Callers: 4 downstream microservices across payment, cron, and invoice clusters.
                      </div>
                    </div>
                  )}
                </div>

                {/* Glass AST Contract Card */}
                <div className="mt-3 flex items-center gap-3 bg-black/60 border border-white/10 rounded-[4px] p-2.5">
                  <div className="relative w-16 h-16 rounded-[4px] overflow-hidden border border-white/20 shrink-0">
                    <Image
                      src="/assets/slides/glass-ast-contract.png"
                      alt="Vectis AST Contract Glass"
                      fill
                      className="object-cover"
                    />
                  </div>
                  <div className="text-xs text-zinc-300 leading-snug">
                    <span className="text-white font-semibold">Vectis AST Contract Standard:</span><br />
                    Guarantees <code>breakingChanges: 0</code> and <code>safeToDeploy: true</code> via deterministic AST diffing before pull request merge.
                  </div>
                </div>
              </div>

              {/* Right Column: Outage Cost Card */}
              <div className="rounded-[5px] border border-white/[0.08] border-l-2 border-l-rose-500 bg-[#0f1013] p-4 flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">
                    Enterprise Downstream Toll · Gartner &amp; DORA Benchmark
                  </span>
                  <div className="text-3xl font-bold tracking-tight text-rose-500 tabular-nums mt-1.5 mb-0.5">
                    $240,000
                  </div>
                  <div className="text-[11px] text-zinc-500 uppercase tracking-wider">
                    Average Direct Loss Per Incident
                  </div>
                  <div className="text-xs text-emerald-400 font-semibold mt-1 mb-2">
                    Payback: 1 intercepted outage covers 2.4 years of Vectis Enterprise ACV
                  </div>

                  <p className="text-xs text-zinc-400 leading-relaxed">
                    When silent breaking changes breach production, emergency post-mortems and emergency rollbacks cause:
                  </p>
                  <ul className="text-xs text-zinc-300 space-y-1.5 mt-2">
                    <li className="flex items-start gap-1.5">
                      <span className="text-zinc-600">•</span>
                      <span><b>$1,400,000</b> financial exposure window across payment clusters</span>
                    </li>
                    <li className="flex items-start gap-1.5">
                      <span className="text-zinc-600">•</span>
                      <span><b>85%</b> of Sev-1 enterprise rollbacks caused by cross-package drift</span>
                    </li>
                    <li className="flex items-start gap-1.5">
                      <span className="text-zinc-600">•</span>
                      <span><b>4,000 hours / year</b> lost in emergency CAB and post-mortems ($2.4M saved)</span>
                    </li>
                  </ul>
                </div>

                <div className="mt-3 p-2 rounded-[4px] bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-300 leading-tight">
                  PCI-DSS Req 10.2.1: Audit trail identity continuity breach triggers mandatory regulatory remediation.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================================================================
            SLIDE 2: ARCHITECTURE (TWO-TIER DECOUPLED PLATFORM)
            ================================================================== */}
        {currentSlide === 2 && (
          <div className="flex-1 flex flex-col justify-center max-w-7xl mx-auto w-full animate-in fade-in zoom-in-95 duration-200">
            <div>
              <span className="px-2 py-0.5 rounded-[3px] bg-[#14151a] border border-white/20 text-[11px] font-semibold text-zinc-200 uppercase tracking-wider">
                02 · Two-Tier Decoupled Platform &amp; Asymptotic Scorer
              </span>
              <h2 className="text-2xl sm:text-4xl font-bold tracking-tight text-white leading-tight mt-2 mb-1.5">
                Sub-Second AST Determinism Meets Agentic Auto-Healing.
              </h2>
              <p className="text-xs sm:text-sm text-zinc-400 max-w-3xl leading-relaxed">
                We reject brute-force LLM sweeps over million-line monorepos.{" "}
                <span className="italic font-serif text-zinc-200">
                  Sub-second graph mathematics isolates the hazard; IBM Bob 2.0 synthesizes the surgical fix.
                </span>
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[1.3fr_0.7fr] gap-4 mt-3.5 items-stretch">
              {/* 3 Tier Bento Columns */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="rounded-[5px] border border-white/[0.08] bg-[#0f1013] p-3.5 flex flex-col justify-between hover:border-white/20 transition-colors">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Tier 1 · Core</span>
                      <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded-[2px]">1.2ms · $0</span>
                    </div>
                    <div className="text-xs font-semibold text-white mb-1">AST &amp; Graph Scorer</div>
                    <p className="text-[11px] text-zinc-400 leading-normal mb-2">
                      NetworkX DAG shockwave traversal with linear O(V+E) iterative DFS cycle breaker.
                    </p>
                    <ul className="text-[11px] text-zinc-300 space-y-1">
                      <li>• Saturation: <code>100*(1-exp(-R/55))</code></li>
                      <li>• Monorepo Density factor: <code>1.0+min(1.5*ratio, 1.25)</code></li>
                      <li>• Adversarial safety: CWE-94 regex isolation</li>
                    </ul>
                  </div>
                </div>

                <div className="rounded-[5px] border border-white/[0.18] border-t-2 border-t-zinc-300 bg-[#0f1013] p-3.5 flex flex-col justify-between hover:border-white/30 transition-colors">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">Tier 2 · Remediation</span>
                      <span className="text-[10px] font-semibold text-zinc-300 bg-zinc-800 px-1.5 py-0.5 rounded-[2px]">Bob + Granite</span>
                    </div>
                    <div className="text-xs font-semibold text-white mb-1">Two-Tier Auto-Healing</div>
                    <p className="text-[11px] text-zinc-400 leading-normal mb-2">
                      Bob Agent Mode invokes FastMCP stdio tools. Granite 3.0 synthesizes dual-layer remediation.
                    </p>
                    <ul className="text-[11px] text-zinc-300 space-y-1">
                      <li>• <b>Layer 1 Membrane:</b> 14-day Proxy with deduplicated <code>ownKeys</code>, <code>toJSON</code></li>
                      <li>• <b>Layer 2 Codemod:</b> Clean git-applyable unified diff PR eliminating technical debt</li>
                    </ul>
                  </div>
                </div>

                <div className="rounded-[5px] border border-white/[0.08] bg-[#0f1013] p-3.5 flex flex-col justify-between hover:border-white/20 transition-colors">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Tier 3 · Governance</span>
                      <span className="text-[10px] font-semibold text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded-[2px]">Docling + Ed25519</span>
                    </div>
                    <div className="text-xs font-semibold text-white mb-1">Dual-Control Gate</div>
                    <p className="text-[11px] text-zinc-400 leading-normal mb-2">
                      Docling extracts PCI-DSS v4.0.1 Req 10.2.1/3.4.2. Vectis mints immutable release passport.
                    </p>
                    <ul className="text-[11px] text-zinc-300 space-y-1">
                      <li>• RFC 8785 JCS canonicalization</li>
                      <li>• Dual-Control: <code>PENDING</code> → <code>APPROVED</code></li>
                      <li>• K8s Validating Webhook Admission</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Constellation 3D Glass Plate */}
              <div className="relative rounded-[6px] border border-white/20 bg-black overflow-hidden shadow-2xl flex items-center justify-center min-h-[200px]">
                <Image
                  src="/assets/slides/glass-dag-constellation.png"
                  alt="Vectis Constellation DAG Plate"
                  fill
                  className="object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-transparent to-transparent" />
                <div className="absolute bottom-2.5 left-3 right-3 text-[10px] text-zinc-400 font-medium">
                  TOPOLOGICAL GRAPH ISOLATION · CORE TO GATEWAY SHOCKWAVE DECAY
                </div>
              </div>
            </div>

            {/* Token Economics Comparison Bar */}
            <div className="mt-3 flex items-center justify-between text-xs bg-[#0f1013] px-4 py-2 border border-white/[0.08] rounded-[4px]">
              <div>
                <span className="text-rose-400 font-semibold">Naive LLM Sweep:</span> 450,000 tokens ($4.50/PR) · 38s latency · High hallucination risk
              </div>
              <div className="text-zinc-600">|</div>
              <div>
                <span className="text-emerald-400 font-semibold">Vectis Two-Tier:</span> 0 tokens on triage (1.2ms) · 1,200 surgical Granite tokens ($0.003) · <b className="text-white">99.9% cost reduction · 100% deterministic</b>
              </div>
            </div>
          </div>
        )}

        {/* ==================================================================
            SLIDE 3: THE IMPACT & LIVE DEMO - 1-CLICK RESOLUTION
            ================================================================== */}
        {currentSlide === 3 && (
          <div className="flex-1 flex flex-col justify-center max-w-7xl mx-auto w-full animate-in fade-in zoom-in-95 duration-200">
            <div>
              <span className="px-2 py-0.5 rounded-[3px] bg-emerald-500/10 border border-emerald-500/25 text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
                03 · Verified ROI &amp; Autonomous Live Gate
              </span>
              <h2 className="text-2xl sm:text-4xl font-bold tracking-tight text-white leading-tight mt-2 mb-1.5">
                From Critical Hazard to Verified Release in 6.2 Seconds.
              </h2>
              <p className="text-xs sm:text-sm text-zinc-400 max-w-3xl leading-relaxed">
                Zero downstream refactoring required. PR #482 ships without delaying release windows or compromising financial compliance.
              </p>
            </div>

            {/* Split: Simulation Box + Release Passport Holographic Tablet */}
            <div className="grid grid-cols-1 lg:grid-cols-[1.25fr_0.75fr] gap-3.5 mt-3 items-stretch">
              {/* Simulation Box */}
              <div className="rounded-[5px] border border-white/[0.12] bg-[#0f1013] p-3.5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Live Gate:</span>
                      <span
                        className={`text-[11px] font-semibold px-2 py-0.5 rounded-[3px] border ${
                          isHealed
                            ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                            : "bg-rose-500/15 border-rose-500/30 text-rose-400"
                        }`}
                      >
                        {isHealed ? "✓ RELEASE APPROVED · RISK: 12.0 / 100" : "⛔ GATE LOCKED · RISK: 84.0 / 100"}
                      </span>
                      <span
                        className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-[3px] border ${
                          isHealed
                            ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                            : "bg-rose-500/10 border-rose-500/20 text-rose-400"
                        }`}
                      >
                        {isHealed ? "K8s: [200 OK]" : "K8s: [403 FORBIDDEN]"}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={handleToggleHeal}
                        className={`px-2.5 py-1 text-xs font-semibold rounded-[3px] border cursor-pointer transition-colors ${
                          isHealed && !isCodemod
                            ? "bg-emerald-500/20 border-emerald-500 text-emerald-300"
                            : "bg-zinc-800/80 border-white/20 text-zinc-200 hover:bg-zinc-700"
                        }`}
                      >
                        ✨ Proxy Shim (L1)
                      </button>
                      <button
                        onClick={handleToggleCodemod}
                        className={`px-2.5 py-1 text-xs font-semibold rounded-[3px] border cursor-pointer transition-colors ${
                          isCodemod
                            ? "bg-emerald-500/20 border-emerald-500 text-emerald-300"
                            : "bg-zinc-800/80 border-white/20 text-zinc-200 hover:bg-zinc-700"
                        }`}
                      >
                        🔧 Codemod PR (L2)
                      </button>
                    </div>
                  </div>

                  {/* Mini Nodes Diagram */}
                  <div className="flex items-center justify-between py-2 border-y border-white/[0.06]">
                    <div className="flex items-center gap-2 text-xs">
                      <div className="px-2.5 py-1.5 rounded-[3px] bg-[#14151a] border border-white/10 flex flex-col">
                        <span className="font-semibold text-zinc-300 text-[11px]">models/user.ts</span>
                        <span className="text-[9px] text-zinc-500">Root Contract</span>
                      </div>
                      <span className="text-zinc-600">→</span>
                      <div
                        className={`px-2.5 py-1.5 rounded-[3px] border flex flex-col transition-colors ${
                          isHealed
                            ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                            : "bg-rose-500/10 border-rose-500/40 text-rose-300 shadow-[0_0_12px_rgba(239,68,68,0.2)]"
                        }`}
                      >
                        <span className="font-semibold text-[11px]">auth/session.ts</span>
                        <span className="text-[9px] opacity-75">
                          {isHealed ? (isCodemod ? "Clean Codemod" : "Proxy Active") : "PR #482 Breaking"}
                        </span>
                      </div>
                      <span className={isHealed ? "text-emerald-500" : "text-rose-500"}>→</span>
                      <div
                        className={`px-2.5 py-1.5 rounded-[3px] border flex flex-col transition-colors ${
                          isHealed
                            ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                            : "bg-rose-500/10 border-rose-500/40 text-rose-300"
                        }`}
                      >
                        <span className="font-semibold text-[11px]">checkout.ts</span>
                        <span className="text-[9px] opacity-75">
                          {isHealed ? "Legacy id Safe" : "Stripe Undefined"}
                        </span>
                      </div>
                      <span className={isHealed ? "text-emerald-500" : "text-rose-500"}>→</span>
                      <div
                        className={`px-2.5 py-1.5 rounded-[3px] border flex flex-col transition-colors ${
                          isHealed
                            ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                            : "bg-rose-500/10 border-rose-500/40 text-rose-300"
                        }`}
                      >
                        <span className="font-semibold text-[11px]">settlement_cron.ts</span>
                        <span className="text-[9px] opacity-75">
                          {isHealed ? "Ledger Verified" : "ledger_undefined"}
                        </span>
                      </div>
                    </div>

                    <div className="text-[11px] text-right">
                      {isHealed ? (
                        <span className="text-emerald-400 font-medium">Dual-Control Approved</span>
                      ) : (
                        <span className="text-zinc-500">Awaiting Remediation</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Granular Code Proof */}
                {isHealed ? (
                  <div className="mt-2 p-2 bg-black/60 border border-white/10 rounded-[3px] text-[11px] leading-relaxed">
                    <div className="flex items-center justify-between text-emerald-400 font-semibold mb-1 text-[10px]">
                      <span>
                        {isCodemod ? "Clean AST Codemod PR (IBM Granite 3.0)" : "Synthesized Dual-Contract Proxy Shim"}
                      </span>
                      <span>{isCodemod ? "Layer 2 Permanent Refactor" : "Layer 1 Ephemeral Membrane (14-Day TTL)"}</span>
                    </div>
                    {isCodemod ? (
                      <div className="text-zinc-300">
                        <code>--- a/src/payments/checkout.ts</code><br />
                        <code>+++ b/src/payments/checkout.ts</code><br />
                        <code>-  const customerId = user.id;</code><br />
                        <code>+  const customerId = user.sub; // migrated from deprecated User.id</code>
                      </div>
                    ) : (
                      <div className="text-zinc-300">
                        <code>export const SessionUserProxy = new Proxy(session, &#123;</code><br />
                        <code>  get: (t, p) =&gt; p === &apos;id&apos; ? t.sub : (p === &apos;tier&apos; ? t.metadata?.tier : t[p]),</code><br />
                        <code>  ownKeys: (t) =&gt; Array.from(new Set([...Reflect.ownKeys(t), &apos;id&apos;, &apos;tier&apos;])),</code><br />
                        <code>  toJSON: (t) =&gt; (&#123; ...t, id: t.sub, tier: t.metadata?.tier &#125;)</code><br />
                        <code>&#125;);</code>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="mt-2 p-2 bg-rose-500/5 border border-rose-500/20 rounded-[3px] text-[11px] text-rose-300">
                    Release Quarantined: Downstream callers orphaned by breaking contract mutation in <code>auth/session.ts</code>.
                  </div>
                )}
              </div>

              {/* Release Passport Holographic Tablet Plate */}
              <div className="relative rounded-[6px] border border-white/20 bg-black overflow-hidden shadow-2xl flex items-center justify-center min-h-[170px]">
                <Image
                  src="/assets/slides/glass-release-passport.png"
                  alt="Vectis Holographic Release Passport"
                  fill
                  className="object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-transparent to-transparent" />
                <div className="absolute bottom-2.5 left-3 right-3 text-[10px] text-white flex items-center justify-between font-medium">
                  <span>RFC 8785 CANONICAL SEAL</span>
                  <span className="text-emerald-400 font-semibold">ED25519 DUAL-CONTROL PASSPORT</span>
                </div>
              </div>
            </div>

            {/* Scorecard Metrics */}
            <div className="grid grid-cols-4 gap-2.5 mt-3">
              <div className="rounded-[4px] border border-white/[0.08] bg-[#0f1013] p-3 text-center">
                <div className="text-xl font-bold text-white tabular-nums">1.2ms</div>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">AST Detection Latency</div>
              </div>
              <div className="rounded-[4px] border border-white/[0.08] bg-[#0f1013] p-3 text-center">
                <div className={`text-xl font-bold tabular-nums ${isHealed ? "text-emerald-400" : "text-rose-500"}`}>
                  {isHealed ? "12.0 / 100" : "84.0 → 12"}
                </div>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">Risk Score Post-Healing</div>
              </div>
              <div className="rounded-[4px] border border-white/[0.08] bg-[#0f1013] p-3 text-center">
                <div className="text-xl font-bold text-emerald-400 tabular-nums">95.8 / 100</div>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">Master 40-Subagent Score</div>
              </div>
              <div className="rounded-[4px] border border-white/[0.08] bg-[#0f1013] p-3 text-center">
                <div className="text-xl font-bold text-white tabular-nums">0 Lines</div>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">Downstream Code Rewrite</div>
              </div>
            </div>

            {/* Commercial Pricing Strip */}
            <div className="grid grid-cols-3 gap-2.5 mt-2.5">
              <div className="rounded-[4px] border border-white/[0.08] bg-[#0f1013] p-2.5">
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider">Seat-Based SaaS</div>
                <div className="text-sm font-semibold text-white mt-0.5">
                  $49 - $99 <span className="text-[10px] text-zinc-500 font-normal">/ committer / mo</span>
                </div>
                <div className="text-[10px] text-zinc-400">Self-serve CI triage, branch protection, monorepo graph</div>
              </div>

              <div className="rounded-[4px] border border-white/20 bg-[#0f1013] p-2.5">
                <div className="text-[10px] text-zinc-400 uppercase tracking-wider">Enterprise VPC</div>
                <div className="text-sm font-semibold text-white mt-0.5">
                  $75,000 - $120,000 <span className="text-[10px] text-zinc-500 font-normal">ACV</span>
                </div>
                <div className="text-[10px] text-zinc-400">watsonx.governance, air-gapped runners, custom FastMCP</div>
              </div>

              <div className="rounded-[4px] border border-white/[0.08] border-l-2 border-l-emerald-500 bg-[#0f1013] p-2.5">
                <div className="text-[10px] text-emerald-400 uppercase tracking-wider font-semibold">CFO Payback Ratio</div>
                <div className="text-sm font-semibold text-emerald-400 mt-0.5">
                  0.31 Outages <span className="text-[10px] text-zinc-500 font-normal">(113 Days)</span>
                </div>
                <div className="text-[10px] text-zinc-400">1 prevented outage ($240k) covers 2.4 yrs of Enterprise ACV</div>
              </div>
            </div>
          </div>
        )}

        {/* Global Slide Footer */}
        <footer className="w-full border-t border-white/[0.08] pt-2.5 flex items-center justify-between text-xs text-zinc-500 shrink-0">
          <div>
            Vectis + IBM Bob 2.0: <span className="italic font-serif text-zinc-400">The Pre-Merge Fulcrum That Eliminates Midnight Disasters</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Use <b>← / →</b> or <b>Space</b> to navigate · <b>1-4</b> for jump · <b>F</b> for Fullscreen</span>
            <Link href="/cockpit" className="text-zinc-300 hover:text-white underline">
              Launch Cockpit Canvas ↗
            </Link>
          </div>
        </footer>
      </main>
    </div>
  );
}
