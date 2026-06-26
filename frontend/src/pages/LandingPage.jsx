import { MessageCircle } from "lucide-react";
import CTASection from "../components/landing/CTASection.jsx";
import BenefitsSection from "../components/landing/BenefitsSection.jsx";
import Footer from "../components/landing/Footer.jsx";
import Header from "../components/landing/Header.jsx";
import Hero from "../components/landing/Hero.jsx";
import HowItWorksSection from "../components/landing/HowItWorksSection.jsx";
import ProblemSection from "../components/landing/ProblemSection.jsx";
import SentinelaSection from "../components/landing/SentinelaSection.jsx";
import SolutionsSection from "../components/landing/SolutionsSection.jsx";
import { WHATSAPP_URL } from "../constants";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-900 antialiased">
      <Header />
      <main>
        <Hero />
        <ProblemSection />
        <SolutionsSection />
        <SentinelaSection />
        <HowItWorksSection />
        <BenefitsSection />
        <CTASection />
      </main>
      <Footer />
      <a
        aria-label="Falar com a IMPACTO no WhatsApp"
        className="fixed bottom-5 right-5 z-50 inline-flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500 text-white shadow-2xl shadow-emerald-950/30 transition hover:-translate-y-1 hover:bg-emerald-400"
        href={WHATSAPP_URL}
        rel="noreferrer"
        target="_blank"
      >
        <MessageCircle size={28} />
      </a>
    </div>
  );
}
