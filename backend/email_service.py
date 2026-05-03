"""Email service for Fisco Facile — Resend transactional emails + scheduling.

- send_email_now: fire-and-forget via Resend (asyncio.to_thread)
- schedule_email: pushes a job into MongoDB collection email_jobs
- run_due_jobs: picked up by APScheduler every minute
"""
import os
import asyncio
import logging
import resend
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
import uuid

logger = logging.getLogger(__name__)

SENDER_NAME = "Fisco Facile"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _resend_api_key() -> str:
    return os.environ.get("RESEND_API_KEY", "")


def _sender_email() -> str:
    return os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")


def _from_header() -> str:
    return f"{SENDER_NAME} <{_sender_email()}>"


def _public_site_url() -> str:
    return os.environ.get(
        "PUBLIC_SITE_URL",
        "http://127.0.0.1:3000",
    ).rstrip("/")


def _support_email() -> str:
    return os.environ.get("SUPPORT_EMAIL", "supporto@fiscofacile.it")


def _company_name() -> str:
    return os.environ.get("COMPANY_LEGAL_NAME", "Fisco Facile")


def _vat_id() -> str:
    return os.environ.get("VAT_ID", "00000000000")


def _email_delivery_mode() -> str:
    return os.environ.get("EMAIL_DELIVERY_MODE", "auto").lower()


def _configure_resend() -> None:
    api_key = _resend_api_key()
    if api_key:
        resend.api_key = api_key


def _use_preview_mode() -> bool:
    if _email_delivery_mode() == "preview":
        return True
    return not _resend_api_key()


# ============================================================
# CORE SEND
# ============================================================
async def send_email_now(
    to: str,
    subject: str,
    html: str,
    attachments: Optional[List[Dict]] = None,
) -> Dict:
    """Send an email immediately via Resend.

    attachments: list of {"filename": str, "content": bytes}
    """
    _configure_resend()

    if _use_preview_mode():
        reason = "preview_mode" if _email_delivery_mode() == "preview" else "no_api_key"
        logger.warning("Email preview mode active — storing preview instead of sending")
        return {
            "status": "previewed",
            "mode": "preview",
            "reason": reason,
            "attachments": [{"filename": a["filename"]} for a in (attachments or [])],
        }

    params = {
        "from": _from_header(),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if attachments:
        # Resend expects content as base64 string OR list[int] of bytes
        import base64
        params["attachments"] = [
            {
                "filename": a["filename"],
                "content": base64.b64encode(a["content"]).decode("utf-8"),
            }
            for a in attachments
        ]

    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Resend OK to={to} id={result.get('id')}")
        return {"status": "sent", "mode": "resend", "id": result.get("id")}
    except Exception as e:
        logger.error(f"Resend FAILED to={to}: {e}")
        return {"status": "failed", "mode": "resend", "error": str(e)}


# ============================================================
# SCHEDULING (MongoDB-backed simple queue)
# ============================================================
async def schedule_email(
    db,
    to: str,
    subject: str,
    html: str,
    send_at: datetime,
    kind: str,
    meta: Optional[Dict] = None,
) -> str:
    job_id = str(uuid.uuid4())
    await db.email_jobs.insert_one({
        "id": job_id,
        "to": to,
        "subject": subject,
        "html": html,
        "kind": kind,
        "meta": meta or {},
        "send_at": _iso(send_at),
        "status": "pending",
        "created_at": _iso(_now()),
    })
    logger.info(f"Scheduled email kind={kind} to={to} at={send_at}")
    return job_id


async def run_due_jobs(db) -> int:
    """Process due email_jobs. Called by APScheduler every minute."""
    now_iso = _iso(_now())
    cursor = db.email_jobs.find(
        {"status": "pending", "send_at": {"$lte": now_iso}},
        {"_id": 0},
    ).limit(50)
    sent = 0
    async for job in cursor:
        result = await send_email_now(
            to=job["to"], subject=job["subject"], html=job["html"]
        )
        await db.email_jobs.update_one(
            {"id": job["id"]},
            {"$set": {
                "status": result.get("status", "failed"),
                "result": result,
                "sent_at": _iso(_now()),
            }},
        )
        if result.get("status") == "sent":
            sent += 1
    return sent


# ============================================================
# TEMPLATES
# ============================================================
def _wrap(html_body: str, preheader: str = "") -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"/><title>Fisco Facile</title></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<span style="display:none;font-size:1px;color:#0a0a0a;">{preheader}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:40px 20px;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#18181b;border:1px solid #27272a;border-radius:16px;overflow:hidden;">
<tr><td style="background:#0a0a0a;padding:24px 32px;border-bottom:1px solid #27272a;">
<span style="color:#fafafa;font-size:20px;font-weight:900;letter-spacing:-0.02em;">Fisco<span style="color:#CCFF00;">.</span> <span style="color:#a1a1aa;font-weight:500;">Facile</span></span>
</td></tr>
<tr><td style="padding:40px 32px;color:#e4e4e7;font-size:15px;line-height:1.7;">
{html_body}
</td></tr>
<tr><td style="padding:24px 32px;background:#0c0c0e;border-top:1px solid #27272a;color:#71717a;font-size:11px;line-height:1.6;">
© 2026 {_company_name()} • P.IVA {_vat_id()}<br/>
Hai ricevuto questa email perché ti sei iscritto/a o hai effettuato un acquisto su Fisco Facile.<br/>
Supporto: {_support_email()}
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def _btn(url: str, label: str) -> str:
    return f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px 0;"><tr><td style="background:#CCFF00;border-radius:8px;"><a href="{url}" style="display:inline-block;padding:14px 28px;color:#000;font-weight:700;text-decoration:none;text-transform:uppercase;letter-spacing:0.05em;font-size:13px;">{label}</a></td></tr></table>'


# ---------- Post-acquisto ----------
def tpl_purchase_confirm(buyer_name: str, package_name: str,
                         download_url: str, amount: float) -> tuple:
    subject = f"✓ Le tue guide sono pronte — {package_name}"
    body = f"""
<h1 style="color:#fafafa;font-size:32px;font-weight:900;letter-spacing:-0.02em;margin:0 0 8px 0;">Grazie {buyer_name or ''}<span style="color:#CCFF00;">.</span></h1>
<p style="color:#a1a1aa;font-size:15px;margin:0 0 24px 0;">Il tuo acquisto è andato a buon fine.</p>
<p>Hai acquistato <b style="color:#fafafa;">{package_name}</b> per <b>€{amount:.2f}</b>. Le guide sono già pronte per te.</p>
{_btn(download_url, "Scarica le guide ora")}
<p style="color:#a1a1aa;font-size:13px;">Salva questa email: il link è valido per sempre.</p>
<hr style="border:none;border-top:1px solid #27272a;margin:32px 0;"/>
<p style="font-size:13px;color:#a1a1aa;">Domande? Scrivici a {_support_email()}, ti rispondiamo entro 48h.</p>
"""
    return subject, _wrap(body, "Le tue guide Fisco Facile sono pronte")


def tpl_purchase_followup(buyer_name: str, download_url: str) -> tuple:
    subject = "Come sfruttare al meglio le tue guide"
    body = f"""
<h1 style="color:#fafafa;font-size:28px;font-weight:900;margin:0 0 16px 0;">Le hai già aperte?</h1>
<p>Ciao {buyer_name or ''}, sono passati 3 giorni dal tuo acquisto. Volevo darti 3 consigli rapidi per sfruttare al massimo le guide Fisco Facile:</p>
<p><b style="color:#CCFF00;">1.</b> Stampa solo le guide che ti servono ora — il resto consultalo dal PDF.</p>
<p><b style="color:#CCFF00;">2.</b> Quando segui una procedura, tieni la guida aperta sul telefono e il portale sul PC.</p>
<p><b style="color:#CCFF00;">3.</b> Salva i numeri di pratica/protocollo che ottieni — ti serviranno per follow-up.</p>
{_btn(download_url, "Riapri l'area download")}
<p style="font-size:13px;color:#a1a1aa;">Hai una procedura specifica e non sai da dove partire? Rispondi qui, ti orientiamo noi.</p>
"""
    return subject, _wrap(body, "3 consigli per sfruttare al meglio le tue guide")


def tpl_purchase_review(buyer_name: str) -> tuple:
    subject = "Una settimana dopo: ci dai il tuo parere?"
    body = f"""
<h1 style="color:#fafafa;font-size:28px;font-weight:900;margin:0 0 16px 0;">Com'è andata?</h1>
<p>Ciao {buyer_name or ''}, è passata una settimana dal tuo acquisto.</p>
<p>Le guide ti sono state utili? Hai risparmiato qualche consulenza?</p>
<p>Una tua recensione (anche solo 2 righe) ci aiuta tantissimo a far conoscere Fisco Facile e a migliorare i contenuti.</p>
{_btn(f"{_public_site_url()}/?review=1", "Lascia una recensione")}
<p style="font-size:13px;color:#a1a1aa;">Se invece qualcosa non va, scrivici qui: leggiamo tutto.</p>
"""
    return subject, _wrap(body, "Ci dai un feedback?")


# ---------- Lead nurturing ----------
def tpl_lead_estratto(nome: str) -> tuple:
    subject = "Il tuo estratto gratuito — Cassetto Fiscale"
    body = f"""
<h1 style="color:#fafafa;font-size:32px;font-weight:900;margin:0 0 8px 0;">Ciao {nome}<span style="color:#CCFF00;">.</span></h1>
<p style="color:#a1a1aa;margin:0 0 24px 0;">Ecco l'estratto che ti avevamo promesso.</p>
<p>In allegato trovi un esempio di una nostra guida: l'apertura del <b>Cassetto Fiscale</b> sul portale dell'Agenzia delle Entrate. Sono solo 4 pagine, ma vedrai com'è scritta una nostra guida.</p>
<p style="color:#a1a1aa;font-size:13px;">Apri l'allegato e dacci un'occhiata. Se ti convince, da domani ti scrivo cosa contiene il pacchetto completo.</p>
<hr style="border:none;border-top:1px solid #27272a;margin:24px 0;"/>
<p style="font-size:13px;color:#a1a1aa;">Niente spam: 3 email in totale, poi sparisco. Promesso.</p>
"""
    return subject, _wrap(body, "Il tuo estratto è in allegato")


def tpl_lead_coupon(nome: str, coupon_code: str) -> tuple:
    subject = f"{nome}, sconto -10€ valido 48h"
    body = f"""
<h1 style="color:#fafafa;font-size:30px;font-weight:900;margin:0 0 16px 0;">Hai letto l'estratto?</h1>
<p>Se ti è piaciuto come è scritto, ho una piccola sorpresa per te.</p>
<p>Le 28 guide del bundle (€69) ti servirebbero per anni: dal 730 all'INPS, dal Cassetto Fiscale alla Fatturazione Elettronica.</p>
<p>Per i prossimi <b style="color:#CCFF00;">2 giorni</b> ti faccio uno sconto di <b style="color:#CCFF00;">-10€</b> sul totale:</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px 0;border:2px dashed #CCFF00;border-radius:12px;padding:20px;background:#0c0c0e;width:100%;">
<tr><td align="center">
<div style="font-size:11px;color:#a1a1aa;text-transform:uppercase;letter-spacing:0.2em;margin-bottom:8px;">Codice sconto</div>
<div style="font-size:32px;font-weight:900;color:#CCFF00;letter-spacing:0.1em;font-family:monospace;">{coupon_code}</div>
</td></tr>
</table>
{_btn(f"{_public_site_url()}/#pricing", "Usa il codice ora")}
<p style="font-size:13px;color:#a1a1aa;">Inseriscilo nel checkout. Bundle a €59 invece di €69.</p>
"""
    return subject, _wrap(body, "Il tuo sconto -10€ valido 48h")


def tpl_lead_last_call(nome: str) -> tuple:
    subject = "Ultima chiamata — domani il prezzo torna pieno"
    body = f"""
<h1 style="color:#fafafa;font-size:30px;font-weight:900;margin:0 0 16px 0;">{nome}, ci siamo.</h1>
<p>Domani il bundle Fisco Facile torna a prezzo pieno (€69).</p>
<p>Quante volte all'anno chiami il commercialista per cose che potresti fare in 10 minuti? Ogni chiamata = 30-50€.</p>
<p>Le 28 guide costano meno di una sola consulenza. E le hai a vita.</p>
{_btn(f"{_public_site_url()}/#pricing", "Sceglilo ora")}
<p style="font-size:13px;color:#a1a1aa;">Se non ti interessa, ignora pure: questa è l'ultima email che ricevi da noi.</p>
"""
    return subject, _wrap(body, "Ultima email — domani prezzo pieno")


# ---------- Customer area ----------
def tpl_customer_access(magic_link: str) -> tuple:
    subject = "Accedi alla tua area riservata Fisco Facile"
    body = f"""
<h1 style="color:#fafafa;font-size:30px;font-weight:900;margin:0 0 16px 0;">Eccoti il tuo accesso<span style="color:#CCFF00;">.</span></h1>
<p>Hai richiesto di accedere alla tua area riservata su Fisco Facile.</p>
<p>Clicca il bottone qui sotto: il link è valido per <b>24 ore</b> e ti mostra tutti i tuoi acquisti con il download diretto delle guide.</p>
{_btn(magic_link, "Accedi all'area riservata")}
<p style="font-size:13px;color:#a1a1aa;">Non hai richiesto tu questo accesso? Ignora pure questa email — non è successo nulla.</p>
"""
    return subject, _wrap(body, "Il tuo link di accesso (24h)")
