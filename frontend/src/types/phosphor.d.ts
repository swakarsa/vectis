import React from "react";

declare module "@phosphor-icons/react" {
  export interface IconProps extends React.SVGAttributes<SVGElement> {
    size?: number | string;
    color?: string;
    weight?: "thin" | "light" | "regular" | "bold" | "fill" | "duotone";
    mirrored?: boolean;
    className?: string;
  }

  export type Icon = React.ForwardRefExoticComponent<
    IconProps & React.RefAttributes<SVGSVGElement>
  >;

  export const ShieldCheck: Icon;
  export const ShieldWarning: Icon;
  export const WarningCircle: Icon;
  export const Sparkle: Icon;
  export const Scales: Icon;
  export const TreeStructure: Icon;
  export const FileCode: Icon;
  export const GitPullRequest: Icon;
  export const GitBranch: Icon;
  export const GitMerge: Icon;
  export const Terminal: Icon;
  export const TerminalWindow: Icon;
  export const ArrowsClockwise: Icon;
  export const DownloadSimple: Icon;
  export const Cpu: Icon;
  export const Check: Icon;
  export const CheckCircle: Icon;
  export const XCircle: Icon;
  export const ArrowRight: Icon;
  export const ArrowLeft: Icon;
  export const ArrowUpRight: Icon;
  export const CaretRight: Icon;
  export const Copy: Icon;
  export const Lightning: Icon;
  export const LockKey: Icon;
  export const ShareNetwork: Icon;
  export const Activity: Icon;
  export const Clock: Icon;
  export const Bug: Icon;
  export const Database: Icon;
  export const Code: Icon;
  export const Browsers: Icon;
  export const Warning: Icon;
}
