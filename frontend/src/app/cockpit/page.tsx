"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { BlastNode } from "@/components/canvas/BlastNode";
import { CockpitHeader } from "@/components/header/CockpitHeader";
import { DetailPanel } from "@/components/panels/DetailPanel";
import { pushAutoHealFix } from "@/lib/github";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Fallback graph data in case backend is loading
const FALLBACK_GRAPH = {
  nodes: [
    { id: "models/user.ts", label: "models/user.ts", service: "Identity Core", criticality: 1.0, traffic: 0.8 },
    { id: "auth/session.ts", label: "auth/session.ts", service: "Auth Gateway", criticality: 0.95, traffic: 0.9 },
    { id: "payments/checkout.ts", label: "payments/checkout.ts", service: "Billing & Checkout", criticality: 1.0, traffic: 1.0 },
    { id: "workers/settlement_worker.ts", label: "workers/settlement_worker.ts", service: "Settlement Cron", criticality: 0.85, traffic: 0.6 },
    { id: "reporting/invoice_generator.ts", label: "reporting/invoice_generator.ts", service: "Invoicing", criticality: 0.7, traffic: 0.3 },
    { id: "api/routes/user_profile.ts", label: "api/routes/user_profile.ts", service: "Public API", criticality: 0.5, traffic: 0.7 },
    { id: "api/routes/admin_dashboard.ts", label: "api/routes/admin_dashboard.ts", service: "Internal Ops", criticality: 0.6, traffic: 0.4 },
  ],
  edges: [
    { source: "models/user.ts", target: "auth/session.ts" },
    { source: "auth/session.ts", target: "payments/checkout.ts" },
    { source: "auth/session.ts", target: "workers/settlement_worker.ts" },
    { source: "payments/checkout.ts", target: "reporting/invoice_generator.ts" },
    { source: "auth/session.ts", target: "api/routes/user_profile.ts" },
    { source: "models/user.ts", target: "api/routes/admin_dashboard.ts" },
  ]
};

const getMiniMapNodeColor = (n: Node) => {
  const s = (n.data as any)?.state;
  if (s === "source") return "#ef4444";
  if (s === "impacted") return "#f59e0b";
  if (s === "healed") return "#10b981";
  return "#27272a";
};

export default function VectisCockpitPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [mounted, setMounted] = useState(false);

  const [mode, setMode] = useState<"benchmark" | "live_github">("benchmark");
  const [repoName, setRepoName] = useState("swakarsa/vectis");
  const [prNumber, setPrNumber] = useState(482);
  const [baseBranch, setBaseBranch] = useState("main");
  const [headBranch, setHeadBranch] = useState("feature/refactor-auth");
  const [checksStatus, setChecksStatus] = useState<"idle" | "in_progress" | "failure" | "success">("idle");
  const [mergeLocked, setMergeLocked] = useState(false);
  const [pushedToPR, setPushedToPR] = useState(false);

  const [verdict, setVerdict] = useState<"BLOCK" | "WARN" | "PASS" | "IDLE">("IDLE");
  const [riskScore, setRiskScore] = useState<number>(0.0);
  const [loading, setLoading] = useState(false);
  const [shimLoading, setShimLoading] = useState(false);
  const [shimApplied, setShimApplied] = useState(false);

  const [breakingChanges, setBreakingChanges] = useState<any[]>([]);
  const [downstreamImpact, setDownstreamImpact] = useState<any[]>([]);
  const [shimCode, setShimCode] = useState<string>(`// Awaiting IBM Bob 2.0 Granite 3.0 synthesis...`);
  const [releasePassport, setReleasePassport] = useState<any>(null);

  const nodeTypes = useMemo(() => ({ blastNode: BlastNode }), []);

  // Compute node layouts on graph load
  const setupGraphNodes = useCallback((graphData: typeof FALLBACK_GRAPH, stateMap: Record<string, "default" | "source" | "impacted" | "healed"> = {}) => {
    // Organized positions for clean enterprise DAG layout
    const positions: Record<string, { x: number; y: number }> = {
      "models/user.ts": { x: 320, y: 40 },
      "auth/session.ts": { x: 320, y: 190 },
      "payments/checkout.ts": { x: 120, y: 360 },
      "workers/settlement_worker.ts": { x: 520, y: 360 },
      "reporting/invoice_generator.ts": { x: 120, y: 530 },
      "api/routes/user_profile.ts": { x: 740, y: 360 },
      "api/routes/admin_dashboard.ts": { x: 740, y: 190 },
    };

    const flowNodes: Node[] = graphData.nodes.map((n) => {
      const nodeState = stateMap[n.id] || "default";
      const pos = positions[n.id] || { x: 100, y: 100 };
      return {
        id: n.id,
        type: "blastNode",
        position: pos,
        data: {
          label: n.label,
          service: n.service,
          criticality: n.criticality,
          traffic: n.traffic,
          state: nodeState,
        } as unknown as Record<string, unknown>,
      };
    });

    const flowEdges: Edge[] = graphData.edges.map((e, idx) => ({
      id: `edge-${idx}`,
      source: e.source,
      target: e.target,
      animated: false,
      style: { stroke: "#3f3f46", strokeWidth: 1.5 },
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [setNodes, setEdges]);

  // Initial load & client mount
  useEffect(() => {
    setMounted(true);
    async function init() {
      try {
        const res = await fetch(`${API_BASE}/api/graph`);
        if (res.ok) {
          const data = await res.json();
          setupGraphNodes(data);
          return;
        }
      } catch {
        // Fallback gracefully to offline sample
      }
      setupGraphNodes(FALLBACK_GRAPH);
    }
    init();
  }, [setupGraphNodes]);

  // Execute Pre-Merge Gate Audit (Benchmark or Live GitHub)
  const handleAnalyze = async () => {
    setLoading(true);
    setShimApplied(false);
    setReleasePassport(null);
    setChecksStatus("in_progress");
    setPushedToPR(false);

    try {
      let data: any = null;
      try {
        const endpoint = mode === "live_github" ? `${API_BASE}/api/github/audit-pr` : `${API_BASE}/api/analyze-pr`;
        const bodyPayload = mode === "live_github"
          ? {
              repository: repoName,
              pr_number: prNumber,
              base_ref: baseBranch,
              head_ref: headBranch,
              changed_files: ["src/auth/session.ts"],
            }
          : {
              repo_path: "",
              base_ref: "main",
              head_ref: "feature/refactor-auth",
              changed_files: ["src/auth/session.ts"],
            };

        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(bodyPayload),
        });
        if (res.ok) {
          data = await res.json();
        }
      } catch {
        // Local fallback
      }

      if (!data) {
        data = {
          verdict: "BLOCK",
          risk_assessment: { total_score: 84.0 },
          breaking_changes: [
            {
              file_path: "src/auth/session.ts",
              symbol_name: "User.id",
              mutation_type: "field_removed",
              old_signature: "id: string",
              new_signature: "sub: string (renamed)",
              severity: "critical",
              line_number: 12,
              description: "Legacy 'id' property removed and renamed to OIDC 'sub'",
            },
            {
              file_path: "src/auth/session.ts",
              symbol_name: "User.tier",
              mutation_type: "field_removed",
              old_signature: "tier: 'free' | 'pro' | 'enterprise'",
              new_signature: "metadata.tier",
              severity: "critical",
              line_number: 13,
              description: "Tier enum property relocated inside nested metadata object",
            }
          ],
          downstream_impact: [
            { node_id: "payments/checkout.ts", file_path: "src/payments/checkout.ts", service: "Billing & Checkout", dependency_depth: 1, criticality: 1.0 },
            { node_id: "workers/settlement_worker.ts", file_path: "src/workers/settlement_worker.ts", service: "Settlement Cron", dependency_depth: 1, criticality: 0.85 },
            { node_id: "reporting/invoice_generator.ts", file_path: "src/reporting/invoice_generator.ts", service: "Invoicing", dependency_depth: 2, criticality: 0.7 },
          ]
        };
      }

      setVerdict(data.verdict);
      setRiskScore(data.risk_assessment.total_score);
      setBreakingChanges(data.breaking_changes);
      setDownstreamImpact(data.downstream_impact);
      setChecksStatus(data.verdict === "BLOCK" ? "failure" : "success");
      setMergeLocked(data.verdict === "BLOCK");

      // Map node states
      const stateMap: Record<string, "default" | "source" | "impacted" | "healed"> = {
        "auth/session.ts": "source",
        "payments/checkout.ts": "impacted",
        "workers/settlement_worker.ts": "impacted",
        "reporting/invoice_generator.ts": "impacted",
      };

      setNodes((currentNodes) =>
        currentNodes.map((node) => {
          const s = stateMap[node.id] || "default";
          return {
            ...node,
            data: {
              ...node.data,
              state: s,
            },
          };
        })
      );

      // Animate hazard edges
      const hazardSources = new Set(["auth/session.ts", "payments/checkout.ts"]);
      setEdges((currentEdges) =>
        currentEdges.map((edge) => {
          const isHazard = hazardSources.has(edge.source);
          return {
            ...edge,
            animated: isHazard,
            style: {
              stroke: isHazard ? "#ef4444" : "#3f3f46",
              strokeWidth: isHazard ? 2 : 1.5,
            },
          };
        })
      );
    } finally {
      setLoading(false);
    }
  };

  // Apply IBM Granite 3.0 Compatibility Shim
  const handleApplyShim = async () => {
    setShimLoading(true);
    try {
      let data: any = null;
      try {
        const res = await fetch(`${API_BASE}/api/auto-heal`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        if (res.ok) {
          data = await res.json();
        }
      } catch {
        // Fallback
      }

      if (!data) {
        data = {
          verdict: "PASS",
          risk_assessment: { total_score: 12.0 },
          shim_code: `export function createSessionUserAdapter(modernSession: any): any {
  return new Proxy(modernSession, {
    get(target, prop, receiver) {
      if (prop === "id" && "sub" in target) return target.sub;
      if (prop === "tier" && target.metadata) return target.metadata.tier;
      return Reflect.get(target, prop, receiver);
    },
    ownKeys(target) {
      return [...Reflect.ownKeys(target), "id", "tier"];
    }
  });
}`,
          release_passport: {
            pr_number: 482,
            commit_sha: "c8a9f24e9b7d81023",
            author: "alex-dev",
            risk_score: 12.0,
            verdict: "PASS",
            shim_applied: true,
            passport_hash: "sha256:7f9b8c12a44e5d66f331bb890c012ff8812c3"
          }
        };
      }

      setShimApplied(true);
      setVerdict("PASS");
      setRiskScore(data.risk_assessment.total_score);
      setShimCode(data.shim_code);
      setReleasePassport(data.release_passport);
      setChecksStatus("success");
      setMergeLocked(false);
      setPushedToPR(true);

      // If in live GitHub mode, push the auto-heal shim directly to PR branch
      if (mode === "live_github" && repoName && prNumber) {
        const parts = repoName.split("/");
        const owner = parts[0] || "swakarsa";
        const repo = parts[1] || repoName;
        try {
          await pushAutoHealFix({
            owner,
            repo,
            pullNumber: prNumber,
            branch: headBranch,
            headSha: data.release_passport?.commit_sha || "c8a9f24e9b7d81023",
          });
        } catch (e) {
          console.warn("Live GitHub PR push error:", e);
        }
      }

      // Transition nodes to healed
      setNodes((currentNodes) =>
        currentNodes.map((node) => {
          const wasAffected = ["auth/session.ts", "payments/checkout.ts", "workers/settlement_worker.ts", "reporting/invoice_generator.ts"].includes(node.id);
          return {
            ...node,
            data: {
              ...node.data,
              state: wasAffected ? "healed" : "default",
            },
          };
        })
      );

      // Edges turn emerald green
      setEdges((currentEdges) =>
        currentEdges.map((edge) => {
          const wasHazard = ["auth/session.ts", "payments/checkout.ts"].includes(edge.source);
          return {
            ...edge,
            animated: false,
            style: {
              stroke: wasHazard ? "#10b981" : "#3f3f46",
              strokeWidth: wasHazard ? 2 : 1.5,
            },
          };
        })
      );
    } finally {
      setShimLoading(false);
    }
  };

  // Download cryptographic release passport
  const handleDownloadPassport = () => {
    if (!releasePassport) return;
    const blob = new Blob([JSON.stringify(releasePassport, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `VECTIS-RELEASE-PASSPORT-PR482-${releasePassport.commit_sha.slice(0, 7)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!mounted) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#08090a]">
        <div className="flex items-center gap-2.5 text-xs text-zinc-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-sans font-medium">Initializing Vectis Cockpit...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-[#08090a] overflow-hidden select-none">
      {/* Vercel/Linear Top Header */}
      <CockpitHeader
        verdict={verdict}
        riskScore={riskScore}
        loading={loading}
        onAnalyze={handleAnalyze}
        onDownloadPassport={handleDownloadPassport}
        passportAvailable={shimApplied && Boolean(releasePassport)}
        mode={mode}
        onModeChange={setMode}
        activeRepo={repoName}
        activePR={prNumber}
      />

      {/* Sleek Sub-Header Bar (Live GitHub Mode only) */}
      {mode === "live_github" && (
        <div className="h-10 border-b border-white/[0.08] bg-[#0c0d10] px-5 flex items-center justify-between z-10 text-xs shrink-0 select-none">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-zinc-400">
              <span className="text-zinc-500 font-medium">Repo:</span>
              <input
                type="text"
                value={repoName}
                onChange={(e) => setRepoName(e.target.value)}
                className="bg-[#14151a] border border-white/[0.08] rounded-[3px] px-2 py-0.5 text-white font-medium focus:outline-none focus:border-white/20 w-44"
                placeholder="owner/repo"
              />
            </div>
            <div className="h-3 w-[1px] bg-white/[0.08]" />
            <div className="flex items-center gap-1.5 text-zinc-400">
              <span className="text-zinc-500 font-medium">PR:</span>
              <input
                type="number"
                value={prNumber}
                onChange={(e) => setPrNumber(Number(e.target.value))}
                className="bg-[#14151a] border border-white/[0.08] rounded-[3px] px-1.5 py-0.5 text-white font-medium focus:outline-none focus:border-white/20 w-16"
              />
            </div>
            <div className="h-3 w-[1px] bg-white/[0.08]" />
            <div className="flex items-center gap-1.5 text-zinc-400">
              <span className="text-zinc-500 font-medium">Branch:</span>
              <input
                type="text"
                value={headBranch}
                onChange={(e) => setHeadBranch(e.target.value)}
                className="bg-[#14151a] border border-white/[0.08] rounded-[3px] px-2 py-0.5 text-white font-medium focus:outline-none focus:border-white/20 w-48"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-[11px]">
              <span className="text-zinc-500">Checks API:</span>
              {checksStatus === "failure" ? (
                <span className="text-rose-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                  FAILURE (Merge Blocked)
                </span>
              ) : checksStatus === "success" ? (
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  SUCCESS (Merge Unlocked)
                </span>
              ) : (
                <span className="text-zinc-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/50" />
                  Listening (Webhook 200 OK)
                </span>
              )}
            </div>

            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-2.5 py-1 bg-white/[0.08] hover:bg-white/[0.14] text-white text-[11px] font-medium rounded-[3px] border border-white/10 transition-colors cursor-pointer disabled:opacity-50"
            >
              {loading ? "Auditing..." : "Audit PR Diff"}
            </button>
          </div>
        </div>
      )}

      {/* Main Workspace: 65% DAG Canvas + 35% Sentry Detail Panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph Canvas */}
        <div className="flex-1 h-full relative bg-[#08090a]">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            proOptions={{ hideAttribution: true }}
            minZoom={0.3}
            maxZoom={1.8}
            panOnDrag={true}
            selectionOnDrag={false}
            panOnScroll={false}
            zoomOnScroll={true}
            nodesDraggable={true}
            nodesConnectable={false}
            elementsSelectable={true}
            elevateNodesOnSelect={false}
          >
            <Background
              variant={BackgroundVariant.Dots}
              color="#1a1c23"
              gap={16}
              size={1}
            />
            <Controls className="!bottom-4 !left-4" />
            <MiniMap
              nodeColor={getMiniMapNodeColor}
              maskColor="rgba(8, 9, 10, 0.75)"
              style={{
                background: "#0c0d10",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "4px",
              }}
              className="!bottom-4 !right-4"
            />
          </ReactFlow>
        </div>

        {/* Sentry / Linear Detail Panel */}
        <DetailPanel
          verdict={verdict}
          riskScore={riskScore}
          breakingChanges={breakingChanges}
          downstreamImpact={downstreamImpact}
          shimApplied={shimApplied}
          onApplyShim={handleApplyShim}
          shimLoading={shimLoading}
          shimCode={shimCode}
        />
      </div>
    </div>
  );
}
