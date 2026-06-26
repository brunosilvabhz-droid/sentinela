import { MessageCircle } from "lucide-react";
import { WHATSAPP_URL } from "../../constants";

export default function CTASection() {
  return (
    <section id="contato" className="bg-slate-950 px-4 py-20 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl rounded-lg border border-white/10 bg-white/[0.06] p-8 text-center shadow-2xl shadow-black/20 sm:p-12">
        <h2 className="text-3xl font-black tracking-tight sm:text-4xl">Quer descobrir quais processos da sua empresa podem ser automatizados ou monitorados?</h2>
        <p className="mx-auto mt-4 max-w-2xl text-lg leading-8 text-slate-300">Solicite um diagnóstico inicial e veja onde sua operação pode ganhar eficiência.</p>
        <a className="mt-8 inline-flex items-center justify-center gap-2 rounded-md bg-emerald-500 px-6 py-3 font-bold text-white transition hover:-translate-y-1 hover:bg-emerald-400" href={WHATSAPP_URL} rel="noreferrer" target="_blank">
          <MessageCircle size={19} /> Falar com a IMPACTO no WhatsApp
        </a>
      </div>
    </section>
  );
}
