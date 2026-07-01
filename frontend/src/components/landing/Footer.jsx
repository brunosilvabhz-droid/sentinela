export default function Footer({ content }) {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 py-10 text-slate-300">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 sm:px-6 md:grid-cols-[1.2fr_1fr_1fr] lg:px-8">
        <div>
          <span className="flex h-16 w-52 items-center justify-center overflow-hidden rounded-md border border-white/10 bg-slate-950/80 shadow-lg shadow-black/20 ring-1 ring-emerald-300/10">
            <img className="h-full w-full object-cover object-center" src={content.headerLogoUrl || content.logoUrl} alt={content.companyName} />
          </span>
          <p className="mt-4 text-sm leading-6">Observabilidade de Processos de Negócio</p>
        </div>
        <div className="text-sm leading-7">
          <strong className="text-white">Contato</strong>
          <p>Domínio: {content.domain}</p>
          <p>E-mail: contato@impactocg.com</p>
        </div>
        <div className="grid content-start gap-2 text-sm">
          <strong className="text-white">Links</strong>
          <a className="transition hover:text-emerald-300" href={content.sentinelaLoginUrl}>Login SENTINELA</a>
          <a className="transition hover:text-emerald-300" href={content.whatsappUrl} rel="noreferrer" target="_blank">WhatsApp</a>
          <a className="transition hover:text-emerald-300" href="#privacidade">Política de Privacidade</a>
        </div>
      </div>
    </footer>
  );
}
