# Odoo Company Bootstrapper

**برنامج ذكي لإنشاء هيكل شركة كامل داخل أودو تلقائياً**

يستخدم Claude CLI (أو Anthropic API / OpenAI / Ollama) لتحويل بيانات الشركة والموظفين والمشاريع والتأمينات إلى سلسلة أوامر دقيقة، ثم ينفّذها عبر XML-RPC على أودو.

مصمم ليعمل بسهولة على **VPS** أو أي خادم Linux.

---

## المميزات

- اتصال مباشر بأودو عبر XML-RPC
- دعم **Claude CLI** (الأفضل) + Anthropic API + OpenAI + Ollama
- إنشاء: الشركة + الشركات التابعة + الأقسام + الوظائف + الموظفون + العقود + المشاريع + الأصناف
- دعم نسب التأمينات الاجتماعية ورسوم سوق العمل
- وضع محاكاة (`--dry-run`)
- استيراد موظفين من Excel/CSV
- واجهة سطر أوامر عربية كاملة مع ألوان وتقارير

---

## التثبيت السريع على VPS

```bash
# 1. استنساخ المستودع
git clone https://github.com/mahdi-m1/odoo-company-bootstrapper.git
cd odoo-company-bootstrapper

# 2. إنشاء بيئة افتراضية وتثبيت
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 3. (اختياري لكن موصى به) تثبيت Claude CLI
npm install -g @anthropic-ai/claude-code
# أو استخدم أي مزود آخر عبر متغيرات البيئة
```

أو استخدم سكربت التثبيت:

```bash
curl -sSL https://raw.githubusercontent.com/mahdi-m1/odoo-company-bootstrapper/main/scripts/install.sh | bash
```

---

## الاستخدام السريع

```bash
# إنشاء ملف إعدادات نموذجي
odoo-bootstrap init

# عدّل config.yaml وضع بيانات أودو والشركة

# اختبار الاتصال
odoo-bootstrap test

# توليد الخطة فقط (مراجعة)
odoo-bootstrap plan

# تنفيذ الإنشاء
odoo-bootstrap run

# محاكاة بدون تنفيذ فعلي
odoo-bootstrap run --dry-run

# استيراد موظفين من Excel
odoo-bootstrap import-employees employees.xlsx
```

---

## إعداد الذكاء الاصطناعي

### 1. Claude CLI (موصى به)

```bash
npm install -g @anthropic-ai/claude-code
# سجّل الدخول عند أول استخدام
claude
```

في `config.yaml`:

```yaml
ai:
  provider: claude
```

### 2. Anthropic API مباشرة

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

```yaml
ai:
  provider: anthropic
```

### 3. OpenAI

```bash
export OPENAI_API_KEY=sk-...
```

```yaml
ai:
  provider: openai
```

### 4. Ollama (محلي)

```bash
# شغّل ollama serve ثم
export OLLAMA_MODEL=llama3.1
```

```yaml
ai:
  provider: ollama
```

---

## هيكل ملف config.yaml

```yaml
odoo:
  url: https://your-odoo.com
  db: odoo
  username: admin
  password: secret
  # api_key: ""   # بديل لكلمة المرور

ai:
  provider: claude   # claude | anthropic | openai | ollama

company:
  name: شركة المثال
  tax_id: "300000000000003"
  address: الرياض
  currency: SAR
  language: ar_001
  country_code: SA
  subsidiaries:
    - name: فرع جدة
      ownership_percentage: 100

projects:
  - name: مشروع تطوير
    start_date: "2026-01-01"
    budget: 500000

products:
  - name: استشارات
    type: service
    list_price: 350

employees:
  - name: أحمد محمد
    job_title: مدير تقني
    salary: 18000
    contract_type: permanent
    department: تقنية المعلومات

insurance:
  employee_contribution_pct: 9.75
  company_contribution_pct: 11.75
  labor_market_fee: 0
```

---

## الأوامر المتاحة

| الأمر | الوصف |
|-------|--------|
| `odoo-bootstrap init` | إنشاء ملف إعدادات نموذجي |
| `odoo-bootstrap test` | اختبار الاتصال بأودو |
| `odoo-bootstrap plan` | توليد خطة الإنشاء |
| `odoo-bootstrap run` | تنفيذ الإنشاء |
| `odoo-bootstrap import-employees <file>` | استيراد موظفين من Excel/CSV |

---

## التشغيل كخدمة على VPS (اختياري)

يمكنك وضع البرنامج خلف systemd أو تشغيله يدوياً عند الحاجة. البرنامج لا يحتاج إلى خادم ويب دائم — هو أداة CLI.

---

## Docker (اختياري)

```bash
docker build -t odoo-bootstrap .
docker run -it --rm -v $(pwd)/config.yaml:/app/config.yaml odoo-bootstrap run
```

---

## المتطلبات

- Python 3.10+
- وصول شبكي إلى سيرفر أودو
- (موصى به) Claude CLI أو مفتاح API لأي مزود ذكاء اصطناعي

---

## الترخيص

MIT
