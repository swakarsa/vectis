"use client";

import React, { useState } from "react";
import { GitBranch, GitPullRequest, ShieldCheck, CaretDown, Check, Globe } from "@phosphor-icons/react";
import { MonorepoOption } from "@/lib/github";

interface RepoSelectorProps {
  repos: MonorepoOption[];
  selectedRepo: MonorepoOption;
  onSelectRepo: (repo: MonorepoOption) => void;
  prNumber: number;
}

export const RepoSelector: React.FC<RepoSelectorProps> = ({
  repos,
  selectedRepo,
  onSelectRepo,
  prNumber,
}) => {
  const [open, setOpen] = useState(false);
  const [customInput, setCustomInput] = useState("");

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customInput.trim()) return;
    const parts = customInput.trim().split("/");
    const repoName = parts.length > 1 ? parts[1] : customInput.trim();
    const newRepo: MonorepoOption = {
      id: customInput.trim(),
      name: repoName,
      fullName: customInput.trim(),
      isBenchmark: false,
      branch: "main",
      description: "Custom connected repository",
    };
    onSelectRepo(newRepo);
    setOpen(false);
    setCustomInput("");
  };

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 bg-[#101114] border border-white/10 hover:border-white/20 rounded-[4px] transition-colors text-xs text-zinc-200"
      >
        <GitPullRequest size={14} className="text-zinc-400" />
        <span className="font-medium text-white">{selectedRepo.fullName}</span>
        <span className="px-1.5 py-0.5 text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-[2px]">
          PR #{prNumber}
        </span>
        <CaretDown size={12} className="text-zinc-500 ml-1" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute left-0 mt-1.5 w-80 bg-[#0d0e12] border border-white/10 rounded-[4px] shadow-2xl z-50 p-2 space-y-1">
            <div className="px-2 py-1 text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
              Select Monorepo / Pull Request
            </div>

            <div className="max-h-56 overflow-y-auto space-y-1">
              {repos.map((r) => {
                const isSelected = r.id === selectedRepo.id;
                return (
                  <button
                    key={r.id}
                    onClick={() => {
                      onSelectRepo(r);
                      setOpen(false);
                    }}
                    className={`w-full text-left px-2.5 py-2 rounded-[4px] transition-colors flex items-start justify-between ${
                      isSelected
                        ? "bg-white/10 text-white"
                        : "text-zinc-300 hover:bg-white/5 hover:text-white"
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-1.5 text-xs font-medium">
                        {r.isBenchmark ? (
                          <ShieldCheck size={13} className="text-blue-400" />
                        ) : (
                          <GitBranch size={13} className="text-zinc-400" />
                        )}
                        <span>{r.fullName}</span>
                      </div>
                      <div className="text-[10px] text-zinc-500 mt-0.5">
                        {r.description} · branch: {r.branch}
                      </div>
                    </div>
                    {isSelected && <Check size={14} className="text-emerald-400 mt-1 shrink-0" />}
                  </button>
                );
              })}
            </div>

            <div className="border-t border-white/10 pt-2 mt-1">
              <form onSubmit={handleCustomSubmit} className="flex gap-1.5">
                <input
                  type="text"
                  placeholder="owner/repo (e.g. org/payments)"
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  className="flex-1 bg-[#16171b] border border-white/10 rounded-[4px] px-2 py-1 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500/50"
                />
                <button
                  type="submit"
                  className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-[4px] font-medium transition-colors"
                >
                  Load
                </button>
              </form>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
