const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL;

if (!rawApiBaseUrl) {
  throw new Error("Missing VITE_API_BASE_URL in apps/web/.env");
}

export const env = {
  apiBaseUrl: rawApiBaseUrl.replace(/\/+$/, ""),
};
