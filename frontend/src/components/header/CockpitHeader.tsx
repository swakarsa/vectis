"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ShieldCheck,
  ShieldWarning,
  GitPullRequest,
  ArrowsClockwise,
  DownloadSimple,
  TerminalWindow,
  ArrowLeft,
} from "@phosphor-icons/react";

interface CockpitHeaderProps {
  verdict: "BLOCK" | "WARN" | "PASS" | "IDLE";
  riskScore: number;
  loading: boolean;
  onAnalyze: () => void;
  onDownloadPassport: () => void;
  passportAvailable: boolean;
  mode?: "benchmark" | "live_github";
  onModeChange?: (mode: "benchmark" | "live_github") => void;
  activeRepo?: string;
  activePR?: number | string;
}

export function CockpitHeader({
  verdict,
  riskScore,
  loading,
  onAnalyze,
  onDownloadPassport,
  passportAvailable,
  mode = "benchmark",
  onModeChange,
  activeRepo = "swakarsa/vectis",
  activePR = 482,
}: CockpitHeaderProps) {
  let statusDot = "bg-zinc-500";
  let statusLabel = "Awaiting PR Analysis";
  let statusTextColor = "text-zinc-400";
  let riskColor = "text-zinc-400";

  if (verdict === "BLOCK") {
    statusDot = "bg-rose-500 animate-pulse";
    statusLabel = "Release Blocked";
    statusTextColor = "text-rose-400";
    riskColor = "text-rose-400";
  } else if (verdict === "WARN") {
    statusDot = "bg-amber-400";
    statusLabel = "Review Required";
    statusTextColor = "text-amber-400";
    riskColor = "text-amber-400";
  } else if (verdict === "PASS") {
    statusDot = "bg-emerald-400";
    statusLabel = "Gate Cleared";
    statusTextColor = "text-emerald-400";
    riskColor = "text-emerald-400";
  }

  return (
    <header className="h-14 border-b border-white/[0.08] bg-[#090a0d]/95 backdrop-blur-md px-5 flex items-center justify-between z-20">
      {/* Left Branding & Mode Toggle */}
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="flex items-center gap-2 text-xs text-zinc-400 hover:text-zinc-200 transition-colors mr-1"
          title="Back to Landing Page"
        >
          <ArrowLeft size={14} />
          <span>Home</span>
        </Link>

        <div className="h-4 w-[1px] bg-white/[0.08]" />

        <Link href="/" className="flex items-center gap-2.5 group">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo-white.png"
            alt="Vectis Logo"
            width={26}
            height={26}
            className="w-6.5 h-6.5 object-contain transition-transform group-hover:scale-105"
          />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-tight text-white group-hover:text-zinc-200 transition-colors">
                Vectis
              </span>
              <span className="text-xs text-zinc-500 font-normal">
                Release Gate
              </span>
            </div>
          </div>
        </Link>

        <div className="h-4 w-[1px] bg-white/[0.08]" />

        {/* Mode Selector */}
        <div className="flex items-center bg-[#131418] border border-white/[0.08] rounded-[4px] p-0.5 text-xs">
          <button
            onClick={() => onModeChange?.("benchmark")}
            className={`px-2.5 py-1 rounded-[3px] font-medium transition-all ${
              mode === "benchmark"
                ? "bg-zinc-800 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            PR #482 Benchmark
          </button>
          <button
            onClick={() => onModeChange?.("live_github")}
            className={`px-2.5 py-1 rounded-[3px] font-medium transition-all flex items-center gap-1.5 ${
              mode === "live_github"
                ? "bg-zinc-800 text-emerald-300 shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live GitHub Defender
          </button>
        </div>

        {/* Live Defender Status Badge */}
        <div className="hidden xl:flex items-center gap-2 text-[11px] text-zinc-500 border border-white/[0.06] bg-white/[0.02] px-2.5 py-1 rounded-[4px]">
          <span className="text-emerald-400 font-mono">CI: ACTIVE</span>
          <span className="text-zinc-600">·</span>
          <span>Webhook: 200 OK</span>
          <span className="text-zinc-600">·</span>
          <span className="text-zinc-400">Fail-Closed Gate</span>
        </div>
      </div>

      {/* Middle Telemetry & Verdict (No badges, No pills) */}
      <div className="flex items-center gap-7">
        {/* Risk Score */}
        <div className="flex items-baseline gap-2">
          <span className="text-xs text-zinc-500 uppercase tracking-wider font-medium">
            Risk Score
          </span>
          <span className={`text-xl font-bold tracking-tight tabular-nums ${riskColor}`}>
            {riskScore.toFixed(1)}
          </span>
          <span className="text-xs text-zinc-600">/ 100</span>
        </div>

        {/* Status Dot + Text (Vercel/Linear style) */}
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${statusDot}`} />
          <span className={`text-xs font-semibold uppercase tracking-wider ${statusTextColor}`}>
            {statusLabel}
          </span>
        </div>
      </div>

      {/* Right Action Buttons (Crisp rectangular style, no pills) */}
      <div className="flex items-center gap-2.5">
        {passportAvailable && (
          <button
            onClick={onDownloadPassport}
            className="h-8 px-3 rounded-[4px] border border-white/[0.1] bg-[#14151a] hover:bg-[#1c1d24] text-xs font-medium text-zinc-200 transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <DownloadSimple size={14} className="text-emerald-400" />
            <span>Release Passport</span>
          </button>
        )}

        <button
          onClick={onAnalyze}
          disabled={loading}
          className="h-8 px-3.5 rounded-[4px] bg-white text-black hover:bg-zinc-200 text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          {loading ? (
            <>
              <ArrowsClockwise size={14} className="animate-spin" />
              <span>Analyzing AST...</span>
            </>
          ) : (
            <>
              <TerminalWindow size={14} weight="bold" />
              <span>Run Gate Audit</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
}
