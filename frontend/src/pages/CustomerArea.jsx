import { useEffect, useState } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import {
  Mail, Loader2, ArrowLeft, ShieldCheck, Download as DownloadIcon,
  Package, Calendar, Euro, ExternalLink, LogOut,
} from "lucide-react";
import FiscoFacileLogo from "@/components/FiscoFacileLogo";
import { showLocalTestFeatures } from "@/lib/runtimeConfig";
import {
  clearCustomerSession,
  getCustomerExpiresAt,
  getCustomerToken,
  isCustomerSessionExpired,
  persistCustomerSession,
} from "@/lib/customerSession";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CustomerArea() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const urlToken = params.get("token");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [testAccessLoading, setTestAccessLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const [sessionToken, setSessionToken] = useState(() => {
    if (isCustomerSessionExpired()) {
      clearCustomerSession();
      return "";
    }
    return getCustomerToken();
  });
  const [sessionExpiresAt, setSessionExpiresAt] = useState(() => {
    if (isCustomerSessionExpired()) return "";
    return getCustomerExpiresAt();
  });
  const [resolvingSession, setResolvingSession] = useState(Boolean(urlToken));
  const [orders, setOrders] = useState(null);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!urlToken) {
      setResolvingSession(false);
      return;
    }

    let active = true;
    setResolvingSession(true);
    setError(null);

    axios
      .post(`${API}/customer/session/exchange`, { token: urlToken })
      .then(({ data }) => {
        if (!active) return;
        persistCustomerSession(data.token, data.expires_at);
        setSessionToken(data.token);
        setSessionExpiresAt(data.expires_at);
        navigate("/area-riservata", { replace: true });
        toast.success("Accesso sicuro attivato.");
      })
      .catch((err) => {
        if (!active) return;
        clearCustomerSession();
        setSessionToken("");
        setSessionExpiresAt("");
        const code = err.response?.status;
        if (code === 403) setError("Il link è scaduto oppure è già stato usato. Richiedine uno nuovo qui sotto.");
        else if (code === 404) setError("Link non valido. Richiedine uno nuovo qui sotto.");
        else setError("Errore di rete. Riprova tra poco.");
        navigate("/area-riservata", { replace: true });
      })
      .finally(() => {
        if (active) setResolvingSession(false);
      });

    return () => {
      active = false;
    };
  }, [urlToken, navigate]);

  useEffect(() => {
    if (resolvingSession) return;
    if (!sessionToken) return;

    if (isCustomerSessionExpired()) {
      clearCustomerSession();
      setSessionToken("");
      setSessionExpiresAt("");
      setOrders(null);
      setError("La sessione è scaduta. Richiedi un nuovo link di accesso.");
      return;
    }

    setLoadingOrders(true);
    setError(null);
    axios
      .get(`${API}/customer/orders`, {
        headers: { "x-customer-token": sessionToken },
      })
      .then((res) => setOrders(res.data))
      .catch((err) => {
        const code = err.response?.status;
        clearCustomerSession();
        setSessionToken("");
        setSessionExpiresAt("");
        setOrders(null);
        if (code === 403 || code === 401) setError("La sessione è scaduta. Richiedi un nuovo link qui sotto.");
        else if (code === 404) setError("Link non valido. Richiedine uno nuovo qui sotto.");
        else setError("Errore di rete. Riprova tra poco.");
      })
      .finally(() => setLoadingOrders(false));
  }, [sessionToken, resolvingSession]);

  const handleRequestAccess = async (e) => {
    e.preventDefault();
    if (!email.trim()) {
      toast.error("Inserisci la tua email.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await axios.post(`${API}/customer/request-access`, { email: email.trim() });
      setSent(true);
      toast.success("Email inviata! Controlla la tua casella.");
    } catch (err) {
      toast.error("Errore. Riprova tra poco.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleTestAccess = async () => {
    setError(null);
    setTestAccessLoading(true);
    try {
      const { data } = await axios.post(`${API}/customer/test-access`);
      toast.success("Accesso test attivato.");
      window.location.href = data.url;
    } catch (err) {
      toast.error("Accesso test non disponibile.");
    } finally {
      setTestAccessLoading(false);
    }
  };

  const handleLogout = () => {
    if (sessionToken) {
      axios.post(`${API}/customer/logout`, {}, {
        headers: { "x-customer-token": sessionToken },
      }).catch(() => {
        // Se il backend non risponde, puliamo comunque la sessione locale.
      });
    }
    clearCustomerSession();
    setSessionToken("");
    setSessionExpiresAt("");
    setOrders(null);
    setError(null);
    setSent(false);
    setEmail("");
    navigate("/area-riservata", { replace: true });
    toast.success("Sei uscito dall'area riservata.");
  };

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
      toast.error("Errore download. Riprova.");
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-white" data-testid="customer-area">
      {/* HEADER */}
      <header className="border-b border-zinc-900 bg-[#09090b]/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-8 py-4 flex items-center justify-between gap-3">
          <Link to="/" className="flex items-center gap-3 font-display text-xl font-black tracking-tight">
            <FiscoFacileLogo size={40} />
            <span className="hidden sm:flex items-center gap-2">
              <span>Fisco<span className="text-[#CCFF00]">.</span></span>
              <span className="text-zinc-400 font-medium">Facile</span>
            </span>
          </Link>
          <div className="hidden sm:flex items-center gap-2 text-xs text-zinc-500">
            <ShieldCheck className="w-4 h-4 text-[#CCFF00]" /> Area riservata cliente
          </div>
          {sessionToken && (
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-2 border border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-600 rounded-lg px-4 py-2 text-sm font-semibold transition-colors"
              data-testid="customer-logout"
            >
              <LogOut className="w-4 h-4" /> Esci
            </button>
          )}
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 sm:px-8 py-12 sm:py-16">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors mb-10"
          data-testid="back-home"
        >
          <ArrowLeft className="w-4 h-4" /> Torna alla home
        </Link>

        {resolvingSession && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-10 h-10 text-[#CCFF00] animate-spin" />
          </div>
        )}

        {/* === No token: REQUEST ACCESS === */}
        {!sessionToken && !resolvingSession && (
          <div className="max-w-xl mx-auto">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
              Area Riservata
            </div>
            <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter leading-tight mb-4">
              Accedi ai tuoi acquisti<span className="text-[#CCFF00]">.</span>
            </h1>
            <p className="text-zinc-400 mb-10 text-lg">
              Inserisci l'email che hai usato per acquistare. Ti inviamo un link sicuro
              per accedere all'area download. Il link si usa una sola volta e apre una sessione protetta.
            </p>

            {error && (
              <div className="mb-6 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-sm text-amber-100">
                {error}
              </div>
            )}

            {sent ? (
              <div className="bg-[#18181B] border border-[#CCFF00]/40 rounded-2xl p-8 text-center" data-testid="access-sent">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#CCFF00] text-black mb-6">
                  <Mail className="w-7 h-7" />
                </div>
                <h3 className="font-display text-2xl font-bold mb-3">Email inviata.</h3>
                <p className="text-zinc-400 leading-relaxed">
                  Se l'indirizzo è associato a un acquisto, riceverai a breve un link
                  per accedere all'area riservata.
                </p>
                <p className="text-xs text-zinc-600 mt-6">
                  Non vedi l'email? Controlla nello spam o richiedi un nuovo link tra qualche minuto.
                </p>
                <button
                  onClick={() => { setSent(false); setEmail(""); }}
                  className="mt-6 text-zinc-400 hover:text-white text-sm font-semibold"
                  data-testid="try-again"
                >
                  Prova un'altra email
                </button>
              </div>
            ) : (
              <form
                onSubmit={handleRequestAccess}
                className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6 sm:p-8 space-y-5"
                data-testid="access-form"
              >
                <div>
                  <label className="block text-xs uppercase tracking-wider text-zinc-500 font-bold mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    autoFocus
                    placeholder="la-tua@email.it"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-lg px-4 py-3.5 focus:ring-2 focus:ring-[#CCFF00] focus:border-transparent outline-none transition-all placeholder:text-zinc-600"
                    data-testid="access-email-input"
                  />
                </div>
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-[#CCFF00] text-black font-bold uppercase tracking-wide py-3.5 rounded-lg hover:bg-[#B3E600] transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
                  data-testid="access-submit"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : (
                    <><Mail className="w-4 h-4" /> Inviami il link</>
                  )}
                </button>
                <p className="text-xs text-zinc-600 text-center">
                  Per la tua sicurezza non chiediamo password. Il link via email è monouso e apre una sessione temporanea.
                </p>
                {showLocalTestFeatures && (
                  <button
                    type="button"
                    onClick={handleTestAccess}
                    disabled={submitting || testAccessLoading}
                    className="w-full border border-dashed border-zinc-700 text-zinc-300 font-semibold py-3.5 rounded-lg hover:border-zinc-500 hover:text-white transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
                    data-testid="customer-test-access"
                  >
                    {testAccessLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (
                      <><ShieldCheck className="w-4 h-4" /> Accedi in test</>
                    )}
                  </button>
                )}
              </form>
            )}
          </div>
        )}

        {/* === Token present: SHOW ORDERS === */}
        {sessionToken && !resolvingSession && (
          <>
            {loadingOrders && (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-10 h-10 text-[#CCFF00] animate-spin" />
              </div>
            )}

            {error && (
              <div className="max-w-md mx-auto text-center py-10">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-zinc-800 text-zinc-400 mb-6">
                  <ShieldCheck className="w-7 h-7" />
                </div>
                <h2 className="font-display text-2xl font-bold mb-3">Accesso non valido</h2>
                <p className="text-zinc-400 mb-8">{error}</p>
                <Link
                  to="/area-riservata"
                  className="inline-flex bg-[#CCFF00] text-black font-bold uppercase tracking-wide px-6 py-3 rounded-lg hover:bg-[#B3E600] transition-colors"
                >
                  Richiedi nuovo link
                </Link>
              </div>
            )}

            {orders && (
              <div data-testid="orders-list">
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
                  Bentornato/a
                </div>
                <h1 className="font-display text-4xl sm:text-5xl font-black tracking-tighter leading-tight mb-3">
                  I tuoi acquisti<span className="text-[#CCFF00]">.</span>
                </h1>
                <p className="text-zinc-400 mb-12">
                  Ciao <span className="font-mono text-[#CCFF00]">{orders.email}</span>,
                  ecco tutti i pacchetti che hai acquistato. Le guide sono tue per sempre.
                </p>
                {sessionExpiresAt && (
                  <div className="mb-8 text-xs uppercase tracking-[0.18em] text-zinc-500">
                    Sessione protetta attiva fino a {sessionExpiresAt.slice(11, 16)}
                  </div>
                )}

                {orders.orders.length === 0 ? (
                  <div className="bg-[#18181B] border border-[#27272A] rounded-2xl p-12 text-center">
                    <Package className="w-12 h-12 text-zinc-700 mx-auto mb-4" />
                    <h3 className="font-display text-xl font-bold mb-2">Nessun acquisto trovato.</h3>
                    <p className="text-zinc-500 mb-6">Non risultano pacchetti acquistati con questa email.</p>
                    <Link
                      to="/#pricing"
                      className="inline-flex bg-[#CCFF00] text-black font-bold uppercase tracking-wide px-6 py-3 rounded-lg hover:bg-[#B3E600] transition-colors"
                    >
                      Scopri i pacchetti
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {orders.orders.map((o) => (
                      <OrderCard key={o.session_id} order={o} onDownload={downloadGuide} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function OrderCard({ order, onDownload }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      className="bg-[#18181B] border border-[#27272A] rounded-2xl overflow-hidden"
      data-testid={`order-${order.session_id.slice(0, 12)}`}
    >
      <div className="p-5 sm:p-8">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500 mb-2">
              {order.guides_count} guide pratiche
            </div>
            <h3 className="font-display text-2xl sm:text-3xl font-black tracking-tight mb-3">
              {order.package_name}
            </h3>
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
              <div className="flex items-center gap-2 text-zinc-400">
                <Euro className="w-4 h-4 text-[#CCFF00]" />
                <span className="font-mono font-bold">€{Number(order.amount).toFixed(2)}</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-400">
                <Calendar className="w-4 h-4 text-[#CCFF00]" />
                <span className="font-mono">
                  {(order.purchased_at || "").slice(0, 10)}
                </span>
              </div>
            </div>
          </div>
          <a
            href={order.download_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 inline-flex items-center justify-center gap-2 bg-[#CCFF00] text-black font-bold uppercase tracking-wide px-5 py-3 rounded-lg hover:bg-[#B3E600] transition-colors text-sm w-full sm:w-auto"
            data-testid={`open-download-${order.session_id.slice(0, 12)}`}
          >
            <ExternalLink className="w-4 h-4" /> Apri area download
          </a>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-6 text-sm text-zinc-400 hover:text-white transition-colors font-semibold"
        >
          {expanded ? "Nascondi guide ↑" : `Mostra le ${order.guides_count} guide ↓`}
        </button>
      </div>

      {expanded && (
        <div className="px-5 sm:px-8 pb-5 sm:pb-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-4 border-t border-zinc-800">
            {order.guides.map((g, i) => (
              <button
                key={`${g.category}-${g.category_index}`}
                onClick={() => onDownload(g)}
                className="group flex items-center gap-3 p-3 rounded-lg bg-zinc-900/40 hover:bg-zinc-800 border border-zinc-800/50 hover:border-zinc-700 transition-all text-left"
                data-testid={`order-guide-${i}`}
              >
                <div className="flex-shrink-0 w-8 h-8 rounded-md bg-zinc-900 flex items-center justify-center font-mono text-[10px] font-bold text-[#CCFF00]">
                  {String(g.category_index).padStart(2, "0")}
                </div>
                <span className="flex-1 text-xs leading-snug text-zinc-300 text-left break-words">{g.title}</span>
                <DownloadIcon className="w-4 h-4 text-zinc-500 group-hover:text-[#CCFF00] flex-shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
