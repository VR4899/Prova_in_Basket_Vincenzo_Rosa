import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import axios from "axios";
import { CheckCircle2, Loader2, XCircle, ArrowLeft, Mail } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Success() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");

  const [status, setStatus] = useState("checking"); // checking | paid | failed | timeout
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!sessionId) {
      setStatus("failed");
      return;
    }

    let attempts = 0;
    const maxAttempts = 10;
    const interval = 2000;
    let active = true;

    const poll = async () => {
      try {
        const { data: res } = await axios.get(`${API}/checkout/status/${sessionId}`);
        if (!active) return;
        setData(res);
        if (res.payment_status === "paid") {
          setStatus("paid");
          return;
        }
        if (res.status === "expired") {
          setStatus("failed");
          return;
        }
        attempts += 1;
        if (attempts >= maxAttempts) {
          setStatus("timeout");
          return;
        }
        setTimeout(poll, interval);
      } catch (e) {
        console.error(e);
        if (!active) return;
        attempts += 1;
        if (attempts >= maxAttempts) {
          setStatus("failed");
          return;
        }
        setTimeout(poll, interval);
      }
    };

    poll();
    return () => {
      active = false;
    };
  }, [sessionId]);

  return (
    <div className="min-h-screen bg-[#09090b] text-white flex items-center justify-center px-6 py-20" data-testid="success-page">
      <div className="max-w-xl w-full">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors mb-10"
          data-testid="back-home"
        >
          <ArrowLeft className="w-4 h-4" /> Torna alla home
        </Link>

        <div className="bg-[#18181B] border border-[#27272A] rounded-3xl p-10 sm:p-14 relative overflow-hidden">
          <div className="absolute -top-32 -right-32 w-64 h-64 bg-[#CCFF00] opacity-10 blur-[100px] pointer-events-none" />

          <div className="relative">
            {status === "checking" && (
              <>
                <Loader2 className="w-16 h-16 text-[#CCFF00] animate-spin mb-8" />
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
                  Verifica in corso
                </div>
                <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight mb-4">
                  Sto controllando il pagamento...
                </h1>
                <p className="text-zinc-400 leading-relaxed">
                  Attendi qualche secondo, ci vuole pochissimo.
                </p>
              </>
            )}

            {status === "paid" && (
              <>
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#CCFF00] text-black mb-8">
                  <CheckCircle2 className="w-9 h-9" strokeWidth={2.5} />
                </div>
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
                  Pagamento ricevuto
                </div>
                <h1 className="font-display text-3xl sm:text-5xl font-black tracking-tight mb-4 leading-tight">
                  Ottimo lavoro<span className="text-[#CCFF00]">.</span>
                </h1>
                <p className="text-zinc-300 leading-relaxed text-lg">
                  Il pagamento è andato a buon fine. Puoi entrare quando vuoi nell&apos;area riservata
                  usando l&apos;email e la password inserite in fase di acquisto.
                </p>

                <div className="mt-8 p-6 rounded-2xl bg-[#0c0c0e] border border-zinc-800 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Importo</span>
                    <span className="font-mono font-bold">
                      €{data ? (data.amount_total / 100).toFixed(2) : "—"}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Pacchetto</span>
                    <span className="font-semibold">{data?.package_id || "—"}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Stato</span>
                    <span className="text-[#CCFF00] font-semibold">Pagato</span>
                  </div>
                </div>

                <Link
                  to={`/download/${sessionId}`}
                  className="mt-8 group bg-[#CCFF00] text-black font-bold uppercase tracking-wide px-8 py-4 rounded-lg hover:bg-[#B3E600] transition-all inline-flex items-center justify-center gap-2 w-full"
                  data-testid="goto-download"
                >
                  Scarica le tue guide ora
                </Link>

                <Link
                  to="/area-riservata"
                  className="mt-3 group border border-zinc-700 text-white font-bold uppercase tracking-wide px-8 py-4 rounded-lg hover:border-zinc-500 hover:bg-zinc-900 transition-all inline-flex items-center justify-center gap-2 w-full"
                  data-testid="goto-customer-area"
                >
                  Vai all&apos;area riservata
                </Link>

                <div className="mt-8 flex items-center gap-3 text-sm text-zinc-500">
                  <Mail className="w-4 h-4" /> Se il servizio email è attivo, controlla anche la cartella spam.
                </div>
              </>
            )}

            {status === "timeout" && (
              <>
                <Loader2 className="w-16 h-16 text-zinc-500 mb-8" />
                <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight mb-4">
                  Verifica ancora in corso
                </h1>
                <p className="text-zinc-400 leading-relaxed">
                  Il pagamento richiede un po' più del solito. Non ti
                  preoccupare: riceverai comunque l'email di conferma. Se hai
                  dubbi, contatta il supporto.
                </p>
              </>
            )}

            {status === "failed" && (
              <>
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-zinc-800 text-zinc-400 mb-8">
                  <XCircle className="w-9 h-9" />
                </div>
                <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight mb-4">
                  Qualcosa non è andato.
                </h1>
                <p className="text-zinc-400 leading-relaxed">
                  La sessione di pagamento non risulta valida. Torna alla home e
                  riprova — non ti è stato addebitato nulla.
                </p>
                <Link
                  to="/"
                  className="mt-8 inline-flex bg-[#CCFF00] text-black font-bold uppercase tracking-wide px-6 py-3 rounded-lg hover:bg-[#B3E600] transition-colors"
                >
                  Torna alla home
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
