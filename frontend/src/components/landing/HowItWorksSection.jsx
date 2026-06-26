import SectionHeader from "./SectionHeader.jsx";

const steps = [
  "Mapeamos seus processos",
  "Identificamos gargalos e riscos",
  "Automatizamos tarefas repetitivas",
  "Monitoramos os pontos críticos",
  "Alertamos antes do problema virar prejuízo",
];

export default function HowItWorksSection() {
  return (
    <section id="como-funciona" className="bg-white py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader eyebrow="Método" title="Como funciona" description="Um caminho objetivo para transformar processos soltos em uma operação monitorada." />
        <div className="mt-12 grid gap-4 md:grid-cols-5">
          {steps.map((step, index) => (
            <div className="rounded-lg border border-slate-200 bg-white p-5 transition hover:-translate-y-1 hover:border-emerald-300 hover:shadow-xl hover:shadow-slate-200/70" key={step}>
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-slate-950 text-sm font-black text-emerald-300">{index + 1}</span>
              <h3 className="mt-5 text-base font-bold leading-6 text-slate-950">{step}</h3>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
