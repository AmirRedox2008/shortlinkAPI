<div dir="rtl">

# 🔗 ShortLink — کوتاه‌کننده لینک

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?logo=vuedotjs&logoColor=white)

لینک کوتاه‌کن Full-Stack با **FastAPI + Redis + Vue.js** — شامل آمار کلیک، کش، Rate Limit، QR Code و داشبورد فارسی، همه در قالب یک پروژه تمیز و قابل دیپلوی.

</div>

## ✨ امکانات

<div dir="rtl">

- 🔗 **کوتاه‌سازی لینک** با کد سفارشی (اختیاری) و تاریخ انقضا
- ⚡ **کش Redis** با TTL — لینک‌های پربازدید بدون حتی یک تماس با دیتابیس سرو می‌شن
- 🛡️ **مقاوم به قطعی Redis** (الگوی Fail-Open) — اگه ردیس بخوابه، اپ همچنان کار می‌کنه
- 🚦 **Rate Limiting** با الگوی INCR/EXPIRE روی هر IP
- 📊 **آمار کامل کلیک** — شمارنده اتمیک، نمودار ۷ روز اخیر، پربازدیدترین منبع‌های ورودی
- 🧾 **ثبت لاگ کلیک در پس‌زمینه** با BackgroundTasks — ریدایرکت منتظر دیتابیس نمی‌مونه
- 📱 **QR Code** برای هر لینک (خروجی PNG)
- 🖥️ **داشبورد فارسی RTL** با Vue 3 + Jinja2 — بدون npm، بدون build، فقط CDN
- 🐳 **Docker Compose** کامل (اپلیکیشن + Redis)
- 📚 **مستندات خودکار** با Swagger UI

</div>

## 📸 دمو


<img width="1920" height="934" alt="Screenshot 2026-10-19 at 10-04-03 لینک_کوتاه" src="https://github.com/user-attachments/assets/7a21c757-2b2a-4dbb-9367-db2532e853bc" />


## 🚀 اجرا با Docker (پیشنهادی)

```bash
git clone https://github.com/AmirRedox2008/shortlink.git
cd shortlink
docker compose up --build
```

- داشبورد: `http://localhost:8000`
- مستندات: `http://localhost:8000/docs`

## 🔧 اجرا بدون Docker

```bash
git clone https://github.com/AmirRedox2008/shortlink.git
cd shortlink

python -m venv venv
source venv/bin/activate          # ویندوز: venv\Scripts\activate

pip install -r requirements.txt

# Redis باید در دسترس باشه:
sudo systemctl start redis-server  # لینوکس
# یا: docker run -d -p 6379:6379 redis:7-alpine

uvicorn main:app --reload
```

## ⚙️ متغیرهای محیطی

| متغیر | پیش‌فرض | توضیح |
|-------|---------|-------|
| `DATABASE_URL` | `sqlite:///./shortener.db` | آدرس دیتابیس |
| `REDIS_URL` | `redis://localhost:6379/0` | آدرس سرور Redis |
| `BASE_URL` | `http://localhost:8000` | دامنه عمومی (برای ساخت لینک کوتاه و QR) |
| `CACHE_TTL` | `3600` | مدت نگهداری لینک در کش (ثانیه) |
| `RATE_LIMIT` | `20` | حداکثر درخواست در هر بازه زمانی |
| `RATE_LIMIT_WINDOW` | `60` | طول بازه زمانی Rate Limit (ثانیه) |

## 📋 API Endpoints

| Method | Path | توضیح |
|--------|------|-------|
| `POST` | `/url/short` | ساخت لینک کوتاه |
| `GET` | `/{code}` | ریدایرکت به لینک اصلی (302) |
| `GET` | `/{code}/stats` | آمار کلیک (روزانه + منبع ورودی) |
| `GET` | `/{code}/qr` | QR Code لینک (تصویر PNG) |
| `GET` | `/url/all` | لیست همه لینک‌ها |
| `DELETE` | `/{code}` | حذف لینک |
| `GET` | `/docs` | مستندات تعاملی Swagger |

### نمونه استفاده

```bash
# ساخت لینک کوتاه
curl -X POST http://localhost:8000/url/short \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com", "custom_code": "gh"}'

# خروجی:
# {"short_code":"gh","original_url":"https://github.com","clicks":0,"expires_at":null}

# ریدایرکت
curl -i http://localhost:8000/gh
```

## 🏗️ ساختار پروژه

```
shortLink/
├── main.py              # اپ FastAPI + روت داشبورد
├── link.py              # API Endpoints
├── core/
│   ├── config.py        # تنظیمات (خواندن از env)
│   ├── cache.py         # لایه کش Redis
│   └── ratelimit.py     # Rate Limiter (INCR/EXPIRE)
├── database/
│   ├── models.py        # مدل‌های SQLAlchemy (Links, ClickLogs)
│   └── session.py       # Engine + Session + init_db
├── template/            # قالب‌های Jinja2 + Vue 3
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🧠 تصمیم‌های فنی

<div dir="rtl">

- **چرا 302 و نه 301؟** چون 301 تو مرورگر کش می‌شه و کلیک‌های بعدی دیگه به سرور نمی‌رسن — یعنی آمار از بین می‌ره. همه سرویس‌های معروف از 302 استفاده می‌کنن.
- **چرا Fail-Open؟** Redis یه سرویس جانبیه، نه قلب اپ. اگه ردیس قطع شه، کش و Rate Limit موقتاً غیرفعال می‌شن ولی ریدایرکت — که وظیفه اصلیه — همچنان کار می‌کنه.
- **شمارنده اتمیک:** به‌جای خواندن/نوشتن ساده، از `UPDATE ... SET clicks = clicks + 1` استفاده شده تا در همزمانی (race condition) عدد گم نشه.
- **ثبت لاگ غیرهمزمان:** ثبت هر کلیک با `BackgroundTasks` بعد از ارسال پاسخ انجام می‌شه تا تاخیر ریدایرکت حداقل باشه.

</div>

## 🗺️ نقشه راه

- [ ] تست‌های pytest + CI با GitHub Actions
- [ ] احراز هویت JWT و لینک‌های اختصاصی هر کاربر
- [ ] مهاجرت به PostgreSQL + Alembic
- [ ] ریدایرکت هوشمند (موبایل/دسکتاپ)
- [ ] دیپلوی زنده روی Railway / Render

## 👨‍💻 توسعه‌دهنده

**[@AmirRedox2008](https://github.com/AmirRedox2008)**

<div dir="rtl">

اگه پروژه برات مفید بود، یه ⭐ بده! ⭐

</div>

<div dir="rtl">

## 📄 لایسنس

این پروژه تحت لایسنس [MIT](LICENSE) منتشر شده است.

</div>
