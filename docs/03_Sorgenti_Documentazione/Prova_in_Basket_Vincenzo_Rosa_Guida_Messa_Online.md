# Guida Messa Online Prova in Basket Vincenzo Rosa

## Obiettivo

Portare il progetto online in modo adatto alla vendita reale, non solo al test locale.

## Infrastruttura consigliata

- Frontend React: Vercel
- Backend FastAPI: Render
- Database: MongoDB Atlas
- Email: Resend con dominio verificato
- Pagamenti: Stripe live

## Prima di pubblicare

- `STRIPE_MOCK=false`
- `ALLOW_TEST_BYPASS=false`
- `PUBLIC_SITE_URL=https://www.tuodominio.it`
- `CORS_ORIGINS=https://www.tuodominio.it`
- sostituisci credenziali admin locali
- ruota tutte le chiavi usate nei test

## Variabili minime

### Backend

- `MONGO_URL`
- `DB_NAME`
- `PUBLIC_SITE_URL`
- `CORS_ORIGINS`
- `STRIPE_API_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `RESEND_API_KEY`
- `SENDER_EMAIL`
- `SUPPORT_EMAIL`
- `COMPANY_LEGAL_NAME`
- `VAT_ID`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD_HASH` oppure `ADMIN_PASSWORD`

### Frontend

- `REACT_APP_BACKEND_URL=https://api.tuodominio.it`

## Google Sheets

- imposta `GOOGLE_SHEETS_SPREADSHEET_ID`
- usa `GOOGLE_SERVICE_ACCOUNT_FILE` o `GOOGLE_SERVICE_ACCOUNT_JSON`
- condividi il foglio con il service account come `Editor`

## Controlli finali

1. landing funzionante
2. lead salvati su DB e Google Sheets
3. checkout reale o test controllato
4. mail post-acquisto
5. area riservata via magic link
6. download PDF
7. dashboard admin
8. pulsanti test non visibili
