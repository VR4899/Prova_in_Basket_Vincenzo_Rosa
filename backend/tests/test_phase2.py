"""Phase 2 backend tests: leads+coupons, checkout w/ coupon, downloads, admin."""
import os, requests, pytest, time
from dotenv import dotenv_values
from pymongo import MongoClient
from datetime import datetime, timezone

BASE = (os.environ.get('REACT_APP_BACKEND_URL') or
        dotenv_values('/app/frontend/.env').get('REACT_APP_BACKEND_URL')).rstrip('/')

BENV = dotenv_values('/app/backend/.env')
MONGO = MongoClient(BENV['MONGO_URL'])[BENV['DB_NAME']]

S = requests.Session(); S.headers.update({'Content-Type':'application/json'})

# -------- LEADS + COUPON --------
@pytest.fixture(scope="module")
def lead():
    r = S.post(f"{BASE}/api/leads", json={
        "nome":"TEST_Phase2","email":"test_phase2@example.com","interesse":"estratto"})
    assert r.status_code==200, r.text
    return r.json()

def test_lead_returns_coupon(lead):
    assert lead.get('coupon_code','').startswith('FF')
    assert len(lead['coupon_code'])==8

def test_lead_schedules_three_email_jobs(lead):
    time.sleep(0.5)
    jobs = list(MONGO.email_jobs.find({"meta.lead_id": lead["id"]}))
    kinds = {j["kind"] for j in jobs}
    assert {"lead_estratto","lead_coupon","lead_last_call"}.issubset(kinds), kinds
    for j in jobs:
        if j["kind"]=="lead_estratto":
            assert j["status"] in ("sent","failed","skipped")
        else:
            assert j["status"]=="pending"

def test_coupon_get_valid(lead):
    code = lead["coupon_code"]
    r = S.get(f"{BASE}/api/coupons/{code}")
    assert r.status_code==200
    d = r.json()
    assert d["code"]==code
    assert d["discount_eur"]==10.0
    assert "bundle" in d["applies_to"]

def test_coupon_get_invalid():
    r = S.get(f"{BASE}/api/coupons/FFINVALID00")
    assert r.status_code==404

# -------- CHECKOUT WITH COUPON --------
def test_checkout_with_valid_coupon(lead):
    r = S.post(f"{BASE}/api/checkout/session", json={
        "package_id":"bundle","origin_url":"https://example.com",
        "coupon": lead["coupon_code"], "email":"buyer@example.com"})
    assert r.status_code==200, r.text
    d = r.json()
    assert d["discount"]==10.0
    assert d["final_amount"]==59.0
    # verify saved in payment_transactions
    tx = MONGO.payment_transactions.find_one({"session_id": d["session_id"]})
    assert tx["coupon"]==lead["coupon_code"]
    assert tx["discount"]==10.0
    assert tx["amount"]==59.0

def test_checkout_with_invalid_coupon():
    r = S.post(f"{BASE}/api/checkout/session", json={
        "package_id":"bundle","origin_url":"https://example.com",
        "coupon":"FFINVALID00"})
    assert r.status_code==200
    d = r.json()
    assert d["discount"]==0.0
    assert d["final_amount"]==69.0

# -------- DOWNLOAD AREA --------
SEED_SID = "cs_test_phase2_seed"

@pytest.fixture(scope="module", autouse=True)
def seed_paid_session():
    # Seed a paid transaction directly
    MONGO.payment_transactions.delete_many({"session_id": SEED_SID})
    MONGO.payment_transactions.insert_one({
        "session_id": SEED_SID, "package_id":"bundle",
        "package_name":"Bundle Privati + Aziende",
        "amount":69.0, "currency":"eur", "payment_status":"paid",
        "status":"complete", "email":"test@example.com", "emails_sent": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    yield
    MONGO.payment_transactions.delete_one({"session_id": SEED_SID})

def test_download_unknown_session():
    r = S.get(f"{BASE}/api/download/cs_does_not_exist_xxx")
    assert r.status_code==404

def test_download_unpaid_session():
    sid = "cs_test_unpaid_seed"
    MONGO.payment_transactions.delete_many({"session_id": sid})
    MONGO.payment_transactions.insert_one({
        "session_id": sid, "package_id":"privati","package_name":"Privati",
        "amount":39.0, "currency":"eur","payment_status":"unpaid",
        "status":"initiated","emails_sent":False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    r = S.get(f"{BASE}/api/download/{sid}")
    assert r.status_code==403
    MONGO.payment_transactions.delete_one({"session_id": sid})

def test_download_paid_session_returns_guides():
    r = S.get(f"{BASE}/api/download/{SEED_SID}")
    assert r.status_code==200, r.text
    d = r.json()
    assert d["package_id"]=="bundle"
    assert len(d["guides"])==28  # 16 privati + 12 aziende
    assert all("url" in g and "title" in g for g in d["guides"])

def test_download_pdf_file_paid():
    r = S.get(f"{BASE}/api/download/{SEED_SID}/file/privati/0")
    assert r.status_code==200
    assert r.headers["content-type"]=="application/pdf"
    assert r.content[:4]==b"%PDF"

def test_download_pdf_idx_out_of_range():
    r = S.get(f"{BASE}/api/download/{SEED_SID}/file/privati/999")
    assert r.status_code==404

def test_download_pdf_unpaid_403():
    sid = "cs_test_unpaid2"
    MONGO.payment_transactions.delete_many({"session_id": sid})
    MONGO.payment_transactions.insert_one({
        "session_id": sid, "package_id":"privati","package_name":"P",
        "amount":39.0,"currency":"eur","payment_status":"unpaid","status":"initiated",
        "emails_sent":False,
        "created_at":datetime.now(timezone.utc).isoformat(),
        "updated_at":datetime.now(timezone.utc).isoformat(),
    })
    r = S.get(f"{BASE}/api/download/{sid}/file/privati/0")
    assert r.status_code==403
    MONGO.payment_transactions.delete_one({"session_id": sid})

# -------- ADMIN --------
@pytest.fixture(scope="module")
def admin_token():
    r = S.post(
        f"{BASE}/api/admin/login",
        json={"email":"admin@fiscofacile.it", "password":"rootroot"},
    )
    assert r.status_code==200, r.text
    return r.json()["token"]

def test_admin_login_wrong():
    r = S.post(
        f"{BASE}/api/admin/login",
        json={"email":"admin@fiscofacile.it", "password":"wrong"},
    )
    assert r.status_code==401

def test_admin_stats_unauth():
    r = S.get(f"{BASE}/api/admin/stats")
    assert r.status_code==401

def test_admin_stats_ok(admin_token):
    r = S.get(f"{BASE}/api/admin/stats", headers={"x-admin-token":admin_token})
    assert r.status_code==200
    d = r.json()
    assert "leads" in d and "orders_paid" in d and "revenue_eur" in d
    assert d["leads"]>=1

def test_admin_leads_ok(admin_token):
    r = S.get(f"{BASE}/api/admin/leads", headers={"x-admin-token":admin_token})
    assert r.status_code==200
    assert "leads" in r.json()
    for l in r.json()["leads"]:
        assert "_id" not in l

def test_admin_orders_ok(admin_token):
    r = S.get(f"{BASE}/api/admin/orders", headers={"x-admin-token":admin_token})
    assert r.status_code==200
    assert "orders" in r.json()

def test_admin_emails_ok(admin_token):
    r = S.get(f"{BASE}/api/admin/emails", headers={"x-admin-token":admin_token})
    assert r.status_code==200
    assert "emails" in r.json()

def test_admin_leads_bad_token():
    r = S.get(f"{BASE}/api/admin/leads", headers={"x-admin-token":"garbage"})
    assert r.status_code==401
