import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Optimize images
  images: {
    formats: ["image/avif", "image/webp"],
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },

  // Production optimizations
  poweredByHeader: false,

  // Environment variables exposed to client
  env: {
    ARCHITECT_AGENT_ID: process.env.ARCHITECT_AGENT_ID,
    CRAFTER_AGENT_ID: process.env.CRAFTER_AGENT_ID,
    LOADER_AGENT_ID: process.env.LOADER_AGENT_ID,
    OPTIONS_AGENT_ID: process.env.OPTIONS_AGENT_ID,
    SUGGEST_AGENT_ID: process.env.SUGGEST_AGENT_ID,
    REPLY_SUGGESTER_AGENT_ID: process.env.REPLY_SUGGESTER_AGENT_ID,
    IDEA_SUGGESTER_AGENT_ID: process.env.IDEA_SUGGESTER_AGENT_ID,
    README_BUILDER_AGENT_ID: process.env.README_BUILDER_AGENT_ID,
  },

  // Headers for security
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "origin-when-cross-origin",
          },
        ],
      },
    ];
  },

  // Redirects (if needed)
  async redirects() {
    return [];
  },
};

export default nextConfig;
