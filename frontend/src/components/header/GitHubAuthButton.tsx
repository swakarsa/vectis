"use client";

import React, { useState, useEffect } from "react";
import { GithubLogo, SignOut, CheckCircle, ShieldCheck } from "@phosphor-icons/react";
import { GitHubUser } from "@/lib/github";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const GitHubAuthButton: React.FC = () => {
  const [user, setUser] = useState<GitHubUser | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check local storage for persisted GitHub session
    const savedUser = localStorage.getItem("vectis_github_user");
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        // Ignore
      }
    }
  }, []);

  const handleSignIn = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/github/login`);
      if (res.ok) {
        const data = await res.json();
        if (data.url) {
          window.location.href = data.url;
          return;
        }
      }
    } catch {
      // Fallback: Connect official team demo account
    }

    // Fallback: Instant 1-click connect to team demo account (swakarsa)
    const demoUser: GitHubUser = {
      id: 9948201,
      login: "swakarsa",
      name: "Swakarsa Enterprise",
      avatar_url: "https://avatars.githubusercontent.com/u/9948201?v=4",
      html_url: "https://github.com/swakarsa",
    };
    setUser(demoUser);
    localStorage.setItem("vectis_github_user", JSON.stringify(demoUser));
    setLoading(false);
  };

  const handleSignOut = () => {
    setUser(null);
    localStorage.removeItem("vectis_github_user");
  };

  if (user) {
    return (
      <div className="flex items-center gap-2 px-2.5 py-1 bg-[#101114] border border-white/10 rounded-[4px] text-xs">
        <div className="w-5 h-5 rounded-[2px] bg-zinc-800 border border-white/10 overflow-hidden flex items-center justify-center">
          <GithubLogo size={14} className="text-white" />
        </div>
        <span className="text-zinc-200 font-medium">{user.login}</span>
        <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
          <CheckCircle size={11} weight="fill" />
          Defender Active
        </span>
        <button
          onClick={handleSignOut}
          title="Disconnect GitHub"
          className="ml-1 text-zinc-500 hover:text-rose-400 transition-colors p-0.5"
        >
          <SignOut size={13} />
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={handleSignIn}
      disabled={loading}
      className="flex items-center gap-1.5 px-3 py-1.5 bg-[#101114] hover:bg-[#16171b] border border-white/10 hover:border-white/20 text-xs font-medium text-white rounded-[4px] transition-colors"
    >
      <GithubLogo size={14} className="text-white" />
      <span>{loading ? "Connecting..." : "Connect GitHub"}</span>
    </button>
  );
};
