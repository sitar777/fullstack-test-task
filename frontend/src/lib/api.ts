const apiBase = process.env.NEXT_PUBLIC_API_URL;

if (!apiBase) {
  throw new Error("NEXT_PUBLIC_API_URL is not configured");
}

export const API_BASE = apiBase.replace(/\/$/, "");
