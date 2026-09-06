# توصيل DZ — Tawsil DZ

منصة توصيل جزائرية متكاملة (زبون / مطعم / سائق / إدارة) مبنية على Flask.

## المزايا

- أربع واجهات: الزبون، المطعم، السائق، لوحة الإدارة
- تتبّع الطلبات لحظياً عبر Socket.IO
- خرائط وتحديد المواقع (Google Maps)
- محفظة إلكترونية وحساب رسوم التوصيل والعمولة
- دعم كامل للعربية (RTL) والعملة الجزائرية (DZD)

## التقنيات

| الطبقة | التقنية |
|---|---|
| الخادم | Flask 3, Flask-SQLAlchemy, Flask-Login |
| اللحظي | Flask-SocketIO |
| قاعدة البيانات | SQLite (تطوير) / PostgreSQL (إنتاج) |
| الواجهة | Jinja2, HTML/CSS/JS |

## التشغيل محلياً

```bash
git clone https://github.com/imadim/tawsil-dz.git
cd tawsil-dz

python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env      # ثم املأ القيم
python app.py
```

ثم افتح: http://localhost:5000

## حسابات تجريبية

| الدور | البريد | كلمة السر |
|---|---|---|
| إدارة | admin@delivery.dz | admin123 |
| زبون | client@test.dz | client123 |
| سائق | chauffeur@test.dz | chauffeur123 |

> غيّر كلمات السر هذه قبل أي استخدام حقيقي.

## النشر على الإنترنت

المشروع يستخدم WebSockets وقاعدة بيانات دائمة، لذا يُنشر على منصة تدعم خادماً يعمل باستمرار
(Render أو Railway). ملف `render.yaml` جاهز للنشر بنقرة على Render.

### خطوات Render

1. اربط المستودع من [render.com](https://render.com) → New → Blueprint
2. سيقرأ `render.yaml` وينشئ الخدمة وقاعدة PostgreSQL تلقائياً
3. أضف متغيرات البيئة الناقصة (`GOOGLE_MAPS_API_KEY` وغيرها)
4. تُنشأ الجداول والبيانات التجريبية تلقائياً عند أول تشغيل

### متغيرات البيئة المطلوبة

انظر ملف `.env.example` للقائمة الكاملة.

## هيكل المشروع

```
app.py            # التطبيق والمسارات
config.py         # الإعدادات
models.py         # نماذج قاعدة البيانات
services.py       # منطق الأعمال (الطلبات، التوصيل، المحفظة)
templates/        # واجهات Jinja2
static/           # CSS / JS / صور
```

## ملاحظة

ملف `.env` وقواعد البيانات المحلية مستثناة من المستودع عبر `.gitignore` — لا ترفع مفاتيحك.
