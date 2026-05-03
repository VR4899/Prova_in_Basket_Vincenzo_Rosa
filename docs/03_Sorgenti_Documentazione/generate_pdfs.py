from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ACCENT = HexColor("#CCFF00")
DARK = HexColor("#09090B")
SURFACE = HexColor("#18181B")
LINE = HexColor("#27272A")
MUTED = HexColor("#71717A")
PANEL = HexColor("#F4F4F5")
TEXT = HexColor("#18181B")
LIGHT_TEXT = HexColor("#D4D4D8")

SOURCE_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = Path(__file__).resolve().parents[1]
ROOT = DOCS_ROOT / "01_PDF_Principali"
PROJECT_ROOT = DOCS_ROOT.parent
PROJECT_NAME = "Prova in Basket Vincenzo Rosa"
PROJECT_DIR = str(PROJECT_ROOT)
SITE_URL = "http://127.0.0.1:3000"
API_URL = "http://127.0.0.1:8000"
ADMIN_LOGIN = "admin@fiscofacile.it / rootroot"


def styles():
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=ACCENT,
            spaceAfter=10,
            alignment=TA_LEFT,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=31,
            textColor=white,
            spaceAfter=14,
            alignment=TA_LEFT,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11.5,
            leading=17,
            textColor=LIGHT_TEXT,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=TEXT,
            spaceBefore=8,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=TEXT,
            spaceBefore=6,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=14.5,
            textColor=TEXT,
            spaceAfter=7,
        ),
        "body_muted": ParagraphStyle(
            "body_muted",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=14.5,
            textColor=MUTED,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.6,
            leading=12,
            textColor=MUTED,
            spaceAfter=5,
        ),
        "card_title": ParagraphStyle(
            "card_title",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=white,
        ),
        "card_value": ParagraphStyle(
            "card_value",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=12,
            textColor=LIGHT_TEXT,
        ),
    }


def draw_cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, A4[1] - 0.45 * cm, A4[0], 0.45 * cm, fill=1, stroke=0)
    canvas.setFillColor(SURFACE)
    canvas.roundRect(2 * cm, 2 * cm, A4[0] - 4 * cm, 2.9 * cm, 16, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(2.3 * cm, 3.32 * cm, "Fisco")
    canvas.setFillColor(ACCENT)
    canvas.drawString(4.25 * cm, 3.32 * cm, ".")
    canvas.setFillColor(white)
    canvas.drawString(4.7 * cm, 3.32 * cm, "Facile")
    canvas.setFillColor(HexColor("#A1A1AA"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2.3 * cm, 2.58 * cm, f"{PROJECT_NAME} · documentazione aggiornata e pronta alla consegna.")
    canvas.restoreState()


def draw_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, A4[1] - 1.1 * cm, A4[0], 1.1 * cm, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(2 * cm, A4[1] - 0.72 * cm, "PROVA IN BASKET VINCENZO ROSA")
    canvas.setFillColor(white)
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 0.72 * cm, f"Pag. {doc.page}")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(2 * cm, 0.85 * cm, "Documentazione coerente con il progetto locale e con le ultime modifiche.")
    canvas.restoreState()


def accent_bullet(text, s):
    return Paragraph(f'<font color="#CCFF00">&#9679;</font> {text}', s["body"])


def cover_meta(rows, s):
    data = [[Paragraph(title, s["card_title"]), Paragraph(value, s["card_value"])] for title, value in rows]
    table = Table(data, colWidths=[5.1 * cm, 10.2 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return table


def info_box(title, body, s, accent=ACCENT):
    table = Table(
        [[Paragraph(title, s["h2"])], [Paragraph(body, s["body"])]],
        colWidths=[15.3 * cm],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 1, accent),
        ("LINEBEFORE", (0, 0), (0, -1), 6, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def build_manual(title, subtitle, meta_rows, sections, out_name, references=None):
    s = styles()
    path = ROOT / out_name
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.1 * cm,
        bottomMargin=1.8 * cm,
        title=title,
        author="Codex per Vincenzo Rosa",
    )
    story = [
        Spacer(1, 3.1 * cm),
        Paragraph(PROJECT_NAME.upper(), s["cover_kicker"]),
        Paragraph(title, s["cover_title"]),
        Paragraph(subtitle, s["cover_subtitle"]),
        cover_meta(meta_rows, s),
        PageBreak(),
    ]

    for section in sections:
        story.append(Paragraph(section["title"], s["h1"]))
        if section.get("intro"):
            story.append(Paragraph(section["intro"], s["body_muted"]))
        for item in section.get("bullets", []):
            story.append(accent_bullet(item, s))
        for para in section.get("paragraphs", []):
            story.append(Paragraph(para, s["body"]))
        for box in section.get("boxes", []):
            story.append(info_box(box["title"], box["body"], s, accent=box.get("accent", ACCENT)))
            story.append(Spacer(1, 0.25 * cm))
        if section.get("page_break"):
            story.append(PageBreak())

    if references:
        story.extend([
            PageBreak(),
            Paragraph("Riferimenti utili", s["h1"]),
            Paragraph("Link e riferimenti pratici per deploy, servizi esterni e condivisione.", s["body_muted"]),
        ])
        for ref in references:
            story.append(Paragraph(ref, s["small"]))

    doc.build(story, onFirstPage=draw_cover, onLaterPages=draw_page)
    return path


def build_presentation():
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    sections = [
        {
            "title": "1. Cos'e il progetto",
            "intro": "Fisco Facile e una piattaforma full-stack per vendere guide fiscali digitali con funnel di lead generation, checkout, email e area clienti.",
            "bullets": [
                "Landing page commerciale con CTA, coupon e raccolta lead.",
                "Checkout Stripe test o reale, con bypass locale opzionale.",
                "Area riservata cliente con accesso via email + password e fallback via mail.",
                "Dashboard admin per lead, ordini, email e statistiche.",
                "Sincronizzazione opzionale con Google Sheets per Leads, Orders e Tracking.",
            ],
        },
        {
            "title": "2. Stack e componenti",
            "bullets": [
                "Frontend: React 19, CRACO, Tailwind, Radix UI.",
                "Backend: FastAPI, Motor, APScheduler.",
                "Database: MongoDB.",
                "Email: Resend con anteprima locale se manca la chiave.",
                "Documenti: PDF generati lato backend con ReportLab.",
            ],
            "boxes": [
                {
                    "title": "Flusso principale",
                    "body": "Lead dalla landing -> email/coupon -> checkout -> conferma acquisto -> area riservata -> download PDF -> dashboard admin e fogli Google per il monitoraggio.",
                }
            ],
        },
        {
            "title": "3. Stato attuale",
            "bullets": [
                "Frontend e backend avviabili in locale su 127.0.0.1.",
                "Google Sheets collegato e verificato sul tab Leads.",
                "Login admin con email + password e protezioni anti brute-force.",
                "Area riservata con login cliente email + password, fallback via magic link e logout reale.",
                "Pulsanti test presenti solo in locale e disattivabili per la condivisione finale.",
            ],
        },
        {
            "title": "4. Cosa consegnare",
            "bullets": [
                "Codice progetto senza file .env e senza credenziali reali.",
                "README e file .env.example aggiornati.",
                "PDF di uso, avvio, messa online, presentazione e condivisione.",
                "Brand kit con logo, mockup e grafiche SVG.",
            ],
        },
    ]
    build_manual(
        title="Presentazione Progetto Fisco Facile",
        subtitle="Sintesi professionale del progetto, del suo funzionamento e del materiale pronto per condivisione o vendita.",
        meta_rows=[
            ("Progetto", PROJECT_NAME),
            ("Sito locale", SITE_URL),
            ("API locale", API_URL),
            ("Aggiornato il", today),
        ],
        sections=sections,
        out_name="Prova_in_Basket_Vincenzo_Rosa_Presentazione_Progetto.pdf",
    )


def build_user_manual():
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    sections = [
        {
            "title": "1. Accesso al sito",
            "intro": "L'applicazione gira in locale con sito pubblico, area riservata e dashboard admin.",
            "bullets": [
                f"Apri il sito su {SITE_URL}.",
                "Per l'area riservata usa /area-riservata.",
                "Per l'admin usa /admin.",
            ],
            "boxes": [
                {"title": "URL locali principali", "body": f"Sito: {SITE_URL} | Area riservata: {SITE_URL}/area-riservata | Admin: {SITE_URL}/admin"}
            ],
        },
        {
            "title": "2. Form lead e marketing",
            "intro": "La landing raccoglie nome, email e interesse e salva il lead anche su Google Sheets se configurato.",
            "bullets": [
                "Vai alla sezione Estratto gratuito.",
                "Compila nome, email e interesse.",
                "Dopo Invia il lead finisce in Admin > Leads e nel tab Google Sheets Leads.",
                "Parte subito la prima mail marketing; le successive vengono pianificate.",
            ],
        },
        {
            "title": "3. Acquisto e modalita test",
            "intro": "Puoi usare sia il checkout Stripe test sia il bypass locale di sviluppo.",
            "bullets": [
                "Prima dell'acquisto il cliente inserisce email e password che usera poi nell'area riservata.",
                "Acquista ora apre Stripe test quando la configurazione e attiva.",
                "Bypass pagamento (test) crea un ordine pagato senza passare da Stripe.",
                "Dopo il pagamento arrivi alla pagina Success e poi alla pagina download.",
            ],
        },
        {
            "title": "4. Area riservata cliente",
            "intro": "L'area riservata serve per vedere gli ordini e scaricare le guide acquistate.",
            "bullets": [
                "Inserisci email e password scelte durante l'acquisto per entrare direttamente.",
                "Se il servizio email e attivo, puoi comunque richiedere un link monouso come fallback.",
                "In locale puoi usare Accedi in test se il flag di test e attivo.",
                "Dopo il login ottieni una sessione protetta e puoi chiuderla con Esci.",
            ],
        },
        {
            "title": "5. Area admin",
            "intro": "La dashboard admin centralizza lead, ordini, email e monitoraggio operativo.",
            "bullets": [
                f"Credenziali locali correnti: {ADMIN_LOGIN}.",
                "Dopo il login trovi statistiche, Leads, Orders ed Email.",
                "Le email possono risultare sent, previewed o pending.",
                "Le email pianificate si possono forzare con Invia ora dalla dashboard.",
            ],
            "page_break": True,
        },
        {
            "title": "6. Google Sheets",
            "intro": "Il foglio Google e una vista operativa esterna al sito, utile per controllo commerciale e tracciamento funnel.",
            "bullets": [
                "Leads contiene contatti, interesse e coupon.",
                "Orders contiene ordini, importi, email e stato pagamento.",
                "Tracking contiene eventi di funnel, login cliente, email e webhook.",
                "Il backend crea i tab automaticamente se non esistono.",
            ],
            "boxes": [
                {
                    "title": "Accesso al foglio",
                    "body": "Per il team basta il normale link condiviso del Google Sheet. Per il backend serve invece il service account Google configurato nel file backend/google-service-account.json oppure nella variabile GOOGLE_SERVICE_ACCOUNT_JSON.",
                }
            ],
        },
        {
            "title": "7. Problemi comuni",
            "intro": "Queste sono le anomalie piu frequenti in locale e come leggerle correttamente.",
            "boxes": [
                {"title": "Il frontend dice che il backend non risponde", "body": "Verifica che il backend sia acceso su 127.0.0.1:8000 e che frontend/.env punti a http://127.0.0.1:8000."},
                {"title": "Non vedo i pulsanti test", "body": "Compaiono solo nella landing e solo in locale, quando apri il sito da localhost o 127.0.0.1.", "accent": HexColor("#A3A3A3")},
                {"title": "Google Sheets non si aggiorna", "body": "Controlla che il backend sia stato riavviato dopo le modifiche e che il foglio sia condiviso con il service account come Editor."},
            ],
        },
    ]
    build_manual(
        title="Manuale d'Uso del sito",
        subtitle="Istruzioni operative aggiornate per usare il progetto in locale, testare lead, acquisti, area riservata, admin e Google Sheets.",
        meta_rows=[
            ("Progetto", PROJECT_NAME),
            ("Sito", SITE_URL),
            ("Admin", ADMIN_LOGIN),
            ("Aggiornato il", today),
        ],
        sections=sections,
        out_name="Prova_in_Basket_Vincenzo_Rosa_Manuale_Uso.pdf",
    )


def build_startup_sheet():
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    sections = [
        {
            "title": "1. Cartella progetto",
            "intro": "Questa e la cartella corretta da usare in Visual Studio Code o nel terminale.",
            "boxes": [{"title": "Percorso progetto", "body": PROJECT_DIR}],
        },
        {
            "title": "2. Avvio backend",
            "intro": "Apri un primo terminale e lancia l'API FastAPI.",
            "paragraphs": [
                f'cd "{PROJECT_DIR}/backend"',
                "source .venv/bin/activate",
                "uvicorn server:app --host 127.0.0.1 --port 8000",
            ],
            "boxes": [
                {
                    "title": "Se la porta 8000 e occupata",
                    "body": "Significa che il backend e gia attivo. In quel caso chiudi il processo precedente oppure usa direttamente quello gia acceso.",
                    "accent": HexColor("#A3A3A3"),
                }
            ],
        },
        {
            "title": "3. Avvio frontend",
            "intro": "Apri un secondo terminale e avvia l'interfaccia React sul loopback locale.",
            "paragraphs": [
                f'cd "{PROJECT_DIR}/frontend"',
                "HOST=127.0.0.1 PORT=3000 BROWSER=none npm start",
            ],
            "boxes": [
                {
                    "title": "Se la porta 3000 e occupata",
                    "body": "Controlla se c'e ancora un vecchio processo Node acceso. Se stavi usando la cartella con il vecchio nome Baket, chiudilo prima di ripartire.",
                }
            ],
        },
        {
            "title": "4. URL e accessi",
            "bullets": [
                f"Sito: {SITE_URL}",
                f"Area riservata: {SITE_URL}/area-riservata",
                f"Admin: {SITE_URL}/admin",
                f"Backend API: {API_URL}",
                f"Credenziali admin locali: {ADMIN_LOGIN}",
            ],
        },
        {
            "title": "5. Test rapido",
            "bullets": [
                "Apri la home e verifica che la landing si carichi.",
                "Compila un lead di prova dal form Estratto gratuito.",
                "Controlla Leads in admin e nel Google Sheet.",
                "Se stai testando la vendita, usa Acquista ora o Bypass pagamento (test).",
                "Controlla area riservata con email + password, download e tab Email.",
            ],
        },
    ]
    build_manual(
        title="Avvio rapido del progetto",
        subtitle="Foglio operativo breve per aprire il progetto, avviare backend e frontend e verificare il funzionamento minimo.",
        meta_rows=[
            ("Progetto", PROJECT_NAME),
            ("Frontend", SITE_URL),
            ("Backend", API_URL),
            ("Aggiornato il", today),
        ],
        sections=sections,
        out_name="Prova_in_Basket_Vincenzo_Rosa_Avvio_Rapido.pdf",
    )


def build_launch_manual():
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    sections = [
        {
            "title": "1. Obiettivo del deploy",
            "intro": "Questa guida serve a trasformare il progetto da ambiente locale a prodotto pubblicabile e vendibile.",
            "bullets": [
                "Frontend consigliato: Vercel.",
                "Backend consigliato: Render.",
                "Database consigliato: MongoDB Atlas.",
                "Email: Resend con dominio verificato.",
                "Pagamenti: Stripe live mode.",
            ],
        },
        {
            "title": "2. Modifiche obbligatorie prima della pubblicazione",
            "bullets": [
                "Imposta STRIPE_MOCK=false.",
                "Imposta ALLOW_TEST_BYPASS=false.",
                "Configura PUBLIC_SITE_URL con il dominio finale.",
                "Configura CORS_ORIGINS con il dominio frontend reale.",
                "Sostituisci ADMIN_EMAIL e ADMIN_PASSWORD con credenziali forti o con un hash admin.",
                "Ruota le chiavi usate nei test locali prima di qualsiasi consegna esterna.",
            ],
            "page_break": True,
        },
        {
            "title": "3. Variabili ambiente essenziali",
            "boxes": [
                {
                    "title": "Backend minimo",
                    "body": "MONGO_URL, DB_NAME, PUBLIC_SITE_URL, CORS_ORIGINS, STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, RESEND_API_KEY, SENDER_EMAIL, SUPPORT_EMAIL, COMPANY_LEGAL_NAME, VAT_ID, ADMIN_EMAIL, ADMIN_PASSWORD_HASH oppure ADMIN_PASSWORD.",
                },
                {
                    "title": "Frontend minimo",
                    "body": "REACT_APP_BACKEND_URL=https://api.tuodominio.it",
                },
            ],
        },
        {
            "title": "4. Google Sheets in produzione",
            "bullets": [
                "Mantieni il service account fuori dal repository.",
                "Condividi il foglio solo con chi deve leggerlo o modificarlo.",
                "Verifica che i tab Leads, Orders e Tracking si popolino anche dopo il deploy pubblico.",
            ],
        },
        {
            "title": "5. Checklist finale pre-vendita",
            "bullets": [
                "Landing corretta su desktop e mobile.",
                "Lead salvati su database e Google Sheets.",
                "Checkout reale con Stripe live o test controllato.",
                "Login area riservata con email + password funzionante, con eventuale fallback email.",
                "Download PDF senza errori.",
                "Dashboard admin raggiungibile e protetta.",
                "Pulsanti test non visibili in produzione.",
            ],
        },
    ]
    build_manual(
        title="Guida messa online e vendita",
        subtitle="Checklist di deploy, configurazione e sicurezza per condividere o vendere il progetto senza lasciare scorciatoie di test aperte.",
        meta_rows=[
            ("Frontend", "Vercel"),
            ("Backend", "Render"),
            ("Database", "MongoDB Atlas"),
            ("Aggiornato il", today),
        ],
        sections=sections,
        out_name="Prova_in_Basket_Vincenzo_Rosa_Guida_Messa_Online.pdf",
        references=[
            "Vercel - Create React App: https://vercel.com/docs/frameworks/create-react-app",
            "Render - Deploy a FastAPI App: https://render.com/docs/deploy-fastapi",
            "MongoDB Atlas - Connect via Drivers: https://www.mongodb.com/docs/atlas/driver-connection/",
            "Google Sheets API - Quickstart Python: https://developers.google.com/workspace/sheets/api/quickstart/python",
            "Stripe - API keys: https://docs.stripe.com/keys",
            "Resend - Managing Domains: https://resend.com/docs/dashboard/domains/introduction",
        ],
    )


def build_sharing_manual():
    today = datetime.now().strftime("%d/%m/%Y %H:%M")
    sections = [
        {
            "title": "1. Cosa inviare",
            "intro": "Per condividere il progetto in modo professionale e pulito non devi spedire tutto alla cieca.",
            "bullets": [
                "Cartella del progetto senza file .env e senza chiavi reali.",
                "README aggiornato.",
                "backend/.env.example e frontend/.env.example.",
                "Cartella docs con PDF, guide e brand kit.",
                "Eventuale link al repository GitHub privato o pubblico.",
            ],
        },
        {
            "title": "2. Cosa NON inviare",
            "bullets": [
                "backend/.env",
                "frontend/.env se contiene URL o chiavi private non definitive",
                "backend/google-service-account.json",
                "node_modules, .venv, build, cache locali",
                "chiavi Stripe, Resend o credenziali admin usate nei test",
            ],
            "boxes": [
                {
                    "title": "Segreti da ruotare prima della consegna",
                    "body": "Chiave Stripe test condivisa in chat, chiave Resend condivisa in chat, eventuali credenziali admin di default e qualsiasi JSON di service account gia usato in locale.",
                    "accent": HexColor("#A3A3A3"),
                }
            ],
        },
        {
            "title": "3. Preparazione consigliata",
            "bullets": [
                "Controlla che .gitignore escluda i file sensibili.",
                "Usa solo i file .env.example come modello.",
                "Rinomina eventuali documenti finali con il nome del progetto, come gia fatto in docs.",
                "Verifica il frontend con REACT_APP_BACKEND_URL allineato a 127.0.0.1 o al dominio pubblico finale.",
            ],
        },
        {
            "title": "4. Come inviarlo bene",
            "paragraphs": [
                "Opzione 1: GitHub. E la migliore se chi riceve deve modificare il progetto.",
                "Opzione 2: cartella compressa .zip. E utile se devi fare una consegna diretta.",
                "Opzione 3: repository + PDF guida + link demo online. E la forma piu professionale.",
            ],
            "boxes": [
                {
                    "title": "Formula di consegna consigliata",
                    "body": "Invia il repository o lo zip del progetto pulito insieme a: Presentazione Progetto, Manuale d'Uso, Avvio rapido e Guida messa online. In questo modo chi riceve ha codice, contesto e istruzioni subito allineati.",
                }
            ],
        },
        {
            "title": "5. Controlli finali prima di spedire",
            "bullets": [
                "Frontend si avvia dal percorso Basket corretto.",
                "Backend risponde su 127.0.0.1:8000.",
                "Lead salvati e visibili in Google Sheets.",
                "PDF aggiornati e coerenti con l'ultima versione del progetto.",
                "Nessuna chiave reale inclusa nei file condivisi.",
            ],
        },
    ]
    build_manual(
        title="Guida alla condivisione del progetto",
        subtitle="Checklist pratica per consegnare il progetto in modo pulito, sicuro e comprensibile a clienti, collaboratori o revisori tecnici.",
        meta_rows=[
            ("Progetto", PROJECT_NAME),
            ("Formato ideale", "Repo GitHub + PDF"),
            ("Consegna locale", "ZIP pulito senza segreti"),
            ("Aggiornato il", today),
        ],
        sections=sections,
        out_name="Prova_in_Basket_Vincenzo_Rosa_Guida_Condivisione.pdf",
    )


def build_launch_markdown():
    content = f"""# Guida Messa Online {PROJECT_NAME}

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
"""
    (SOURCE_ROOT / "Prova_in_Basket_Vincenzo_Rosa_Guida_Messa_Online.md").write_text(content, encoding="utf-8")


def main():
    build_presentation()
    build_startup_sheet()
    build_user_manual()
    build_launch_manual()
    build_sharing_manual()
    build_launch_markdown()


if __name__ == "__main__":
    main()
