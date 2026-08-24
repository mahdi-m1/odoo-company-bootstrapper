"""نماذج البيانات باستخدام Pydantic — مخصص للشركات في البحرين
يدعم نظام الرواتب الشهرية ونظام الساعات + مهن ومنتجات ديناميكية
"""

from __future__ import annotations

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class OdooConnection(BaseModel):
    url: str = Field(..., description="رابط أودو")
    db: str = Field(..., description="اسم قاعدة البيانات")
    username: str = Field(..., description="اسم المستخدم")
    password: Optional[str] = Field(None, description="كلمة المرور")
    api_key: Optional[str] = Field(None, description="مفتاح API")


class Subsidiary(BaseModel):
    name: str
    ownership_percentage: float = Field(100.0, ge=0, le=100)
    tax_id: Optional[str] = None
    address: Optional[str] = None
    currency: str = "BHD"


class CompanyData(BaseModel):
    name: str
    tax_id: Optional[str] = None
    address: Optional[str] = None
    currency: str = "BHD"
    language: str = "ar_001"
    country_code: str = "BH"
    subsidiaries: List[Subsidiary] = Field(default_factory=list)
    work_system: Literal["monthly", "hourly", "mixed"] = "mixed"


class Project(BaseModel):
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = None
    description: Optional[str] = None


class Profession(BaseModel):
    """مهنة قابلة للإدخال حسب الحاجة — لاستقرار hr.job"""
    name: str
    code: Optional[str] = None
    department: Optional[str] = None
    default_hourly_rate: Optional[float] = None
    description: Optional[str] = None


class ProductCategory(BaseModel):
    name: str
    type: Literal["product", "service", "consu"] = "service"
    uom: str = "Units"
    list_price: Optional[float] = None
    hourly_rate: Optional[float] = None
    description: Optional[str] = None
    related_profession: Optional[str] = None


class Employee(BaseModel):
    name: str
    job_title: str
    wage_type: Literal["monthly", "hourly"] = "monthly"
    salary: float = 0
    hourly_rate: Optional[float] = None
    expected_hours_per_month: Optional[float] = None
    contract_type: Literal["permanent", "temporary", "freelance", "hourly"] = "permanent"
    nationality: Literal["bahraini", "expat", "gcc"] = "bahraini"
    department: Optional[str] = None
    work_email: Optional[str] = None
    identification_id: Optional[str] = None

    def effective_monthly_cost(self) -> float:
        if self.wage_type == "hourly" and self.hourly_rate:
            hours = self.expected_hours_per_month or 160
            return self.hourly_rate * hours
        return self.salary


class InsuranceRules(BaseModel):
    employee_contribution_pct: float = Field(8.0)
    company_contribution_pct: float = Field(18.0)
    expat_employee_pct: float = Field(1.0)
    expat_company_pct: float = Field(3.0)
    labor_market_fee: float = Field(0.0)
    other_monthly_deductions: List[dict] = Field(default_factory=list)
    health_insurance: Optional[float] = None


class BootstrapRequest(BaseModel):
    company: CompanyData
    professions: List[Profession] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    products: List[ProductCategory] = Field(default_factory=list)
    employees: List[Employee] = Field(default_factory=list)
    insurance: InsuranceRules = Field(default_factory=InsuranceRules)
    dry_run: bool = False


class ExecutionStep(BaseModel):
    order: int
    action: str
    model: str
    description: str
    data: dict
    status: Literal["pending", "success", "failed", "skipped"] = "pending"
    result_id: Optional[int] = None
    error: Optional[str] = None


class ExecutionPlan(BaseModel):
    steps: List[ExecutionStep]
    summary: str
    estimated_records: int
