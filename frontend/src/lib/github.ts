/**
 * GitHub API & Defender client helpers for Vectis Cockpit
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface GitHubUser {
  id: number;
  login: string;
  name: string;
  avatar_url: string;
  html_url: string;
}

export interface MonorepoOption {
  id: string;
  name: string;
  fullName: string;
  isBenchmark: boolean;
  branch: string;
  description: string;
}

export const BENCHMARK_REPO: MonorepoOption = {
  id: "benchmark-pr482",
  name: "FinTech Core Monorepo",
  fullName: "swakarsa/fintech-monorepo",
  isBenchmark: true,
  branch: "feature/refactor-auth",
  description: "PR #482 OIDC 2.0 contract drift benchmark",
};

export async function fetchUserRepos(token?: string): Promise<MonorepoOption[]> {
  try {
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE}/api/user/repos`, { headers });
    if (res.ok) {
      const data = await res.json();
      return [
        BENCHMARK_REPO,
        ...data.map((r: any) => ({
          id: r.full_name || r.name,
          name: r.name,
          fullName: r.full_name || r.name,
          isBenchmark: false,
          branch: r.default_branch || "main",
          description: r.private ? "Private repository" : "Public repository",
        })),
      ];
    }
  } catch {
    // Return benchmark fallback
  }
  return [BENCHMARK_REPO];
}

export async function pushAutoHealFix(params: {
  owner: string;
  repo: string;
  pullNumber: number;
  branch: string;
  headSha: string;
  token?: string;
}) {
  const res = await fetch(`${API_BASE}/api/pr/push-fix`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      owner: params.owner,
      repo: params.repo,
      pull_number: params.pullNumber,
      branch: params.branch,
      head_sha: params.headSha,
      token: params.token,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to push fix to GitHub PR");
  }
  return res.json();
}
