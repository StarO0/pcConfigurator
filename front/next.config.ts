import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  compress: true,
  serverExternalPackages: ["jspdf", "canvg", "html2canvas", "core-js"],
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async rewrites() {
    const backend = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000/api/v1";
    return [
      {
        source: "/api-backend/:path*",
        destination: `${backend}/:path*`,
      },
    ];
  },
};

export default nextConfig;
