"use client";

import React from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import { FileCode, ShieldWarning, ShieldCheck, WarningCircle, GitBranch } from "@phosphor-icons/react";

export interface BlastNodeData extends Record<string, unknown> {
  label: string;
  service?: string;
  criticality?: number;
  traffic?: number;
  state?: "default" | "source" | "impacted" | "healed";
  mutationsCount?: number;
}

export const BlastNode = React.memo(function BlastNode({ data, selected }: NodeProps) {
  const nodeData = data as unknown as BlastNodeData;
  const state = nodeData.state || "default";

  // Card appearance depending on state
  let borderStyle = "border-white/[0.08] bg-[#101114]";
  let dotColor = "bg-zinc-600";
  let statusText = "Stable";
  let statusTextColor = "text-zinc-500";
  let icon = <FileCode size={14} className="text-zinc-400" />;

  if (state === "source") {
    borderStyle = "border-rose-500/70 bg-[#181114] shadow-[0_0_16px_rgba(239,68,68,0.22)] hazard-glow";
    dotColor = "bg-rose-500 animate-pulse";
    statusText = "Breaking Source";
    statusTextColor = "text-rose-400 font-medium";
    icon = <ShieldWarning size={14} weight="bold" className="text-rose-400" />;
  } else if (state === "impacted") {
    borderStyle = "border-amber-500/50 bg-[#151210] shadow-[0_0_12px_rgba(245,158,11,0.12)]";
    dotColor = "bg-amber-400";
    statusText = "Downstream Hazard";
    statusTextColor = "text-amber-400 font-medium";
    icon = <WarningCircle size={14} weight="bold" className="text-amber-400" />;
  } else if (state === "healed") {
    borderStyle = "border-emerald-500/50 bg-[#0e1613] shadow-[0_0_12px_rgba(16,185,129,0.12)]";
    dotColor = "bg-emerald-400";
    statusText = "Compatibility Shim Active";
    statusTextColor = "text-emerald-400 font-medium";
    icon = <ShieldCheck size={14} weight="bold" className="text-emerald-400" />;
  }

  return (
    <div
      className={`rounded-[6px] border ${borderStyle} ${
        selected ? "ring-1 ring-white/20" : ""
      } p-3 min-w-[210px] text-left transition-colors duration-150 select-none`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-zinc-500 !border-0 !w-1.5 !h-1.5 !rounded-none"
      />

      {/* Top Header: Icon & File Label */}
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-1.5 truncate">
          {icon}
          <span className="text-xs text-zinc-200 font-semibold tracking-tight truncate">
            {nodeData.label}
          </span>
        </div>
      </div>

      {/* Service Subtitle */}
      {nodeData.service && (
        <div className="text-[11px] text-zinc-400 mb-2 truncate">
          {nodeData.service}
        </div>
      )}

      {/* Status indicator row (Dot + Text, no badge, no pill) */}
      <div className="flex items-center justify-between pt-1.5 border-t border-white/[0.04] text-[11px]">
        <div className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
          <span className={`text-[11px] ${statusTextColor}`}>{statusText}</span>
        </div>

        {nodeData.criticality !== undefined && (
          <span className="text-zinc-500 text-[11px]">
            Crit: {nodeData.criticality}
          </span>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-zinc-500 !border-0 !w-1.5 !h-1.5 !rounded-none"
      />
    </div>
  );
});
