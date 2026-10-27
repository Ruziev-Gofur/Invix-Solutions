// Адрес API внутри docker-сети. Rewrites вычисляются при сборке,
// поэтому в Dockerfile он передаётся как build-arg.
const API = process.env.API_INTERNAL_URL ?? "http://backend:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    if (process.env.DEMO_MODE === "true") return [];
    // Браузер и Mini App ходят только на один origin (Next.js),
    // /api/* и картинки проксируются на FastAPI.
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default nextConfig;
