"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, TerminalWindow } from "@phosphor-icons/react";

export function LandingFooter() {
  return (
    <footer className="border-t border-white/[0.08] bg-[#060708] pt-20 pb-12">
      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        {/* Call to Action Banner */}
        <div className="max-w-4xl mx-auto text-center pb-20 border-b border-white/[0.08]">
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            Deploy with mathematical certainty.
          </h2>
          <p className="mt-4 text-sm sm:text-base text-zinc-400 max-w-xl mx-auto leading-relaxed">
            Stop relying on luck and flaky unit tests. Protect every pull request with deterministic AST intelligence and autonomous shims.
          </p>

          <div className="mt-8 flex justify-center">
            <Link
              href="/cockpit"
              className="h-10 px-6 rounded-[4px] bg-white text-black hover:bg-zinc-200 text-xs sm:text-sm font-semibold transition-colors flex items-center gap-2 cursor-pointer shadow-sm"
            >
              <TerminalWindow size={16} weight="bold" />
              <span>Launch Interactive Cockpit</span>
              <ArrowRight size={14} weight="bold" />
            </Link>
          </div>
        </div>

        {/* Enterprise B2B SaaS Footer: Left Copyright | Center Hackathon | Right Navigation */}
        <div className="pt-8 flex flex-col lg:flex-row items-center justify-between gap-6 text-xs text-zinc-500">
          {/* Left: Founder Copyright */}
          <div className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/logo-white.png"
              alt="Vectis Logo"
              width={22}
              height={22}
              className="w-5.5 h-5.5 object-contain"
            />
            <span className="text-zinc-400 font-normal">
              &copy; 2026 Vectis, Inc. All rights reserved.
            </span>
          </div>

          {/* Center: Subtle Hackathon Attribution */}
          <div className="text-zinc-500 font-normal text-center">
            Built for IBM Bob 2.0 Hackathon on{" "}
            <a
              href="https://lablab.ai/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-zinc-400 hover:text-zinc-200 underline underline-offset-2 transition-colors"
            >
              lablab.ai
            </a>
          </div>

          {/* Right: Spacious Minimalist Navigation Links */}
          <div className="flex items-center gap-6 text-zinc-400">
            <a
              href="https://github.com/swakarsa/vectis"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-zinc-200 transition-colors"
            >
              GitHub
            </a>
            <Link
              href="/cockpit"
              className="hover:text-zinc-200 transition-colors"
            >
              Live Cockpit
            </Link>
            <a
              href="#architecture"
              className="hover:text-zinc-200 transition-colors"
            >
              Architecture
            </a>
            <a
              href="#compliance"
              className="hover:text-zinc-200 transition-colors"
            >
              PCI-DSS Audit
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
