import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import FiscoFacileLogo from "@/components/FiscoFacileLogo";
import { showLocalTestFeatures } from "@/lib/runtimeConfig";
import {
  ArrowRight,
  Check,
  Zap,
  Shield,
  Clock,
  FileText,
  Sparkles,
  TrendingDown,
  BookOpen,
  ChevronDown,
  Mail,
  Star,
  CircleDot,
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PACKAGES = {
  privati: {
    id: "privati",
    name: "Privati",
    price: 39,
    badge: "Per chi gestisce solo i propri impegni",
    guides: [
      "Cassetto Fiscale: come accedere e leggerlo",
      "Comunicazione IBAN per rimborsi",
      "Visura Catastale online",
      "Rateizzazione Avviso Bonario",
      "Pagamento F24 online",
      "730 spiegato semplice (anche precompilato)",
      "Cartelle esattoriali: come gestirle",
      "Appuntamento INPS in pochi click",
      "Versamento contributi INPS",
      "Domanda NASPI passo-passo",
      "Bonus e detrazioni più richieste",
      "ISEE: a cosa serve davvero",
      "Identità digitale (SPID/CIE)",
      "Riscatto laurea per pensione",
      "Codice fiscale duplicato/online",
      "Controllo posizione contributiva",
    ],
  },
  aziende: {
    id: "aziende",
    name: "Aziende & P.IVA",
    price: 39,
    badge: "Per imprenditori e partite IVA",
    guides: [
      "Cassetto Fiscale aziendale",
      "Comunicazione IBAN aziendale",
      "Rateizzazione Avviso Bonario",
      "F24 Online: IVA, IRPEF, contributi",
      "Certificato Partita IVA",
      "Regime Forfettario: requisiti e adempimenti",
      "Liquidazioni IVA Trimestrali (LIPE)",
      "Dichiarazione IVA annuale",
      "Dichiarazione IRAP",
      "Fatturazione Elettronica: emissione",
      "Controllo fatture vendita/acquisto",
      "Visura Camerale e Prima Nota",
    ],
  },
  bundle: {
    id: "bundle",
    name: "Bundle Completo",
    price: 67.50,
    oldPrice: 90,
    badge: "Tutte le 28 guide insieme — Sconto 25%",
    guides: [],
  },
};

const BENEFITS = [
  {
    icon: Sparkles,
    title: "Zero burocratese",
    desc: "Testi scritti per umani, non per consulenti. Frasi brevi, parole vere.",
  },
  {
    icon: TrendingDown,
    title: "Risparmio immediato",
    desc: "Smetti di pagare 50€ ogni volta che chiedi una cosa al commercialista.",
  },
  {
    icon: FileText,
    title: "Step-by-step reali",
    desc: "Screenshot dei portali ufficiali. Click dopo click, fino al risultato.",
  },
  {
    icon: Shield,
    title: "Aggiornato 2026",
    desc: "Riferimenti normativi sempre al passo con le ultime circolari.",
  },
];

const TESTIMONIALS = [
  { name: "Marco R.", city: "Milano", role: "Freelance", text: "Ho fatto la mia prima Liquidazione IVA da solo grazie alla guida. Mai più consulenze al telefono a 80€." },
  { name: "Giulia T.", city: "Roma", role: "Privata", text: "Ho rateizzato una cartella in 10 minuti, seguendo gli screenshot. Avevo paura di sbagliare, invece tutto perfetto." },
  { name: "Andrea V.", city: "Torino", role: "P.IVA", text: "Le guide sui forfettari sono fatte benissimo. Spiegano tutto, anche le cose che il commercialista dà per scontate." },
  { name: "Sara L.", city: "Napoli", role: "Privata", text: "Ho preso il pacchetto bundle per il 730 e per aiutare mio padre con la NASPI. Soldi spesi benissimo." },
  { name: "Luca M.", city: "Bologna", role: "Imprenditore", text: "Finalmente capisco cosa pago in F24. Prima firmavo e basta. Ora controllo tutto." },
  { name: "Elisa P.", city: "Firenze", role: "Privata", text: "Il Cassetto Fiscale non lo avevo mai aperto. In 5 minuti ho scoperto un rimborso di 200€ dimenticato." },
];

const FAQS = [
  { q: "Come ricevo le guide?", a: "Subito dopo il pagamento puoi entrare nell'area riservata con email e password usate in acquisto. Se il servizio email è attivo ricevi anche la conferma con il link diretto al download. I PDF restano tuoi per sempre." },
  { q: "I PDF sono aggiornati?", a: "Sì. Le guide sono aggiornate al 2026 con riferimenti normativi recenti. Le revisioni minori sono incluse per 12 mesi." },
  { q: "Sono adatte anche a chi non è esperto?", a: "Sono nate proprio per loro. Niente burocratese, solo procedure chiare con screenshot reali dei portali." },
  { q: "Posso restituire il prodotto?", a: "Trattandosi di prodotto digitale scaricabile, il diritto di recesso decade ai sensi del Codice del Consumo (art. 59). Tuttavia se non sei soddisfatto scrivici, troviamo una soluzione." },
  { q: "Sostituiscono il commercialista?", a: "No: per dichiarazioni complesse, contenziosi e ottimizzazione fiscale serve un professionista. Le guide ti rendono autonomo sulle pratiche ordinarie." },
];

export default function Landing() {
  const [activeTab, setActiveTab] = useState("privati");
  const [openFaq, setOpenFaq] = useState(null);
  const [loading, setLoading] = useState(null);
  const [leadForm, setLeadForm] = useState({ nome: "", email: "", interesse: "estratto_gratuito" });
  const [purchaseAccess, setPurchaseAccess] = useState({ email: "", password: "" });
  const [leadLoading, setLeadLoading] = useState(false);
  const [coupon, setCoupon] = useState("");
  const [couponInfo, setCouponInfo] = useState(null);
  const [couponChecking, setCouponChecking] = useState(false);
  // If user comes back cancelled, show toast
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("cancelled") === "true") {
      toast.error("Pagamento annullato. Quando vuoi, puoi riprovare.");
      window.history.replaceState({}, "", "/");
    }
  }, []);

  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const buildCheckoutPayload = (packageId) => {
    const normalizedEmail = purchaseAccess.email.trim().toLowerCase();
    const normalizedPassword = purchaseAccess.password.trim();

    if (!normalizedEmail || !normalizedPassword) {
      toast.error("Prima di acquistare inserisci email e password per l'area riservata.");
      return null;
    }

    if (normalizedPassword.length < 8) {
      toast.error("La password deve avere almeno 8 caratteri.");
      return null;
    }

    const payload = {
      package_id: packageId,
      origin_url: window.location.origin,
      email: normalizedEmail,
      password: normalizedPassword,
    };
    if (couponInfo) payload.coupon = couponInfo.code;
    return payload;
  };

  const handleCheckout = async (packageId) => {
    const payload = buildCheckoutPayload(packageId);
    if (!payload) return;
    setLoading(`stripe:${packageId}`);
    try {
      const { data } = await axios.post(`${API}/checkout/session`, payload);
      window.location.href = data.url;
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Impossibile avviare il checkout. Riprova tra poco.");
      setLoading(null);
    }
  };

  const handleTestBypassCheckout = async (packageId) => {
    const payload = buildCheckoutPayload(packageId);
    if (!payload) return;
    setLoading(`bypass:${packageId}`);
    try {
      const { data } = await axios.post(`${API}/checkout/test-bypass`, payload);
      toast.success("Pagamento bypassato in modalita test.");
      window.location.href = data.url;
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Bypass test non disponibile. Controlla il backend.");
      setLoading(null);
    }
  };

  const checkCoupon = async () => {
    if (!coupon.trim()) return;
    setCouponChecking(true);
    try {
      const { data } = await axios.get(`${API}/coupons/${coupon.trim().toUpperCase()}`);
      setCouponInfo(data);
      toast.success(`Codice valido! Sconto -€${data.discount_eur} applicato.`);
    } catch (err) {
      setCouponInfo(null);
      toast.error("Codice non valido o scaduto.");
    } finally {
      setCouponChecking(false);
    }
  };

  const handleLeadSubmit = async (e) => {
    e.preventDefault();
    const normalizedLead = {
      nome: leadForm.nome.trim(),
      email: leadForm.email.trim().toLowerCase(),
      interesse: leadForm.interesse.trim(),
    };

    if (!normalizedLead.nome || !normalizedLead.email || !normalizedLead.interesse) {
      toast.error("Compila nome, email e interesse.");
      return;
    }
    setLeadLoading(true);
    try {
      await axios.post(`${API}/leads`, {
        nome: normalizedLead.nome,
        email: normalizedLead.email,
        interesse: normalizedLead.interesse,
      });
      toast.success("Perfetto! Ti scriviamo a breve con l'estratto.");
      setLeadForm({ nome: "", email: "", interesse: "estratto_gratuito" });
    } catch (err) {
      console.error(err);
      const backendDetail = err?.response?.data?.detail;
      const fallbackMessage = err?.message === "Network Error"
        ? "Il backend non risponde. Controlla che sia acceso su 127.0.0.1:8000."
        : "Invio non riuscito. Riprova tra poco.";
      const message = Array.isArray(backendDetail)
        ? backendDetail.map((item) => item?.msg).filter(Boolean).join(" ")
        : backendDetail || fallbackMessage;
      toast.error(message);
    } finally {
      setLeadLoading(false);
    }
  };

  return (
    <div className="bg-[#09090b] text-white min-h-screen relative" data-testid="landing-root">
      {/* HEADER */}
      <header
        className="fixed top-0 left-0 right-0 z-50 bg-[#09090b]/80 backdrop-blur-md border-b border-[#27272a]"
        data-testid="site-header"
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-8 py-4 flex items-center justify-between">
          <a
            href="#top"
            className="flex items-center gap-3 font-display text-xl font-black tracking-tight"
            data-testid="logo"
          >
            <FiscoFacileLogo size={48} />
            <span className="hidden sm:flex items-center gap-2">
              <span className="relative">
                Fisco
                <span className="text-[#CCFF00]">.</span>
              </span>
              <span className="text-zinc-400 font-medium">Facile</span>
            </span>
          </a>

          <nav className="hidden md:flex items-center gap-8 text-sm text-zinc-400">
            <button onClick={() => scrollTo("benefits")} className="hover:text-white transition-colors" data-testid="nav-benefits">
              Vantaggi
            </button>
            <button onClick={() => scrollTo("guides")} className="hover:text-white transition-colors" data-testid="nav-guides">
              Guide
            </button>
            <button onClick={() => scrollTo("pricing")} className="hover:text-white transition-colors" data-testid="nav-pricing">
              Prezzi
            </button>
            <button onClick={() => scrollTo("faq")} className="hover:text-white transition-colors" data-testid="nav-faq">
              FAQ
            </button>
            <a
              href="/area-riservata"
              className="text-[#CCFF00] hover:text-white transition-colors font-semibold flex items-center gap-1.5"
              data-testid="nav-area-riservata"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#CCFF00] animate-pulse"></span>
              Area Riservata
            </a>
          </nav>

          <button
            onClick={() => scrollTo("pricing")}
            className="bg-[#CCFF00] text-black font-bold text-sm uppercase tracking-wide px-5 py-2.5 rounded-lg hover:bg-[#B3E600] transition-colors"
            data-testid="header-cta"
          >
            Acquista
          </button>
        </div>
      </header>

      {/* HERO */}
      <section
        id="top"
        className="relative pt-32 sm:pt-40 pb-20 sm:pb-32 overflow-hidden noise"
      >
        <div className="absolute inset-0 grid-bg opacity-60 pointer-events-none" />
        <div className="absolute top-1/3 -right-40 w-[500px] h-[500px] rounded-full bg-[#CCFF00] opacity-10 blur-[120px] pulse-glow pointer-events-none" />
        <div className="absolute bottom-0 -left-32 w-[400px] h-[400px] rounded-full bg-[#CCFF00] opacity-5 blur-[120px] pointer-events-none" />

        {/* Decorative rotating emblem */}
        <div className="hidden lg:block absolute top-32 right-12 xl:right-24 pointer-events-none opacity-90">
          <FiscoFacileLogo size={320} showRotation={true} />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 sm:px-8">
          <div className="reveal max-w-5xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900/80 border border-zinc-800 text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-8">
              <CircleDot className="w-3 h-3" /> La fiscalità italiana, finalmente semplice
            </div>

            <h1
              className="font-display text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black leading-[0.95] tracking-tighter"
              data-testid="hero-headline"
            >
              Smetti di regalare <br />
              <span className="text-zinc-500">tempo e soldi</span>
              <br />
              alla burocrazia<span className="text-[#CCFF00]">.</span>
            </h1>

            <p className="mt-8 text-lg sm:text-xl text-zinc-400 leading-relaxed max-w-2xl font-medium">
              Guide pratiche, step-by-step, scritte per gli umani. Gestisci da solo
              Agenzia delle Entrate, INPS e Riscossione — senza pagare consulenti
              costosi.
            </p>

            <div className="mt-10 flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <button
                onClick={() => scrollTo("pricing")}
                className="group bg-[#CCFF00] text-black font-bold uppercase tracking-wide px-8 py-4 rounded-lg hover:bg-[#B3E600] transition-all flex items-center gap-2"
                data-testid="hero-cta-primary"
              >
                Scopri i pacchetti
                <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
              </button>
              <button
                onClick={() => scrollTo("guides")}
                className="text-zinc-300 hover:text-white font-semibold transition-colors flex items-center gap-2"
                data-testid="hero-cta-secondary"
              >
                Vedi tutte le 28 guide
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            <div className="mt-14 flex flex-wrap gap-x-10 gap-y-4 text-sm">
              {[
                ["28", "Guide pratiche"],
                ["5.000+", "Italiani serviti"],
                ["2026", "Versione aggiornata"],
                ["48h", "Supporto medio"],
              ].map(([n, l]) => (
                <div key={l} className="flex items-baseline gap-2">
                  <span className="font-mono font-bold text-2xl text-[#CCFF00]">{n}</span>
                  <span className="text-zinc-500 font-medium">{l}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* BENEFITS */}
      <section
        id="benefits"
        className="section-soft relative py-24 sm:py-32"
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-8">
          <div className="max-w-3xl mb-16">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
              Perché Fisco Facile
            </div>
            <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-tight">
              Quattro motivi per cui <br className="hidden sm:block" />
              <span className="text-zinc-500">funziona davvero.</span>
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {BENEFITS.map((b, i) => {
              const Icon = b.icon;
              return (
                <div
                  key={b.title}
                  className="group bg-[#18181B] border border-[#27272A] rounded-2xl p-7 hover:-translate-y-1 hover:border-zinc-600 transition-all"
                  data-testid={`benefit-card-${i}`}
                >
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-zinc-800/60 text-[#CCFF00] mb-6 group-hover:bg-[#CCFF00]/10 transition-colors">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="font-display text-xl font-bold mb-3">{b.title}</h3>
                  <p className="text-zinc-400 leading-relaxed text-sm">{b.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* GUIDES TABS */}
      <section
        id="guides"
        className="section-soft relative py-24 sm:py-32"
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-8">
          <div className="max-w-3xl mb-12">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
              Cosa c'è dentro
            </div>
            <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-tight">
              28 guide, due pacchetti.
            </h2>
            <p className="mt-6 text-lg text-zinc-400">
              Ogni guida è un PDF dettagliato con screenshot dei portali ufficiali e procedure passo-passo.
            </p>
          </div>

          <div className="flex gap-2 mb-10 p-1.5 bg-[#18181B] border border-[#27272A] rounded-xl w-fit">
            {["privati", "aziende"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-2.5 rounded-lg font-bold text-sm uppercase tracking-wide transition-all ${
                  activeTab === tab
                    ? "bg-[#CCFF00] text-black"
                    : "text-zinc-400 hover:text-white"
                }`}
                data-testid={`tab-${tab}`}
              >
                {PACKAGES[tab].name}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="guides-grid">
            {PACKAGES[activeTab].guides.map((g, i) => (
              <div
                key={g}
                className="flex items-start gap-3 p-4 rounded-xl bg-[#18181B] border border-[#27272A] hover:border-zinc-600 transition-colors"
              >
                <div className="flex-shrink-0 w-7 h-7 rounded-md bg-zinc-800 flex items-center justify-center font-mono text-xs text-[#CCFF00] font-bold">
                  {String(i + 1).padStart(2, "0")}
                </div>
                <span className="text-zinc-300 text-sm leading-relaxed pt-0.5">{g}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="section-soft relative py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-6 sm:px-8">
          <div className="max-w-3xl mb-16 text-center mx-auto">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
              Pacchetti
            </div>
            <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-tight">
              Scegli il tuo. <br />
              <span className="text-zinc-500">Pagamento una tantum.</span>
            </h2>
            <p className="mt-6 text-lg text-zinc-400">
              Nessun abbonamento. Compri una volta, le guide sono tue per sempre.
            </p>
          </div>

          <div className="max-w-4xl mx-auto mb-10 rounded-3xl border border-zinc-800 bg-[#111114] p-6 sm:p-8" data-testid="purchase-access-box">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-3">
              Accesso Cliente
            </div>
            <h3 className="font-display text-2xl sm:text-3xl font-black tracking-tight mb-3">
              Prima di acquistare, scegli le credenziali con cui rientrare<span className="text-[#CCFF00]">.</span>
            </h3>
            <p className="text-zinc-400 leading-relaxed mb-6">
              Inserisci qui email e password: saranno le stesse da usare poi nell&apos;area riservata per
              ritrovare i tuoi acquisti. Se hai gia un account cliente, riusa le stesse credenziali.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                type="email"
                required
                placeholder="Email per l'area riservata"
                value={purchaseAccess.email}
                onChange={(e) => setPurchaseAccess((prev) => ({ ...prev, email: e.target.value }))}
                className="bg-zinc-900 border border-zinc-800 text-white rounded-lg px-4 py-3.5 focus:ring-2 focus:ring-[#CCFF00] focus:border-transparent outline-none transition-all placeholder:text-zinc-600"
                data-testid="purchase-access-email"
              />
              <input
                type="password"
                required
                placeholder="Password area riservata"
                value={purchaseAccess.password}
                onChange={(e) => setPurchaseAccess((prev) => ({ ...prev, password: e.target.value }))}
                className="bg-zinc-900 border border-zinc-800 text-white rounded-lg px-4 py-3.5 focus:ring-2 focus:ring-[#CCFF00] focus:border-transparent outline-none transition-all placeholder:text-zinc-600"
                data-testid="purchase-access-password"
              />
            </div>

            <p className="mt-4 text-xs text-zinc-500">
              Ti basta una password di almeno 8 caratteri. In questo modo puoi rientrare anche senza dipendere dalla mail.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {/* PRIVATI */}
            <PricingCard
              pkg={PACKAGES.privati}
              loading={loading === "stripe:privati"}
              testLoading={loading === "bypass:privati"}
              onBuy={() => handleCheckout("privati")}
              onTestBypass={() => handleTestBypassCheckout("privati")}
              showTestBypass={showLocalTestFeatures}
              testId="pricing-card-privati"
              perks={[
                "16 guide pratiche per privati",
                "PDF aggiornati al 2026",
                "Screenshot portali reali",
                "Download immediato",
                "Supporto via email",
              ]}
            />

            {/* BUNDLE */}
            <PricingCard
              pkg={PACKAGES.bundle}
              loading={loading === "stripe:bundle"}
              testLoading={loading === "bypass:bundle"}
              onBuy={() => handleCheckout("bundle")}
              onTestBypass={() => handleTestBypassCheckout("bundle")}
              showTestBypass={showLocalTestFeatures}
              highlighted
              testId="pricing-card-bundle"
              perks={[
                "Tutte le 28 guide (Privati + Aziende)",
                "Risparmi 22,50€ (sconto del 25%)",
                "Aggiornamenti gratuiti per 12 mesi",
                "Supporto prioritario",
                "Accesso all'area bonus",
              ]}
            />

            {/* AZIENDE */}
            <PricingCard
              pkg={PACKAGES.aziende}
              loading={loading === "stripe:aziende"}
              testLoading={loading === "bypass:aziende"}
              onBuy={() => handleCheckout("aziende")}
              onTestBypass={() => handleTestBypassCheckout("aziende")}
              showTestBypass={showLocalTestFeatures}
              testId="pricing-card-aziende"
              perks={[
                "12 guide avanzate per P.IVA",
                "Fatturazione elettronica step-by-step",
                "Liquidazioni IVA e LIPE",
                "Cassetto Fiscale aziendale",
                "Supporto via email",
              ]}
            />
          </div>

          <p className="text-center mt-10 text-sm text-zinc-500 flex items-center justify-center gap-2">
            <Shield className="w-4 h-4" /> Pagamento sicuro tramite Stripe • Carta di credito, Apple Pay, Google Pay
          </p>

          {/* COUPON INPUT */}
          <div className="mt-12 max-w-md mx-auto">
            {!couponInfo ? (
              <div className="flex gap-2 items-center bg-[#0c0c0e] border border-zinc-800 rounded-lg p-2" data-testid="coupon-box">
                <input
                  type="text"
                  placeholder="Hai un codice sconto?"
                  value={coupon}
                  onChange={(e) => setCoupon(e.target.value.toUpperCase())}
                  className="flex-1 bg-transparent text-white px-3 py-2 outline-none placeholder:text-zinc-600 font-mono text-sm tracking-wider"
                  data-testid="coupon-input"
                />
                <button
                  onClick={checkCoupon}
                  disabled={couponChecking || !coupon.trim()}
                  className="bg-zinc-800 hover:bg-zinc-700 text-white font-bold text-xs uppercase tracking-wide px-4 py-2 rounded-md transition-colors disabled:opacity-50"
                  data-testid="coupon-apply"
                >
                  {couponChecking ? "..." : "Applica"}
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between gap-3 bg-[#CCFF00]/10 border border-[#CCFF00]/40 rounded-lg p-4" data-testid="coupon-applied">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-md bg-[#CCFF00] text-black flex items-center justify-center">
                    <Check className="w-5 h-5" strokeWidth={3} />
                  </div>
                  <div>
                    <div className="font-mono font-bold text-[#CCFF00] text-sm">{couponInfo.code}</div>
                    <div className="text-xs text-zinc-400">Sconto -€{couponInfo.discount_eur} applicato</div>
                  </div>
                </div>
                <button
                  onClick={() => { setCouponInfo(null); setCoupon(""); }}
                  className="text-zinc-500 hover:text-white text-xs font-semibold"
                  data-testid="coupon-remove"
                >
                  Rimuovi
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="section-soft relative py-24 sm:py-32 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 mb-12">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
            Dicono di noi
          </div>
          <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-tight max-w-4xl">
            Storie vere di chi ha smesso di pagare consulenze inutili.
          </h2>
        </div>

        <div className="relative overflow-x-auto sm:overflow-visible testimonial-scroll">
          <div className="flex gap-4 sm:gap-6 marquee-track w-max px-6 sm:px-0 pb-2 sm:pb-0">
            {[...TESTIMONIALS, ...TESTIMONIALS].map((t, i) => (
              <div
                key={i}
                className="w-[85vw] max-w-[360px] flex-shrink-0 p-6 sm:p-7 rounded-2xl bg-[#18181B] border border-[#27272A]"
              >
                <div className="flex gap-0.5 mb-4 text-[#CCFF00]">
                  {[...Array(5)].map((_, j) => (
                    <Star key={j} className="w-4 h-4 fill-current" />
                  ))}
                </div>
                <p className="text-zinc-300 leading-relaxed mb-6">"{t.text}"</p>
                <div className="flex items-center gap-3 pt-4 border-t border-zinc-800">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#CCFF00] to-[#7a9900] flex items-center justify-center font-bold text-black">
                    {t.name[0]}
                  </div>
                  <div>
                    <div className="font-semibold text-sm">{t.name}</div>
                    <div className="text-xs text-zinc-500">
                      {t.role} • {t.city}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* LEAD CAPTURE */}
      <section className="section-soft relative py-24 sm:py-32">
        <div className="max-w-4xl mx-auto px-6 sm:px-8">
          <div className="relative bg-[#18181B] border border-[#27272A] rounded-3xl p-6 sm:p-10 lg:p-14 overflow-hidden">
            <div className="absolute -top-20 -right-20 w-64 h-64 bg-[#CCFF00] opacity-10 blur-[100px] pointer-events-none" />
            <div className="relative text-center">
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">
                Estratto gratuito
              </div>
              <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight leading-tight">
                Provala prima di comprare<span className="text-[#CCFF00]">.</span>
              </h2>
              <p className="mt-4 text-zinc-400 max-w-2xl mx-auto">
                Ti inviamo gratis un estratto di una guida (apertura del Cassetto Fiscale) così vedi com'è scritto. Niente spam.
              </p>

              <form
                onSubmit={handleLeadSubmit}
                className="mt-8 max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-stretch"
                data-testid="lead-form"
              >
                <input
                  type="text"
                  required
                  placeholder="Il tuo nome"
                  value={leadForm.nome}
                  onChange={(e) => setLeadForm((p) => ({ ...p, nome: e.target.value }))}
                  className="bg-zinc-900 border border-zinc-800 text-white rounded-lg px-4 py-3.5 focus:ring-2 focus:ring-[#CCFF00] focus:border-transparent outline-none transition-all placeholder:text-zinc-600 text-left"
                  data-testid="lead-input-nome"
                />
                <input
                  type="email"
                  required
                  placeholder="Email"
                  value={leadForm.email}
                  onChange={(e) => setLeadForm((p) => ({ ...p, email: e.target.value }))}
                  className="bg-zinc-900 border border-zinc-800 text-white rounded-lg px-4 py-3.5 focus:ring-2 focus:ring-[#CCFF00] focus:border-transparent outline-none transition-all placeholder:text-zinc-600 text-left"
                  data-testid="lead-input-email"
                />
                <select
                  required
                  value={leadForm.interesse}
                  onChange={(e) => setLeadForm((p) => ({ ...p, interesse: e.target.value }))}
                  className="bg-zinc-900 border border-zinc-800 text-white rounded-lg px-4 py-3.5 focus:ring-2 focus:ring-[#CCFF00] focus:border-transparent outline-none transition-all text-left"
                  data-testid="lead-input-interesse"
                >
                  <option value="estratto_gratuito">Estratto gratuito</option>
                  <option value="privati">Privati</option>
                  <option value="aziende">Aziende &amp; P.IVA</option>
                  <option value="bundle">Bundle completo</option>
                </select>
                <button
                  type="submit"
                  disabled={leadLoading}
                  className="bg-[#CCFF00] text-black font-bold uppercase tracking-wide px-6 py-3.5 rounded-lg hover:bg-[#B3E600] transition-colors disabled:opacity-60 flex items-center justify-center gap-2 w-full"
                  data-testid="lead-submit"
                >
                  {leadLoading ? "Invio..." : (<><Mail className="w-4 h-4" /> Invia</>)}
                </button>
              </form>
              <p className="mt-4 text-xs text-zinc-600">
                Iscrivendoti accetti la nostra{" "}
                <Link to="/privacy-policy" className="text-zinc-400 underline underline-offset-4 hover:text-white">
                  Privacy Policy
                </Link>
                . Puoi disiscriverti in qualunque momento.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="section-soft relative py-24 sm:py-32">
        <div className="max-w-3xl mx-auto px-6 sm:px-8">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] mb-4">FAQ</div>
          <h2 className="font-display text-4xl sm:text-5xl font-black tracking-tight leading-tight mb-12">
            Domande ricorrenti.
          </h2>

          <div className="space-y-2" data-testid="faq-list">
            {FAQS.map((f, i) => (
              <div key={i} className="border-b border-zinc-800">
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between gap-4 py-6 text-left hover:text-[#CCFF00] transition-colors"
                  data-testid={`faq-item-${i}`}
                >
                  <span className="font-display font-bold text-lg sm:text-xl">{f.q}</span>
                  <ChevronDown
                    className={`w-5 h-5 flex-shrink-0 transition-transform ${
                      openFaq === i ? "rotate-180 text-[#CCFF00]" : "text-zinc-500"
                    }`}
                  />
                </button>
                {openFaq === i && (
                  <div className="pb-6 text-zinc-400 leading-relaxed">{f.a}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="section-soft relative py-24 sm:py-32 overflow-hidden">
        <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-[#CCFF00] opacity-10 blur-[120px] pointer-events-none" />
        <div className="relative max-w-4xl mx-auto px-6 sm:px-8 text-center">
          <h2 className="font-display text-4xl sm:text-6xl lg:text-7xl font-black tracking-tighter leading-[0.95]">
            Basta consulenze a 80€ <br />
            per cose che <span className="text-[#CCFF00]">puoi fare in 10 minuti</span>.
          </h2>
          <button
            onClick={() => scrollTo("pricing")}
            className="mt-12 group bg-[#CCFF00] text-black font-bold uppercase tracking-wide px-10 py-5 rounded-lg hover:bg-[#B3E600] transition-all inline-flex items-center gap-2 text-lg"
            data-testid="final-cta"
          >
            Scegli il pacchetto
            <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="section-soft py-20">
        <div className="max-w-7xl mx-auto px-6 sm:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 sm:gap-4">
                <FiscoFacileLogo size={72} />
                <div className="font-display text-2xl sm:text-3xl font-black tracking-tight">
                  Fisco<span className="text-[#CCFF00]">.</span>{" "}
                  <span className="text-zinc-500">Facile</span>
                </div>
              </div>
              <p className="mt-6 text-zinc-500 max-w-md text-sm leading-relaxed">
                Guide pratiche per gestire la tua fiscalità senza commercialista.
                Aggiornate al 2026 e scritte da chi la burocrazia la conosce.
              </p>
              <Link
                to="/admin"
                className="mt-6 inline-flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-900 px-5 py-3 text-sm font-semibold text-zinc-200 transition-colors hover:border-[#CCFF00] hover:text-white"
                data-testid="footer-admin-link"
              >
                Area Admin
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div>
              <div className="font-bold text-sm uppercase tracking-wider mb-4 text-zinc-400">Prodotto</div>
              <ul className="space-y-2 text-sm text-zinc-500">
                <li><button onClick={() => scrollTo("guides")} className="hover:text-white">Guide</button></li>
                <li><button onClick={() => scrollTo("pricing")} className="hover:text-white">Pacchetti</button></li>
                <li><button onClick={() => scrollTo("faq")} className="hover:text-white">FAQ</button></li>
              </ul>
            </div>

            <div>
              <div className="font-bold text-sm uppercase tracking-wider mb-4 text-zinc-400">Legale</div>
              <ul className="space-y-2 text-sm text-zinc-500">
                <li><Link to="/privacy-policy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link to="/termini-di-servizio" className="hover:text-white">Termini di servizio</Link></li>
                <li><Link to="/cookie-policy" className="hover:text-white">Cookie Policy</Link></li>
              </ul>
            </div>
          </div>

          <div className="mt-14 pt-8 border-t border-zinc-900/60 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs text-zinc-600">
            <div>© 2026 Fisco Facile — P.IVA 00000000000 • Roma</div>
            <div>Made with care for chi vuole capirci qualcosa.</div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function PricingCard({
  pkg,
  loading,
  testLoading = false,
  onBuy,
  onTestBypass,
  showTestBypass = false,
  highlighted,
  perks,
  testId,
}) {
  return (
    <div
      className={`relative rounded-3xl p-8 sm:p-10 transition-all ${
        highlighted
          ? "bg-gradient-to-b from-[#1a1a0a] to-[#18181B] border-[#CCFF00] border-2 shadow-[0_0_60px_rgba(204,255,0,0.12)] lg:-translate-y-4"
          : "bg-[#18181B] border border-[#27272A] hover:border-zinc-600 hover:-translate-y-1"
      }`}
      data-testid={testId}
    >
      {highlighted && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-[#CCFF00] text-black text-xs font-black uppercase tracking-[0.2em] px-4 py-1.5 rounded-full">
          Miglior valore
        </div>
      )}

      {pkg.oldPrice && (
        <div className="absolute top-6 right-6 bg-[#CCFF00] text-black text-xs font-black uppercase tracking-wider px-3 py-1.5 rounded-md transform rotate-3">
          -{Math.round(((pkg.oldPrice - pkg.price) / pkg.oldPrice) * 100)}%
        </div>
      )}

      <div className="mb-6">
        <div className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500 mb-3">
          {pkg.badge}
        </div>
        <h3 className="font-display text-3xl font-black mb-3">{pkg.name}</h3>
        <div className="flex items-baseline gap-3 flex-wrap">
          {pkg.oldPrice && (
            <span className="font-mono text-xl text-zinc-600 line-through">€{pkg.oldPrice}</span>
          )}
          <span className="font-mono text-5xl sm:text-6xl font-black tracking-tighter">
            €{Number.isInteger(pkg.price) ? pkg.price : pkg.price.toFixed(2).replace(".", ",")}
          </span>
          <span className="text-zinc-500 text-sm">una tantum</span>
        </div>
      </div>

      <ul className="space-y-3 mb-8">
        {perks.map((p) => (
          <li key={p} className="flex items-start gap-3 text-zinc-300 text-sm">
            <div className={`flex-shrink-0 mt-0.5 w-5 h-5 rounded-md flex items-center justify-center ${
              highlighted ? "bg-[#CCFF00] text-black" : "bg-zinc-800 text-[#CCFF00]"
            }`}>
              <Check className="w-3.5 h-3.5" strokeWidth={3} />
            </div>
            <span>{p}</span>
          </li>
        ))}
      </ul>

      <button
        onClick={onBuy}
        disabled={loading || testLoading}
        className={`w-full font-bold uppercase tracking-wide py-4 rounded-lg transition-all flex items-center justify-center gap-2 disabled:opacity-60 ${
          highlighted
            ? "bg-[#CCFF00] text-black hover:bg-[#B3E600]"
            : "bg-zinc-800 text-white hover:bg-zinc-700 border border-zinc-700"
        }`}
        data-testid={`buy-button-${pkg.id}`}
      >
        {loading ? "Caricamento..." : (
          <>
            <Zap className="w-4 h-4" /> Acquista ora
          </>
        )}
      </button>

      {showTestBypass && onTestBypass && (
        <button
          onClick={onTestBypass}
          disabled={loading || testLoading}
          className="w-full mt-3 font-semibold py-3 rounded-lg transition-all flex items-center justify-center gap-2 disabled:opacity-60 bg-transparent text-zinc-300 hover:text-white border border-dashed border-zinc-700 hover:border-zinc-500"
          data-testid={`test-bypass-button-${pkg.id}`}
        >
          {testLoading ? "Bypass in corso..." : "Bypass pagamento (test)"}
        </button>
      )}
    </div>
  );
}
