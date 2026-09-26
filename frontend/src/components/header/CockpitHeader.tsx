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
    <header className="h-14 border-b border-white/[0.08] bg-[#090a0d]/95 backdrop-blur-md px-5 flex items-center justify-between z-20 select-none">
      {/* Left: Branding & Mode Switcher */}
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition-colors"
          title="Back to Landing Page"
        >
          <ArrowLeft size={13} />
          <span>Home</span>
        </Link>

        <div className="h-3.5 w-[1px] bg-white/[0.1]" />

        <Link href="/" className="flex items-center gap-2 group">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo-white.png"
            alt="Vectis Logo"
            width={22}
            height={22}
            className="w-5.5 h-5.5 object-contain"
          />
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-semibold tracking-tight text-white">
              Vectis
            </span>
            <span className="text-[11px] text-zinc-500 font-normal">
              Release Gate
            </span>
          </div>
        </Link>

        <div className="h-3.5 w-[1px] bg-white/[0.1]" />

        {/* Mode Segment Switch */}
        <div className="flex items-center bg-[#131418] border border-white/[0.08] rounded-[4px] p-0.5 text-xs">
          <button
            onClick={() => onModeChange?.("benchmark")}
            className={`px-3 py-1 rounded-[3px] font-medium transition-all cursor-pointer ${
              mode === "benchmark"
                ? "bg-zinc-800 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            PR #482 Benchmark
          </button>
          <button
            onClick={() => onModeChange?.("live_github")}
            className={`px-3 py-1 rounded-[3px] font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
              mode === "live_github"
                ? "bg-zinc-800 text-emerald-300 shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Live GitHub Defender
          </button>
        </div>
      </div>

      {/* Center: Clean Gate Status */}
      <div className="flex items-center gap-2 text-xs">
        <span className={`w-2 h-2 rounded-full ${statusDot}`} />
        <span className={`font-semibold tracking-tight ${statusTextColor}`}>
          {statusLabel}
        </span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2.5">
        <GitHubAuthButton />

        {passportAvailable && (
          <button
            onClick={onDownloadPassport}
            className="h-8 px-3 rounded-[4px] border border-white/[0.1] bg-[#14151a] hover:bg-[#1c1d24] text-xs font-medium text-zinc-200 transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <DownloadSimple size={13} className="text-emerald-400" />
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
      </div>
    </header>
  );
}
