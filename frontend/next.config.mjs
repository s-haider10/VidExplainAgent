// frontend/next.config.mjs

/** @type {import('next').NextConfig} */
const nextConfig = {
  // F7.1: Set up a proxy to the backend API
  // This tells Next.js to forward any request starting with /api
  // to  FastAPI server running on http://localhost:8000
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
