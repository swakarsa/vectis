"use client";

import React, { useState } from "react";
import { CaretDown, Question, ShieldCheck, Lightning, Cpu, LockKey, GitPullRequest } from "@phosphor-icons/react";

interface FAQItem {
  id: string;
  icon: React.ReactNode;
  question: string;
  answer: string;
  tag: string;
}

const FAQS: FAQItem[] = [
  {
    id: "tsc-vs-vectis",
    icon: <Lightning size={16} className="text-amber-400" />,
    tag: "Architectural Differentiation",
    question: "Why can't large monorepos just rely on TypeScript Compiler (tsc) and unit tests?",
    answer:
      "Modern enterprise monorepos partition compilation per package to keep CI under 15 minutes. 'tsc' verifies lexical types within build boundaries, but cannot detect cross-package contract mutations or transitive downstream runtime failures. Unit tests rely on hardcoded fixtures and mocks that pass green even when production schemas diverge. Vectis crawls the entire repository dependency DAG and computes multi-hop blast radius across all services before merge."
  },
  {
    id: "zero-hallucination-speed",
    icon: <Cpu size={16} className="text-emerald-400" />,
    tag: "Deterministic Performance",
    question: "How does Vectis achieve 1.2ms latency with 0.0% hallucination?",
    answer:
      "Vectis does NOT use an LLM for contract drift detection. The core engine is built on deterministic Python-native AST parsing and NetworkX graph traversal algorithms. Risk scoring uses an exact mathematical formula: Impact = Depth^(-0.5) * Criticality * TrafficWeight. Because graph evaluation is purely algebraic and deterministic, execution finishes in 1.2ms with zero hallucination."
  },
  {
    id: "granite-safety",
    icon: <ShieldCheck size={16} className="text-emerald-400" />,
    tag: "IBM Granite 3.0 Engine",
    question: "How does IBM Granite 3.0 generate safe, zero-overhead compatibility shims?",
    answer:
      "When a breaking contract mutation is blocked, Vectis invokes IBM Granite 3.0 8B Instruct on watsonx.ai. Using formal ChatML prompt engineering, Granite synthesizes standard ES6 Proxy adapters implementing 5 runtime traps: get, set, ownKeys, getOwnPropertyDescriptor, and has. The synthesized shim transparently bridges old signatures to new contracts with zero external dependencies, allowing downstream consumers to migrate incrementally without downtime."
  },
  {
    id: "zero-code-egress",
    icon: <LockKey size={16} className="text-rose-400" />,
    tag: "Enterprise Privacy",
    question: "Does Vectis upload proprietary company code to external AI servers?",
    answer:
      "No. Vectis follows a strict Zero Code Egress architecture. AST parsing, dependency graph extraction, and risk scoring execute 100% locally inside your CI/CD runner. Only the minimal mutated symbol signature (e.g., 'User.id -> SessionUser.sub') is sent to IBM watsonx.ai for shim generation. Your source code, business logic, and repository tree never leave your enterprise perimeter."
  },
  {
    id: "github-integration",
    icon: <GitPullRequest size={16} className="text-zinc-300" />,
    tag: "CI/CD & Security",
    question: "How does Vectis integrate with GitHub Actions and Code Scanning?",
    answer:
      "Vectis provides native GitHub integration via the Checks API and Webhooks. Pull requests receive inline review annotations and branch protection blocks. Audit reports are exported as OASIS SARIF v2.1.0 and ingested directly into GitHub Security Code Scanning alerts. Once verified, Vectis issues an RFC 8785 canonical JSON Cryptographic Release Passport with HMAC-SHA256 attestation."
  }
];

export function FAQSection() {
  const [openId, setOpenId] = useState<string | null>("tsc-vs-vectis");

  const toggle = (id: string) => {
    setOpenId((prev) => (prev === id ? null : id));
  };

  return (
    <section id="faq" className="py-20 md:py-28 border-t border-white/[0.08] bg-[#08090a]">
      <div className="max-w-4xl mx-auto px-5 sm:px-8">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-[4px] border border-white/[0.08] bg-[#0c0d10] text-zinc-400 text-xs mb-3">
            <Question size={14} className="text-zinc-400" />
            <span className="font-medium">Frequently Asked Questions</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-bold tracking-tight text-white">
            Architecture, Verification & Privacy.
          </h2>
          <p className="mt-3 text-sm text-zinc-400 leading-relaxed">
            Everything enterprise engineering leads and hackathon judges need to know about deterministic release safety.
          </p>
        </div>

        {/* Accordion Container */}
        <div className="space-y-3">
          {FAQS.map((faq) => {
            const isOpen = openId === faq.id;
            return (
              <div
                key={faq.id}
                className="border border-white/[0.08] rounded-[4px] bg-[#0c0d10] transition-colors hover:border-white/[0.14] overflow-hidden"
              >
                <button
                  onClick={() => toggle(faq.id)}
                  className="w-full p-4 sm:p-5 text-left flex items-start justify-between gap-4 cursor-pointer focus:outline-none"
                  aria-expanded={isOpen}
                >
                  <div className="flex items-start gap-3.5">
                    <div className="w-7 h-7 rounded-[4px] bg-[#14151a] border border-white/[0.08] flex items-center justify-center shrink-0 mt-0.5">
                      {faq.icon}
                    </div>
                    <div>
                      <span className="text-[10px] uppercase tracking-wider text-zinc-500 font-semibold block mb-1">
                        {faq.tag}
                      </span>
                      <h3 className="text-sm sm:text-base font-semibold text-zinc-100 leading-snug">
                        {faq.question}
                      </h3>
                    </div>
                  </div>

                  <div className="shrink-0 pt-1 text-zinc-400">
                    <CaretDown
                      size={16}
                      className={`transition-transform duration-200 ${isOpen ? "rotate-180 text-white" : ""}`}
                    />
                  </div>
                </button>

                {isOpen && (
                  <div className="px-5 pb-5 pt-1 text-xs sm:text-sm text-zinc-400 leading-relaxed border-t border-white/[0.04]">
                    <div className="pl-10">{faq.answer}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
