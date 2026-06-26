import { AlertTriangle, FileSpreadsheet, Repeat2, Split, TimerOff, Workflow } from "lucide-react";
import SectionHeader from "./SectionHeader.jsx";

const problems = [
  ["Relatórios manuais", FileSpreadsheet],
  ["Planilhas desatualizadas", TimerOff],
  ["Sistemas que não conversam", Split],
  ["Falhas descobertas tarde demais", AlertTriangle],
  ["Retrabalho operacional", Repeat2],
  ["Falta de alertas", Workflow],
];

export default function ProblemSection() {
  return (
    <section className="bg-white py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader eyebrow="O problema" title="Empresas perdem dinheiro com processos invisíveis" />
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {problems.map(([label, Icon]) => (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 transition hover:-translate-y-1 hover:border-red-200 hover:bg-white hover:shadow-xl hover:shadow-slate-200/70" key={label}>
              <Icon className="text-red-500" size={26} />
              <h3 className="mt-5 text-lg font-bold text-slate-950">{label}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">Quando ninguém monitora, pequenos desvios viram atraso, custo e perda de controle.</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
