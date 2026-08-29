import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Session 7 (release readiness): standalone output — a self-contained
  // server.js plus only the node_modules deps actually traced as used,
  // built by docker/Dockerfile.prod. ../Dockerfile (the dev/CI image)
  // doesn't opt into this; it ships a full `npm install` tree and runs
  // `next start` via the Next.js CLI instead. This setting only changes
  // what `next build` additionally emits into `.next/standalone` — it
  // has no effect on `next dev` or `npm test`.
  output: "standalone",
};

export default nextConfig;
