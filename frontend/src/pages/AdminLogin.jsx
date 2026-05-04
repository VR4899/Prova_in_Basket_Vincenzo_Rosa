import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Lock, Loader2 } from "lucide-react";
import {
  clearAdminSession,
  getAdminToken,
  hydrateAdminSession,
  isAdminSessionExpired,
  persistAdminSession,
} from "@/lib/adminSession";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const ADMIN_LOGIN_TIMEOUT_MS = 15000;

export default function AdminLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    hydrateAdminSession();
    if (isAdminSessionExpired()) {
      clearAdminSession();
      return;
    }
    if (getAdminToken()) {
      navigate("/admin/dashboard");
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await axios.post(
        `${API}/admin/login`,
        { email, password },
        { timeout: ADMIN_LOGIN_TIMEOUT_MS },
      );
      persistAdminSession(data.token, data.expires_at);
      toast.success("Accesso effettuato.");
      navigate("/admin/dashboard");
    } catch (err) {
      if (err.code === "ECONNABORTED") {
        toast.error("Il backend impiega troppo a rispondere. Se Render si sta riattivando, attendi un minuto e riprova.");
      } else if (!err.response) {
        toast.error("Il backend pubblico non e raggiungibile al momento.");
      } else if (err.response?.status === 429) {
        toast.error("Troppi tentativi. Aspetta qualche minuto prima di riprovare.");
      } else {
        toast.error("Email o password errata.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-white flex items-center justify-center px-4 sm:px-6" data-testid="admin-login">
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <div className="font-display text-3xl font-black tracking-tight mb-2">
            Fisco<span className="text-[#CCFF00]">.</span> <span className="text-zinc-400 font-medium">Facile</span>
          </div>
          <div className="text-xs font-bold uppercase tracking-[0.3em] text-[#CCFF00]">
            Admin Area
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6 sm:p-8 space-y-5"
          data-testid="admin-login-form"
        >
          <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-zinc-800/60 text-[#CCFF00] mb-4 mx-auto">
            <Lock className="w-7 h-7" />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wider text-zinc-500 font-bold mb-2">
              Email
            </label>
            <input
              type="email"
              required
              autoFocus
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@fiscofacile.it"
              className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-lg px-4 py-3.5 focus:ring-2 focus:ring-[#CCFF00] focus:border-transparent outline-none transition-all placeholder:text-zinc-600"
              data-testid="admin-email-input"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wider text-zinc-500 font-bold mb-2">
              Password
            </label>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-zinc-900 border border-zinc-800 text-white rounded-lg px-4 py-3.5 focus:ring-2 focus:ring-[#CCFF00] focus:border-transparent outline-none transition-all placeholder:text-zinc-600"
              data-testid="admin-password-input"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#CCFF00] text-black font-bold uppercase tracking-wide py-3.5 rounded-lg hover:bg-[#B3E600] transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            data-testid="admin-login-submit"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Accedi"}
          </button>
          <p className="text-xs leading-5 text-zinc-500">
            La sessione admin viene salvata solo per questa finestra e scade automaticamente.
          </p>
        </form>

        <div className="text-center mt-6">
          <a href="/" className="text-xs text-zinc-500 hover:text-white">← Torna al sito</a>
        </div>
      </div>
    </div>
  );
}
