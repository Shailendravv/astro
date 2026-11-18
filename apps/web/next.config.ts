import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const nextConfig: NextConfig = {
  // Self-contained server output for the Docker image (apps/web/Dockerfile).
  output: "standalone",
  async redirects() {
    return [{ source: "/", destination: "/en", permanent: false }];
  },
};

export default withNextIntl(nextConfig);
