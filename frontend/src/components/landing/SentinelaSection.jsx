import { CheckCircle2, LogIn, MessageCircle } from "lucide-react";
import { SENTINELA_LOGIN_URL, WHATSAPP_URL } from "../../constants";

const features = [
  "Monitoramento de Excel, CSV, bancos de dados e APIs",
  "Regras personalizadas por cliente",
  "Alertas por e-mail e WhatsApp",
  "Histórico de execuções",
  "Dashboard de ocorrências",
  "Ambiente multiempresa",
];

export default function SentinelaSection() {
  return (
    <section id="sentinela" className="bg-slate-950 py-20 text-white">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 sm:px-6 lg:grid-cols-[1fr_0.9fr] lg:px-8">
        <div>
          <span className="text-sm font-bold uppercase tracking-[0.18em] text-amber-300">Plataforma</span>
          <h2 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">SENTINELA: observabilidade de processos de negócio</h2>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
            O SENTINELA é a plataforma da IMPACTO para monitorar dados, regras e processos críticos. Ele identifica exceções, dispara alertas automáticos e mantém o histórico das ocorrências.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <a className="inline-flex items-center justify-center gap-2 rounded-md bg-emerald-500 px-6 py-3 font-bold text-white transition hover:-translate-y-1 hover:bg-emerald-400" href={SENTINELA_LOGIN_URL}>
              <LogIn size={18} /> Acessar SENTINELA
            </a>
            <a className="inline-flex items-center justify-center gap-2 rounded-md border border-white/20 px-6 py-3 font-bold text-white transition hover:-translate-y-1 hover:border-amber-300 hover:text-amber-200" href={WHATSAPP_URL} rel="noreferrer" target="_blank">
              <MessageCircle size={18} /> Quero conhecer
            </a>
          </div>
        </div>

        <div className="rounded-lg border border-white/10 bg-white/[0.06] p-6 shadow-2xl shadow-black/20">
          <div className="grid gap-4">
            {features.map((feature) => (
              <div className="flex items-start gap-3 rounded-md bg-white/[0.05] p-4" key={feature}>
                <CheckCircle2 className="mt-0.5 shrink-0 text-emerald-300" size={20} />
                <span className="text-sm leading-6 text-slate-200">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
