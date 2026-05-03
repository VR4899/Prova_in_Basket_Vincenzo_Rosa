# Link Pubblico Landing

Per avere un link pubblico stabile della landing, usa:

- `frontend/` su Vercel
- `backend/` su Render

## Frontend su Vercel

1. Crea un nuovo progetto Vercel collegando il repository GitHub.
2. Imposta come Root Directory: `frontend`
3. Build Command: `npm run build`
4. Output Directory: `build`
5. Environment Variables:
   - `REACT_APP_BACKEND_URL=https://tuo-backend.onrender.com`
   - `REACT_APP_ENABLE_TEST_FEATURES=false`
   - `REACT_APP_PUBLIC_SUPPORT_EMAIL=supporto@example.com`

## Backend su Render

1. Collega il repository su Render come Blueprint oppure Web Service
2. Se usi il Blueprint, Render leggerà `render.yaml`
3. Se crei il servizio a mano:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Environment Variables minime:
   - `MONGO_URL`
   - `DB_NAME`
   - `PUBLIC_SITE_URL=https://tuo-frontend.vercel.app`
   - `CORS_ORIGINS=https://tuo-frontend.vercel.app`
   - `ADMIN_EMAIL`
   - `ADMIN_PASSWORD_HASH` oppure `ADMIN_PASSWORD`

## Variabili facoltative ma utili

- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `STRIPE_API_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `RESEND_API_KEY`
- `SENDER_EMAIL`

## Ordine corretto

1. pubblica prima il backend
2. copia l'URL pubblico Render
3. inseriscilo in Vercel come `REACT_APP_BACKEND_URL`
4. pubblica il frontend
5. copia l'URL pubblico Vercel
6. aggiorna su Render:
   - `PUBLIC_SITE_URL`
   - `CORS_ORIGINS`
7. ridistribuisci il backend

## Risultato

Alla fine avrai:

- una landing pubblica tipo `https://nome-progetto.vercel.app`
- un backend pubblico tipo `https://nome-progetto.onrender.com`
