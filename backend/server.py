from fastapi import FastAPI, APIRouter, HTTPException, Request, Header, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
import logging
import html
import hashlib
import hmac
import secrets
import string
from io import BytesIO
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timedelta, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest,
)

from pdf_service import generate_guide_pdf
from email_service import (
    send_email_now, schedule_email, run_due_jobs,
    tpl_purchase_confirm, tpl_purchase_followup, tpl_purchase_review,
    tpl_lead_estratto, tpl_lead_coupon, tpl_lead_last_call,
    tpl_customer_access,
)
from google_sheets_service import google_sheets_sync


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.environ.get(name, "").strip()
    try:
        value = int(raw) if raw else default
    except ValueError:
        value = default
    return max(value, minimum)


def _parse_csv_env(raw: str) -> List[str]:
    return [item.strip().rstrip("/") for item in raw.split(",") if item.strip()]


def _build_cors_origins() -> List[str]:
    origins = {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
    origins.update(_parse_csv_env(os.environ.get("CORS_ORIGINS", "")))
    public_site_url = os.environ.get("PUBLIC_SITE_URL", "").strip().rstrip("/")
    if public_site_url:
        origins.add(public_site_url)
    return sorted(origins)


def _cors_origin_regex() -> str:
    return (
        os.environ.get("CORS_ALLOW_ORIGIN_REGEX", "").strip()
        or r"https://.*\.vercel\.app"
    )


mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "rootroot").strip()
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "").strip()
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@fiscofacile.it").lower().strip()
ADMIN_SESSION_HOURS = _env_int("ADMIN_SESSION_HOURS", 4)
ADMIN_MAX_FAILED_ATTEMPTS = _env_int("ADMIN_MAX_FAILED_ATTEMPTS", 5, minimum=1)
ADMIN_LOCKOUT_MINUTES = _env_int("ADMIN_LOCKOUT_MINUTES", 15)
ADMIN_PREVIEW_TOKEN_MINUTES = _env_int("ADMIN_PREVIEW_TOKEN_MINUTES", 10)
CUSTOMER_MAGIC_LINK_HOURS = _env_int("CUSTOMER_MAGIC_LINK_HOURS", 24)
CUSTOMER_SESSION_HOURS = _env_int("CUSTOMER_SESSION_HOURS", 12)
CUSTOMER_ACCESS_MAX_REQUESTS_PER_HOUR = _env_int("CUSTOMER_ACCESS_MAX_REQUESTS_PER_HOUR", 5)
CUSTOMER_TEST_ACCESS_LOCAL_ONLY = os.environ.get("CUSTOMER_TEST_ACCESS_LOCAL_ONLY", "true").lower() == "true"
ALLOW_TEST_BYPASS = os.environ.get("ALLOW_TEST_BYPASS", "false").lower() == "true"
TEST_BYPASS_LOCAL_ONLY = os.environ.get("TEST_BYPASS_LOCAL_ONLY", "true").lower() == "true"
PUBLIC_SITE_URL = os.environ.get(
    "PUBLIC_SITE_URL",
    "http://127.0.0.1:3000",
).rstrip("/")

# ============================================================
# PRODUCT CATALOG (backend-only, never trust frontend)
# ============================================================
GUIDES = {
    "privati": [
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
    "aziende": [
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
}

PACKAGES: Dict[str, Dict] = {
    "privati": {
        "name": "Pacchetto Privati", "price": 39.00, "currency": "eur",
        "description": "16 guide pratiche per privati",
        "includes": ["privati"],
    },
    "aziende": {
        "name": "Pacchetto Aziende", "price": 39.00, "currency": "eur",
        "description": "12 guide pratiche per aziende e P.IVA",
        "includes": ["aziende"],
    },
    "bundle": {
        "name": "Bundle Privati + Aziende", "price": 67.50, "currency": "eur",
        "description": "Tutte le 28 guide insieme — sconto 25%",
        "includes": ["privati", "aziende"],
    },
}

app = FastAPI()
api_router = APIRouter(prefix="/api")


# ============================================================
# MODELS
# ============================================================
class LeadCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    interesse: Optional[str] = Field(default="generale", max_length=50)


class LeadOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    nome: str
    email: str
    interesse: Optional[str] = "generale"
    coupon_code: Optional[str] = None
    created_at: str


class CheckoutRequest(BaseModel):
    package_id: str
    origin_url: str
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    coupon: Optional[str] = None


class CheckoutResponse(BaseModel):
    url: str
    session_id: str
    final_amount: float
    discount: float = 0.0


class CheckoutStatusOut(BaseModel):
    session_id: str
    status: str
    payment_status: str
    amount_total: int
    currency: str
    package_id: Optional[str] = None
    already_processed: bool = False


class DownloadInfo(BaseModel):
    package_id: str
    package_name: str
    buyer_email: Optional[str] = None
    paid_at: Optional[str] = None
    guides: List[Dict]


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class CustomerAccessRequest(BaseModel):
    email: EmailStr


class CustomerPasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class CustomerSessionExchangeRequest(BaseModel):
    token: str = Field(..., min_length=12, max_length=512)


# ============================================================
# HELPERS
# ============================================================
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat()


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _constant_time_eq(left: str, right: str) -> bool:
    return hmac.compare_digest((left or "").encode("utf-8"), (right or "").encode("utf-8"))


def _normalize_email(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hash_pbkdf2_password(password: str, iterations: int = 390000) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${derived}"


def _verify_pbkdf2_hash(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt, expected_hash = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
    except (TypeError, ValueError):
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return _constant_time_eq(derived, expected_hash)


def _admin_password_matches(password: str) -> bool:
    if ADMIN_PASSWORD_HASH:
        return _verify_pbkdf2_hash(password, ADMIN_PASSWORD_HASH)
    return _constant_time_eq(password, ADMIN_PASSWORD)


async def _find_customer_account(email: str) -> Optional[Dict]:
    return await db.customer_accounts.find_one({"email": _normalize_email(email)}, {"_id": 0})


async def _ensure_customer_account(email: str, password: str) -> Dict:
    normalized_email = _normalize_email(email)
    raw_password = (password or "").strip()
    if not normalized_email or not raw_password:
        raise HTTPException(
            status_code=400,
            detail="Inserisci email e password per creare il tuo accesso cliente.",
        )

    now_iso = _now_iso()
    account = await _find_customer_account(normalized_email)
    if account:
        stored_hash = (account.get("password_hash") or "").strip()
        if stored_hash and not _verify_pbkdf2_hash(raw_password, stored_hash):
            raise HTTPException(
                status_code=401,
                detail="Questa email è gia registrata. Usa la password corretta per continuare.",
            )

        password_hash = stored_hash or _hash_pbkdf2_password(raw_password)
        await db.customer_accounts.update_one(
            {"email": normalized_email},
            {"$set": {
                "password_hash": password_hash,
                "updated_at": now_iso,
                "last_checkout_at": now_iso,
            }},
        )
        return {
            **account,
            "email": normalized_email,
            "password_hash": password_hash,
            "updated_at": now_iso,
            "last_checkout_at": now_iso,
        }

    account_doc = {
        "id": str(uuid.uuid4()),
        "email": normalized_email,
        "password_hash": _hash_pbkdf2_password(raw_password),
        "created_at": now_iso,
        "updated_at": now_iso,
        "last_checkout_at": now_iso,
    }
    await db.customer_accounts.insert_one(account_doc)
    return account_doc


async def _authenticate_customer_account(email: str, password: str) -> Dict:
    normalized_email = _normalize_email(email)
    raw_password = (password or "").strip()
    account = await _find_customer_account(normalized_email)
    if not account:
        raise HTTPException(status_code=401, detail="Credenziali non valide.")

    stored_hash = (account.get("password_hash") or "").strip()
    if not stored_hash or not _verify_pbkdf2_hash(raw_password, stored_hash):
        raise HTTPException(status_code=401, detail="Credenziali non valide.")

    now_iso = _now_iso()
    await db.customer_accounts.update_one(
        {"email": normalized_email},
        {"$set": {"updated_at": now_iso, "last_login_at": now_iso}},
    )
    return {**account, "email": normalized_email, "updated_at": now_iso, "last_login_at": now_iso}


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    client_info = getattr(request, "client", None)
    if client_info and client_info.host:
        return client_info.host
    return "unknown"


def _gen_coupon() -> str:
    return "FF" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))


async def _validate_coupon(code: str) -> Optional[Dict]:
    if not code:
        return None
    code = code.upper().strip()
    coupon = await db.coupons.find_one({"code": code}, {"_id": 0})
    if not coupon:
        return None
    # check expiry
    expires = coupon.get("expires_at")
    if expires and expires < _now_iso():
        return None
    if coupon.get("used"):
        return None
    return coupon


async def _resolve_checkout(payload: CheckoutRequest):
    pkg = PACKAGES.get(payload.package_id)
    if not pkg:
        raise HTTPException(status_code=400, detail="Pacchetto non valido")

    base_amount = float(pkg["price"])
    discount = 0.0
    coupon_used: Optional[str] = None
    if payload.coupon:
        coupon = await _validate_coupon(payload.coupon)
        if coupon and payload.package_id in coupon.get("applies_to", []):
            discount = float(coupon["discount_eur"])
            coupon_used = coupon["code"]

    final_amount = max(round(base_amount - discount, 2), 1.0)
    origin = payload.origin_url.rstrip("/")
    metadata = {
        "package_id": payload.package_id,
        "package_name": pkg["name"],
        "source": "fisco_facile_landing",
        "origin_url": origin,
    }
    if payload.email:
        metadata["email"] = payload.email
    if coupon_used:
        metadata["coupon"] = coupon_used

    return pkg, final_amount, discount, coupon_used, origin, metadata


async def _cleanup_admin_security_state() -> None:
    now = _now_iso()
    await db.admin_sessions.delete_many({"expires_at": {"$lte": now}})
    await db.admin_preview_tokens.delete_many({"expires_at": {"$lte": now}})


def _admin_login_attempt_key(ip_address: str) -> str:
    return f"admin_ip:{ip_address}"


async def _get_admin_login_attempt(email: str, ip_address: str) -> Optional[Dict]:
    key = _admin_login_attempt_key(ip_address)
    attempt = await db.admin_login_attempts.find_one({"key": key}, {"_id": 0})
    if not attempt:
        return None

    now = _now_utc()
    locked_until = _parse_iso(attempt.get("locked_until"))
    if locked_until and locked_until <= now:
        await db.admin_login_attempts.delete_one({"key": key})
        return None

    last_failed_at = _parse_iso(attempt.get("last_failed_at"))
    if (
        last_failed_at
        and not locked_until
        and last_failed_at <= now - timedelta(minutes=ADMIN_LOCKOUT_MINUTES)
    ):
        await db.admin_login_attempts.delete_one({"key": key})
        return None

    return attempt


async def _register_admin_login_failure(email: str, ip_address: str) -> Dict:
    key = _admin_login_attempt_key(ip_address)
    now = _now_utc()
    attempt = await _get_admin_login_attempt(email, ip_address)
    failed_attempts = int((attempt or {}).get("failed_attempts", 0)) + 1
    locked_until = None

    update_doc = {
        "email": email,
        "ip_address": ip_address,
        "failed_attempts": failed_attempts,
        "last_failed_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    if failed_attempts >= ADMIN_MAX_FAILED_ATTEMPTS:
        locked_until = (now + timedelta(minutes=ADMIN_LOCKOUT_MINUTES)).isoformat()
        update_doc["locked_until"] = locked_until
    else:
        update_doc["locked_until"] = ""

    await db.admin_login_attempts.update_one(
        {"key": key},
        {
            "$set": update_doc,
            "$setOnInsert": {"key": key, "created_at": now.isoformat()},
        },
        upsert=True,
    )
    return {"failed_attempts": failed_attempts, "locked_until": locked_until}


async def _clear_admin_login_failures(email: str, ip_address: str) -> None:
    await db.admin_login_attempts.delete_one({"key": _admin_login_attempt_key(ip_address)})


async def _find_admin_session(token: str) -> Optional[Dict]:
    token_hash = _hash_token(token)
    session = await db.admin_sessions.find_one({"token_hash": token_hash}, {"_id": 0})
    if session:
        return session
    return await db.admin_sessions.find_one({"token": token}, {"_id": 0})


async def _delete_admin_session(session: Dict) -> None:
    if session.get("id"):
        await db.admin_sessions.delete_one({"id": session["id"]})
        return
    if session.get("token_hash"):
        await db.admin_sessions.delete_one({"token_hash": session["token_hash"]})
        return
    if session.get("token"):
        await db.admin_sessions.delete_one({"token": session["token"]})


async def _get_admin_session(token: Optional[str]) -> Optional[Dict]:
    if not token:
        return None

    await _cleanup_admin_security_state()
    session = await _find_admin_session(token)
    if not session or session.get("revoked_at"):
        return None

    expires_at = _parse_iso(session.get("expires_at"))
    if not expires_at or expires_at <= _now_utc():
        await _delete_admin_session(session)
        return None

    lookup = {}
    if session.get("id"):
        lookup = {"id": session["id"]}
    elif session.get("token_hash"):
        lookup = {"token_hash": session["token_hash"]}
    elif session.get("token"):
        lookup = {"token": session["token"]}

    if lookup:
        await db.admin_sessions.update_one(
            lookup,
            {"$set": {"last_seen_at": _now_iso()}},
        )
    return session


async def _verify_admin(token: Optional[str]) -> bool:
    return bool(await _get_admin_session(token))


async def _create_admin_preview_token(email_id: str) -> Dict:
    preview_token = secrets.token_urlsafe(24)
    expires_at = (_now_utc() + timedelta(minutes=ADMIN_PREVIEW_TOKEN_MINUTES)).isoformat()
    await db.admin_preview_tokens.insert_one({
        "id": str(uuid.uuid4()),
        "email_id": email_id,
        "token_hash": _hash_token(preview_token),
        "expires_at": expires_at,
        "created_at": _now_iso(),
        "last_used_at": None,
    })
    return {"token": preview_token, "expires_at": expires_at}


async def _verify_admin_preview_token(email_id: str, preview_token: str) -> bool:
    if not preview_token:
        return False

    await _cleanup_admin_security_state()
    doc = await db.admin_preview_tokens.find_one(
        {
            "email_id": email_id,
            "token_hash": _hash_token(preview_token),
        },
        {"_id": 0},
    )
    if not doc:
        return False

    expires_at = _parse_iso(doc.get("expires_at"))
    if not expires_at or expires_at <= _now_utc():
        await db.admin_preview_tokens.delete_one({"id": doc["id"]})
        return False

    await db.admin_preview_tokens.update_one(
        {"id": doc["id"]},
        {"$set": {"last_used_at": _now_iso()}},
    )
    return True


async def _cleanup_customer_security_state() -> None:
    now = _now_iso()
    cutoff = (_now_utc() - timedelta(hours=1)).isoformat()
    await db.customer_tokens.delete_many({"expires_at": {"$lte": now}})
    await db.customer_sessions.delete_many({"expires_at": {"$lte": now}})
    await db.customer_access_attempts.delete_many({"window_started_at": {"$lte": cutoff}})


def _customer_access_attempt_key(ip_address: str) -> str:
    return f"customer_access_ip:{ip_address}"


async def _is_customer_access_rate_limited(ip_address: str) -> bool:
    await _cleanup_customer_security_state()
    key = _customer_access_attempt_key(ip_address)
    attempt = await db.customer_access_attempts.find_one({"key": key}, {"_id": 0})
    if not attempt:
        return False

    window_started_at = _parse_iso(attempt.get("window_started_at"))
    if not window_started_at or window_started_at <= _now_utc() - timedelta(hours=1):
        await db.customer_access_attempts.delete_one({"key": key})
        return False

    return int(attempt.get("count", 0)) >= CUSTOMER_ACCESS_MAX_REQUESTS_PER_HOUR


async def _register_customer_access_attempt(ip_address: str, email: str) -> None:
    key = _customer_access_attempt_key(ip_address)
    now = _now_utc()
    now_iso = now.isoformat()
    attempt = await db.customer_access_attempts.find_one({"key": key}, {"_id": 0})
    if not attempt:
        await db.customer_access_attempts.insert_one({
            "key": key,
            "ip_address": ip_address,
            "email": email,
            "count": 1,
            "window_started_at": now_iso,
            "last_attempt_at": now_iso,
            "created_at": now_iso,
        })
        return

    window_started_at = _parse_iso(attempt.get("window_started_at"))
    if not window_started_at or window_started_at <= now - timedelta(hours=1):
        await db.customer_access_attempts.update_one(
            {"key": key},
            {"$set": {
                "email": email,
                "count": 1,
                "window_started_at": now_iso,
                "last_attempt_at": now_iso,
            }},
        )
        return

    await db.customer_access_attempts.update_one(
        {"key": key},
        {"$set": {"email": email, "last_attempt_at": now_iso}, "$inc": {"count": 1}},
    )


def _is_local_request(request: Request) -> bool:
    ip_address = _client_ip(request)
    if ip_address in {"127.0.0.1", "::1", "localhost"}:
        return True

    for header_name in ("origin", "referer"):
        header_value = request.headers.get(header_name, "")
        if not header_value:
            continue
        if "127.0.0.1" in header_value or "localhost" in header_value:
            return True
    return False


async def _find_customer_token(raw_token: str) -> Optional[Dict]:
    token_hash = _hash_token(raw_token)
    doc = await db.customer_tokens.find_one({"token_hash": token_hash}, {"_id": 0})
    if doc:
        return doc
    return await db.customer_tokens.find_one({"token": raw_token}, {"_id": 0})


async def _find_customer_session(raw_token: str) -> Optional[Dict]:
    token_hash = _hash_token(raw_token)
    doc = await db.customer_sessions.find_one({"token_hash": token_hash}, {"_id": 0})
    if doc:
        return doc
    return await db.customer_sessions.find_one({"token": raw_token}, {"_id": 0})


async def _delete_customer_token_doc(doc: Dict) -> None:
    if doc.get("id"):
        await db.customer_tokens.delete_one({"id": doc["id"]})
        return
    if doc.get("token_hash"):
        await db.customer_tokens.delete_one({"token_hash": doc["token_hash"]})
        return
    if doc.get("token"):
        await db.customer_tokens.delete_one({"token": doc["token"]})


async def _delete_customer_session_doc(doc: Dict) -> None:
    if doc.get("id"):
        await db.customer_sessions.delete_one({"id": doc["id"]})
        return
    if doc.get("token_hash"):
        await db.customer_sessions.delete_one({"token_hash": doc["token_hash"]})
        return
    if doc.get("token"):
        await db.customer_sessions.delete_one({"token": doc["token"]})


async def _create_customer_magic_token(
    *,
    email: str,
    mode: str = "magic_link",
    session_ids: Optional[List[str]] = None,
) -> Dict:
    raw_token = secrets.token_urlsafe(32)
    expires_at = (_now_utc() + timedelta(hours=CUSTOMER_MAGIC_LINK_HOURS)).isoformat()
    token_doc = {
        "id": str(uuid.uuid4()),
        "token_hash": _hash_token(raw_token),
        "email": email,
        "mode": mode,
        "session_ids": session_ids or [],
        "expires_at": expires_at,
        "created_at": _now_iso(),
        "consumed_at": None,
        "used": False,
    }
    await db.customer_tokens.insert_one(token_doc)
    return {"token": raw_token, "expires_at": expires_at, "doc": token_doc}


async def _consume_customer_magic_token(raw_token: str) -> Dict:
    await _cleanup_customer_security_state()
    doc = await _find_customer_token(raw_token)
    if not doc:
        raise HTTPException(status_code=404, detail="Token non valido")

    expires_at = _parse_iso(doc.get("expires_at"))
    if not expires_at or expires_at <= _now_utc():
        await _delete_customer_token_doc(doc)
        raise HTTPException(status_code=403, detail="Token scaduto")

    if doc.get("consumed_at") or doc.get("used"):
        raise HTTPException(status_code=403, detail="Link già utilizzato")

    token_hash = doc.get("token_hash") or _hash_token(raw_token)
    now_iso = _now_iso()
    lookup = {}
    if doc.get("id"):
        lookup = {"id": doc["id"]}
    elif doc.get("token_hash"):
        lookup = {"token_hash": doc["token_hash"]}
    elif doc.get("token"):
        lookup = {"token": doc["token"]}
    await db.customer_tokens.update_one(
        lookup,
        {"$set": {
            "token_hash": token_hash,
            "consumed_at": now_iso,
            "used": True,
            "updated_at": now_iso,
        }, "$unset": {"token": ""}},
    )
    return {**doc, "token_hash": token_hash, "consumed_at": now_iso, "used": True}


async def _create_customer_session(token_doc: Dict) -> Dict:
    raw_session_token = secrets.token_urlsafe(32)
    expires_at = (_now_utc() + timedelta(hours=CUSTOMER_SESSION_HOURS)).isoformat()
    session_doc = {
        "id": str(uuid.uuid4()),
        "token_hash": _hash_token(raw_session_token),
        "email": token_doc["email"],
        "mode": token_doc.get("mode", "magic_link"),
        "session_ids": token_doc.get("session_ids", []),
        "source_token_id": token_doc.get("id"),
        "expires_at": expires_at,
        "created_at": _now_iso(),
        "last_seen_at": _now_iso(),
    }
    await db.customer_sessions.insert_one(session_doc)
    return {"token": raw_session_token, "expires_at": expires_at, "doc": session_doc}


async def _create_customer_session_for_email(
    email: str,
    *,
    mode: str = "password_login",
    session_ids: Optional[List[str]] = None,
) -> Dict:
    return await _create_customer_session({
        "email": _normalize_email(email),
        "mode": mode,
        "session_ids": session_ids or [],
    })


async def _get_customer_session(raw_token: Optional[str]) -> Optional[Dict]:
    if not raw_token:
        return None

    await _cleanup_customer_security_state()
    doc = await _find_customer_session(raw_token)
    if not doc:
        return None

    expires_at = _parse_iso(doc.get("expires_at"))
    if not expires_at or expires_at <= _now_utc():
        await _delete_customer_session_doc(doc)
        return None

    lookup = {}
    if doc.get("id"):
        lookup = {"id": doc["id"]}
    elif doc.get("token_hash"):
        lookup = {"token_hash": doc["token_hash"]}
    elif doc.get("token"):
        lookup = {"token": doc["token"]}

    if lookup:
        await db.customer_sessions.update_one(
            lookup,
            {"$set": {"last_seen_at": _now_iso()}, "$unset": {"token": ""}},
        )
    return doc


async def _track_sheet_event(
    event_type: str,
    entity_type: str,
    entity_id: str,
    *,
    lead_id: str = "",
    session_id: str = "",
    email: str = "",
    package_id: str = "",
    amount: Optional[float] = None,
    status: str = "",
    payment_status: str = "",
    source: str = "",
    note: str = "",
    metadata: Optional[Dict] = None,
    created_at: Optional[str] = None,
):
    await google_sheets_sync.append_tracking_event(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        lead_id=lead_id,
        session_id=session_id,
        email=email,
        package_id=package_id,
        amount=amount or "",
        status=status,
        payment_status=payment_status,
        source=source,
        note=note,
        metadata=metadata or {},
        created_at=created_at or _now_iso(),
    )


# ============================================================
# ROUTES
# ============================================================
@api_router.get("/")
async def root():
    return {"message": "Fisco Facile API", "version": "2.0"}


@api_router.get("/packages")
async def list_packages():
    return {
        "packages": [
            {
                "id": pid, "name": p["name"], "price": p["price"],
                "currency": p["currency"], "description": p["description"],
            }
            for pid, p in PACKAGES.items()
        ]
    }


# ----------- Leads + nurturing -----------
@api_router.post("/leads", response_model=LeadOut)
async def create_lead(payload: LeadCreate):
    lead_id = str(uuid.uuid4())
    coupon_code = _gen_coupon()
    nome = payload.nome.strip()
    email = payload.email.lower().strip()

    # store coupon valid 7 days, -10€ off bundle
    await db.coupons.insert_one({
        "code": coupon_code, "discount_eur": 10.0,
        "applies_to": ["bundle", "privati", "aziende"],
        "lead_email": email, "used": False,
        "created_at": _now_iso(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    })

    doc = {
        "id": lead_id, "nome": nome, "email": email,
        "interesse": (payload.interesse or "generale").strip(),
        "coupon_code": coupon_code,
        "created_at": _now_iso(),
    }
    await db.leads.insert_one(doc.copy())
    await google_sheets_sync.append_lead({
        **doc,
        "source": "fisco_facile_landing",
        "origin_url": PUBLIC_SITE_URL,
    })
    await _track_sheet_event(
        "lead_created",
        "lead",
        lead_id,
        lead_id=lead_id,
        email=email,
        source="fisco_facile_landing",
        note="Lead creato dalla landing",
        metadata={"coupon_code": coupon_code, "interesse": doc["interesse"]},
        created_at=doc["created_at"],
    )

    # Schedule lead nurturing sequence
    now = datetime.now(timezone.utc)
    # Day 0 — estratto immediately (with PDF attachment via send_email_now path)
    subj0, html0 = tpl_lead_estratto(nome)
    sample_pdf = generate_guide_pdf(
        title="Cassetto Fiscale: come accedere e leggerlo",
        package_name="ESTRATTO GRATUITO",
        guide_index=1, total=16, buyer_email=email,
    )
    lead_email_result = await send_email_now(
        to=email, subject=subj0, html=html0,
        attachments=[{"filename": "FiscoFacile_Estratto.pdf", "content": sample_pdf}],
    )
    await db.email_jobs.insert_one({
        "id": str(uuid.uuid4()), "to": email, "subject": subj0,
        "html": html0,
        "kind": "lead_estratto",
        "status": lead_email_result.get("status", "failed"),
        "send_at": _now_iso(),
        "sent_at": _now_iso() if lead_email_result.get("status") in ("sent", "previewed") else None,
        "created_at": _now_iso(), "meta": {"lead_id": lead_id},
        "result": lead_email_result,
    })

    # Day 2 — coupon
    subj2, html2 = tpl_lead_coupon(nome, coupon_code)
    await schedule_email(db, email, subj2, html2,
                        send_at=now + timedelta(days=2),
                        kind="lead_coupon",
                        meta={"lead_id": lead_id, "coupon": coupon_code})

    # Day 4 — last call
    subj4, html4 = tpl_lead_last_call(nome)
    await schedule_email(db, email, subj4, html4,
                        send_at=now + timedelta(days=4),
                        kind="lead_last_call",
                        meta={"lead_id": lead_id})

    return LeadOut(**doc)


@api_router.get("/leads", response_model=List[LeadOut])
async def list_leads():
    leads = await db.leads.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [LeadOut(**l) for l in leads]


# ----------- Coupon validation -----------
@api_router.get("/coupons/{code}")
async def check_coupon(code: str):
    coupon = await _validate_coupon(code)
    if not coupon:
        raise HTTPException(status_code=404, detail="Codice non valido o scaduto")
    return {
        "code": coupon["code"],
        "discount_eur": coupon["discount_eur"],
        "applies_to": coupon["applies_to"],
    }


# ----------- Checkout -----------
@api_router.post("/checkout/session", response_model=CheckoutResponse)
async def create_checkout_session(payload: CheckoutRequest, request: Request):
    buyer_email = _normalize_email(payload.email)
    buyer_password = (payload.password or "").strip()

    normalized_payload = CheckoutRequest(
        package_id=payload.package_id,
        origin_url=payload.origin_url,
        email=buyer_email,
        coupon=payload.coupon,
    )
    pkg, final_amount, discount, coupon_used, origin, metadata = await _resolve_checkout(normalized_payload)
    await _ensure_customer_account(buyer_email, buyer_password)
    success_url = f"{origin}/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/?cancelled=true"

    host_url = str(request.base_url)
    webhook_url = f"{host_url.rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    checkout_request = CheckoutSessionRequest(
        amount=final_amount, currency=pkg["currency"],
        success_url=success_url, cancel_url=cancel_url, metadata=metadata,
    )
    session = await stripe_checkout.create_checkout_session(checkout_request)

    tx_doc = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "package_id": payload.package_id, "package_name": pkg["name"],
        "amount": final_amount, "discount": discount,
        "coupon": coupon_used, "currency": pkg["currency"],
        "email": buyer_email, "metadata": metadata,
        "origin_url": origin,
        "status": "initiated", "payment_status": "unpaid",
        "emails_sent": False,
        "created_at": _now_iso(), "updated_at": _now_iso(),
    }
    await db.payment_transactions.insert_one(tx_doc)
    await google_sheets_sync.upsert_order(tx_doc)
    await _track_sheet_event(
        "checkout_session_created",
        "order",
        session.session_id,
        session_id=session.session_id,
        email=buyer_email,
        package_id=payload.package_id,
        amount=final_amount,
        status="initiated",
        payment_status="unpaid",
        source=metadata.get("source", "fisco_facile_landing"),
        note="Checkout session creata",
        metadata={"coupon": coupon_used, "origin_url": origin},
        created_at=tx_doc["created_at"],
    )

    return CheckoutResponse(
        url=session.url, session_id=session.session_id,
        final_amount=final_amount, discount=discount,
    )


@api_router.post("/checkout/test-bypass", response_model=CheckoutResponse)
async def create_test_bypass_checkout(payload: CheckoutRequest, request: Request):
    if not ALLOW_TEST_BYPASS:
        raise HTTPException(status_code=403, detail="Bypass test non abilitato")
    if TEST_BYPASS_LOCAL_ONLY and not _is_local_request(request):
        raise HTTPException(status_code=403, detail="Bypass test consentito solo in locale")

    buyer_email = _normalize_email(payload.email)
    buyer_password = (payload.password or "").strip()

    normalized_payload = CheckoutRequest(
        package_id=payload.package_id,
        origin_url=payload.origin_url,
        email=buyer_email,
        coupon=payload.coupon,
    )
    pkg, final_amount, discount, coupon_used, origin, metadata = await _resolve_checkout(normalized_payload)
    await _ensure_customer_account(buyer_email, buyer_password)
    session_id = f"cs_bypass_{uuid.uuid4().hex[:20]}"
    amount_total = int(round(final_amount * 100))

    tx = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "package_id": payload.package_id,
        "package_name": pkg["name"],
        "amount": final_amount,
        "amount_total": amount_total,
        "discount": discount,
        "coupon": coupon_used,
        "currency": pkg["currency"],
        "email": buyer_email,
        "metadata": {**metadata, "test_bypass": "true"},
        "origin_url": origin,
        "status": "complete",
        "payment_status": "paid",
        "emails_sent": False,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.payment_transactions.insert_one(tx)
    await google_sheets_sync.upsert_order(tx)
    await _track_sheet_event(
        "checkout_test_bypass_created",
        "order",
        session_id,
        session_id=session_id,
        email=buyer_email,
        package_id=payload.package_id,
        amount=final_amount,
        status="complete",
        payment_status="paid",
        source=metadata.get("source", "fisco_facile_landing"),
        note="Ordine creato con bypass test",
        metadata={"coupon": coupon_used, "test_bypass": True},
        created_at=tx["created_at"],
    )
    await _trigger_post_purchase(tx, amount_total)

    return CheckoutResponse(
        url=f"{origin}/success?session_id={session_id}",
        session_id=session_id,
        final_amount=final_amount,
        discount=discount,
    )


@api_router.get("/checkout/status/{session_id}", response_model=CheckoutStatusOut)
async def get_checkout_status(session_id: str, request: Request):
    tx = await db.payment_transactions.find_one(
        {"session_id": session_id}, {"_id": 0}
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Sessione non trovata")

    if tx.get("payment_status") == "paid" and tx.get("status") == "complete":
        return CheckoutStatusOut(
            session_id=session_id, status=tx["status"],
            payment_status=tx["payment_status"],
            amount_total=int(round(float(tx["amount"]) * 100)),
            currency=tx["currency"], package_id=tx.get("package_id"),
            already_processed=True,
        )

    host_url = str(request.base_url)
    webhook_url = f"{host_url.rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    try:
        status_resp = await stripe_checkout.get_checkout_status(session_id)
    except Exception as e:
        logging.warning(f"Stripe lookup failed for {session_id}: {e}")
        return CheckoutStatusOut(
            session_id=session_id, status=tx.get("status", "pending"),
            payment_status=tx.get("payment_status", "unpaid"),
            amount_total=int(round(float(tx["amount"]) * 100)),
            currency=tx.get("currency", "eur"),
            package_id=tx.get("package_id"), already_processed=False,
        )

    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": status_resp.status,
            "payment_status": status_resp.payment_status,
            "amount_total": status_resp.amount_total,
            "updated_at": _now_iso(),
        }},
    )
    updated_tx = {
        **tx,
        "status": status_resp.status,
        "payment_status": status_resp.payment_status,
        "amount_total": status_resp.amount_total,
        "updated_at": _now_iso(),
    }
    await google_sheets_sync.upsert_order(updated_tx)

    # Trigger post-purchase emails ONCE on successful payment
    if (status_resp.payment_status == "paid"
            and not tx.get("emails_sent")):
        await _track_sheet_event(
            "order_paid",
            "order",
            session_id,
            session_id=session_id,
            email=updated_tx.get("email") or updated_tx.get("metadata", {}).get("email", ""),
            package_id=updated_tx.get("package_id", ""),
            amount=updated_tx.get("amount"),
            status=updated_tx.get("status", ""),
            payment_status="paid",
            source=updated_tx.get("metadata", {}).get("source", ""),
            note="Pagamento confermato da polling checkout",
            metadata={"amount_total": status_resp.amount_total},
            created_at=updated_tx.get("updated_at"),
        )
        await _trigger_post_purchase(tx, status_resp.amount_total)

    return CheckoutStatusOut(
        session_id=session_id, status=status_resp.status,
        payment_status=status_resp.payment_status,
        amount_total=status_resp.amount_total,
        currency=status_resp.currency,
        package_id=tx.get("package_id"), already_processed=False,
    )


async def _trigger_post_purchase(tx: Dict, amount_cents: int):
    email = tx.get("email") or tx.get("metadata", {}).get("email")
    if not email:
        # No buyer email — mark and return (Stripe might not give email)
        now = _now_iso()
        await db.payment_transactions.update_one(
            {"session_id": tx["session_id"]},
            {"$set": {"emails_sent": True, "emails_sent_at": now}},
        )
        await google_sheets_sync.upsert_order({
            **tx,
            "emails_sent": True,
            "emails_sent_at": now,
            "updated_at": now,
        })
        await _track_sheet_event(
            "purchase_email_skipped",
            "order",
            tx["session_id"],
            session_id=tx["session_id"],
            package_id=tx.get("package_id", ""),
            amount=tx.get("amount"),
            status=tx.get("status", ""),
            payment_status=tx.get("payment_status", ""),
            source=tx.get("metadata", {}).get("source", ""),
            note="Nessuna email cliente disponibile per il post-acquisto",
            created_at=now,
        )
        return

    package_name = tx.get("package_name", "Le tue guide")
    origin = tx.get("origin_url") or PUBLIC_SITE_URL
    download_url = f"{origin}/download/{tx['session_id']}"
    amount = amount_cents / 100.0
    name = email.split("@")[0]

    # Day 0 — confirm + download link (immediate)
    subj0, html0 = tpl_purchase_confirm(name, package_name, download_url, amount)
    purchase_email_result = await send_email_now(to=email, subject=subj0, html=html0)
    await db.email_jobs.insert_one({
        "id": str(uuid.uuid4()), "to": email, "subject": subj0,
        "html": html0, "kind": "purchase_confirm",
        "status": purchase_email_result.get("status", "failed"),
        "send_at": _now_iso(),
        "sent_at": _now_iso() if purchase_email_result.get("status") in ("sent", "previewed") else None,
        "created_at": _now_iso(),
        "meta": {"session_id": tx["session_id"]},
        "result": purchase_email_result,
    })

    # Day 3 — followup
    now = datetime.now(timezone.utc)
    subj3, html3 = tpl_purchase_followup(name, download_url)
    await schedule_email(db, email, subj3, html3,
                        send_at=now + timedelta(days=3),
                        kind="purchase_followup",
                        meta={"session_id": tx["session_id"]})

    # Day 7 — review
    subj7, html7 = tpl_purchase_review(name)
    await schedule_email(db, email, subj7, html7,
                        send_at=now + timedelta(days=7),
                        kind="purchase_review",
                        meta={"session_id": tx["session_id"]})

    # Mark coupon as used if present
    if tx.get("coupon"):
        await db.coupons.update_one(
            {"code": tx["coupon"]},
            {"$set": {"used": True, "used_at": _now_iso()}},
        )

    now = _now_iso()
    await db.payment_transactions.update_one(
        {"session_id": tx["session_id"]},
        {"$set": {"emails_sent": True, "emails_sent_at": now}},
    )
    updated_tx = {
        **tx,
        "email": email,
        "emails_sent": True,
        "emails_sent_at": now,
        "updated_at": now,
    }
    await google_sheets_sync.upsert_order(updated_tx)
    await _track_sheet_event(
        "purchase_emails_triggered",
        "order",
        tx["session_id"],
        session_id=tx["session_id"],
        email=email,
        package_id=tx.get("package_id", ""),
        amount=tx.get("amount"),
        status=tx.get("status", ""),
        payment_status=tx.get("payment_status", ""),
        source=tx.get("metadata", {}).get("source", ""),
        note="Sequenza email post-acquisto creata",
        metadata={"download_url": download_url},
        created_at=now,
    )


@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    host_url = str(request.base_url)
    webhook_url = f"{host_url.rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    try:
        event = await stripe_checkout.handle_webhook(body, signature)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook non valido")

    if event.session_id:
        await db.payment_transactions.update_one(
            {"session_id": event.session_id},
            {"$set": {
                "payment_status": event.payment_status,
                "webhook_event": event.event_type,
                "updated_at": _now_iso(),
            }},
        )
        tx_updated = await db.payment_transactions.find_one(
            {"session_id": event.session_id}, {"_id": 0}
        )
        if tx_updated:
            await google_sheets_sync.upsert_order(tx_updated)
            await _track_sheet_event(
                "stripe_webhook_received",
                "order",
                event.session_id,
                session_id=event.session_id,
                email=tx_updated.get("email") or tx_updated.get("metadata", {}).get("email", ""),
                package_id=tx_updated.get("package_id", ""),
                amount=tx_updated.get("amount"),
                status=tx_updated.get("status", ""),
                payment_status=event.payment_status,
                source=tx_updated.get("metadata", {}).get("source", ""),
                note=event.event_type,
                metadata={"webhook_event": event.event_type},
                created_at=tx_updated.get("updated_at"),
            )
        # Trigger post-purchase emails if paid
        if event.payment_status == "paid":
            tx = await db.payment_transactions.find_one(
                {"session_id": event.session_id}, {"_id": 0}
            )
            if tx and not tx.get("emails_sent"):
                await _trigger_post_purchase(tx, tx.get("amount_total", int(tx["amount"] * 100)))

    return {"received": True}


# ----------- Download protected -----------
@api_router.get("/download/{session_id}")
async def get_download_info(session_id: str):
    tx = await db.payment_transactions.find_one(
        {"session_id": session_id}, {"_id": 0}
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Acquisto non trovato")
    if tx.get("payment_status") != "paid":
        raise HTTPException(status_code=403, detail="Pagamento non completato")

    pkg = PACKAGES.get(tx["package_id"], {})
    guides_list = []
    counter = 0
    for cat in pkg.get("includes", []):
        for idx, title in enumerate(GUIDES.get(cat, [])):
            counter += 1
            guides_list.append({
                "global_index": counter, "category": cat,
                "category_index": idx + 1, "title": title,
                "url": f"/api/download/{session_id}/file/{cat}/{idx}",
            })

    return DownloadInfo(
        package_id=tx["package_id"], package_name=tx.get("package_name", ""),
        buyer_email=tx.get("email"),
        paid_at=tx.get("updated_at"), guides=guides_list,
    )


@api_router.get("/download/{session_id}/file/{category}/{idx}")
async def download_guide_file(session_id: str, category: str, idx: int):
    tx = await db.payment_transactions.find_one(
        {"session_id": session_id}, {"_id": 0}
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Acquisto non trovato")
    if tx.get("payment_status") != "paid":
        raise HTTPException(status_code=403, detail="Pagamento non completato")

    pkg = PACKAGES.get(tx["package_id"], {})
    if category not in pkg.get("includes", []):
        raise HTTPException(status_code=403, detail="Categoria non inclusa nel pacchetto")

    guides = GUIDES.get(category, [])
    if idx < 0 or idx >= len(guides):
        raise HTTPException(status_code=404, detail="Guida non trovata")

    title = guides[idx]
    pdf_bytes = generate_guide_pdf(
        title=title,
        package_name="PRIVATI" if category == "privati" else "AZIENDE",
        guide_index=idx + 1, total=len(guides),
        buyer_email=tx.get("email"),
    )
    safe = "".join(c if c.isalnum() else "_" for c in title)[:60]
    filename = f"FiscoFacile_{safe}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ----------- Admin -----------
@api_router.post("/admin/login")
async def admin_login(payload: AdminLogin, request: Request):
    email = payload.email.lower().strip()
    ip_address = _client_ip(request)
    user_agent = request.headers.get("user-agent", "").strip()

    attempt = await _get_admin_login_attempt(email, ip_address)
    if attempt and attempt.get("locked_until"):
        locked_until = _parse_iso(attempt["locked_until"])
        retry_after = ADMIN_LOCKOUT_MINUTES * 60
        if locked_until:
            retry_after = max(int((locked_until - _now_utc()).total_seconds()), 1)
        raise HTTPException(
            status_code=429,
            detail="Troppi tentativi di accesso. Riprova tra qualche minuto.",
            headers={"Retry-After": str(retry_after)},
        )

    email_ok = _constant_time_eq(email, ADMIN_EMAIL)
    password_ok = _admin_password_matches(payload.password)
    if not email_ok or not password_ok:
        await _register_admin_login_failure(email, ip_address)
        raise HTTPException(status_code=401, detail="Credenziali errate")

    await _clear_admin_login_failures(email, ip_address)
    token = secrets.token_urlsafe(32)
    expires = (_now_utc() + timedelta(hours=ADMIN_SESSION_HOURS)).isoformat()
    await db.admin_sessions.insert_one({
        "id": str(uuid.uuid4()),
        "token_hash": _hash_token(token),
        "email": email,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "expires_at": expires,
        "created_at": _now_iso(),
        "last_seen_at": _now_iso(),
    })
    return {"token": token, "expires_at": expires}


def _x_admin_token(x_admin_token: Optional[str] = Header(None)):
    return x_admin_token


@api_router.post("/admin/logout")
async def admin_logout(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token:
        session = await _find_admin_session(x_admin_token)
        if session:
            await _delete_admin_session(session)
    return {"ok": True}


@api_router.get("/admin/stats")
async def admin_stats(x_admin_token: Optional[str] = Header(None)):
    if not await _verify_admin(x_admin_token):
        raise HTTPException(status_code=401, detail="Non autorizzato")

    leads_count = await db.leads.count_documents({})
    paid_count = await db.payment_transactions.count_documents({"payment_status": "paid"})
    total_count = await db.payment_transactions.count_documents({})
    pending_jobs = await db.email_jobs.count_documents({"status": "pending"})
    sent_jobs = await db.email_jobs.count_documents({"status": "sent"})
    previewed_jobs = await db.email_jobs.count_documents({"status": "previewed"})

    paid_txs = await db.payment_transactions.find(
        {"payment_status": "paid"}, {"_id": 0, "amount": 1}
    ).to_list(1000)
    revenue = round(sum(float(t.get("amount", 0)) for t in paid_txs), 2)

    return {
        "leads": leads_count,
        "orders_paid": paid_count,
        "orders_total": total_count,
        "revenue_eur": revenue,
        "emails_pending": pending_jobs,
        "emails_sent": sent_jobs,
        "emails_previewed": previewed_jobs,
    }


@api_router.get("/admin/leads")
async def admin_leads(x_admin_token: Optional[str] = Header(None)):
    if not await _verify_admin(x_admin_token):
        raise HTTPException(status_code=401, detail="Non autorizzato")
    leads = await db.leads.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"leads": leads}


@api_router.get("/admin/orders")
async def admin_orders(x_admin_token: Optional[str] = Header(None)):
    if not await _verify_admin(x_admin_token):
        raise HTTPException(status_code=401, detail="Non autorizzato")
    orders = await db.payment_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"orders": orders}


@api_router.get("/admin/emails")
async def admin_emails(x_admin_token: Optional[str] = Header(None)):
    if not await _verify_admin(x_admin_token):
        raise HTTPException(status_code=401, detail="Non autorizzato")
    jobs = await db.email_jobs.find({}, {"_id": 0, "html": 0}).sort("created_at", -1).to_list(500)
    for job in jobs:
        job["preview_available"] = True
        job["send_now_available"] = job.get("status") in ("pending", "failed", "previewed")
    return {"emails": jobs}


@api_router.get("/admin/emails/{email_id}/preview", response_class=HTMLResponse)
async def admin_email_preview(
    email_id: str,
    x_admin_token: Optional[str] = Header(None),
    preview_token: Optional[str] = None,
):
    is_authorized = await _verify_admin(x_admin_token)
    if not is_authorized and not await _verify_admin_preview_token(email_id, preview_token or ""):
        raise HTTPException(status_code=401, detail="Non autorizzato")

    job = await db.email_jobs.find_one({"id": email_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Email non trovata")

    raw_html = job.get("html") or ""
    if raw_html.lstrip().startswith("<"):
        return HTMLResponse(raw_html)

    body = (
        "<!DOCTYPE html><html><body style='font-family: sans-serif; padding: 24px;'>"
        f"<h1 style='margin-bottom: 8px;'>Anteprima email</h1>"
        f"<p><strong>Destinatario:</strong> {html.escape(job.get('to', ''))}</p>"
        f"<p><strong>Oggetto:</strong> {html.escape(job.get('subject', ''))}</p>"
        f"<pre style='white-space: pre-wrap; background: #f4f4f5; padding: 16px; border-radius: 8px;'>"
        f"{html.escape(raw_html or 'Contenuto non disponibile.')}</pre>"
        "</body></html>"
    )
    return HTMLResponse(body)


@api_router.post("/admin/emails/{email_id}/preview-link")
async def admin_email_preview_link(
    email_id: str,
    request: Request,
    x_admin_token: Optional[str] = Header(None),
):
    if not await _verify_admin(x_admin_token):
        raise HTTPException(status_code=401, detail="Non autorizzato")

    job = await db.email_jobs.find_one({"id": email_id}, {"_id": 0, "id": 1})
    if not job:
        raise HTTPException(status_code=404, detail="Email non trovata")

    preview = await _create_admin_preview_token(email_id)
    base_url = str(request.base_url).rstrip("/")
    return {
        "preview_url": (
            f"{base_url}/api/admin/emails/{email_id}/preview"
            f"?preview_token={preview['token']}"
        ),
        "expires_at": preview["expires_at"],
    }


@api_router.post("/admin/emails/{email_id}/send-now")
async def admin_email_send_now(email_id: str, x_admin_token: Optional[str] = Header(None)):
    if not await _verify_admin(x_admin_token):
        raise HTTPException(status_code=401, detail="Non autorizzato")

    job = await db.email_jobs.find_one({"id": email_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Email non trovata")

    if job.get("status") == "sent":
        return {"ok": True, "status": "sent", "already_sent": True}

    if not job.get("to") or not job.get("subject"):
        raise HTTPException(status_code=400, detail="Email non valida")

    result = await send_email_now(
        to=job["to"],
        subject=job["subject"],
        html=job.get("html") or "",
    )
    now = _now_iso()
    status = result.get("status", "failed")

    await db.email_jobs.update_one(
        {"id": email_id},
        {"$set": {
            "status": status,
            "result": result,
            "sent_at": now if status in ("sent", "previewed") else None,
            "updated_at": now,
            "manual_triggered_at": now,
        }},
    )
    await _track_sheet_event(
        "admin_email_send_now",
        "email_job",
        email_id,
        email=job.get("to", ""),
        status=status,
        source="admin_dashboard",
        note=f"Invio manuale email {job.get('kind', '')}",
        metadata={"kind": job.get("kind"), "result": result},
        created_at=now,
    )

    return {
        "ok": status in ("sent", "previewed"),
        "status": status,
        "result": result,
        "manual_triggered_at": now,
    }


# ----------- Customer Area (magic link) -----------
@api_router.post("/customer/login")
async def customer_password_login(payload: CustomerPasswordLoginRequest):
    email = _normalize_email(payload.email)
    await _authenticate_customer_account(email, payload.password)
    paid_orders = await db.payment_transactions.count_documents(
        {"email": email, "payment_status": "paid"}
    )

    session_payload = await _create_customer_session_for_email(email, mode="password_login")
    await _track_sheet_event(
        "customer_session_started",
        "customer_access",
        session_payload["doc"]["id"],
        email=email,
        status="active",
        source="customer_area",
        note="Sessione cliente aperta da login email e password",
        metadata={"mode": "password_login", "paid_orders": paid_orders},
        created_at=_now_iso(),
    )
    return {
        "ok": True,
        "token": session_payload["token"],
        "expires_at": session_payload["expires_at"],
    }


@api_router.post("/customer/request-access")
async def request_customer_access(payload: CustomerAccessRequest, request: Request):
    email = _normalize_email(payload.email)
    ip_address = _client_ip(request)
    rate_limited = await _is_customer_access_rate_limited(ip_address)
    await _register_customer_access_attempt(ip_address, email)

    # Always return success even if no orders found (do not leak account existence)
    paid_count = await db.payment_transactions.count_documents(
        {"email": email, "payment_status": "paid"}
    )

    if paid_count > 0 and not rate_limited:
        token_payload = await _create_customer_magic_token(email=email)
        token = token_payload["token"]

        # Build magic link from request origin (or fall back)
        origin = request.headers.get("origin") or request.headers.get("referer", "")
        if origin:
            origin = origin.rstrip("/").split("/area-riservata")[0]
        if not origin:
            origin = PUBLIC_SITE_URL
        magic_link = f"{origin}/area-riservata?token={token}"

        subject, html = tpl_customer_access(magic_link)
        customer_email_result = await send_email_now(to=email, subject=subject, html=html)
        await db.email_jobs.insert_one({
            "id": str(uuid.uuid4()), "to": email, "subject": subject,
            "html": html, "kind": "customer_access",
            "status": customer_email_result.get("status", "failed"),
            "send_at": _now_iso(),
            "sent_at": _now_iso() if customer_email_result.get("status") in ("sent", "previewed") else None,
            "created_at": _now_iso(),
            "meta": {"token": token[:8] + "..."},
            "result": customer_email_result,
        })
        await _track_sheet_event(
            "customer_access_requested",
            "customer_access",
            token_payload["doc"]["id"],
            email=email,
            status=customer_email_result.get("status", ""),
            source="customer_area",
            note="Magic link area riservata inviato",
            metadata={"paid_orders_found": paid_count > 0, "rate_limited": False},
            created_at=_now_iso(),
        )
    elif rate_limited:
        await _track_sheet_event(
            "customer_access_rate_limited",
            "customer_access",
            f"rate_limited_{ip_address}",
            email=email,
            status="ignored",
            source="customer_area",
            note="Richiesta magic link limitata per eccesso di tentativi",
            metadata={"paid_orders_found": paid_count > 0},
            created_at=_now_iso(),
        )
    else:
        await _track_sheet_event(
            "customer_access_requested",
            "customer_access",
            f"no_orders_{email}",
            email=email,
            status="ignored",
            source="customer_area",
            note="Richiesta accesso senza ordini pagati",
            metadata={"paid_orders_found": False},
            created_at=_now_iso(),
        )

    return {
        "ok": True,
        "message": "Se l'email è associata a un acquisto, ti abbiamo inviato il link di accesso.",
    }


@api_router.post("/customer/session/exchange")
async def exchange_customer_session(payload: CustomerSessionExchangeRequest):
    token_doc = await _consume_customer_magic_token(payload.token.strip())
    session_payload = await _create_customer_session(token_doc)
    await _track_sheet_event(
        "customer_session_started",
        "customer_access",
        session_payload["doc"]["id"],
        email=token_doc["email"],
        status="active",
        source="customer_area",
        note="Sessione cliente aperta da magic link",
        metadata={"mode": token_doc.get("mode", "magic_link")},
        created_at=_now_iso(),
    )
    return {
        "ok": True,
        "token": session_payload["token"],
        "expires_at": session_payload["expires_at"],
    }


@api_router.post("/customer/test-access")
async def request_customer_test_access(request: Request):
    if not ALLOW_TEST_BYPASS:
        raise HTTPException(status_code=403, detail="Accesso test non abilitato")
    if CUSTOMER_TEST_ACCESS_LOCAL_ONLY and not _is_local_request(request):
        raise HTTPException(status_code=403, detail="Accesso test disponibile solo in locale")

    paid_orders = await db.payment_transactions.find(
        {"payment_status": "paid"}, {"_id": 0}
    ).sort("created_at", -1).to_list(25)
    if not paid_orders:
        fallback_session_id = f"cs_test_access_{uuid.uuid4().hex[:20]}"
        fallback_order = {
            "id": str(uuid.uuid4()),
            "session_id": fallback_session_id,
            "package_id": "bundle",
            "package_name": PACKAGES["bundle"]["name"],
            "amount": float(PACKAGES["bundle"]["price"]),
            "amount_total": int(round(float(PACKAGES["bundle"]["price"]) * 100)),
            "discount": 0.0,
            "coupon": None,
            "currency": PACKAGES["bundle"]["currency"],
            "email": "accesso-test@locale",
            "metadata": {
                "package_id": "bundle",
                "package_name": PACKAGES["bundle"]["name"],
                "source": "customer_test_access",
                "origin_url": PUBLIC_SITE_URL,
                "test_bypass": "true",
                "auto_seeded": "true",
            },
            "origin_url": PUBLIC_SITE_URL,
            "status": "complete",
            "payment_status": "paid",
            "emails_sent": True,
            "emails_sent_at": _now_iso(),
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        await db.payment_transactions.insert_one(fallback_order)
        await google_sheets_sync.upsert_order(fallback_order)
        await _track_sheet_event(
            "customer_test_access_seeded_order",
            "order",
            fallback_session_id,
            session_id=fallback_session_id,
            email=fallback_order["email"],
            package_id="bundle",
            amount=fallback_order["amount"],
            status="complete",
            payment_status="paid",
            source="customer_test_access",
            note="Ordine demo creato automaticamente per Accedi in test",
            metadata={"auto_seeded": True},
            created_at=fallback_order["created_at"],
        )
        paid_orders = [fallback_order]

    session_ids = [order["session_id"] for order in paid_orders]
    label_email = next(
        (order.get("email") for order in paid_orders if order.get("email")),
        "accesso-test@locale",
    )
    token_payload = await _create_customer_magic_token(
        email=label_email,
        mode="test_bypass",
        session_ids=session_ids,
    )

    origin = request.headers.get("origin") or request.headers.get("referer", "")
    if origin:
        origin = origin.rstrip("/").split("/area-riservata")[0]
    if not origin:
        origin = PUBLIC_SITE_URL

    return {
        "ok": True,
        "token": token_payload["token"],
        "url": f"{origin}/area-riservata?token={token_payload['token']}",
    }


@api_router.post("/customer/logout")
async def customer_logout(x_customer_token: Optional[str] = Header(None)):
    if x_customer_token:
        session = await _find_customer_session(x_customer_token)
        if session:
            await _track_sheet_event(
                "customer_session_closed",
                "customer_access",
                session.get("id", "customer_session"),
                email=session.get("email", ""),
                status="closed",
                source="customer_area",
                note="Logout area riservata cliente",
                metadata={"mode": session.get("mode", "magic_link")},
                created_at=_now_iso(),
            )
            await _delete_customer_session_doc(session)
    return {"ok": True}


@api_router.get("/customer/orders")
async def customer_orders(
    token: Optional[str] = None,
    x_customer_token: Optional[str] = Header(None),
):
    auth_token = x_customer_token or token
    sess = await _get_customer_session(auth_token)
    if not sess:
        raise HTTPException(status_code=404, detail="Token non valido")

    email = sess["email"]
    if sess.get("mode") == "test_bypass":
        orders = await db.payment_transactions.find(
            {"session_id": {"$in": sess.get("session_ids", [])}, "payment_status": "paid"},
            {"_id": 0},
        ).sort("created_at", -1).to_list(100)
    else:
        orders = await db.payment_transactions.find(
            {"email": email, "payment_status": "paid"}, {"_id": 0}
        ).sort("created_at", -1).to_list(100)

    # Decorate each order with download info
    result = []
    for o in orders:
        pkg = PACKAGES.get(o.get("package_id"), {})
        guides = []
        for cat in pkg.get("includes", []):
            for idx, title in enumerate(GUIDES.get(cat, [])):
                guides.append({
                    "category": cat, "category_index": idx + 1,
                    "title": title,
                    "url": f"/api/download/{o['session_id']}/file/{cat}/{idx}",
                })
        result.append({
            "session_id": o["session_id"],
            "package_id": o["package_id"],
            "package_name": o.get("package_name"),
            "amount": o.get("amount"),
            "purchased_at": o.get("updated_at") or o.get("created_at"),
            "guides_count": len(guides),
            "download_url": f"/download/{o['session_id']}",
            "guides": guides,
        })

    return {"email": email, "orders": result}


# ============================================================
# APP SETUP
# ============================================================
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_build_cors_origins(),
    allow_origin_regex=_cors_origin_regex(),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Scheduler — process due email jobs every minute
scheduler = AsyncIOScheduler(timezone="UTC")


async def _run_jobs_safe():
    try:
        sent = await run_due_jobs(db)
        if sent:
            logger.info(f"Scheduler dispatched {sent} due emails")
    except Exception as e:
        logger.error(f"Scheduler tick failed: {e}")


@app.on_event("startup")
async def on_startup():
    scheduler.add_job(_run_jobs_safe, "interval", minutes=1, id="email_dispatcher",
                      replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — email dispatcher every 60s")


@app.on_event("shutdown")
async def shutdown_db_client():
    if scheduler.running:
        scheduler.shutdown(wait=False)
    client.close()
