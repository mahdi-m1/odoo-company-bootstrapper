"""تنفيذ خطة الإنشاء على أودو — مع تجهيز الموديولات والصلاحيات أولاً"""

from __future__ import annotations

import logging
from typing import List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from .models import ExecutionPlan, ExecutionStep, BootstrapRequest
from .odoo_client import OdooClient
from .ai_provider import get_ai_provider

logger = logging.getLogger(__name__)
console = Console()


class PlanExecutor:
    def __init__(self, client: OdooClient, dry_run: bool = False):
        self.client = client
        self.dry_run = dry_run

    def prepare(self, extra_modules: List[str] = None) -> dict:
        console.print("\n[bold cyan]① تجهيز أودو[/] — صلاحيات + تثبيت الموديولات...")
        if self.dry_run:
            console.print("[yellow]محاكاة التجهيز[/]")
            return {"ready": True, "messages": ["dry-run"], "modules": {}, "permissions": {}}
        prep = self.client.prepare_for_bootstrap(extra_modules=extra_modules)
        for msg in prep.get("messages", []):
            console.print(f"  • {msg}")
        if prep.get("ready"):
            console.print("[green]✓ التجهيز اكتمل[/]\n")
        else:
            console.print("[yellow]⚠ التجهيز جزئي — يُفضّل مستخدم admin[/]\n")
        return prep

    def execute(self, plan: ExecutionPlan, prepare: bool = True) -> ExecutionPlan:
        if prepare:
            self.prepare()
        console.print(f"[bold cyan]② تنفيذ الخطة[/] — خطوات: {len(plan.steps)}")
        if self.dry_run:
            console.print("[yellow]محاكاة فقط[/]\n")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), TextColumn("{task.completed}/{task.total}"), console=console,
        ) as progress:
            task = progress.add_task("تنفيذ...", total=len(plan.steps))
            for step in plan.steps:
                progress.update(task, description=f"[cyan]{step.description}")
                try:
                    if self.dry_run:
                        step.status = "skipped"
                        step.result_id = 0
                    else:
                        if step.action == "create":
                            rid = self.client.create(step.model, step.data)
                            step.result_id = rid
                            step.status = "success"
                            console.print(f"  [green]✓[/] {step.model} (id={rid}) — {step.description}")
                        elif step.action == "write":
                            ids = step.data.pop("_ids", [])
                            self.client.write(step.model, ids, step.data)
                            step.status = "success"
                        elif step.action in ("install_module", "install_modules"):
                            names = step.data.get("modules") or step.data.get("names") or []
                            if isinstance(names, str):
                                names = [names]
                            report = self.client.install_modules(names)
                            step.status = "success"
                            console.print(f"  [green]✓[/] تثبيت: {report.get('installed')} / مسبق: {report.get('already')}")
                        else:
                            step.status = "skipped"
                except Exception as e:
                    step.status = "failed"
                    step.error = str(e)
                    console.print(f"  [red]✗[/] {step.description}: {e}")
                    logger.exception("فشل %s", step.order)
                progress.advance(task)

        self._print_summary(plan)
        return plan

    def _print_summary(self, plan: ExecutionPlan) -> None:
        table = Table(title="ملخص التنفيذ")
        table.add_column("الحالة", style="bold")
        table.add_column("العدد")
        success = sum(1 for s in plan.steps if s.status == "success")
        failed = sum(1 for s in plan.steps if s.status == "failed")
        skipped = sum(1 for s in plan.steps if s.status == "skipped")
        table.add_row("[green]نجاح[/]", str(success))
        table.add_row("[red]فشل[/]", str(failed))
        table.add_row("[yellow]تخطي[/]", str(skipped))
        console.print(table)


def build_plan_from_ai(request: BootstrapRequest, provider_name: str = "claude") -> ExecutionPlan:
    provider = get_ai_provider(provider_name)
    payload = request.model_dump(exclude_none=True)
    console.print("[bold]توليد الخطة بالذكاء الاصطناعي...[/]")
    raw = provider.generate_plan(payload)
    steps = [
        ExecutionStep(
            order=s.get("order", 0), action=s.get("action", "create"),
            model=s.get("model", ""), description=s.get("description", ""), data=s.get("data", {}),
        )
        for s in raw.get("steps", [])
    ]
    steps.sort(key=lambda x: x.order)
    return ExecutionPlan(
        steps=steps, summary=raw.get("summary", ""),
        estimated_records=raw.get("estimated_records", len(steps)),
    )


def build_fallback_plan(request: BootstrapRequest) -> ExecutionPlan:
    steps: List[ExecutionStep] = []
    order = 1
    company_data = {"name": request.company.name, "street": request.company.address or ""}
    if request.company.tax_id:
        company_data["vat"] = request.company.tax_id
    steps.append(ExecutionStep(order=order, action="create", model="res.company",
        description=f"إنشاء الشركة: {request.company.name}", data=company_data))
    order += 1
    for sub in request.company.subsidiaries:
        steps.append(ExecutionStep(order=order, action="create", model="res.company",
            description=f"فرع: {sub.name}", data={"name": sub.name, "street": sub.address or ""}))
        order += 1
    departments = {emp.department for emp in request.employees if emp.department}
    for dept in departments:
        steps.append(ExecutionStep(order=order, action="create", model="hr.department",
            description=f"قسم: {dept}", data={"name": dept}))
        order += 1
    job_names = set()
    for prof in getattr(request, "professions", []) or []:
        job_names.add(prof.name)
        steps.append(ExecutionStep(order=order, action="create", model="hr.job",
            description=f"مهنة: {prof.name}", data={"name": prof.name}))
        order += 1
    for emp in request.employees:
        if emp.job_title and emp.job_title not in job_names:
            job_names.add(emp.job_title)
            steps.append(ExecutionStep(order=order, action="create", model="hr.job",
                description=f"وظيفة: {emp.job_title}", data={"name": emp.job_title}))
            order += 1
    for emp in request.employees:
        steps.append(ExecutionStep(order=order, action="create", model="hr.employee",
            description=f"موظف: {emp.name}",
            data={"name": emp.name, "job_title": emp.job_title,
                  "work_email": emp.work_email or "", "identification_id": emp.identification_id or ""}))
        order += 1
    for proj in request.projects:
        steps.append(ExecutionStep(order=order, action="create", model="project.project",
            description=f"مشروع: {proj.name}",
            data={"name": proj.name, "date_start": proj.start_date, "date": proj.end_date}))
        order += 1
    for prod in request.products:
        price = prod.list_price or prod.hourly_rate or 0
        steps.append(ExecutionStep(order=order, action="create", model="product.template",
            description=f"صنف: {prod.name}",
            data={"name": prod.name, "type": prod.type, "list_price": price}))
        order += 1
    return ExecutionPlan(steps=steps,
        summary="خطة: تجهيز موديولات + شركة + مهن + موظفون + مشاريع + أصناف",
        estimated_records=len(steps))
