# Prova in Basket Vincenzo Rosa

Progetto full-stack per la vendita di guide fiscali digitali con:

- landing page commerciale
- raccolta lead e sequenza email marketing
- checkout Stripe test o reale
- area riservata cliente con magic link
- dashboard admin
- sincronizzazione opzionale con Google Sheets

## Stack

- Frontend: React 19, CRACO, Tailwind CSS, Radix UI
- Backend: FastAPI, Motor, APScheduler
- Database: MongoDB
- Email: Resend
- Pagamenti: Stripe
- Documenti: ReportLab

## Struttura

```text
backend/   API, PDF, email, checkout, Google Sheets, admin
frontend/  landing, success, download, area riservata, admin
docs/      PDF guida, presentazione, messa online, brand kit
memory/    brief e materiale di progetto
```

## Avvio locale

### Backend

```bash
cd backend
source .venv/bin/activate
uvicorn server:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
HOST=127.0.0.1 PORT=3000 BROWSER=none npm start
```

## URL utili

- Sito: `http://127.0.0.1:3000`
- Area riservata: `http://127.0.0.1:3000/area-riservata`
- Admin: `http://127.0.0.1:3000/admin`
- API: `http://127.0.0.1:8000`

## Configurazione ambiente

1. Copia i file esempio:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Per la pubblicazione puoi partire anche da:

```bash
cp backend/.env.production.example backend/.env
cp frontend/.env.production.example frontend/.env
```

2. Compila almeno:

### Backend

- `MONGO_URL`
- `DB_NAME`
- `PUBLIC_SITE_URL`
- `CORS_ORIGINS`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD_HASH` oppure `ADMIN_PASSWORD`

### Facoltativi ma utili

- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_FILE` oppure `GOOGLE_SERVICE_ACCOUNT_JSON`
- `STRIPE_API_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `RESEND_API_KEY`
- `SENDER_EMAIL`
- `SUPPORT_EMAIL`
- `COMPANY_LEGAL_NAME`
- `VAT_ID`

### Frontend

- `REACT_APP_BACKEND_URL=http://127.0.0.1:8000`
- `REACT_APP_ENABLE_TEST_FEATURES=false`
- `REACT_APP_PUBLIC_SUPPORT_EMAIL=supporto@example.com`

## Modalita test

- `ALLOW_TEST_BYPASS=true` abilita il bypass backend
- `TEST_BYPASS_LOCAL_ONLY=true` limita il bypass checkout alle richieste locali
- `REACT_APP_ENABLE_TEST_FEATURES=true` mostra i pulsanti test solo nel browser locale
- `STRIPE_MOCK=true` evita Stripe reale
- se `RESEND_API_KEY` manca, le email vengono salvate come anteprima in admin

Per una consegna piu vicina alla produzione conviene lasciare a `false`:

- `ALLOW_TEST_BYPASS`
- `REACT_APP_ENABLE_TEST_FEATURES`
- `STRIPE_MOCK`

## Google Sheets

Se configurato, il backend usa tre tab:

- `Leads`
- `Orders`
- `Tracking`

Ricorda di condividere il foglio con l'email del service account come `Editor`.

### Credenziali Google richieste

Per motivi di sicurezza, questa cartella di condivisione non include il file:

- `backend/google-service-account.json`

Quindi Google Sheets non funzionera finche non aggiungi una delle due opzioni:

- `backend/google-service-account.json`
- variabile ambiente `GOOGLE_SERVICE_ACCOUNT_JSON`

Senza una di queste credenziali:

- il sito continua a funzionare
- ma la sincronizzazione di `Leads`, `Orders` e `Tracking` su Google Sheets resta disattivata

## Documentazione inclusa

Dentro `docs/` trovi:

- presentazione del progetto
- manuale d'uso
- avvio rapido
- guida messa online
- guida alla condivisione
- brand kit

## Condivisione sicura

Prima di inviare il progetto:

1. non condividere `backend/.env`
2. non condividere `backend/google-service-account.json`
3. non condividere chiavi Stripe o Resend reali
4. usa solo `.env.example` come template
5. ruota eventuali chiavi già esposte durante i test

## Verifiche fatte

- build frontend ok
- lead -> Google Sheets verificato
- principali endpoint backend verificati
- test backend: 25 passavano già; sistemati i test fragili sui download demo e la validazione del webhook
