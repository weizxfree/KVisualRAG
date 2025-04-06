import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: `${process.env.MINO_IMAGE_URL_PREFIX}`,
        //hostname: '192.168.1.5',
        port: '9110', // 如果使用的是特定端口
        pathname: '/ai-chat/**', // 允许所有路径
      },
    ], // 允许加载来自 minio 的图片
  },
};

export default nextConfig;
