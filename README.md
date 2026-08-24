# Odoo Company Bootstrapper — البحرين

**برنامج ذكي لإنشاء هيكل شركة كامل داخل أودو تلقائياً**  
مخصص للشركات في **مملكة البحرين** (عملة BHD + تأمينات SIO 2026)

يدعم:
- واجهة سطح مكتب رسومية (Desktop GUI)
- سطر أوامر CLI
- Claude CLI / Anthropic / OpenAI / Ollama

---

## المميزات

- اتصال مباشر بأودو عبر XML-RPC
- واجهة سطح مكتب عربية كاملة (Flet)
- نسب التأمينات الاجتماعية SIO 2026:
  - **البحريني**: موظف 8% + شركة 18% = 26%
  - **الوافد**: موظف 1% + شركة 3% (إصابات عمل)
- دعم الجنسية (بحريني / وافد / خليجي) لكل موظف
- إنشاء: الشركة + الفروع + الأقسام + الوظائف + الموظفون + المشاريع + الأصناف
- وضع محاكاة (`--dry-run`)
- استيراد موظفين من Excel/CSV

---

## التثبيت السريع

```bash
git clone https://github.com/mahdi-m1/odoo-company-bootstrapper.git
cd odoo-company-bootstrapper

python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# موصى به: Claude CLI
npm install -g @anthropic-ai/claude-code
```

أو:

```bash
curl -sSL https://raw.githubusercontent.com/mahdi-m1/odoo-company-bootstrapper/main/scripts/install.sh | bash
```

---

## الاستخدام

### 1. واجهة سطح المكتب (موصى بها)

```bash
odoo-bootstrap desktop
```

تفتح نافذة رسومية فيها تبويبات:
- الاتصال والذكاء الاصطناعي
- الشركة والفروع
- الموظفون (مع اختيار الجنسية)
- المشاريع والأصناف
- التأمينات SIO
- التنفيذ والسجل

### 2. سطر الأوامر

```bash
odoo-bootstrap init          # إنشاء config.yaml
odoo-bootstrap test          # اختبار الاتصال
odoo-bootstrap plan          # توليد الخطة
odoo-bootstrap run           # تنفيذ
odoo-bootstrap run --dry-run # محاكاة فقط
odoo-bootstrap import-employees employees.xlsx
```

---

## إعدادات البحرين الافتراضية

| البند | القيمة |
|-------|--------|
| العملة | BHD |
| الدولة | BH |
| حصة الموظف البحريني | 8% |
| حصة الشركة (بحريني) | 18% |
| حصة الموظف الوافد | 1% |
| حصة الشركة (وافد) | 3% |

---

## مزودو الذكاء الاصطناعي

```yaml
ai:
  provider: claude    # Claude CLI (الأفضل)
  # provider: anthropic
  # provider: openai
  # provider: ollama
```

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export OLLAMA_MODEL=llama3.1
```

---

## الأوامر

| الأمر | الوصف |
|-------|--------|
| `odoo-bootstrap desktop` | فتح واجهة سطح المكتب |
| `odoo-bootstrap init` | إنشاء ملف إعدادات |
| `odoo-bootstrap test` | اختبار الاتصال بأودو |
| `odoo-bootstrap plan` | توليد خطة الإنشاء |
| `odoo-bootstrap run` | تنفيذ الإنشاء |
| `odoo-bootstrap import-employees` | استيراد موظفين |

---

## Docker

```bash
docker build -t odoo-bootstrap .
docker run -it --rm -v $(pwd)/config.yaml:/data/config.yaml odoo-bootstrap run
```

---

## المتطلبات

- Python 3.10+
- وصول شبكي إلى سيرفر أودو
- (موصى به) Claude CLI أو مفتاح API

---

## الترخيص

MIT
