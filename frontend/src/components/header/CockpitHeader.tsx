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
  Cpu,
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
  onApplyShim?: () => void;
  shimLoading?: boolean;
  mobileView?: "canvas" | "panel";
  onToggleMobileView?: (view: "canvas" | "panel") => void;
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
  onApplyShim,
  shimLoading = false,
  mobileView = "canvas",
  onToggleMobileView,
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
    <header className="h-11 shrink-0 border-b border-white/[0.08] bg-[#090a0d]/95 backdrop-blur-md px-3 sm:px-4 flex items-center justify-between z-20 select-none whitespace-nowrap overflow-x-auto">
      {/* Left: Branding & Mode Switcher */}
      <div className="flex items-center gap-2.5 shrink-0 whitespace-nowrap">
        <Link
          href="/"
          className="flex items-center gap-1 text-xs text-zinc-400 hover:text-white transition-colors shrink-0 whitespace-nowrap"
          title="Back to Landing Page"
        >
          <ArrowLeft size={12} />
          <span className="hidden sm:inline">Home</span>
        </Link>

        <div className="h-3 w-[1px] bg-white/[0.1] shrink-0" />

        <Link href="/" className="flex items-center gap-1.5 group shrink-0 whitespace-nowrap">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo-white.png"
            alt="Vectis Logo"
            width={18}
            height={18}
            className="w-4.5 h-4.5 object-contain shrink-0"
          />
          <div className="flex items-center gap-1 shrink-0 whitespace-nowrap">
            <span className="text-xs font-semibold tracking-tight text-white">
              Vectis
            </span>
            <span className="text-[10px] text-zinc-500 font-normal hidden md:inline">
              Release Gate
            </span>
          </div>
        </Link>

        <div className="h-3 w-[1px] bg-white/[0.1] shrink-0" />

        {/* Mode Segment Switch */}
        <div className="flex items-center bg-[#131418] border border-white/[0.08] rounded-[3px] p-0.5 text-[11px] shrink-0 whitespace-nowrap">
          <button
            onClick={() => onModeChange?.("benchmark")}
            className={`px-2.5 py-0.5 rounded-[2px] font-medium transition-all cursor-pointer whitespace-nowrap shrink-0 ${
              mode === "benchmark"
                ? "bg-zinc-800 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
            title="Simulation Sandbox (Pre-configured PR #482 OIDC contract drift benchmark)"
          >
            Sandbox
          </button>
          <button
            onClick={() => onModeChange?.("live_github")}
            className={`px-2.5 py-0.5 rounded-[2px] font-medium transition-all flex items-center gap-1.5 cursor-pointer whitespace-nowrap shrink-0 ${
              mode === "live_github"
                ? "bg-zinc-800 text-emerald-300 shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
            title="Vectis Live Gate (Real-time release gate & AST contract verification connected to your repositories)"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
            <span>Live Gate</span>
          </button>
        </div>

        {/* Mobile View Toggle */}
        <div className="flex lg:hidden items-center bg-[#131418] border border-white/[0.08] rounded-[3px] p-0.5 text-[10px]">
          <button
            onClick={() => onToggleMobileView?.("canvas")}
            className={`px-2 py-0.5 rounded-[2px] font-medium ${mobileView === 'canvas' ? 'bg-zinc-800 text-white' : 'text-zinc-400'}`}
          >
            Canvas
          </button>
          <button
            onClick={() => onToggleMobileView?.("panel")}
            className={`px-2 py-0.5 rounded-[2px] font-medium ${mobileView === 'panel' ? 'bg-zinc-800 text-white' : 'text-zinc-400'}`}
          >
            Details
          </button>
        </div>
      </div>

      {/* Center: Clean Gate Status */}
      <div className="flex items-center gap-1.5 text-xs shrink-0 whitespace-nowrap px-2">
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${statusDot}`} />
        <span className={`font-semibold tracking-tight whitespace-nowrap ${statusTextColor}`}>
          {statusLabel}
        </span>
        {passportAvailable && (
          <button
            onClick={onDownloadPassport}
            className="ml-1 text-[11px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors cursor-pointer whitespace-nowrap shrink-0"
            title="Download Cryptographic Release Passport"
          >
            <DownloadSimple size={12} weight="bold" />
            <span className="underline underline-offset-2">Passport</span>
          </button>
        )}
      </div>

      {/* Right: Actions - Fixed 2 elements */}
      <div className="flex items-center gap-2 shrink-0 whitespace-nowrap">
        <GitHubAuthButton />

        {/* Primary Action Button: Auto-Heal in Sandbox, Run Audit in Live Gate */}
        {mode === "benchmark" ? (
          !shimApplied ? (
            <button
              onClick={onApplyShim}
              disabled={shimLoading}
              className="h-7 px-3 rounded-[3px] bg-white text-black hover:bg-zinc-200 text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50 whitespace-nowrap shrink-0 shadow-sm"
              title="Auto-Heal PR with IBM Granite 3.0"
            >
              {shimLoading ? (
                <>
                  <ArrowsClockwise size={13} className="animate-spin shrink-0" />
                  <span>Synthesizing Shim...</span>
                </>
              ) : (
                <>
                  <Cpu size={14} weight="bold" className="shrink-0" />
                  <span>Auto-Heal PR with Granite 3.0</span>
                </>
              )}
            </button>
          ) : (
            <div className="flex items-center gap-1.5 shrink-0">
              <button
                onClick={onDownloadPassport}
                className="h-7 px-2.5 rounded-[3px] bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 text-xs font-medium transition-colors flex items-center gap-1.5 cursor-pointer whitespace-nowrap shrink-0"
                title="Download Cryptographic Release Passport (RFC 8785)"
              >
                <DownloadSimple size={13} weight="bold" className="shrink-0" />
                <span>Release Passport</span>
              </button>
              {onResetToBreaking && (
                <button
                  onClick={onResetToBreaking}
                  className="h-7 px-2 rounded-[3px] bg-white/[0.06] hover:bg-white/[0.12] text-zinc-400 hover:text-white text-xs font-medium transition-colors flex items-center gap-1 cursor-pointer whitespace-nowrap shrink-0"
                  title="Reset Demo to Breaking State"
                >
                  <ArrowsClockwise size={12} className="shrink-0" />
                  <span>Reset</span>
                </button>
              )}
            </div>
          )
        ) : (
          <button
            onClick={onAnalyze}
            disabled={loading}
            className="h-7 px-3 rounded-[3px] bg-white text-black hover:bg-zinc-200 text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50 whitespace-nowrap shrink-0"
          >
            {loading ? (
              <>
                <ArrowsClockwise size={12} className="animate-spin shrink-0" />
                <span>Auditing...</span>
              </>
            ) : (
              <>
                <TerminalWindow size={12} weight="bold" className="shrink-0" />
                <span>Run Gate Audit</span>
              </>
            )}
          </button>
        )}
      </div>
    </header>
  );
}
