import impactoLogo from "../../assets/impacto-logo.png";
import { COMPANY_DOMAIN, SENTINELA_LOGIN_URL, WHATSAPP_URL } from "../../constants";

export default function Footer() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 py-10 text-slate-300">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 sm:px-6 md:grid-cols-[1.2fr_1fr_1fr] lg:px-8">
        <div>
          <img className="h-14 w-44 rounded bg-white object-contain p-2" src={impactoLogo} alt="IMPACTO" />
          <p className="mt-4 text-sm leading-6">Observabilidade de Processos de Negócio</p>
        </div>
        <div className="text-sm leading-7">
          <strong className="text-white">Contato</strong>
          <p>Domínio: {COMPANY_DOMAIN}</p>
          <p>WhatsApp: (31) 9127-5790</p>
        </div>
        <div className="grid content-start gap-2 text-sm">
          <strong className="text-white">Links</strong>
          <a className="transition hover:text-emerald-300" href={SENTINELA_LOGIN_URL}>Login SENTINELA</a>
          <a className="transition hover:text-emerald-300" href={WHATSAPP_URL} rel="noreferrer" target="_blank">WhatsApp</a>
          <a className="transition hover:text-emerald-300" href="#privacidade">Política de Privacidade</a>
        </div>
      </div>
    </footer>
  );
}
