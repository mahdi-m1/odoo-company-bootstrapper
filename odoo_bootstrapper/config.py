"""إدارة الإعدادات"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from .models import OdooConnection, CompanyData, Project, ProductCategory, Employee, InsuranceRules


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
            # "api_key": "",
        },
        "ai": {
            "provider": "claude",  # claude | anthropic | openai | ollama
        },
        "company": {
            "name": "شركة المثال للتجارة",
            "tax_id": "300000000000003",
            "address": "الرياض، المملكة العربية السعودية",
            "currency": "SAR",
            "language": "ar_001",
            "country_code": "SA",
            "subsidiaries": [
                {
                    "name": "فرع جدة",
                    "ownership_percentage": 100,
                    "tax_id": "",
                    "address": "جدة",
                    "currency": "SAR",
                }
            ],
        },
        "projects": [
            {
                "name": "مشروع تطوير النظام",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "budget": 500000,
                "description": "مشروع تطوير داخلي",
            }
        ],
        "products": [
            {
                "name": "استشارات تقنية",
                "type": "service",
                "uom": "Hours",
                "list_price": 350,
                "description": "ساعة استشارة تقنية",
            },
            {
                "name": "ترخيص برمجيات",
                "type": "product",
                "uom": "Units",
                "list_price": 5000,
            },
        ],
        "employees": [
            {
                "name": "أحمد محمد",
                "job_title": "مدير تقني",
                "salary": 18000,
                "contract_type": "permanent",
                "department": "تقنية المعلومات",
                "work_email": "ahmed@example.com",
            },
            {
                "name": "سارة علي",
                "job_title": "محاسبة",
                "salary": 12000,
                "contract_type": "permanent",
                "department": "المالية",
            },
        ],
        "insurance": {
            "employee_contribution_pct": 9.75,
            "company_contribution_pct": 11.75,
            "labor_market_fee": 0,
            "other_monthly_deductions": [],
            "health_insurance": None,
        },
    }
