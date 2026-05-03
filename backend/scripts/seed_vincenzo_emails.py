"""Demo email seeder for Vincenzo's test account."""
import os
import sys
import asyncio
import uuid
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Add backend dir to path so we can import email_service & pdf_service
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient

# Load env from backend dir (script is in /scripts/)
load_dotenv(Path(__file__).parent.parent / ".env")

import resend
resend.api_key = os.environ["RESEND_API_KEY"]

# Force-set the email_service module level key
import email_service
email_service.RESEND_API_KEY = os.environ["RESEND_API_KEY"]

from email_service import (
    send_email_now,
    tpl_purchase_confirm, tpl_purchase_followup, tpl_purchase_review,
    tpl_lead_estratto, tpl_lead_coupon, tpl_customer_access,
)
from pdf_service import generate_guide_pdf

EMAIL = "vincenzo.rosa99@gmail.com"
NAME = "Vincenzo"
SESSION_ID = "cs_test_vincenzo_demo"
ORIGIN = os.environ.get("PUBLIC_SITE_URL", "http://127.0.0.1:3000").rstrip("/")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]

    tok_doc = await db.customer_tokens.find_one(
        {"email": EMAIL}, sort=[("created_at", -1)]
    )
    token = tok_doc["token"] if tok_doc else None
    magic_link = f"{ORIGIN}/area-riservata?token={token}"
    download_url = f"{ORIGIN}/download/{SESSION_ID}"

    emails_to_send = [
        ("purchase_confirm",
         *tpl_purchase_confirm(NAME, "Bundle Privati + Aziende", download_url, 67.50)),
        ("lead_coupon",
         *tpl_lead_coupon(NAME, "FFDEMO99")),
        ("purchase_followup",
         *tpl_purchase_followup(NAME, download_url)),
        ("purchase_review",
         *tpl_purchase_review(NAME)),
        ("customer_access",
         *tpl_customer_access(magic_link)),
    ]

    print(f"📨 Sending 6 emails to {EMAIL}...\n")
    for kind, subject, html in emails_to_send:
        r = await send_email_now(to=EMAIL, subject=subject, html=html)
        status_icon = "✅" if r.get("status") == "sent" else "❌"
        print(f"{status_icon} {kind}: {r}")

    # Estratto with PDF
    pdf = generate_guide_pdf(
        title="Cassetto Fiscale: come accedere e leggerlo",
        package_name="ESTRATTO GRATUITO",
        guide_index=1, total=16, buyer_email=EMAIL,
    )
    s, h = tpl_lead_estratto(NAME)
    r = await send_email_now(
        to=EMAIL, subject=s, html=h,
        attachments=[{"filename": "FiscoFacile_Estratto.pdf", "content": pdf}],
    )
    icon = "✅" if r.get("status") == "sent" else "❌"
    print(f"{icon} lead_estratto + PDF: {r}")

    print(f"\n🎯 Magic link: {magic_link}")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
