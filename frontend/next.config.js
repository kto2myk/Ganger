/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: true
  },
  images: {
    remotePatterns: [
      // 画像配信ドメインを後で追加
      { protocol: 'https', hostname: '**' }
    ]
  }
};

module.exports = nextConfig;
