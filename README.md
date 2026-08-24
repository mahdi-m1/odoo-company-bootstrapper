# Odoo Company Bootstrapper — البحرين 🇧🇭

**برنامج ذكي لإنشاء هيكل شركة كامل داخل أودو تلقائياً**  
مخصص لشركات **مملكة البحرين** مع واجهة سطح مكتب عربية + دعم CLI.

يستخدم Claude CLI (أو Anthropic / OpenAI / Ollama) لتحويل بيانات الشركة والموظفين والمشاريع وتأمينات SIO إلى أوامر دقيقة، ثم ينفّذها عبر XML-RPC على أودو.

---

## المميزات

- واجهة سطح مكتب عربية (CustomTkinter)
- إعدادات افتراضية للبحرين: عملة **BHD**، دولة **BH**
- نسب تأمينات **SIO 2026**: موظف **8%** | شركة **18%** (بحرينيين)
- اتصال مباشر بأودو عبر XML-RPC
- دعم Claude CLI + Anthropic + OpenAI + Ollama
- إنشاء: الشركة + الفروع + الأقسام + الوظائف + الموظفون + المشاريع + الأصناف
- وضع محاكاة (`--dry-run`)
- استيراد موظفين من Excel/CSV

---

## التثبيت

```bash
git clone https://github.com/mahdi-m1/odoo-company-bootstrapper.git
cd odoo-company-bootstrapper

python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# (موصى به)
npm install -g @anthropic-ai/claude-code
```

---

## التشغيل

### واجهة سطح المكتب

```bash
odoo-bootstrap ui
```

تبويبات الواجهة:
1. الاتصال بأودو
2. الشركة والفروع
3. الموظفون والتأمين (SIO)
4. المشاريع والأصناف
5. تشغيل (توليد خطة + تنفيذ)

### سطر الأوامر

```bash
odoo-bootstrap init
odoo-bootstrap test
odoo-bootstrap plan
odoo-bootstrap run
odoo-bootstrap run --dry-run
odoo-bootstrap import-employees employees.xlsx
```

---

## تأمينات البحرين (SIO 2026)

| النوع | حصة الموظف | حصة الشركة | المجموع |
|--------|------------|------------|---------|
| بحريني (قطاع خاص) | 8% | 18% | **26%** |
| مغترب | 1% | 3% + EOSB | حسب الحالة |

- حصة الشركة ترتفع 1% كل يناير حتى 2028
- يمكن تعديل النسب من الواجهة أو من `config.yaml`

---

## مزودي الذكاء الاصطناعي

| المزود | الإعداد |
|--------|---------|
| Claude CLI | `provider: claude` |
| Anthropic API | `provider: anthropic` + `ANTHROPIC_API_KEY` |
| OpenAI | `provider: openai` + `OPENAI_API_KEY` |
| Ollama | `provider: ollama` |

---

## الترخيص

MIT
