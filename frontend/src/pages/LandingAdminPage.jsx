import { ArrowLeft, ImagePlus, RotateCcw, Save } from "lucide-react";
import { useState } from "react";
import {
  DEFAULT_LANDING_CONTENT,
  loadLandingContent,
  resetLandingContent,
  saveLandingContent,
} from "../landingContent.js";

export default function LandingAdminPage() {
  const [content, setContent] = useState(() => loadLandingContent());
  const [message, setMessage] = useState("");

  function updateField(field, value) {
    setContent((current) => ({ ...current, [field]: value }));
  }

  function updateMetric(index, field, value) {
    setContent((current) => ({
      ...current,
      metrics: current.metrics.map((metric, metricIndex) =>
        metricIndex === index ? { ...metric, [field]: value } : metric,
      ),
    }));
  }

  async function uploadImage(field, file) {
    if (!file) return;
    const dataUrl = await fileToDataUrl(file);
    updateField(field, dataUrl);
  }

  function save() {
    saveLandingContent(content);
    window.dispatchEvent(new Event("impacto-landing-updated"));
    setMessage("Landing atualizada neste navegador.");
  }

  function restore() {
    resetLandingContent();
    setContent(DEFAULT_LANDING_CONTENT);
    window.dispatchEvent(new Event("impacto-landing-updated"));
    setMessage("Conteúdo padrão restaurado.");
  }

  return (
    <main className="landing-admin min-h-screen bg-slate-100 px-4 py-8 text-slate-950 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <span className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-700">Super-admin</span>
            <h1 className="mt-2 text-3xl font-black">Editar landing IMPACTO</h1>
            <p className="mt-2 text-slate-600">Ajuste textos, links e imagens da landing sem mexer no código.</p>
          </div>
          <a className="inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 font-semibold transition hover:border-emerald-400" href="/">
            <ArrowLeft size={17} /> Ver landing
          </a>
        </div>

        {message && <div className="mb-5 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-emerald-800">{message}</div>}

        <section className="grid gap-5 lg:grid-cols-[1fr_320px]">
          <div className="grid gap-5">
            <Panel title="Informações principais">
              <Input label="Nome da empresa" value={content.companyName} onChange={(value) => updateField("companyName", value)} />
              <Input label="Domínio" value={content.domain} onChange={(value) => updateField("domain", value)} />
              <Input label="Etiqueta do hero" value={content.eyebrow} onChange={(value) => updateField("eyebrow", value)} />
              <Textarea label="Título principal" value={content.heroTitle} onChange={(value) => updateField("heroTitle", value)} />
              <Textarea label="Subtítulo" value={content.heroSubtitle} onChange={(value) => updateField("heroSubtitle", value)} />
            </Panel>

            <Panel title="Links">
              <Input label="URL WhatsApp" value={content.whatsappUrl} onChange={(value) => updateField("whatsappUrl", value)} />
              <Input label="URL Login SENTINELA" value={content.sentinelaLoginUrl} onChange={(value) => updateField("sentinelaLoginUrl", value)} />
            </Panel>

            <Panel title="Cards do dashboard ilustrativo">
              <div className="grid gap-4 sm:grid-cols-2">
                {content.metrics.map((metric, index) => (
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4" key={index}>
                    <Input label="Valor" value={metric.value} onChange={(value) => updateMetric(index, "value", value)} />
                    <Input label="Rótulo" value={metric.label} onChange={(value) => updateMetric(index, "label", value)} />
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <aside className="grid content-start gap-5">
            <Panel title="Imagens">
              <ImageInput label="Logo do cabeçalho" value={content.logoUrl} onChange={(file) => uploadImage("logoUrl", file)} />
              <ImageInput label="Imagem de fundo do hero" value={content.heroImageUrl} onChange={(file) => uploadImage("heroImageUrl", file)} />
            </Panel>

            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <button className="mb-3 inline-flex w-full items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 py-3 font-bold text-white transition hover:bg-emerald-500" onClick={save}>
                <Save size={18} /> Salvar alterações
              </button>
              <button className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-slate-300 px-4 py-3 font-bold text-slate-700 transition hover:border-red-300 hover:text-red-700" onClick={restore}>
                <RotateCcw size={18} /> Restaurar padrão
              </button>
              <p className="mt-4 text-xs leading-5 text-slate-500">
                Nesta fase, as alterações ficam salvas no navegador. O próximo passo é persistir isso no backend para todos os usuários.
              </p>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

function Panel({ title, children }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-black">{title}</h2>
      <div className="grid gap-4">{children}</div>
    </section>
  );
}

function Input({ label, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm font-semibold text-slate-700">
      {label}
      <input className="min-h-11 rounded-md border border-slate-300 px-3 text-slate-950 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function Textarea({ label, value, onChange }) {
  return (
    <label className="grid gap-1 text-sm font-semibold text-slate-700">
      {label}
      <textarea className="min-h-28 rounded-md border border-slate-300 px-3 py-2 text-slate-950 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function ImageInput({ label, value, onChange }) {
  return (
    <div className="grid gap-3">
      <span className="text-sm font-semibold text-slate-700">{label}</span>
      <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
        <img className="max-h-32 w-full rounded bg-white object-contain p-2" src={value} alt={label} />
      </div>
      <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-700 transition hover:border-emerald-400">
        <ImagePlus size={17} /> Trocar imagem
        <input className="hidden" type="file" accept="image/*" onChange={(event) => onChange(event.target.files?.[0])} />
      </label>
    </div>
  );
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
