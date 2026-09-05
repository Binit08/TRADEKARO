/**
 * Fix 1: Rewrites removed — replaced by explicit server-side proxy route handlers
 * that inject BACKEND_API_KEY. See /api/proxy/* routes.
 */
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Rewrites removed — Fix 1: API calls now go through /api/proxy/* route handlers
  // which inject the API key server-side. No backend secrets are exposed to the browser.
};

export default nextConfig;
