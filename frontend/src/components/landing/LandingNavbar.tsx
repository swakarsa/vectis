"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, TerminalWindow, GitPullRequest } from "@phosphor-icons/react";

export function LandingNavbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/[0.08] bg-[#08090a]/90 backdrop-blur-md">
      <div className="relative max-w-7xl mx-auto px-5 sm:px-8 h-14 flex items-center justify-between">
        {/* Left: Branding */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/logo-white.png"
              alt="Vectis Logo"
              width={26}
              height={26}
              className="w-6.5 h-6.5 object-contain transition-transform group-hover:scale-105"
            />
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-tight text-white group-hover:text-zinc-200 transition-colors">
                Vectis
              </span>
              <span className="text-xs text-zinc-500 font-normal">
                | Release Gate
              </span>
            </div>
          </Link>

          <div className="hidden md:flex items-center gap-1 pl-4 border-l border-white/[0.08] text-xs text-zinc-400">
            <span className="flex items-center gap-1.5 text-zinc-300">
              <GitPullRequest size={13} className="text-zinc-500" />
              <span>fintech-monorepo</span>
            </span>
          </div>
        </div>

        {/* Center: Quick Links (Centering perfectly with viewport & hero section) */}
        <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 items-center gap-8 text-xs font-medium text-zinc-400">
          <a href="#problem" className="hover:text-zinc-200 transition-colors">
            Problem
          </a>
          <a href="#workflow" className="hover:text-zinc-200 transition-colors">
            3-Step Workflow
          </a>
          <a href="#architecture" className="hover:text-zinc-200 transition-colors">
            Architecture
          </a>
          <a href="#compliance" className="hover:text-zinc-200 transition-colors">
            PCI-DSS v4.0.1
          </a>
        </div>

        {/* Right: CTA to Cockpit */}
        <div className="flex items-center gap-3">
          <Link
            href="/cockpit"
            className="h-8 px-3.5 rounded-[4px] bg-white text-black hover:bg-zinc-200 text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <TerminalWindow size={14} weight="bold" />
            <span>Launch Cockpit</span>
            <ArrowRight size={13} weight="bold" />
          </Link>
        </div>
      </div>
    </nav>
  );
}
