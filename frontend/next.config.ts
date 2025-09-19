// frontend/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  // 念のため appDir を明示（Next 15 では既定で有効だが保険）
  experimental: {
    appDir: true,
  },
};

export default nextConfig;
