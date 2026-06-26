import { BarChart3, Bell, Bot, Cable, Gauge, Wrench } from "lucide-react";
import SectionHeader from "./SectionHeader.jsx";

const solutions = [
  ["Automação de processos repetitivos", Bot],
  ["Integração entre sistemas", Cable],
  ["Dashboards e indicadores", BarChart3],
  ["Monitoramento operacional", Gauge],
  ["Alertas por e-mail e WhatsApp", Bell],
  ["Desenvolvimento sob medida", Wrench],
];

export default function SolutionsSection() {
  return (
    <section id="solucoes" className="bg-slate-50 py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader eyebrow="Soluções" title="O que a IMPACTO entrega" description="Tecnologia aplicada aos pontos reais da operação, com integração, automação e acompanhamento contínuo." />
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {solutions.map(([label, Icon]) => (
            <div className="rounded-lg border border-slate-200 bg-white p-6 transition hover:-translate-y-1 hover:border-emerald-300 hover:shadow-xl hover:shadow-emerald-950/10" key={label}>
              <span className="inline-flex rounded-md bg-emerald-50 p-3 text-emerald-700"><Icon size={24} /></span>
              <h3 className="mt-5 text-lg font-bold text-slate-950">{label}</h3>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
