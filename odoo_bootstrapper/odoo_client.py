"""عميل الاتصال بأودو عبر XML-RPC"""

from __future__ import annotations

import logging
from typing import Any, Optional, List, Dict
import xmlrpc.client

from .models import OdooConnection

logger = logging.getLogger(__name__)


class OdooClient:
    """عميل بسيط وآمن للتعامل مع أودو عبر XML-RPC"""

    def __init__(self, conn: OdooConnection):
        self.conn = conn
        self.uid: Optional[int] = None
        self.common = None
        self.models = None
        self._connect()

    def _connect(self) -> None:
        url = self.conn.url.rstrip("/")
        self.common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        self.models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

        password = self.conn.api_key or self.conn.password
        if not password:
            raise ValueError("يجب توفير كلمة المرور أو API Key")

        self.uid = self.common.authenticate(
            self.conn.db, self.conn.username, password, {}
        )
        if not self.uid:
            raise ConnectionError("فشل المصادقة مع أودو. تحقق من البيانات.")

        logger.info("تم الاتصال بأودو بنجاح (uid=%s)", self.uid)

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        password = self.conn.api_key or self.conn.password
        return self.models.execute_kw(
            self.conn.db,
            self.uid,
            password,
            model,
            method,
            args,
            kwargs or {},
        )

    def search_read(
        self,
        model: str,
        domain: List = None,
        fields: List[str] = None,
        limit: int = 0,
    ) -> List[Dict]:
        return self.execute(
            model,
            "search_read",
            domain or [],
            {"fields": fields or [], "limit": limit},
        )

    def create(self, model: str, values: Dict) -> int:
        return self.execute(model, "create", [values])

    def write(self, model: str, ids: List[int], values: Dict) -> bool:
        return self.execute(model, "write", ids, values)

    def search(self, model: str, domain: List = None, limit: int = 0) -> List[int]:
        return self.execute(model, "search", domain or [], {"limit": limit})

    def exists(self, model: str, domain: List) -> bool:
        return bool(self.search(model, domain, limit=1))

    def test_connection(self) -> dict:
        version = self.common.version()
        company = self.search_read(
            "res.company", [], ["name", "currency_id"], limit=1
        )
        return {
            "success": True,
            "version": version.get("server_version", "unknown"),
            "uid": self.uid,
            "company": company[0]["name"] if company else None,
        }
