import { Activity, BellRing, Clock3, Link2, LogIn, MessageCircle, TrendingUp } from "lucide-react";

const metricIcons = [Activity, BellRing, Link2, Clock3];
const metricTones = ["text-emerald-300", "text-red-300", "text-sky-300", "text-amber-300"];

export default function Hero({ content }) {
  return (
    <section id="inicio" className="relative isolate overflow-hidden bg-slate-950 pt-32 text-white sm:pt-36 lg:pt-32">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_18%_20%,rgba(16,185,129,0.25),transparent_32%),radial-gradient(circle_at_82%_10%,rgba(37,99,235,0.25),transparent_34%),linear-gradient(135deg,#061224_0%,#0f172a_48%,#06251d_100%)]" />
      <img className="absolute right-[-10rem] top-28 -z-10 hidden w-[52rem] opacity-[0.08] xl:block" src={content.heroImageUrl || content.logoUrl} alt="" />

      <div className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8 lg:pb-24">
        <div className="max-w-4xl">
          <span className="inline-flex rounded-full border border-emerald-300/30 bg-emerald-400/10 px-4 py-2 text-sm font-semibold text-emerald-200">
            {content.eyebrow}
          </span>
          <h1 className="mt-7 max-w-4xl text-4xl font-black leading-tight tracking-tight text-white sm:text-6xl">
            {content.heroTitle}
          </h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-200 sm:text-xl">
            {content.heroSubtitle}
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <a className="inline-flex items-center justify-center gap-2 rounded-md bg-emerald-500 px-6 py-3 font-bold text-white shadow-xl shadow-emerald-950/30 transition hover:-translate-y-1 hover:bg-emerald-400" href={content.whatsappUrl} rel="noreferrer" target="_blank">
              <MessageCircle size={19} /> Solicitar diagnóstico pelo WhatsApp
            </a>
            <a className="inline-flex items-center justify-center gap-2 rounded-md border border-white/20 bg-white/8 px-6 py-3 font-bold text-white transition hover:-translate-y-1 hover:border-emerald-200 hover:bg-white/12" href={content.sentinelaLoginUrl}>
              <LogIn size={19} /> Acessar SENTINELA
            </a>
          </div>
        </div>

        <div className="mt-14 grid gap-4 md:grid-cols-4">
          {content.metrics.map((metric, index) => {
            const Icon = metricIcons[index] || Activity;
            return (
              <div className="rounded-lg border border-white/10 bg-white/[0.07] p-5 shadow-2xl shadow-slate-950/20 backdrop-blur transition hover:-translate-y-1 hover:border-emerald-300/40" key={metric.label}>
                <Icon className={metricTones[index] || "text-emerald-300"} size={24} />
                <strong className="mt-5 block text-3xl font-black text-white">{metric.value}</strong>
                <span className="mt-1 block text-sm text-slate-300">{metric.label}</span>
              </div>
            );
          })}
        </div>

        <div className="mt-5 flex items-center gap-2 text-sm font-semibold text-emerald-200">
          <TrendingUp size={17} /> Automatizar. Monitorar. Alertar. Evoluir.
        </div>
      </div>
    </section>
  );
}
