"use client";

import React from "react";
import { LandingNavbar } from "@/components/landing/LandingNavbar";
import { HeroSection } from "@/components/landing/HeroSection";
import { OutageProblemSection } from "@/components/landing/OutageProblemSection";
import { WorkflowLoopSection } from "@/components/landing/WorkflowLoopSection";
import { BentoGridSection } from "@/components/landing/BentoGridSection";
import { LandingFooter } from "@/components/landing/LandingFooter";

export default function LandingPage() {
  return (
    <main className="min-h-screen w-full bg-[#08090a] text-zinc-100 flex flex-col font-sans selection:bg-rose-500/20 selection:text-rose-200">
      {/* 1. Developer Navbar */}
      <LandingNavbar />

      {/* 2. Hero & Interactive CLI Terminal */}
      <HeroSection />

      {/* 3. Outage Root Cause Analysis & Comparison */}
      <OutageProblemSection />

      {/* 4. Native GitHub CI Gatekeeper 3-Step Workflow & PR Mockup */}
      <WorkflowLoopSection />

      {/* 5. 4 Core Pillars Bento Grid */}
      <BentoGridSection />

      {/* 6. Final Call to Action & Footer */}
      <LandingFooter />
    </main>
  );
}
