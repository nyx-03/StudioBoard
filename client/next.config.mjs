/** @type {import('next').NextConfig} */
const nextConfig = {
  reactCompiler: true,

  async rewrites() {
    return [
      {
        source: '/api/:path*',
        // Force un slash final côté backend (Django APPEND_SLASH) pour éviter les 301
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
