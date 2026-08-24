"""واجهة ويب عربية — المنفذ 80 — مهن + ساعات + منتجات ديناميكية"""
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from .config import AppConfig, get_default_config_template, load_yaml_config, save_yaml_config
from .models import (BootstrapRequest, CompanyData, Employee, InsuranceRules,
    ProductCategory, Profession, Project, Subsidiary)
from .odoo_client import OdooClient
from .executor import PlanExecutor, build_plan_from_ai, build_fallback_plan

CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "./config.yaml"))
PLAN_PATH = Path("./plan.json")
app = FastAPI(title="Odoo Bootstrapper BH", docs_url=None, redoc_url=None)

def _cfg():
    if CONFIG_PATH.exists():
        return load_yaml_config(CONFIG_PATH)
    data = get_default_config_template()
    data.setdefault("professions", [
        {"name": "عامل بالساعة", "default_hourly_rate": 2.5, "department": "تشغيل"},
        {"name": "فني صيانة", "default_hourly_rate": 4.0, "department": "صيانة"},
    ])
    data.setdefault("company", {})["work_system"] = "mixed"
    save_yaml_config(CONFIG_PATH, data)
    return data

CSS = """
body{margin:0;font-family:Tahoma,Arial,sans-serif;background:#0f1419;color:#e7ecf3}
header{background:#1a2332;padding:12px 20px;display:flex;justify-content:space-between;align-items:center}
nav a{color:#94a3b8;text-decoration:none;margin-right:12px}
nav a:hover{color:#3b82f6}
main{max-width:900px;margin:20px auto;padding:0 16px}
.card{background:#1a2332;border-radius:10px;padding:18px;margin-bottom:14px;border:1px solid #2a3548}
label{display:block;margin:8px 0 4px;color:#94a3b8;font-size:.9rem}
input,select,textarea{width:100%;padding:8px 10px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#e7ecf3;box-sizing:border-box}
textarea{min-height:90px}
button,.btn{background:#3b82f6;color:#fff;border:none;padding:9px 16px;border-radius:6px;cursor:pointer;text-decoration:none;display:inline-block;margin:4px 2px}
button.ok{background:#22c55e}
.alert{background:#1e3a5f;padding:10px;border-radius:6px;margin-bottom:12px}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{text-align:right;padding:6px;border-bottom:1px solid #2a3548}
.hint{color:#94a3b8;font-size:.85rem}
"""

def _page(title, body, msg=""):
    alert = f'<div class="alert">{msg}</div>' if msg else ""
    return f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>{title}</title><style>{CSS}</style></head>
<body><header><h1 style="margin:0;font-size:1.2rem">🇧🇭 Odoo Bootstrapper</h1>
<nav><a href="/">الرئيسية</a><a href="/settings">الإعدادات</a><a href="/company">الشركة</a>
<a href="/professions">المهن</a><a href="/products">المنتجات</a><a href="/employees">الموظفون</a><a href="/run">تشغيل</a></nav></header>
<main>{alert}{body}</main></body></html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    c = _cfg().get("company", {})
    body = f"""<div class="card"><h2>مرحباً</h2>
<p>شركة: <b>{c.get('name') or '—'}</b> | {c.get('currency','BHD')} | نظام: {c.get('work_system','mixed')}</p>
<p><a class="btn" href="/settings">الإعدادات</a> <a class="btn" href="/professions">المهن</a>
<a class="btn" href="/products">المنتجات</a> <a class="btn" href="/employees">الموظفون</a>
<a class="btn ok" href="/run">تشغيل</a></p>
<p class="hint">المهن والمنتجات تُدخل حسب الحاجة. يدعم نظام الساعات.</p></div>"""
    return _page("الرئيسية", body)

@app.get("/settings", response_class=HTMLResponse)
def settings_get():
    o = _cfg().get("odoo", {}); ai = _cfg().get("ai", {})
    body = f"""<div class="card"><h2>الاتصال بأودو</h2><form method="post" action="/settings">
<label>رابط أودو</label><input name="url" value="{o.get('url','')}" required/>
<label>قاعدة البيانات</label><input name="db" value="{o.get('db','')}" required/>
<label>المستخدم</label><input name="username" value="{o.get('username','admin')}"/>
<label>كلمة المرور</label><input name="password" type="password" value="{o.get('password','')}"/>
<label>الذكاء الاصطناعي</label><select name="ai_provider">
<option value="claude">Claude CLI</option>
<option value="anthropic">Anthropic</option>
<option value="openai">OpenAI</option>
<option value="ollama">Ollama</option>
</select><p><button type="submit">حفظ</button>
<button type="submit" name="action" value="test">اختبار الاتصال</button></p></form></div>"""
    return _page("الإعدادات", body)

@app.post("/settings", response_class=HTMLResponse)
def settings_post(url: str = Form(...), db: str = Form(...), username: str = Form("admin"),
                  password: str = Form(""), ai_provider: str = Form("claude"), action: Optional[str] = Form(None)):
    cfg = _cfg()
    cfg["odoo"] = {"url": url.strip(), "db": db.strip(), "username": username.strip(), "password": password}
    cfg["ai"] = {"provider": ai_provider}
    save_yaml_config(CONFIG_PATH, cfg)
    msg = "تم الحفظ"
    if action == "test":
        try:
            conn = AppConfig(ODOO_URL=url, ODOO_DB=db, ODOO_USERNAME=username, ODOO_PASSWORD=password or None).get_odoo_connection()
            info = OdooClient(conn).test_connection()
            msg = f"✓ ناجح — {info['version']} | {info['company']}"
        except Exception as e:
            msg = f"✗ {e}"
    return HTMLResponse(_page("الإعدادات", f'<div class="card"><p>{msg}</p><a class="btn" href="/settings">رجوع</a></div>', msg))

@app.get("/company", response_class=HTMLResponse)
def company_get():
    c = _cfg().get("company", {})
    subs = "\n".join(f"{s.get('name','')} | {s.get('ownership_percentage',100)}" for s in c.get("subsidiaries", []))
    body = f"""<div class="card"><h2>الشركة</h2><form method="post" action="/company">
<label>الاسم</label><input name="name" value="{c.get('name','')}" required/>
<label>السجل CR</label><input name="tax_id" value="{c.get('tax_id') or ''}"/>
<label>العنوان</label><input name="address" value="{c.get('address','المنامة، مملكة البحرين')}"/>
<label>العملة</label><input name="currency" value="{c.get('currency','BHD')}"/>
<label>نظام العمل</label><select name="work_system">
<option value="monthly">شهري</option><option value="hourly">ساعات</option><option value="mixed" selected>مختلط</option>
</select>
<label>الفروع (اسم | نسبة)</label><textarea name="subsidiaries">{subs}</textarea>
<p><button type="submit">حفظ</button></p></form></div>"""
    return _page("الشركة", body)

@app.post("/company", response_class=HTMLResponse)
def company_post(name: str = Form(...), tax_id: str = Form(""), currency: str = Form("BHD"),
                 address: str = Form(""), work_system: str = Form("mixed"), subsidiaries: str = Form("")):
    cfg = _cfg(); subs = []
    for line in subsidiaries.strip().splitlines():
        if not line.strip(): continue
        parts = [p.strip() for p in line.split("|")]
        subs.append({"name": parts[0], "ownership_percentage": float(parts[1]) if len(parts)>1 else 100, "currency": currency})
    cfg["company"] = {"name": name, "tax_id": tax_id or None, "currency": currency, "address": address,
        "language": "ar_001", "country_code": "BH", "work_system": work_system, "subsidiaries": subs}
    save_yaml_config(CONFIG_PATH, cfg)
    return RedirectResponse("/company", status_code=303)

@app.get("/professions", response_class=HTMLResponse)
def professions_get():
    rows = _cfg().get("professions", [])
    lines = "\n".join(f"{r.get('name','')} | {r.get('default_hourly_rate') or ''} | {r.get('department') or ''}" for r in rows)
    table = "".join(f"<tr><td>{r.get('name')}</td><td>{r.get('default_hourly_rate') or '—'}</td><td>{r.get('department') or '—'}</td></tr>" for r in rows)
    body = f"""<div class="card"><h2>المهن</h2><p class="hint">أدخل المهن مع سعر الساعة لاستقرار hr.job</p>
<table><tr><th>المهنة</th><th>سعر الساعة</th><th>القسم</th></tr>{table or '<tr><td colspan=3>—</td></tr>'}</table>
<form method="post" action="/professions"><label>سطر: الاسم | سعر الساعة | القسم</label>
<textarea name="lines">{lines}</textarea><p><button type="submit">حفظ</button></p></form></div>"""
    return _page("المهن", body)

@app.post("/professions", response_class=HTMLResponse)
def professions_post(lines: str = Form("")):
    cfg = _cfg(); professions = []
    for line in lines.strip().splitlines():
        if not line.strip(): continue
        parts = [p.strip() for p in line.split("|")]
        rate = float(parts[1]) if len(parts)>1 and parts[1] else None
        professions.append({"name": parts[0], "default_hourly_rate": rate, "department": parts[2] if len(parts)>2 else None})
    cfg["professions"] = professions
    save_yaml_config(CONFIG_PATH, cfg)
    return RedirectResponse("/professions", status_code=303)

@app.get("/products", response_class=HTMLResponse)
def products_get():
    rows = _cfg().get("products", [])
    lines = "\n".join(f"{r.get('name','')} | {r.get('type','service')} | {r.get('uom','Units')} | {r.get('list_price') or r.get('hourly_rate') or ''}" for r in rows)
    table = "".join(f"<tr><td>{r.get('name')}</td><td>{r.get('type')}</td><td>{r.get('uom')}</td><td>{r.get('list_price') or r.get('hourly_rate') or '—'}</td></tr>" for r in rows)
    body = f"""<div class="card"><h2>المنتجات</h2><p class="hint">للساعة: Hours + السعر</p>
<table><tr><th>الاسم</th><th>النوع</th><th>الوحدة</th><th>السعر</th></tr>{table or '<tr><td colspan=4>—</td></tr>'}</table>
<form method="post" action="/products"><label>سطر: اسم | service/product | Hours/Units | سعر</label>
<textarea name="lines">{lines}</textarea><p><button type="submit">حفظ</button></p></form></div>"""
    return _page("المنتجات", body)

@app.post("/products", response_class=HTMLResponse)
def products_post(lines: str = Form("")):
    cfg = _cfg(); products = []
    for line in lines.strip().splitlines():
        if not line.strip(): continue
        parts = [p.strip() for p in line.split("|")]
        uom = parts[2] if len(parts)>2 else "Units"
        price = float(parts[3]) if len(parts)>3 and parts[3] else None
        item = {"name": parts[0], "type": parts[1] if len(parts)>1 else "service", "uom": uom, "list_price": price}
        if uom.lower() in ("hours", "hour", "ساعة", "ساعات"):
            item["hourly_rate"] = price; item["uom"] = "Hours"
        products.append(item)
    cfg["products"] = products
    save_yaml_config(CONFIG_PATH, cfg)
    return RedirectResponse("/products", status_code=303)

@app.get("/employees", response_class=HTMLResponse)
def employees_get():
    rows = _cfg().get("employees", [])
    lines = "\n".join(f"{e.get('name','')} | {e.get('job_title','')} | {e.get('wage_type','monthly')} | {e.get('salary') or e.get('hourly_rate') or 0} | {e.get('expected_hours_per_month') or ''} | {e.get('department') or ''}" for e in rows)
    table = "".join(f"<tr><td>{e.get('name')}</td><td>{e.get('job_title')}</td><td>{e.get('wage_type','monthly')}</td><td>{e.get('salary') or e.get('hourly_rate') or '—'}</td><td>{e.get('expected_hours_per_month') or '—'}</td></tr>" for e in rows)
    body = f"""<div class="card"><h2>الموظفون</h2><p class="hint">hourly | سعر الساعة | ساعات/شهر</p>
<table><tr><th>الاسم</th><th>المهنة</th><th>الأجر</th><th>راتب/ساعة</th><th>ساعات</th></tr>{table or '<tr><td colspan=5>—</td></tr>'}</table>
<form method="post" action="/employees"><label>سطر: اسم | مهنة | monthly/hourly | قيمة | ساعات | قسم</label>
<textarea name="lines">{lines}</textarea><p><button type="submit">حفظ</button></p></form></div>"""
    return _page("الموظفون", body)

@app.post("/employees", response_class=HTMLResponse)
def employees_post(lines: str = Form("")):
    cfg = _cfg(); employees = []
    for line in lines.strip().splitlines():
        if not line.strip(): continue
        parts = [p.strip() for p in line.split("|")]
        wt = (parts[2] if len(parts)>2 else "monthly").lower()
        if wt not in ("monthly", "hourly"): wt = "monthly"
        val = float(parts[3]) if len(parts)>3 and parts[3] else 0
        hours = float(parts[4]) if len(parts)>4 and parts[4] else None
        emp = {"name": parts[0], "job_title": parts[1] if len(parts)>1 else "", "wage_type": wt,
               "contract_type": "hourly" if wt=="hourly" else "permanent",
               "department": parts[5] if len(parts)>5 else None, "nationality": "bahraini"}
        if wt == "hourly":
            emp["hourly_rate"] = val; emp["salary"] = 0; emp["expected_hours_per_month"] = hours or 160
        else:
            emp["salary"] = val
        employees.append(emp)
    cfg["employees"] = employees
    save_yaml_config(CONFIG_PATH, cfg)
    return RedirectResponse("/employees", status_code=303)

def _build_request(cfg, dry_run=False):
    c = cfg.get("company", {})
    return BootstrapRequest(
        company=CompanyData(name=c.get("name","شركة"), tax_id=c.get("tax_id"), address=c.get("address"),
            currency=c.get("currency","BHD"), country_code="BH", work_system=c.get("work_system","mixed"),
            subsidiaries=[Subsidiary(**s) for s in c.get("subsidiaries", [])]),
        professions=[Profession(**p) for p in cfg.get("professions", [])],
        projects=[Project(**p) for p in cfg.get("projects", [])],
        products=[ProductCategory(**p) for p in cfg.get("products", [])],
        employees=[Employee(**e) for e in cfg.get("employees", [])],
        insurance=InsuranceRules(**{k:v for k,v in cfg.get("insurance",{}).items() if k in InsuranceRules.model_fields}),
        dry_run=dry_run)

@app.get("/run", response_class=HTMLResponse)
def run_get():
    body = """<div class="card"><h2>تشغيل</h2><form method="post" action="/run">
<label><input type="checkbox" name="dry_run" value="1"/> محاكاة فقط</label>
<p><button type="submit" name="action" value="plan">توليد الخطة</button>
<button type="submit" name="action" value="execute" class="ok">تنفيذ على أودو</button></p></form></div>"""
    if PLAN_PATH.exists():
        try:
            plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
            steps = "".join(f"<tr><td>{s.get('order')}</td><td>{s.get('model')}</td><td>{s.get('description')}</td><td>{s.get('status','')}</td></tr>" for s in plan.get("steps",[]))
            body += f'<div class="card"><h3>آخر خطة</h3><p>{plan.get("summary","")}</p><table><tr><th>#</th><th>نموذج</th><th>وصف</th><th>حالة</th></tr>{steps}</table></div>'
        except Exception: pass
    return _page("تشغيل", body)

@app.post("/run", response_class=HTMLResponse)
def run_post(action: str = Form("plan"), dry_run: Optional[str] = Form(None)):
    cfg = _cfg(); dry = dry_run == "1"
    request = _build_request(cfg, dry); provider = cfg.get("ai",{}).get("provider","claude"); log = []
    try:
        if action == "plan" or not PLAN_PATH.exists():
            log.append("توليد الخطة...")
            try: plan = build_plan_from_ai(request, provider)
            except Exception as e:
                log.append(f"AI فشل ({e}) — احتياطية"); plan = build_fallback_plan(request)
            PLAN_PATH.write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
            log.append(plan.summary); log.append(f"خطوات: {len(plan.steps)}")
            for s in plan.steps: log.append(f"  {s.order}. [{s.model}] {s.description}")
        if action == "execute":
            data = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
            from .models import ExecutionPlan, ExecutionStep
            plan = ExecutionPlan(steps=[ExecutionStep(**s) for s in data["steps"]], summary=data.get("summary",""), estimated_records=data.get("estimated_records",0))
            o = cfg["odoo"]
            conn = AppConfig(ODOO_URL=o.get("url",""), ODOO_DB=o.get("db",""), ODOO_USERNAME=o.get("username","admin"), ODOO_PASSWORD=o.get("password")).get_odoo_connection()
            result = PlanExecutor(OdooClient(conn), dry_run=dry).execute(plan)
            PLAN_PATH.write_text(json.dumps(result.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
            ok = sum(1 for s in result.steps if s.status=="success"); fail = sum(1 for s in result.steps if s.status=="failed")
            log.append(f"نجاح={ok} فشل={fail}")
    except Exception as e: log.append(f"خطأ: {e}")
    body = f'<div class="card"><h2>النتيجة</h2><pre style="white-space:pre-wrap">{chr(10).join(log)}</pre><a class="btn" href="/run">رجوع</a></div>'
    return _page("تشغيل", body, log[0] if log else "")

def run_server(host="0.0.0.0", port=80):
    import uvicorn
    print(f"http://{host}:{port}/")
    uvicorn.run(app, host=host, port=port, log_level="info")
