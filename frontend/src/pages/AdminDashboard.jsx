import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import {
  Users, ShoppingBag, Mail, Euro, LogOut, Loader2, CheckCircle2, Clock, XCircle, ExternalLink,
} from "lucide-react";
import {
  clearAdminSession,
  getAdminExpiresAt,
  getAdminToken,
  hydrateAdminSession,
  isAdminSessionExpired,
} from "@/lib/adminSession";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

async function fetchAdminData(token) {
  const headers = { "x-admin-token": token };
  const [statsRes, leadsRes, ordersRes, emailsRes] = await Promise.all([
    axios.get(`${API}/admin/stats`, { headers }),
    axios.get(`${API}/admin/leads`, { headers }),
    axios.get(`${API}/admin/orders`, { headers }),
    axios.get(`${API}/admin/emails`, { headers }),
  ]);

  return {
    stats: statsRes.data,
    leads: leadsRes.data.leads,
    orders: ordersRes.data.orders,
    emails: emailsRes.data.emails,
  };
}

export default function AdminDashboard() {
  hydrateAdminSession();
  const navigate = useNavigate();
  const token = getAdminToken();
  const expiresAt = getAdminExpiresAt();
  const [stats, setStats] = useState(null);
  const [tab, setTab] = useState("overview");
  const [leads, setLeads] = useState([]);
  const [orders, setOrders] = useState([]);
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sendingEmailId, setSendingEmailId] = useState(null);
  const [openingPreviewId, setOpeningPreviewId] = useState(null);

  useEffect(() => {
    if (!token || isAdminSessionExpired()) {
      clearAdminSession();
      navigate("/admin");
      return;
    }
    fetchAdminData(token)
      .then((data) => {
        setStats(data.stats);
        setLeads(data.leads);
        setOrders(data.orders);
        setEmails(data.emails);
      })
      .catch((err) => {
        if (err.response?.status === 401) {
          clearAdminSession();
          navigate("/admin");
        } else toast.error("Errore caricamento dati.");
      })
      .finally(() => setLoading(false));
  }, [token, navigate]);

  const refreshAdminData = async () => {
    const data = await fetchAdminData(token);
    setStats(data.stats);
    setLeads(data.leads);
    setOrders(data.orders);
    setEmails(data.emails);
  };

  const handleSendNow = async (emailJob) => {
    if (!token) return;
    setSendingEmailId(emailJob.id);
    try {
      const headers = { "x-admin-token": token };
      const { data } = await axios.post(`${API}/admin/emails/${emailJob.id}/send-now`, {}, { headers });
      await refreshAdminData();

      if (data.status === "sent") {
        toast.success(`Email ${emailJob.kind} inviata subito.`);
      } else if (data.status === "previewed") {
        toast.success(`Email ${emailJob.kind} generata in anteprima.`);
      } else {
        toast.error(`Invio ${emailJob.kind} non riuscito.`);
      }
    } catch (err) {
      if (err.response?.status === 401) {
        clearAdminSession();
        navigate("/admin");
      } else {
        toast.error("Errore durante l'invio manuale.");
      }
    } finally {
      setSendingEmailId(null);
    }
  };

  const handleOpenPreview = async (emailJob) => {
    if (!token) return;
    const previewWindow = window.open("", "_blank", "noopener,noreferrer");
    setOpeningPreviewId(emailJob.id);

    try {
      const headers = { "x-admin-token": token };
      const { data } = await axios.post(`${API}/admin/emails/${emailJob.id}/preview-link`, {}, { headers });

      if (previewWindow) {
        previewWindow.location = data.preview_url;
      } else {
        window.open(data.preview_url, "_blank", "noopener,noreferrer");
      }
    } catch (err) {
      if (previewWindow) previewWindow.close();
      if (err.response?.status === 401) {
        clearAdminSession();
        navigate("/admin");
      } else {
        toast.error("Impossibile aprire l'anteprima dell'email.");
      }
    } finally {
      setOpeningPreviewId(null);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await axios.post(`${API}/admin/logout`, {}, { headers: { "x-admin-token": token } });
      }
    } catch {
      // Anche se il logout server-side fallisce, puliamo la sessione locale.
    }
    clearAdminSession();
    navigate("/admin");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-[#CCFF00] animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090b] text-white" data-testid="admin-dashboard">
      <header className="border-b border-zinc-900 sticky top-0 bg-[#09090b]/80 backdrop-blur-md z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-8 py-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 sm:gap-4 min-w-0">
            <span className="font-display text-xl font-black tracking-tight">
              Fisco<span className="text-[#CCFF00]">.</span> <span className="text-zinc-400 font-medium">Facile</span>
            </span>
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#CCFF00] px-2 py-1 rounded-md bg-zinc-900 border border-zinc-800">
              Admin
            </span>
            {expiresAt && (
              <span className="hidden sm:inline text-[11px] text-zinc-500">
                Sessione attiva fino a {expiresAt.slice(11, 16)}
              </span>
            )}
          </div>
          <button
            onClick={logout}
            className="text-zinc-400 hover:text-white text-sm flex items-center gap-2 transition-colors"
            data-testid="admin-logout"
          >
            <LogOut className="w-4 h-4" /> Esci
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-8 py-8 sm:py-12">
        {/* STATS CARDS */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          <StatCard icon={Users} label="Lead totali" value={stats.leads} testId="stat-leads" />
          <StatCard icon={ShoppingBag} label="Ordini pagati" value={stats.orders_paid} testId="stat-orders" />
          <StatCard icon={Euro} label="Fatturato" value={`€${stats.revenue_eur.toFixed(2)}`} testId="stat-revenue" />
          <StatCard
            icon={Mail}
            label="Email inviate"
            value={stats.emails_sent}
            sub={`${stats.emails_pending} in coda • ${stats.emails_previewed || 0} anteprime`}
            testId="stat-emails"
          />
        </div>

        {/* TABS */}
        <div className="flex gap-2 mb-8 p-1.5 bg-[#18181B] border border-[#27272A] rounded-xl w-full overflow-x-auto">
          {[
            ["overview", "Overview"],
            ["leads", `Lead (${leads.length})`],
            ["orders", `Ordini (${orders.length})`],
            ["emails", `Email (${emails.length})`],
          ].map(([id, label]) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`px-5 py-2 rounded-lg font-bold text-sm uppercase tracking-wide transition-all whitespace-nowrap ${
                tab === id ? "bg-[#CCFF00] text-black" : "text-zinc-400 hover:text-white"
              }`}
              data-testid={`tab-${id}`}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Panel title="Ultimi lead">
              {leads.slice(0, 5).map((l) => (
                <Row key={l.id} left={l.nome} right={l.email} sub={l.created_at?.slice(0, 16).replace("T", " ")} />
              ))}
              {leads.length === 0 && <Empty>Ancora nessun lead.</Empty>}
            </Panel>
            <Panel title="Ultimi ordini">
              {orders.slice(0, 5).map((o) => (
                <Row
                  key={o.session_id}
                  left={o.package_name}
                  right={`€${o.amount?.toFixed(2)}`}
                  sub={o.email || "—"}
                  badge={
                    o.payment_status === "paid"
                      ? <Badge color="green"><CheckCircle2 className="w-3 h-3" /> Pagato</Badge>
                      : <Badge color="zinc"><Clock className="w-3 h-3" /> {o.status || o.payment_status}</Badge>
                  }
                />
              ))}
              {orders.length === 0 && <Empty>Ancora nessun ordine.</Empty>}
            </Panel>
          </div>
        )}

        {tab === "leads" && (
          <Panel title="Tutti i lead">
            <table className="w-full min-w-[760px] text-sm" data-testid="leads-table">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
                  <th className="py-3">Nome</th>
                  <th className="py-3">Email</th>
                  <th className="py-3">Coupon</th>
                  <th className="py-3">Interesse</th>
                  <th className="py-3 text-right">Data</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((l) => (
                  <tr key={l.id} className="border-b border-zinc-900 hover:bg-zinc-900/40">
                    <td className="py-3 font-semibold">{l.nome}</td>
                    <td className="py-3 text-zinc-400 font-mono text-xs">{l.email}</td>
                    <td className="py-3">
                      <span className="font-mono text-xs px-2 py-1 rounded bg-zinc-800 text-[#CCFF00]">
                        {l.coupon_code || "—"}
                      </span>
                    </td>
                    <td className="py-3 text-zinc-400">{l.interesse}</td>
                    <td className="py-3 text-right text-zinc-500 text-xs font-mono">
                      {l.created_at?.slice(0, 16).replace("T", " ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {leads.length === 0 && <Empty>Nessun lead ancora.</Empty>}
          </Panel>
        )}

        {tab === "orders" && (
          <Panel title="Tutti gli ordini">
            <table className="w-full min-w-[760px] text-sm" data-testid="orders-table">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
                  <th className="py-3">Pacchetto</th>
                  <th className="py-3">Email</th>
                  <th className="py-3">Coupon</th>
                  <th className="py-3 text-right">Importo</th>
                  <th className="py-3 text-center">Stato</th>
                  <th className="py-3 text-right">Data</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.session_id} className="border-b border-zinc-900 hover:bg-zinc-900/40">
                    <td className="py-3 font-semibold">{o.package_name}</td>
                    <td className="py-3 text-zinc-400 font-mono text-xs">{o.email || "—"}</td>
                    <td className="py-3">
                      {o.coupon ? (
                        <span className="font-mono text-xs px-2 py-1 rounded bg-zinc-800 text-[#CCFF00]">{o.coupon}</span>
                      ) : (
                        <span className="text-zinc-600">—</span>
                      )}
                    </td>
                    <td className="py-3 text-right font-mono font-bold">€{o.amount?.toFixed(2)}</td>
                    <td className="py-3 text-center">
                      {o.payment_status === "paid"
                        ? <Badge color="green"><CheckCircle2 className="w-3 h-3" /> Pagato</Badge>
                        : <Badge color="zinc"><Clock className="w-3 h-3" /> {o.payment_status}</Badge>}
                    </td>
                    <td className="py-3 text-right text-zinc-500 text-xs font-mono">
                      {o.created_at?.slice(0, 16).replace("T", " ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {orders.length === 0 && <Empty>Nessun ordine ancora.</Empty>}
          </Panel>
        )}

        {tab === "emails" && (
          <Panel title="Email schedulate / inviate">
            <table className="w-full min-w-[980px] text-sm" data-testid="emails-table">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider text-zinc-500 border-b border-zinc-800">
                  <th className="py-3">Tipo</th>
                  <th className="py-3">Destinatario</th>
                  <th className="py-3">Oggetto</th>
                  <th className="py-3 text-center">Stato</th>
                  <th className="py-3">Anteprima</th>
                  <th className="py-3 text-center">Azione</th>
                  <th className="py-3 text-right">Invio prog.</th>
                </tr>
              </thead>
              <tbody>
                {emails.map((e) => (
                  <tr key={e.id} className="border-b border-zinc-900 hover:bg-zinc-900/40">
                    <td className="py-3">
                      <span className="font-mono text-xs px-2 py-1 rounded bg-zinc-800">{e.kind}</span>
                    </td>
                    <td className="py-3 text-zinc-400 font-mono text-xs">{e.to}</td>
                    <td className="py-3 text-zinc-300 max-w-md truncate">{e.subject}</td>
                    <td className="py-3 text-center">
                      {e.status === "sent"
                        ? <Badge color="green"><CheckCircle2 className="w-3 h-3" /> Inviata</Badge>
                        : e.status === "previewed"
                        ? <Badge color="amber"><Mail className="w-3 h-3" /> Anteprima</Badge>
                        : e.status === "failed"
                        ? <Badge color="red"><XCircle className="w-3 h-3" /> Errore</Badge>
                        : <Badge color="zinc"><Clock className="w-3 h-3" /> Pending</Badge>}
                    </td>
                    <td className="py-3">
                      {e.preview_available ? (
                        <button
                          type="button"
                          onClick={() => handleOpenPreview(e)}
                          disabled={openingPreviewId === e.id}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-[#CCFF00] hover:text-white transition-colors"
                        >
                          {openingPreviewId === e.id ? (
                            <><Loader2 className="w-3 h-3 animate-spin" /> Apro...</>
                          ) : (
                            <><ExternalLink className="w-3 h-3" /> Apri</>
                          )}
                        </button>
                      ) : (
                        <span className="text-zinc-600">—</span>
                      )}
                    </td>
                    <td className="py-3 text-center">
                      {e.send_now_available ? (
                        <button
                          type="button"
                          onClick={() => handleSendNow(e)}
                          disabled={sendingEmailId === e.id}
                          className="inline-flex items-center gap-2 rounded-lg border border-[#CCFF00]/30 bg-[#CCFF00]/10 px-3 py-2 text-xs font-bold uppercase tracking-wide text-[#CCFF00] hover:bg-[#CCFF00] hover:text-black transition-colors disabled:opacity-60 disabled:hover:bg-[#CCFF00]/10 disabled:hover:text-[#CCFF00]"
                          data-testid={`email-send-now-${e.id}`}
                        >
                          {sendingEmailId === e.id ? (
                            <><Loader2 className="w-3 h-3 animate-spin" /> Invio...</>
                          ) : (
                            "Invia ora"
                          )}
                        </button>
                      ) : (
                        <span className="text-zinc-600">—</span>
                      )}
                    </td>
                    <td className="py-3 text-right text-zinc-500 text-xs font-mono">
                      {e.send_at?.slice(0, 16).replace("T", " ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {emails.length === 0 && <Empty>Nessuna email ancora.</Empty>}
          </Panel>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub, testId }) {
  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-2xl p-5 sm:p-6" data-testid={testId}>
      <div className="flex items-center justify-between mb-4">
        <Icon className="w-5 h-5 text-[#CCFF00]" />
      </div>
      <div className="font-mono text-3xl font-black tracking-tighter">{value}</div>
      <div className="text-xs text-zinc-500 uppercase tracking-wider mt-2">{label}</div>
      {sub && <div className="text-xs text-zinc-600 mt-1">{sub}</div>}
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-2xl p-4 sm:p-6 overflow-x-auto">
      <h3 className="font-display text-xl font-bold mb-5">{title}</h3>
      {children}
    </div>
  );
}

function Row({ left, right, sub, badge }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-3 border-b border-zinc-900 last:border-0">
      <div className="min-w-0 flex-1">
        <div className="font-semibold truncate">{left}</div>
        {sub && <div className="text-xs text-zinc-500 mt-0.5 truncate">{sub}</div>}
      </div>
      {badge && <div className="sm:self-auto">{badge}</div>}
      <div className="text-zinc-400 text-sm font-mono whitespace-nowrap">{right}</div>
    </div>
  );
}

function Badge({ color, children }) {
  const colors = {
    green: "bg-[#CCFF00]/10 text-[#CCFF00] border-[#CCFF00]/30",
    amber: "bg-amber-500/10 text-amber-300 border-amber-500/30",
    red: "bg-red-500/10 text-red-400 border-red-500/30",
    zinc: "bg-zinc-800 text-zinc-400 border-zinc-700",
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-bold uppercase tracking-wider ${colors[color]}`}>
      {children}
    </span>
  );
}

function Empty({ children }) {
  return <div className="text-center text-zinc-500 py-12 text-sm">{children}</div>;
}
