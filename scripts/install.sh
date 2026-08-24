#!/usr/bin/env bash
set -euo pipefail

echo "=============================================="
echo "  Odoo Company Bootstrapper - Installer"
echo "=============================================="

REPO_URL="https://github.com/mahdi-m1/odoo-company-bootstrapper.git"
INSTALL_DIR="${INSTALL_DIR:-$HOME/odoo-company-bootstrapper}"

# تحقق من Python
if ! command -v python3 &>/dev/null; then
  echo "Python 3 مطلوب. ثبّته أولاً."
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python: $PYTHON_VERSION"

# استنساخ أو تحديث
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "تحديث المستودع الموجود..."
  cd "$INSTALL_DIR"
  git pull
else
  echo "استنساخ المستودع إلى $INSTALL_DIR ..."
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

# بيئة افتراضية
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

pip install --upgrade pip
pip install -e .

# إنشاء config إن لم يوجد
if [ ! -f "config.yaml" ]; then
  odoo-bootstrap init
  echo ""
  echo "→ تم إنشاء config.yaml — عدّله ببيانات أودو الخاصة بك"
fi

echo ""
echo "=============================================="
echo "  التثبيت اكتمل بنجاح!"
echo "=============================================="
echo ""
echo "لتفعيل البيئة في كل جلسة:"
echo "  cd $INSTALL_DIR && source .venv/bin/activate"
echo ""
echo "الأوامر الأساسية:"
echo "  odoo-bootstrap init          # إنشاء إعدادات"
echo "  odoo-bootstrap test          # اختبار الاتصال"
echo "  odoo-bootstrap plan          # توليد الخطة"
echo "  odoo-bootstrap run           # تنفيذ الإنشاء"
echo ""
echo "موصى به: تثبيت Claude CLI"
echo "  npm install -g @anthropic-ai/claude-code"
echo ""
