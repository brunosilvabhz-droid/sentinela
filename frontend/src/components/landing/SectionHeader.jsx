export default function SectionHeader({ eyebrow, title, description, light = false }) {
  return (
    <div className="mx-auto max-w-3xl text-center">
      {eyebrow && <span className={`text-sm font-bold uppercase tracking-[0.18em] ${light ? "text-emerald-300" : "text-emerald-700"}`}>{eyebrow}</span>}
      <h2 className={`mt-3 text-3xl font-black tracking-tight sm:text-4xl ${light ? "text-white" : "text-slate-950"}`}>{title}</h2>
      {description && <p className={`mt-4 text-base leading-7 ${light ? "text-slate-300" : "text-slate-600"}`}>{description}</p>}
    </div>
  );
}
