import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import { Download as DownloadIcon, FileText, ArrowLeft, Loader2, ShieldCheck, Lock } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Download() {
  const { sessionId } = useParams();
  const [info, setInfo] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState("all");

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await axios.get(`${API}/download/${sessionId}`);
        setInfo(data);
      } catch (err) {
        const code = err.response?.status;
        if (code === 403) setError("Pagamento non ancora confermato. Riprova tra qualche minuto.");
        else if (code === 404) setError("Acquisto non trovato. Verifica il link nell'email.");
        else setError("Errore di rete. Riprova tra poco.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [sessionId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-[#CCFF00] animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#09090b] text-white flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <Lock className="w-12 h-12 text-zinc-500 mx-auto mb-6" />
          <h1 className="font-display text-3xl font-black mb-4">Accesso negato</h1>
          <p className="text-zinc-400 mb-8">{error}</p>
          <Link to="/" className="inline-flex items-center gap-2 text-[#CCFF00] hover:underline" data-testid="back-home-link">
            <ArrowLeft className="w-4 h-4" /> Torna alla home
          </Link>
        </div>
      </div>
    );
  }

  const categories = [...new Set(info.guides.map((g) => g.category))];
  const filtered = activeFilter === "all"
    ? info.guides
    : info.guides.filter((g) => g.category === activeFilter);

  const downloadGuide = async (guide) => {
    try {
      const res = await axios.get(`${BACKEND_URL}${guide.url}`, { responseType: "blob" });
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safe = guide.title.replace(/[^a-zA-Z0-9]/g, "_").slice(0, 60);
      a.download = `FiscoFacile_${safe}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-white" data-testid="download-page">
      {/* HEADER */}
      <header className="border-b border-zinc-900 bg-[#09090b]/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 sm:px-8 py-4 flex items-center justify-between">
          <Link to="/" className="font-display text-xl font-black tracking-tight" data-testid="logo-link">
            Fisco<span className="text-[#CCFF00]">.</span> <span className="text-zinc-400 font-medium">Facile</span>
          </Link>
          <div className="hidden sm:flex items-center gap-2 text-xs text-zinc-500">
            <ShieldCheck className="w-4 h-4 text-[#CCFF00]" /> Area download protetta
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 sm:px-8 py-16">
        <div className="mb-14">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
            La tua libreria
          </div>
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tighter leading-tight">
            {info.package_name}<span className="text-[#CCFF00]">.</span>
          </h1>
          <p className="mt-6 text-lg text-zinc-400 max-w-2xl">
            Scarica le tue guide quando vuoi. Salva questo link nei preferiti — è valido per sempre.
          </p>

          <div className="mt-8 flex flex-wrap gap-x-10 gap-y-3 text-sm">
            {info.buyer_email && (
              <div>
                <span className="text-zinc-500">Acquirente: </span>
                <span className="font-mono text-[#CCFF00]">{info.buyer_email}</span>
              </div>
            )}
            <div>
              <span className="text-zinc-500">Guide disponibili: </span>
              <span className="font-mono font-bold">{info.guides.length}</span>
            </div>
          </div>
        </div>

        {/* Category filter (only for bundle) */}
        {categories.length > 1 && (
          <div className="flex gap-2 mb-8 p-1.5 bg-[#18181B] border border-[#27272A] rounded-xl w-fit">
            <button
              onClick={() => setActiveFilter("all")}
              className={`px-5 py-2 rounded-lg font-bold text-sm uppercase tracking-wide transition-all ${
                activeFilter === "all" ? "bg-[#CCFF00] text-black" : "text-zinc-400 hover:text-white"
              }`}
              data-testid="filter-all"
            >
              Tutte ({info.guides.length})
            </button>
            {categories.map((c) => (
              <button
                key={c}
                onClick={() => setActiveFilter(c)}
                className={`px-5 py-2 rounded-lg font-bold text-sm uppercase tracking-wide transition-all ${
                  activeFilter === c ? "bg-[#CCFF00] text-black" : "text-zinc-400 hover:text-white"
                }`}
                data-testid={`filter-${c}`}
              >
                {c === "privati" ? "Privati" : "Aziende"} (
                {info.guides.filter((g) => g.category === c).length})
              </button>
            ))}
          </div>
        )}

        {/* GUIDES GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="guides-list">
          {filtered.map((g) => (
            <div
              key={g.global_index}
              className="group flex items-center gap-4 p-5 rounded-xl bg-[#18181B] border border-[#27272A] hover:border-[#CCFF00]/40 transition-all"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-zinc-900 flex items-center justify-center font-mono text-xs font-bold text-[#CCFF00]">
                {String(g.global_index).padStart(2, "0")}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs uppercase tracking-wider text-zinc-500 mb-1">
                  {g.category === "privati" ? "Privati" : "Aziende"}
                </div>
                <div className="font-semibold text-sm leading-snug truncate">{g.title}</div>
              </div>
              <button
                onClick={() => downloadGuide(g)}
                className="flex-shrink-0 inline-flex items-center gap-2 bg-zinc-800 hover:bg-[#CCFF00] hover:text-black text-white px-4 py-2.5 rounded-lg font-semibold text-sm transition-all"
                data-testid={`download-btn-${g.category}-${g.category_index}`}
              >
                <DownloadIcon className="w-4 h-4" /> PDF
              </button>
            </div>
          ))}
        </div>

        <div className="mt-16 p-6 rounded-2xl bg-[#0c0c0e] border border-zinc-900 flex items-start gap-4">
          <FileText className="w-6 h-6 text-[#CCFF00] flex-shrink-0 mt-0.5" />
          <div className="text-sm text-zinc-400 leading-relaxed">
            <strong className="text-white">Hai bisogno di aiuto?</strong>
            <br />
            Scrivi a <a href="mailto:supporto@fiscofacile.it" className="text-[#CCFF00] hover:underline">supporto@fiscofacile.it</a> indicando il tuo ordine. Rispondiamo entro 48h.
          </div>
        </div>
      </div>
    </div>
  );
}
