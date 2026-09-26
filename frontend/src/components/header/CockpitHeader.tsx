"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ShieldWarning,
  GitPullRequest,
  ArrowsClockwise,
  DownloadSimple,
  TerminalWindow,
  ArrowLeft,
} from "@phosphor-icons/react";
import { GitHubAuthButton } from "./GitHubAuthButton";

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
  shimApplied?: boolean;
  onResetToBreaking?: () => void;
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
  shimApplied,
  onResetToBreaking,
}: CockpitHeaderProps) {
  let statusDot = "bg-zinc-500";
  let statusLabel = "Awaiting PR Analysis";
  let statusTextColor = "text-zinc-400";

  if (verdict === "BLOCK") {
    statusDot = "bg-rose-500 animate-pulse";
    statusLabel = `Release Blocked (${riskScore.toFixed(0)}/100)`;
    statusTextColor = "text-rose-400";
  } else if (verdict === "WARN") {
    statusDot = "bg-amber-400";
    statusLabel = `Review Required (${riskScore.toFixed(0)}/100)`;
    statusTextColor = "text-amber-400";
  } else if (verdict === "PASS") {
    statusDot = "bg-emerald-400";
    statusLabel = `Gate Cleared (${riskScore.toFixed(0)}/100)`;
    statusTextColor = "text-emerald-400";
  }

  return (
    <header className="h-12 shrink-0 border-b border-white/[0.08] bg-[#090a0d]/95 backdrop-blur-md px-4 flex items-center justify-between z-20 select-none">
      {/* Left: Branding & Mode Switcher */}
      <div className="flex items-center gap-2.5">
        <Link
          href="/"
          className="flex items-center gap-1 text-xs text-zinc-400 hover:text-white transition-colors"
          title="Back to Landing Page"
        >
          <ArrowLeft size={12} />
          <span>Home</span>
        </Link>

        <div className="h-3 w-[1px] bg-white/[0.1]" />

        <Link href="/" className="flex items-center gap-1.5 group">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo-white.png"
            alt="Vectis Logo"
            width={20}
            height={20}
            className="w-5 h-5 object-contain"
          />
          <div className="flex items-center gap-1">
            <span className="text-xs font-semibold tracking-tight text-white">
              Vectis
            </span>
            <span className="text-[10px] text-zinc-500 font-normal">
              Release Gate
            </span>
          </div>
        </Link>

        <div className="h-3 w-[1px] bg-white/[0.1]" />

        {/* Mode Segment Switch */}
        <div className="flex items-center bg-[#131418] border border-white/[0.08] rounded-[3px] p-0.5 text-[11px]">
          <button
            onClick={() => onModeChange?.("benchmark")}
            className={`px-2.5 py-0.5 rounded-[2px] font-medium transition-all cursor-pointer ${
              mode === "benchmark"
                ? "bg-zinc-800 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
            title="Interactive Jury Simulation Sandbox (Pre-configured PR #482 OIDC contract drift)"
          >
            Jury Simulation Sandbox
          </button>
          <button
            onClick={() => onModeChange?.("live_github")}
            className={`px-2.5 py-0.5 rounded-[2px] font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
              mode === "live_github"
                ? "bg-zinc-800 text-emerald-300 shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
            title="Swakarsa Live Defender (Direct real-time GitHub Bot connected to your repositories)"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Swakarsa Live Defender
          </button>
        </div>
      </div>

      {/* Center: Clean Gate Status */}
      <div className="flex items-center gap-2 text-xs">
        <span className={`w-2 h-2 rounded-full ${statusDot}`} />
        <span className={`font-semibold tracking-tight ${statusTextColor}`}>
          {statusLabel}
        </span>
        {passportAvailable && (
          <button
            onClick={onDownloadPassport}
            className="ml-1 text-[11px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors cursor-pointer"
            title="Download Cryptographic Release Passport"
          >
            <DownloadSimple size={12} weight="bold" />
            <span className="underline underline-offset-2">Passport</span>
          </button>
        )}
      </div>

      {/* Right: Actions - Fixed 2 elements (Never expands or bloats) */}
      <div className="flex items-center gap-2">
        <GitHubAuthButton />

        {/* Dynamic Single-Slot Primary Action */}
        {mode === "benchmark" && shimApplied && onResetToBreaking ? (
          <button
            onClick={onResetToBreaking}
            className="h-8 px-3 rounded-[3px] border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-xs font-semibold text-rose-300 transition-colors flex items-center gap-1.5 cursor-pointer"
            title="Re-inject breaking contract mutations to test the blocker again (Jury Simulation Sandbox only)"
          >
            <ShieldWarning size={13} className="text-rose-400" />
            <span>Re-inject Drift</span>
          </button>
        ) : (
          <button
            onClick={onAnalyze}
            disabled={loading}
            className="h-8 px-3.5 rounded-[3px] bg-white text-black hover:bg-zinc-200 text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {loading ? (
              <>
                <ArrowsClockwise size={13} className="animate-spin" />
                <span>Analyzing AST...</span>
              </>
            ) : (
              <>
                <TerminalWindow size={13} weight="bold" />
                <span>Run Gate Audit</span>
              </>
            )}
          </button>
        )}
      </div>
    </header>
  );
}
