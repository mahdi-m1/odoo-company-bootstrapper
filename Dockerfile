FROM python:3.12-slim

WORKDIR /app

# تثبيت الأدوات الأساسية
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# نسخ المشروع
COPY . .

# تثبيت الحزمة
RUN pip install --no-cache-dir -e .

# إنشاء مجلد للعمل
RUN mkdir -p /data
WORKDIR /data

ENTRYPOINT ["odoo-bootstrap"]
CMD ["--help"]
