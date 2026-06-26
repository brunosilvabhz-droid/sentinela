import { Check } from "lucide-react";
import SectionHeader from "./SectionHeader.jsx";

const benefits = [
  "Redução de retrabalho",
  "Menos erros operacionais",
  "Mais previsibilidade",
  "Economia de tempo",
  "Decisões baseadas em dados",
  "Retorno rápido sobre o investimento",
];

export default function BenefitsSection() {
  return (
    <section className="bg-slate-50 py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader eyebrow="Benefícios" title="Sua empresa, sem surpresas" />
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {benefits.map((benefit) => (
            <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-5 transition hover:-translate-y-1 hover:border-emerald-300" key={benefit}>
              <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-emerald-50 text-emerald-700"><Check size={19} /></span>
              <strong className="text-slate-950">{benefit}</strong>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
