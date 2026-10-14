import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const projectRoot = fileURLToPath(new URL(".", import.meta.url));

const nextConfig: NextConfig = {
  output: "export",
  poweredByHeader: false,
  agentRules: false,
  devIndicators: false,
  turbopack: { root: projectRoot },
};

export default nextConfig;
