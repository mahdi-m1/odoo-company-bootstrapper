"""واجهة سطر الأوامر الرئيسية"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .config import AppConfig, get_default_config_template, load_yaml_config, save_yaml_config
from .models import (
    BootstrapRequest, CompanyData, Employee, InsuranceRules,
    ProductCategory, Project, Subsidiary, Profession,
)
from .odoo_client import OdooClient
from .executor import PlanExecutor, build_plan_from_ai, build_fallback_plan

app = typer.Typer(
    name="odoo-bootstrap",
    help="إنشاء شركات أودو — البحرين | نظام ساعات | واجهة ويب منفذ 80",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def _version_callback(value: bool):
    if value:
        console.print(f"odoo-company-bootstrapper [bold green]v{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main(version: Optional[bool] = typer.Option(None, "--version", "-v", callback=_version_callback, is_eager=True)):
    pass


@app.command("init")
def init_config(path: str = typer.Option("./config.yaml", "--path", "-p"), force: bool = typer.Option(False, "--force", "-f")):
    p = Path(path)
    if p.exists() and not force:
        console.print(f"[yellow]موجود:[/] {path} — استخدم --force")
        raise typer.Exit(1)
    save_yaml_config(path, get_default_config_template())
    console.print(Panel.fit(f"[green]تم إنشاء[/] {path}\nثم: odoo-bootstrap ui", title="نجح"))


@app.command("test")
def test_connection(config: str = typer.Option("./config.yaml", "--config", "-c")):
    cfg = load_yaml_config(config)
    if not cfg:
        console.print("[red]نفّذ: odoo-bootstrap init[/]")
        raise typer.Exit(1)
    o = cfg.get("odoo", {})
    try:
        conn = AppConfig(
            ODOO_URL=o.get("url", ""), ODOO_DB=o.get("db", ""),
            ODOO_USERNAME=o.get("username", "admin"), ODOO_PASSWORD=o.get("password"),
            ODOO_API_KEY=o.get("api_key"),
        ).get_odoo_connection()
        info = OdooClient(conn).test_connection()
        console.print(Panel.fit(
            f"[green]ناجح![/]\nالإصدار: {info['version']}\nuid: {info['uid']}\nالشركة: {info['company']}",
            title="أودو",
        ))
    except Exception as e:
        console.print(f"[red]فشل:[/] {e}")
        raise typer.Exit(1)


@app.command("plan")
def generate_plan(
    config: str = typer.Option("./config.yaml", "--config", "-c"),
    output: str = typer.Option("./plan.json", "--output", "-o"),
    use_ai: bool = typer.Option(True, "--ai/--no-ai"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
):
    cfg = load_yaml_config(config)
    request = _build_request(cfg)
    ai_p = provider or cfg.get("ai", {}).get("provider", "claude")
    if use_ai:
        try:
            plan = build_plan_from_ai(request, ai_p)
        except Exception as e:
            console.print(f"[yellow]AI فشل ({e}) — احتياطية[/]")
            plan = build_fallback_plan(request)
    else:
        plan = build_fallback_plan(request)
    Path(output).write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(Panel(plan.summary, title="الخطة", border_style="cyan"))
    console.print(f"خطوات: {len(plan.steps)} → {output}")


@app.command("run")
def run_bootstrap(
    config: str = typer.Option("./config.yaml", "--config", "-c"),
    plan_file: Optional[str] = typer.Option(None, "--plan"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    use_ai: bool = typer.Option(True, "--ai/--no-ai"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    yes: bool = typer.Option(False, "--yes", "-y"),
):
    cfg = load_yaml_config(config)
    request = _build_request(cfg)
    request.dry_run = dry_run
    ai_p = provider or cfg.get("ai", {}).get("provider", "claude")
    if plan_file and Path(plan_file).exists():
        data = json.loads(Path(plan_file).read_text(encoding="utf-8"))
        from .models import ExecutionPlan, ExecutionStep
        plan = ExecutionPlan(
            steps=[ExecutionStep(**s) for s in data["steps"]],
            summary=data.get("summary", ""),
            estimated_records=data.get("estimated_records", 0),
        )
    else:
        try:
            plan = build_plan_from_ai(request, ai_p) if use_ai else build_fallback_plan(request)
        except Exception:
            plan = build_fallback_plan(request)
    console.print(Panel(plan.summary, title="الخطة"))
    if not yes and not dry_run and not typer.confirm("المتابعة؟"):
        raise typer.Exit()
    o = cfg.get("odoo", {})
    conn = AppConfig(
        ODOO_URL=o.get("url", ""), ODOO_DB=o.get("db", ""),
        ODOO_USERNAME=o.get("username", "admin"), ODOO_PASSWORD=o.get("password"),
    ).get_odoo_connection()
    result = PlanExecutor(OdooClient(conn), dry_run=dry_run).execute(plan)
    Path("./last_run_result.json").write_text(
        json.dumps(result.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )


@app.command("ui")
def launch_ui(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(80, "--port", "-p"),
):
    """واجهة الويب على المنفذ 80"""
    try:
        from .webapp import run_server
        console.print(f"[bold green]http://localhost:{port}/[/]")
        run_server(host=host, port=port)
    except PermissionError:
        console.print("[red]المنفذ 80 محظور — جرّب:[/] odoo-bootstrap ui --port 8080")
        raise typer.Exit(1)
    except ImportError as e:
        console.print(f"[red]{e}[/] — pip install fastapi uvicorn")
        raise typer.Exit(1)


def _build_request(cfg: dict) -> BootstrapRequest:
    c = cfg.get("company", {})
    return BootstrapRequest(
        company=CompanyData(
            name=c.get("name", "شركة"),
            tax_id=c.get("tax_id"),
            address=c.get("address"),
            currency=c.get("currency", "BHD"),
            country_code="BH",
            work_system=c.get("work_system", "mixed"),
            subsidiaries=[Subsidiary(**s) for s in c.get("subsidiaries", [])],
        ),
        professions=[Profession(**p) for p in cfg.get("professions", [])],
        projects=[Project(**p) for p in cfg.get("projects", [])],
        products=[ProductCategory(**p) for p in cfg.get("products", [])],
        employees=[Employee(**e) for e in cfg.get("employees", [])],
        insurance=InsuranceRules(**{k: v for k, v in cfg.get("insurance", {}).items() if k in InsuranceRules.model_fields}),
    )


if __name__ == "__main__":
    app()
