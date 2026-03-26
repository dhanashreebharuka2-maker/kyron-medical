/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${api}/api/:path*`,
      },
      { source: "/health", destination: `${api}/health` },
    ];
  },
  // Polling avoids native file watchers exhausting FDs on macOS (EMFILE), which can
  // leave dev compilation incomplete and break /_next asset serving.
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
};

export default nextConfig;
