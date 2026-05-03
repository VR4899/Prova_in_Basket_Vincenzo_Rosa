import asyncio
import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import stripe


@dataclass
class CheckoutSessionRequest:
    amount: float
    currency: str
    success_url: str
    cancel_url: str
    metadata: Optional[Dict[str, str]] = None


@dataclass
class CheckoutSessionResult:
    session_id: str
    url: str


@dataclass
class CheckoutStatusResult:
    status: str
    payment_status: str
    amount_total: int
    currency: str


@dataclass
class WebhookEventResult:
    session_id: Optional[str]
    payment_status: str
    event_type: str


_mock_sessions: Dict[str, CheckoutStatusResult] = {}


class StripeCheckout:
    def __init__(self, api_key: str, webhook_url: Optional[str] = None):
        stripe.api_key = api_key
        self.api_key = api_key
        self.webhook_url = webhook_url
        self.webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        self.use_mock = (
            os.environ.get("STRIPE_MOCK", "").lower() == "true"
            or api_key == "sk_test_emergent"
        )

    async def create_checkout_session(
        self, request: CheckoutSessionRequest
    ) -> CheckoutSessionResult:
        if self.use_mock:
            return self._create_mock_session(request)

        metadata = request.metadata or {}
        params: Dict[str, Any] = {
            "mode": "payment",
            "success_url": request.success_url,
            "cancel_url": request.cancel_url,
            "metadata": metadata,
            "line_items": [
                {
                    "price_data": {
                        "currency": request.currency,
                        "product_data": {
                            "name": metadata.get("package_name", "Fisco Facile")
                        },
                        "unit_amount": int(round(request.amount * 100)),
                    },
                    "quantity": 1,
                }
            ],
        }
        if metadata.get("email"):
            params["customer_email"] = metadata["email"]

        session = await asyncio.to_thread(stripe.checkout.Session.create, **params)
        return CheckoutSessionResult(session_id=session.id, url=session.url)

    async def get_checkout_status(self, session_id: str) -> CheckoutStatusResult:
        if session_id in _mock_sessions:
            return _mock_sessions[session_id]

        session = await asyncio.to_thread(stripe.checkout.Session.retrieve, session_id)
        return CheckoutStatusResult(
            status=getattr(session, "status", "open") or "open",
            payment_status=getattr(session, "payment_status", "unpaid") or "unpaid",
            amount_total=getattr(session, "amount_total", 0) or 0,
            currency=getattr(session, "currency", "eur") or "eur",
        )

    async def handle_webhook(
        self, body: bytes, signature: Optional[str] = None
    ) -> WebhookEventResult:
        event = await asyncio.to_thread(self._parse_event, body, signature)
        event_type = self._read_attr(event, "type", "")
        data = self._read_attr(event, "data", {}) or {}
        obj = self._read_attr(data, "object", {}) or {}
        return WebhookEventResult(
            session_id=self._read_attr(obj, "id"),
            payment_status=self._read_attr(obj, "payment_status", "unpaid") or "unpaid",
            event_type=event_type,
        )

    def _parse_event(self, body: bytes, signature: Optional[str]):
        if self.webhook_secret and signature:
            return stripe.Webhook.construct_event(body, signature, self.webhook_secret)
        if self.use_mock:
            return json.loads(body.decode("utf-8"))
        if not self.webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET non configurato")
        raise ValueError("Stripe-Signature mancante o non valida")

    @staticmethod
    def _read_attr(value: Any, name: str, default: Any = None) -> Any:
        if isinstance(value, dict):
            return value.get(name, default)
        return getattr(value, name, default)

    @staticmethod
    def _create_mock_session(
        request: CheckoutSessionRequest,
    ) -> CheckoutSessionResult:
        session_id = f"cs_dev_{uuid.uuid4().hex[:20]}"
        _mock_sessions[session_id] = CheckoutStatusResult(
            status="complete",
            payment_status="paid",
            amount_total=int(round(request.amount * 100)),
            currency=request.currency,
        )
        return CheckoutSessionResult(
            session_id=session_id,
            url=request.success_url.replace("{CHECKOUT_SESSION_ID}", session_id),
        )
