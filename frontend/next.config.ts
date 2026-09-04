import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  poweredByHeader: false,

  // Playwright reaches the Dockerized Next dev server through the published
  // localhost/127.0.0.1 port. Next 16 blocks cross-origin dev assets unless
  // those hosts are explicitly allowed.
  allowedDevOrigins: [
    "127.0.0.1",
    "localhost",
  ],
};

export default nextConfig;
