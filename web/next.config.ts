import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'tw-03.access.glows.ai',
        port: '24131', // 如果使用的是特定端口
        pathname: '/ai-chat/**', // 允许所有路径
      },
      {
        protocol: 'http',
        hostname: '127.0.0.1',
        port: '9110',
        pathname: '/ai-chat/**',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '9110',
        pathname: '/ai-chat/**',
      },
    ], // 允许加载来自 minio 的图片
  },
};

export default nextConfig;