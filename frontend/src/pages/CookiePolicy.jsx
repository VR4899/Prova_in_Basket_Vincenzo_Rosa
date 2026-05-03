import { Link } from "react-router-dom";
import { ArrowLeft, Cookie, ShieldCheck } from "lucide-react";
import FiscoFacileLogo from "@/components/FiscoFacileLogo";

export default function CookiePolicy() {
  return (
    <div className="min-h-screen bg-[#09090b] text-white">
      <div className="max-w-4xl mx-auto px-6 sm:px-8 py-16">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors mb-10"
        >
          <ArrowLeft className="w-4 h-4" /> Torna alla home
        </Link>

        <div className="flex items-center gap-4 mb-10">
          <FiscoFacileLogo size={56} />
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00]">Legale</div>
            <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tight">
              Cookie Policy<span className="text-[#CCFF00]">.</span>
            </h1>
          </div>
        </div>

        <div className="space-y-8 text-zinc-300 leading-relaxed">
          <section>
            <h2 className="text-2xl font-bold text-white mb-3">1. Cookie tecnici</h2>
            <p>
              Il progetto utilizza cookie e strumenti tecnici minimi per garantire la
              navigazione, mantenere le sessioni attive e proteggere l&apos;accesso alle aree riservate.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">2. Cookie di funzionalita</h2>
            <p>
              Alcune preferenze locali possono essere memorizzate nel browser per migliorare
              l&apos;esperienza utente, ad esempio per la gestione delle sessioni amministrative
              e dell&apos;area cliente.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. Strumenti terzi</h2>
            <p>
              In caso di utilizzo di servizi esterni come Stripe o altri provider, questi
              possono impostare propri cookie secondo le rispettive policy ufficiali.
            </p>
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-[#18181B] p-6">
            <div className="flex items-center gap-3 mb-3 text-white font-semibold">
              <ShieldCheck className="w-5 h-5 text-[#CCFF00]" />
              Nota operativa
            </div>
            <p className="flex items-start gap-2">
              <Cookie className="w-4 h-4 text-[#CCFF00] mt-1 flex-shrink-0" />
              Prima della pubblicazione finale conviene allineare questa pagina al banner cookie
              e agli strumenti effettivamente installati in produzione.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
