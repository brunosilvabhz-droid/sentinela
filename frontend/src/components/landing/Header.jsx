import { LogIn, MessageCircle } from "lucide-react";

const links = [
  ["Início", "#inicio"],
  ["Soluções", "#solucoes"],
  ["SENTINELA", "#sentinela"],
  ["Como Funciona", "#como-funciona"],
  ["Contato", "#contato"],
];

export default function Header({ content }) {
  return (
    <header className="impacto-header fixed inset-x-0 top-0 z-40 border-b border-white/10 bg-slate-950/94 shadow-2xl shadow-slate-950/20 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-5 px-4 py-3 sm:px-6 lg:px-8">
        <a className="flex min-w-0 items-center gap-3" href="#inicio" aria-label={content.companyName}>
          <span className="flex h-14 w-40 items-center justify-center overflow-hidden rounded-md border border-white/10 bg-slate-950/70 shadow-lg shadow-black/20 ring-1 ring-emerald-300/10 lg:w-48">
            <img className="h-full w-full object-cover object-center" src={content.headerLogoUrl || content.logoUrl} alt={content.companyName} />
          </span>
        </a>

        <nav className="impacto-desktop-nav min-w-0 items-center justify-center gap-5 text-sm font-semibold text-slate-200 xl:gap-7">
          {links.map(([label, href]) => (
            <a className="whitespace-nowrap transition hover:text-emerald-300" href={href} key={href}>
              {label}
            </a>
          ))}
        </nav>

        <div className="impacto-desktop-actions items-center justify-end gap-2 xl:gap-3">
          <a className="inline-flex items-center gap-2 rounded-md border border-white/15 px-3 py-2 text-sm font-semibold text-white transition hover:border-emerald-300 hover:text-emerald-200 xl:px-4" href={content.sentinelaLoginUrl}>
            <LogIn size={16} /> Login SENTINELA
          </a>
          <a className="inline-flex items-center gap-2 rounded-md bg-emerald-500 px-3 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-950/25 transition hover:-translate-y-0.5 hover:bg-emerald-400 xl:px-4" href={content.whatsappUrl} rel="noreferrer" target="_blank">
            <MessageCircle size={16} /> Falar no WhatsApp
          </a>
        </div>

        <div className="impacto-mobile-actions items-center justify-end gap-2">
          <a className="inline-flex items-center justify-center rounded-md border border-white/15 p-2 text-white" href={content.sentinelaLoginUrl} aria-label="Login SENTINELA">
            <LogIn size={19} />
          </a>
          <a className="inline-flex items-center justify-center rounded-md bg-emerald-500 p-2 text-white" href={content.whatsappUrl} rel="noreferrer" target="_blank" aria-label="Falar no WhatsApp">
            <MessageCircle size={19} />
          </a>
        </div>
      </div>
      <nav className="impacto-mobile-nav mx-auto max-w-7xl gap-4 overflow-x-auto px-4 pb-3 text-xs font-semibold text-slate-200 sm:px-6">
        {links.map(([label, href]) => (
          <a className="shrink-0 transition hover:text-emerald-300" href={href} key={href}>
            {label}
          </a>
        ))}
      </nav>
    </header>
  );
}
