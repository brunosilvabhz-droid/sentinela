import impactoLogo from "./assets/impacto-logo-dark.png";
import impactoHeaderLogo from "./assets/impacto-logo-header.png";
import { SENTINELA_LOGIN_URL, WHATSAPP_URL, COMPANY_DOMAIN } from "./constants";

export const LANDING_CONTENT_KEY = "impacto_landing_content_v1";

export const DEFAULT_LANDING_CONTENT = {
  companyName: "IMPACTO",
  domain: COMPANY_DOMAIN,
  logoUrl: impactoLogo,
  headerLogoUrl: impactoHeaderLogo,
  heroImageUrl: impactoLogo,
  eyebrow: "Observabilidade de processos de negócio",
  heroTitle: "Seus processos continuam funcionando quando ninguém está olhando?",
  heroSubtitle:
    "A IMPACTO automatiza tarefas repetitivas, integra sistemas e monitora processos críticos para detectar problemas antes que eles gerem prejuízo.",
  whatsappUrl: WHATSAPP_URL,
  sentinelaLoginUrl: SENTINELA_LOGIN_URL,
  metrics: [
    { label: "Processos monitorados", value: "128" },
    { label: "Alertas em tempo real", value: "24/7" },
    { label: "Integrações ativas", value: "36" },
    { label: "Economia estimada", value: "18h/sem" },
  ],
};

export function loadLandingContent() {
  try {
    const stored = JSON.parse(localStorage.getItem(LANDING_CONTENT_KEY) || "{}");
    return {
      ...DEFAULT_LANDING_CONTENT,
      ...stored,
      metrics: stored.metrics?.length ? stored.metrics : DEFAULT_LANDING_CONTENT.metrics,
    };
  } catch {
    return DEFAULT_LANDING_CONTENT;
  }
}

export function saveLandingContent(content) {
  localStorage.setItem(LANDING_CONTENT_KEY, JSON.stringify(content));
}

export function resetLandingContent() {
  localStorage.removeItem(LANDING_CONTENT_KEY);
}
