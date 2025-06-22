// next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,  // ✅ Must be true
  },
};
module.exports = {
  images: {
    domains: ['upload.wikimedia.org'],
  },
};
module.exports = nextConfig;
