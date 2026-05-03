import { Link } from "react-router-dom";
import { ArrowLeft, Mail, ShieldCheck } from "lucide-react";
import FiscoFacileLogo from "@/components/FiscoFacileLogo";
import { publicSupportEmail } from "@/lib/runtimeConfig";

export default function PrivacyPolicy() {
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
              Privacy Policy<span className="text-[#CCFF00]">.</span>
            </h1>
          </div>
        </div>

        <div className="space-y-8 text-zinc-300 leading-relaxed">
          <section>
            <h2 className="text-2xl font-bold text-white mb-3">1. Dati raccolti</h2>
            <p>
              Il sito raccoglie i dati strettamente necessari per gestire lead, ordini,
              accessi all&apos;area riservata, email informative e supporto post-acquisto.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">2. Finalita del trattamento</h2>
            <p>
              I dati vengono usati per inviare estratti gratuiti, gestire acquisti,
              consegnare le guide digitali, monitorare il funnel commerciale e offrire
              assistenza amministrativa e tecnica.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. Conservazione e accesso</h2>
            <p>
              I dati possono essere conservati su MongoDB e, se abilitato, sincronizzati
              anche su Google Sheets per finalita operative interne. L&apos;accesso e limitato
              agli amministratori autorizzati del progetto.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">4. Servizi terzi</h2>
            <p>
              Il progetto puo usare Stripe per i pagamenti, Resend per l&apos;invio email e
              Google Sheets per il monitoraggio. Ogni servizio tratta i dati secondo le
              proprie policy ufficiali.
            </p>
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-[#18181B] p-6">
            <div className="flex items-center gap-3 mb-3 text-white font-semibold">
              <ShieldCheck className="w-5 h-5 text-[#CCFF00]" />
              Contatto privacy
            </div>
            <p className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-[#CCFF00]" />
              {publicSupportEmail}
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
