"""إدارة الإعدادات — البحرين + نظام الساعات + مهن ديناميكية"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

from .models import OdooConnection

load_dotenv()


class AppConfig(BaseSettings):
    odoo_url: str = Field("", alias="ODOO_URL")
    odoo_db: str = Field("", alias="ODOO_DB")
    odoo_username: str = Field("admin", alias="ODOO_USERNAME")
    odoo_password: Optional[str] = Field(None, alias="ODOO_PASSWORD")
    odoo_api_key: Optional[str] = Field(None, alias="ODOO_API_KEY")
    ai_provider: str = Field("claude", alias="AI_PROVIDER")
    config_path: str = Field("./config.yaml", alias="CONFIG_PATH")

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_odoo_connection(self) -> OdooConnection:
        return OdooConnection(
            url=self.odoo_url,
            db=self.odoo_db,
            username=self.odoo_username,
            password=self.odoo_password,
            api_key=self.odoo_api_key,
        )


def load_yaml_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml_config(path: str | Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def get_default_config_template() -> dict:
    return {
        "odoo": {
            "url": "https://your-odoo.com",
            "db": "odoo",
            "username": "admin",
            "password": "changeme",
        },
        "ai": {"provider": "claude"},
        "company": {
            "name": "شركة المثال للتجارة",
            "tax_id": "",
            "address": "المنامة، مملكة البحرين",
            "currency": "BHD",
            "language": "ar_001",
            "country_code": "BH",
            "work_system": "mixed",
            "subsidiaries": [
                {"name": "فرع الرفاع", "ownership_percentage": 100, "address": "الرفاع", "currency": "BHD"}
            ],
        },
        "professions": [
            {"name": "مدير تقني", "default_hourly_rate": None, "department": "تقنية المعلومات"},
            {"name": "محاسبة", "default_hourly_rate": None, "department": "المالية"},
            {"name": "عامل بالساعة", "default_hourly_rate": 2.5, "department": "تشغيل"},
            {"name": "فني صيانة", "default_hourly_rate": 4.0, "department": "صيانة"},
        ],
        "projects": [
            {"name": "مشروع تطوير النظام", "start_date": "2026-01-01", "end_date": "2026-12-31", "budget": 50000}
        ],
        "products": [
            {"name": "استشارات تقنية", "type": "service", "uom": "Hours", "list_price": 40, "hourly_rate": 40},
            {"name": "صيانة بالساعة", "type": "service", "uom": "Hours", "list_price": 15, "hourly_rate": 15},
            {"name": "ترخيص برمجيات", "type": "product", "uom": "Units", "list_price": 500},
        ],
        "employees": [
            {"name": "أحمد محمد", "job_title": "مدير تقني", "wage_type": "monthly", "salary": 1200, "contract_type": "permanent", "department": "تقنية المعلومات"},
            {"name": "سارة علي", "job_title": "محاسبة", "wage_type": "monthly", "salary": 850, "contract_type": "permanent", "department": "المالية"},
            {"name": "خالد سعيد", "job_title": "عامل بالساعة", "wage_type": "hourly", "salary": 0, "hourly_rate": 2.5, "expected_hours_per_month": 160, "contract_type": "hourly", "department": "تشغيل"},
        ],
        "insurance": {
            "employee_contribution_pct": 8.0,
            "company_contribution_pct": 18.0,
            "labor_market_fee": 0,
            "other_monthly_deductions": [],
            "health_insurance": None,
        },
    }
