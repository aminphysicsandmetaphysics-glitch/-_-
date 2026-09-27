# راهنمای خیلی ساده اجرای پروژه روی Render

این پروژه حالا فایل `render.yaml` دارد. یعنی لازم نیست دیتابیس، بک‌اند و فرانت‌اند را جدا جدا دستی بسازی.

## کاری که باید انجام بدهی

### 1. فایل‌های جدید را در GitHub آپلود کن

اگر با Git کار می‌کنی:

```bash
cd energy-audit-app
git add .
git commit -m "Add Render deployment blueprint"
git push
```

اگر با سایت GitHub آپلود می‌کنی، کل فایل‌های تغییر کرده را آپلود کن، مخصوصاً:

- `render.yaml`
- `backend/Dockerfile`
- `backend/app/main.py`
- `backend/app/core/config.py`

### 2. در Render برو به Blueprint

1. وارد سایت Render شو.
2. روی `New` بزن.
3. گزینه `Blueprint` را انتخاب کن.
4. ریپازیتوری GitHub پروژه را انتخاب کن.
5. اگر Render مسیر فایل را پرسید، این را بده:

```text
energy-audit-app/render.yaml
```

اگر ریپازیتوری فقط همین پروژه است و فایل `render.yaml` در ریشه ریپو قرار دارد، مسیر می‌شود:

```text
render.yaml
```

### 3. Apply را بزن

Render خودش این 3 مورد را می‌سازد:

- دیتابیس PostgreSQL
- بک‌اند FastAPI
- فرانت‌اند React

### 4. صبر کن تا Deploy تمام شود

بعد از چند دقیقه باید این آدرس‌ها را ببینی:

- Frontend:

```text
https://energy-audit-frontend.onrender.com
```

- Backend:

```text
https://energy-audit-backend.onrender.com
```

- تست بک‌اند:

```text
https://energy-audit-backend.onrender.com/health
```

اگر جواب `{"status":"ok"}` دیدی یعنی بک‌اند درست اجرا شده است.

## نکته مهم درباره اسم سرویس‌ها

در فایل `render.yaml` اسم‌ها این‌ها هستند:

- `energy-audit-backend`
- `energy-audit-frontend`
- `energy-audit-db`

اگر در Render اسم سرویس‌ها را تغییر بدهی، باید آدرس‌ها هم در `render.yaml` تغییر کنند. برای راحتی، اسم‌ها را تغییر نده.

## اگر خطا گرفتی

از صفحه سرویس در Render وارد بخش `Logs` شو و متن خطا را برای من بفرست. من دقیقاً می‌گویم چه چیزی را اصلاح کنی.
