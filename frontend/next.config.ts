import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  transpilePackages: ["@phosphor-icons/react"],
};

export default nextConfig;
