# Odoo Company Bootstrapper — البحرين 🇧🇭

برنامج لإنشاء هيكل شركة في أودو مع **نظام الساعات** و**مهن/منتجات ديناميكية** وواجهة ويب على **المنفذ 80**.

## التشغيل السريع

```bash
git clone https://github.com/mahdi-m1/odoo-company-bootstrapper.git
cd odoo-company-bootstrapper
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# واجهة الويب على المنفذ 80
odoo-bootstrap ui
# أو بدون صلاحيات root:
odoo-bootstrap ui --port 8080
```

ثم افتح المتصفح: `http://عنوان-السيرفر/` أو `http://localhost:8080/`

## المميزات

- **نظام عمل مختلط**: شهري / ساعات / مختلط
- **مهن حسب الحاجة** مع سعر ساعة اختياري → استقرار `hr.job` في أودو
- **منتجات وخدمات بالساعة** (وحدة Hours)
- **موظفون**: راتب شهري أو سعر ساعة + ساعات متوقعة
- تأمينات **SIO البحرين 2026**: 8% موظف / 18% شركة
- واجهة ويب عربية RTL على المنفذ **80**
- CLI + Claude CLI / OpenAI / Ollama

## صفحات الواجهة

| الصفحة | الوظيفة |
|--------|---------|
| الإعدادات | اتصال أودو + مزود الذكاء الاصطناعي |
| الشركة | الاسم، CR، نظام العمل (شهري/ساعات) |
| المهن | إدخال المهن وأسعار الساعة |
| المنتجات | خدمات بالساعة أو منتجات |
| الموظفون | شهري أو hourly |
| تشغيل | توليد الخطة + التنفيذ |

## أوامر CLI

```bash
odoo-bootstrap init
odoo-bootstrap test
odoo-bootstrap plan
odoo-bootstrap run
odoo-bootstrap ui --port 80
```

## ملاحظة المنفذ 80

على Linux قد تحتاج صلاحيات:

```bash
sudo odoo-bootstrap ui
# أو
sudo setcap 'cap_net_bind_service=+ep' $(readlink -f $(which python3))
odoo-bootstrap ui
```

## الترخيص

MIT
