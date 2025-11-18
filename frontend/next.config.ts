import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Disable dev indicator in development
  devIndicators: {
    buildActivity: false,
    buildActivityPosition: 'bottom-right',
  },
};

export default nextConfig;
