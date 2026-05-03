import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import Landing from "@/pages/Landing";
import Success from "@/pages/Success";
import Download from "@/pages/Download";
import CustomerArea from "@/pages/CustomerArea";
import AdminLogin from "@/pages/AdminLogin";
import AdminDashboard from "@/pages/AdminDashboard";
import PrivacyPolicy from "@/pages/PrivacyPolicy";
import TermsOfService from "@/pages/TermsOfService";
import CookiePolicy from "@/pages/CookiePolicy";

function App() {
  return (
    <div className="App">
      <Toaster
        theme="dark"
        position="top-right"
        toastOptions={{
          style: {
            background: "#18181b",
            border: "1px solid #27272a",
            color: "#fafafa",
          },
        }}
      />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/success" element={<Success />} />
          <Route path="/download/:sessionId" element={<Download />} />
          <Route path="/area-riservata" element={<CustomerArea />} />
          <Route path="/privacy-policy" element={<PrivacyPolicy />} />
          <Route path="/termini-di-servizio" element={<TermsOfService />} />
          <Route path="/cookie-policy" element={<CookiePolicy />} />
          <Route path="/admin" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
