import { LogIn, MessageCircle } from "lucide-react";
import impactoLogo from "../../assets/impacto-logo.png";
import { SENTINELA_LOGIN_URL, WHATSAPP_URL } from "../../constants";

const links = [
  ["Início", "#inicio"],
  ["Soluções", "#solucoes"],
  ["SENTINELA", "#sentinela"],
  ["Como Funciona", "#como-funciona"],
  ["Contato", "#contato"],
];

export default function Header() {
  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-white/10 bg-slate-950/88 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <a className="flex items-center gap-3" href="#inicio" aria-label="IMPACTO">
          <img className="h-11 w-32 rounded bg-white object-contain p-1.5 sm:w-40" src={impactoLogo} alt="IMPACTO" />
        </a>

        <nav className="hidden items-center gap-6 text-sm font-medium text-slate-200 lg:flex">
          {links.map(([label, href]) => (
            <a className="transition hover:text-emerald-300" href={href} key={href}>
              {label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <a className="inline-flex items-center gap-2 rounded-md border border-white/15 px-4 py-2 text-sm font-semibold text-white transition hover:border-emerald-300 hover:text-emerald-200" href={SENTINELA_LOGIN_URL}>
            <LogIn size={16} /> Login SENTINELA
          </a>
          <a className="inline-flex items-center gap-2 rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-950/25 transition hover:-translate-y-0.5 hover:bg-emerald-400" href={WHATSAPP_URL} rel="noreferrer" target="_blank">
            <MessageCircle size={16} /> Falar no WhatsApp
          </a>
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <a className="inline-flex items-center justify-center rounded-md border border-white/15 p-2 text-white" href={SENTINELA_LOGIN_URL} aria-label="Login SENTINELA">
            <LogIn size={19} />
          </a>
          <a className="inline-flex items-center justify-center rounded-md bg-emerald-500 p-2 text-white" href={WHATSAPP_URL} rel="noreferrer" target="_blank" aria-label="Falar no WhatsApp">
            <MessageCircle size={19} />
          </a>
        </div>
      </div>
      <nav className="flex gap-4 overflow-x-auto px-4 pb-3 text-xs font-semibold text-slate-200 sm:px-6 lg:hidden">
        {links.map(([label, href]) => (
          <a className="shrink-0 transition hover:text-emerald-300" href={href} key={href}>
            {label}
          </a>
        ))}
      </nav>
    </header>
  );
}
