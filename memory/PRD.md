# Fisco Facile — PRD

## Original Problem Statement
Costruire una landing page (selezione collaboratori ZALE MARKETING — Prova in Basket) per il funnel di vendita di un infoprodotto: guide pratiche di fiscalità italiana per Privati (€39), Aziende (€39) e Bundle (€69).

## User Choices (literal)
- Brand: **Fisco Facile**
- Stile: **Moderno fintech** (dark + accent lime #CCFF00)
- Funzionalità: **Solo landing statica** (single page) — poi estesa in Fase 2
- Integrazione Google Sheets: **No** (lead salvati su MongoDB)
- Pagamento: **Stripe** (test mode, key sandbox)
- Email provider Fase 2: **Resend** (tplt e.g. onboarding@resend.dev)
- PDF: **placeholder generati al volo** (reportlab)
- Email post-acquisto: **3 email** (giorno 0/3/7)
- Email lead nurturing: **3 email** (giorno 0/2/4)
- Area download: **/download/{session_id}** protetta
- Admin password: **rootroot**
- Lingua: italiano

## Architecture
- Backend: FastAPI + MongoDB (Motor async) + emergentintegrations Stripe + resend SDK + reportlab + APScheduler
- Frontend: React 19 + react-router-dom v7 + lucide-react + sonner (toast) + Tailwind 3
- All routes prefixed `/api`. Frontend hits `REACT_APP_BACKEND_URL`.

## Personas
1. Privato cittadino italiano che vuole gestire 730/INPS/Cassetto Fiscale senza commercialista
2. Imprenditore/P.IVA che vuole capire IVA, F24, fatturazione elettronica
3. Bundle hunter che prende tutto

## Core Requirements (static)
- Landing single page con: hero, benefici, tabs guide, pricing 3 tiers, testimonials, lead form, FAQ, final CTA, footer
- Lead capture salvato su MongoDB (collection `leads`) + coupon -10€ generato per ogni lead
- Stripe Checkout per i 3 pacchetti con security backend-only pricing + supporto coupon
- Pagina `/success?session_id=...` con polling stato pagamento + bottone download
- Pagina `/download/{session_id}` protetta (verifica payment_status='paid' prima di servire i PDF)
- Generazione PDF placeholder al volo (28 guide, brandizzate Fisco Facile)
- Sequenza email 3+3 (post-acquisto e lead nurturing) con APScheduler dispatcher ogni 60s
- Admin dashboard `/admin` con stats + lead + ordini + email log
- Webhook `/api/webhook/stripe` per ricevere eventi

## Implemented (2026-05-01)
**Fase 1 — MVP Landing**
- Backend `server.py` con endpoint: `/api/packages`, `/api/leads`, `/api/checkout/session`, `/api/checkout/status/{sid}` (con fallback graceful), `/api/webhook/stripe`
- Collection `leads`, `payment_transactions`
- `Landing.jsx` con tutte le sezioni, design fintech dark + lime
- `Success.jsx` con polling

**Fase 2 — Delivery + Email + Admin (2026-05-02)**
- `pdf_service.py`: generate_guide_pdf con reportlab (cover + indice + 6 sezioni)
- `email_service.py`: 6 template HTML (3 post-acquisto + 3 lead), Resend integration via asyncio.to_thread, MongoDB-backed scheduler (collection `email_jobs`)
- Coupon system: collection `coupons`, codice FF+6char, -10€ valido 7gg, applicato in checkout
- Admin auth: `/api/admin/login` con password env, token in `admin_sessions` (12h expiry)
- Admin endpoints: `/api/admin/stats|leads|orders|emails`
- Download protetto: `/api/download/{sid}` (info) + `/api/download/{sid}/file/{cat}/{idx}` (PDF stream)
- Frontend: `Download.jsx`, `AdminLogin.jsx`, `AdminDashboard.jsx` (4 stat cards + 4 tabs)
- Coupon UI nella pricing section (con apply/remove)
- APScheduler: dispatcher ogni 60s, processa email_jobs pending con send_at <= now
- Trigger automatici: lead creato → 1 sent immediato + 2 schedulate, payment paid → 1 sent + 2 schedulate
- Test agent Iter 2: 100% backend (19/19), 100% frontend, scheduler verificato pulito

**Fase 3 — Branding & Polish (2026-05-02)**
- Bundle pricing: €90 → €67,50 con sconto del 25% (badge -25% rotated sulla pricing card)
- Logo `FiscoFacileLogo.jsx` SVG inline in stile Stratton Oakmont: leone araldico (faccia + criniera sunburst + occhi/naso/bocca ruggente) dentro doppio anello con testo curvo "FISCO • FACILE" (top) e "GUIDE FISCALI · ROMA · MMXXVI" (bottom). Animazione di rotazione 25s opzionale.
- Logo grande in hero (320px, ruotante), logo header (48px), logo footer (72px)
- Sfondi sezioni omogeneizzati: rimossi `bg-[#0c0c0e]` alternati, tutte le sezioni ora condividono lo stesso `#09090b` con divisori soft a gradiente lime via classe `.section-soft::before`
- `border-t border-zinc-900` rimossi → transizioni più morbide, ritmo visivo dato da spacing + grid background

## Backlog (P1)
- Logo SVG / mockup grafici dei pacchetti per usare come hero/pricing (richiesto nel brief ZALE)
- Verificare/configurare dominio reale Resend per inviare a chiunque (non solo email verificate)
- Sequenza email marketing pre-acquisto SMS (Twilio?) come canale aggiuntivo

## Backlog (P2)
- A/B test pricing card highlighted
- Analytics (Plausible/PostHog)
- Cookie banner GDPR + Privacy Policy / Termini reali
- Coupon admin UI (creare codici manuali con discount/expiry custom)
- Refactoring server.py in router separati (admin/downloads/leads)
- Cleanup admin sessions scadute (TTL index)
- Unique index su leads.email
- Asincronizzare invio email su lead create (asyncio.create_task)
- Toast su errore download in Download.jsx
- Webhook signature validation strict (in produzione)

## Next Tasks (priority)
1. **Logo & mockup grafici** dei pacchetti (Fase 3 — completare il brief ZALE)
2. **Verifica dominio Resend** per email reali a tutti
3. Polish finale + screenshot per consegna ZALE

## Test data
- Admin: password `rootroot`
- Seed paid order: `cs_test_admin_seed` (bundle €69) → /download/cs_test_admin_seed
