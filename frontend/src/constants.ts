export const WHATSAPP_URL =
  "https://wa.me/553191275790?text=Ol%C3%A1,%20quero%20saber%20mais%20sobre%20as%20solu%C3%A7%C3%B5es%20da%20Impacto";

export const SENTINELA_LOGIN_URL =
  import.meta.env.VITE_SENTINELA_LOGIN_URL || "https://app.impactocg.com/app";

export const COMPANY_DOMAIN = "impactocg.com";

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const DEFAULT_API_FALLBACK_URL = import.meta.env.DEV ? "https://sentinela-api-ef0m.onrender.com/api/v1" : "";

export const API_FALLBACK_URLS = [
  API_URL,
  import.meta.env.VITE_API_FALLBACK_URL || DEFAULT_API_FALLBACK_URL,
].filter((url, index, urls) => url && urls.indexOf(url) === index);
