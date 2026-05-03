import { Link } from "react-router-dom";
import { ArrowLeft, FileText } from "lucide-react";
import FiscoFacileLogo from "@/components/FiscoFacileLogo";

export default function TermsOfService() {
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
              Termini di servizio<span className="text-[#CCFF00]">.</span>
            </h1>
          </div>
        </div>

        <div className="space-y-8 text-zinc-300 leading-relaxed">
          <section>
            <h2 className="text-2xl font-bold text-white mb-3">1. Oggetto</h2>
            <p>
              Il progetto vende guide digitali informative e consente l&apos;accesso ad
              un&apos;area riservata per il download dei materiali acquistati.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">2. Natura del contenuto</h2>
            <p>
              Le guide hanno finalita informative e operative. Non sostituiscono un
              commercialista o un professionista abilitato nei casi complessi o contenziosi.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. Accesso e download</h2>
            <p>
              Dopo il pagamento confermato, il cliente riceve un accesso personale all&apos;area
              riservata e puo scaricare i PDF compresi nel pacchetto acquistato.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">4. Rimborsi e recesso</h2>
            <p>
              Trattandosi di contenuti digitali scaricabili, la gestione di recesso e rimborsi
              deve essere verificata in base alla normativa applicabile e alle policy commerciali
              definitive del titolare del progetto.
            </p>
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-[#18181B] p-6">
            <div className="flex items-center gap-3 mb-3 text-white font-semibold">
              <FileText className="w-5 h-5 text-[#CCFF00]" />
              Nota importante
            </div>
            <p>
              Questa pagina e una base operativa. Prima della pubblicazione conviene farla
              revisionare con dati aziendali, policy di rimborso e testi legali definitivi.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
