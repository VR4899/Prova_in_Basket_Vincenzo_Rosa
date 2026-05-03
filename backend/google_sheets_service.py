"""Optional Google Sheets sync for leads, orders and tracking events."""
import asyncio
import json
import logging
import os
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    GOOGLE_LIBS_AVAILABLE = True
except ModuleNotFoundError:
    Credentials = None
    build = None
    GOOGLE_LIBS_AVAILABLE = False


logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _col_letter(index: int) -> str:
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


class GoogleSheetsSync:
    def __init__(self) -> None:
        self._service = None
        self._meta_cache = None
        self._lock = Lock()

        self.spreadsheet_id = os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
        self.credentials_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
        self.credentials_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        self.default_credentials_file = ROOT_DIR / "google-service-account.json"

        self.tabs = {
            "leads": {
                "title": os.environ.get("GOOGLE_SHEETS_LEADS_TAB", "Leads").strip() or "Leads",
                "headers": [
                    "id", "created_at", "nome", "email", "interesse",
                    "coupon_code", "source", "origin_url",
                ],
            },
            "orders": {
                "title": os.environ.get("GOOGLE_SHEETS_ORDERS_TAB", "Orders").strip() or "Orders",
                "headers": [
                    "session_id", "id", "created_at", "updated_at", "package_id",
                    "package_name", "email", "amount", "amount_total", "discount",
                    "coupon", "currency", "status", "payment_status",
                    "emails_sent", "origin_url", "source",
                ],
            },
            "tracking": {
                "title": os.environ.get("GOOGLE_SHEETS_TRACKING_TAB", "Tracking").strip() or "Tracking",
                "headers": [
                    "event_id", "created_at", "event_type", "entity_type", "entity_id",
                    "lead_id", "session_id", "email", "package_id", "amount",
                    "status", "payment_status", "source", "note", "metadata_json",
                ],
            },
        }

    @property
    def enabled(self) -> bool:
        return bool(GOOGLE_LIBS_AVAILABLE and self.spreadsheet_id and self._has_credentials())

    def _has_credentials(self) -> bool:
        return bool(
            self.credentials_json
            or self.credentials_file
            or self.default_credentials_file.exists()
        )

    def _load_credentials_info(self) -> Optional[Dict[str, Any]]:
        if self.credentials_json:
            try:
                return json.loads(self.credentials_json)
            except json.JSONDecodeError as exc:
                logger.error("GOOGLE_SERVICE_ACCOUNT_JSON non valido: %s", exc)
                return None

        file_path = self.credentials_file or str(self.default_credentials_file)
        path = Path(file_path)
        if not path.exists():
            return None

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Impossibile leggere credenziali Google da %s: %s", path, exc)
            return None

    def _get_service(self):
        if self._service is not None:
            return self._service

        if not GOOGLE_LIBS_AVAILABLE:
            logger.warning("Librerie Google non installate nel virtualenv backend: sync Google Sheets disattivata")
            return None

        info = self._load_credentials_info()
        if not info:
            return None

        credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
        self._service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        return self._service

    def _refresh_meta(self) -> Dict[str, Any]:
        service = self._get_service()
        if service is None:
            raise RuntimeError("Google Sheets non configurato")

        self._meta_cache = service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id
        ).execute()
        return self._meta_cache

    def _get_meta(self) -> Dict[str, Any]:
        if self._meta_cache is None:
            return self._refresh_meta()
        return self._meta_cache

    def _ensure_sheet(self, sheet_key: str) -> str:
        service = self._get_service()
        if service is None:
            raise RuntimeError("Google Sheets non configurato")

        title = self.tabs[sheet_key]["title"]
        headers = self.tabs[sheet_key]["headers"]

        meta = self._get_meta()
        sheet_titles = {
            sheet["properties"]["title"]: sheet["properties"]["sheetId"]
            for sheet in meta.get("sheets", [])
        }

        if title not in sheet_titles:
            service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": [{"addSheet": {"properties": {"title": title}}}]},
            ).execute()
            meta = self._refresh_meta()
            sheet_titles = {
                sheet["properties"]["title"]: sheet["properties"]["sheetId"]
                for sheet in meta.get("sheets", [])
            }

        header_range = f"{title}!A1:{_col_letter(len(headers))}1"
        header_values = service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=header_range,
        ).execute().get("values", [])

        current_headers = header_values[0] if header_values else []
        if current_headers != headers:
            service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=header_range,
                valueInputOption="RAW",
                body={"values": [headers]},
            ).execute()

        return title

    def _append_row_sync(self, sheet_key: str, row: Dict[str, Any]) -> None:
        service = self._get_service()
        if service is None:
            return

        with self._lock:
            title = self._ensure_sheet(sheet_key)
            headers = self.tabs[sheet_key]["headers"]
            values = [[self._serialize_value(row.get(header, "")) for header in headers]]
            service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{title}!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": values},
            ).execute()

    def _upsert_row_sync(self, sheet_key: str, key_field: str, row: Dict[str, Any]) -> None:
        service = self._get_service()
        if service is None:
            return

        with self._lock:
            title = self._ensure_sheet(sheet_key)
            headers = self.tabs[sheet_key]["headers"]
            key_value = str(row.get(key_field, "")).strip()
            if not key_value:
                raise ValueError(f"Chiave mancante per il foglio {sheet_key}")

            first_col = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{title}!A:A",
            ).execute().get("values", [])

            target_row = None
            for index, values in enumerate(first_col[1:], start=2):
                if values and str(values[0]).strip() == key_value:
                    target_row = index
                    break

            if target_row is None:
                target_row = len(first_col) + 1 if first_col else 2

            end_col = _col_letter(len(headers))
            service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{title}!A{target_row}:{end_col}{target_row}",
                valueInputOption="USER_ENTERED",
                body={"values": [[self._serialize_value(row.get(header, "")) for header in headers]]},
            ).execute()

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        return value

    async def append_lead(self, lead: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        row = {
            "id": lead.get("id"),
            "created_at": lead.get("created_at"),
            "nome": lead.get("nome"),
            "email": lead.get("email"),
            "interesse": lead.get("interesse"),
            "coupon_code": lead.get("coupon_code"),
            "source": lead.get("source", "landing"),
            "origin_url": lead.get("origin_url", ""),
        }
        await self._safe_to_thread(self._append_row_sync, "leads", row)

    async def upsert_order(self, order: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        metadata = order.get("metadata") or {}
        row = {
            "session_id": order.get("session_id"),
            "id": order.get("id"),
            "created_at": order.get("created_at"),
            "updated_at": order.get("updated_at"),
            "package_id": order.get("package_id"),
            "package_name": order.get("package_name"),
            "email": order.get("email") or metadata.get("email"),
            "amount": order.get("amount"),
            "amount_total": order.get("amount_total"),
            "discount": order.get("discount"),
            "coupon": order.get("coupon"),
            "currency": order.get("currency"),
            "status": order.get("status"),
            "payment_status": order.get("payment_status"),
            "emails_sent": order.get("emails_sent"),
            "origin_url": order.get("origin_url") or metadata.get("origin_url"),
            "source": metadata.get("source", order.get("source", "")),
        }
        await self._safe_to_thread(self._upsert_row_sync, "orders", "session_id", row)

    async def append_tracking_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        *,
        lead_id: str = "",
        session_id: str = "",
        email: str = "",
        package_id: str = "",
        amount: Any = "",
        status: str = "",
        payment_status: str = "",
        source: str = "",
        note: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ) -> None:
        if not self.enabled:
            return
        event_time = created_at or ""
        safe_event_time = (
            event_time.replace(":", "").replace("-", "").replace(".", "").replace("+", "_")
            if event_time else "no_time"
        )
        row = {
            "event_id": f"trk_{event_type}_{entity_id}_{safe_event_time}",
            "created_at": event_time,
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "lead_id": lead_id,
            "session_id": session_id,
            "email": email,
            "package_id": package_id,
            "amount": amount,
            "status": status,
            "payment_status": payment_status,
            "source": source,
            "note": note,
            "metadata_json": metadata or {},
        }
        await self._safe_to_thread(self._append_row_sync, "tracking", row)

    async def _safe_to_thread(self, fn, *args) -> None:
        try:
            await asyncio.to_thread(fn, *args)
        except Exception as exc:
            logger.error("Google Sheets sync fallita: %s", exc)


google_sheets_sync = GoogleSheetsSync()
