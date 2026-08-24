"""عميل أودو: تثبيت الموديولات + صلاحيات Admin كاملة"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional, List, Dict
import xmlrpc.client

from .models import OdooConnection

logger = logging.getLogger(__name__)

REQUIRED_MODULES = [
    "base", "mail", "contacts",
    "hr", "hr_contract", "project", "product",
    "sale_management", "account",
]


class OdooClient:
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
        self.uid = self.common.authenticate(self.conn.db, self.conn.username, password, {})
        if not self.uid:
            raise ConnectionError("فشل المصادقة مع أودو. تحقق من البيانات.")
        logger.info("تم الاتصال بأودو (uid=%s)", self.uid)

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        password = self.conn.api_key or self.conn.password
        return self.models.execute_kw(
            self.conn.db, self.uid, password, model, method, args, kwargs or {},
        )

    def search_read(self, model: str, domain: List = None, fields: List[str] = None, limit: int = 0) -> List[Dict]:
        return self.execute(model, "search_read", domain or [], {"fields": fields or [], "limit": limit})

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
        company = self.search_read("res.company", [], ["name", "currency_id"], limit=1)
        return {
            "success": True,
            "version": version.get("server_version", "unknown"),
            "uid": self.uid,
            "company": company[0]["name"] if company else None,
            "is_admin": self.is_admin(),
        }

    def is_admin(self) -> bool:
        try:
            groups = self.execute("res.users", "read", [self.uid], {"fields": ["groups_id"]})
            if not groups:
                return False
            group_ids = groups[0].get("groups_id", [])
            data = self.search_read(
                "ir.model.data",
                [("module", "=", "base"), ("name", "=", "group_system")],
                ["res_id"], limit=1,
            )
            if data and data[0]["res_id"] in group_ids:
                return True
            return self.uid in (1, 2)
        except Exception:
            return self.uid in (1, 2)

    def ensure_admin_access(self) -> dict:
        result = {"is_admin": False, "granted": False, "message": ""}
        if self.is_admin():
            result["is_admin"] = True
            result["message"] = "المستخدم لديه صلاحيات كاملة (Admin)"
            return result
        try:
            data = self.search_read(
                "ir.model.data",
                [("module", "=", "base"), ("name", "=", "group_system")],
                ["res_id"], limit=1,
            )
            if not data:
                result["message"] = "استخدم مستخدم admin في إعدادات الاتصال"
                return result
            group_id = data[0]["res_id"]
            self.execute("res.users", "write", [[self.uid], {"groups_id": [(4, group_id)]}])
            result["is_admin"] = self.is_admin()
            result["granted"] = result["is_admin"]
            result["message"] = "تم منح صلاحيات Admin" if result["granted"] else "فشل منح Admin — استخدم حساب المدير"
        except Exception as e:
            result["message"] = f"لا يمكن منح Admin ({e}). استخدم حساب admin."
        return result

    def get_module_state(self, technical_name: str) -> Optional[str]:
        rows = self.search_read(
            "ir.module.module", [("name", "=", technical_name)], ["name", "state"], limit=1,
        )
        return rows[0].get("state") if rows else None

    def install_modules(self, module_names: List[str] = None, wait: bool = True, timeout_sec: int = 300) -> dict:
        names = module_names or REQUIRED_MODULES
        report = {"already": [], "installed": [], "missing": [], "failed": [], "skipped": []}
        to_install_ids = []
        for name in names:
            if name == "base":
                report["already"].append(name)
                continue
            state = self.get_module_state(name)
            if state is None:
                report["missing"].append(name)
                continue
            if state == "installed":
                report["already"].append(name)
                continue
            if state in ("uninstalled", "to install", "to upgrade"):
                ids = self.search("ir.module.module", [("name", "=", name)], limit=1)
                if ids:
                    to_install_ids.extend(ids)
                    report["installed"].append(name)
            else:
                report["skipped"].append(f"{name}({state})")
        if not to_install_ids:
            return report
        try:
            self.execute("ir.module.module", "button_immediate_install", [to_install_ids])
            if wait:
                deadline = time.time() + timeout_sec
                pending = list(report["installed"])
                while pending and time.time() < deadline:
                    still = [n for n in pending if self.get_module_state(n) != "installed"]
                    pending = still
                    if pending:
                        time.sleep(2)
                for name in pending:
                    report["installed"].remove(name)
                    report["failed"].append(name)
        except Exception as e:
            logger.exception("فشل تثبيت الموديولات")
            for name in list(report["installed"]):
                if self.get_module_state(name) != "installed":
                    report["installed"].remove(name)
                    report["failed"].append(f"{name}: {e}")
        return report

    def prepare_for_bootstrap(self, extra_modules: List[str] = None) -> dict:
        result = {"permissions": {}, "modules": {}, "ready": False, "messages": []}
        perm = self.ensure_admin_access()
        result["permissions"] = perm
        result["messages"].append(perm["message"])
        modules = list(REQUIRED_MODULES)
        if extra_modules:
            for m in extra_modules:
                if m not in modules:
                    modules.append(m)
        mod_report = self.install_modules(modules)
        result["modules"] = mod_report
        if mod_report["installed"]:
            result["messages"].append("تم تثبيت: " + ", ".join(mod_report["installed"]))
        if mod_report["already"]:
            result["messages"].append("مثبت مسبقاً: " + ", ".join(mod_report["already"]))
        if mod_report["missing"]:
            result["messages"].append("غير متوفر: " + ", ".join(mod_report["missing"]))
        if mod_report["failed"]:
            result["messages"].append("فشل: " + ", ".join(mod_report["failed"]))
        critical_failed = [x for x in mod_report["failed"] if any(c in str(x) for c in ("hr", "product", "project"))]
        result["ready"] = perm.get("is_admin") or self.uid in (1, 2)
        if critical_failed:
            result["ready"] = False
            result["messages"].append("تحذير: موديولات حرجة فشلت")
        return result
