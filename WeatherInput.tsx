import { useRef, useState } from "react";
import { api } from "../api/client";

export function WeatherInput({ buildingId, city }: { buildingId: number; city?: string }) {
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [rowCount, setRowCount] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function autoFetch() {
    setBusy(true);
    setStatus(null);
    try {
      const rows = await api.autoFetchWeather(buildingId, city);
      setRowCount(rows.length);
      setStatus(`داده‌های آب‌وهوای یک سال اخیر برای «${city ?? "شهر پروژه"}» به‌صورت خودکار دریافت و ذخیره شد (${rows.length} روز).`);
    } catch (err) {
      setStatus(
        err instanceof Error
          ? `دریافت خودکار ناموفق بود: ${err.message}. می‌توانید فایل اکسل را دستی بارگذاری کنید.`
          : "دریافت خودکار ناموفق بود.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setStatus(null);
    try {
      const rows = await api.importWeatherExcel(buildingId, file);
      setRowCount(Array.isArray(rows) ? rows.length : null);
      setStatus("فایل اکسل آب‌وهوا با موفقیت وارد شد.");
    } catch {
      setStatus("وارد کردن فایل اکسل ناموفق بود. ستون‌های Date و Mean/Avg Temp را بررسی کنید.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">مرحله ۳ از ۶</p>
          <h2>داده‌های آب‌وهوایی</h2>
          <p>
            سیستم داده‌های آب‌وهوای یک سال اخیر را به‌صورت خودکار از سرویس Open-Meteo (بر اساس نام شهر) دریافت می‌کند —
            نیازی به وارد کردن دستی نیست، مگر اینکه بخواهید داده‌های اندازه‌گیری‌شده خودتان را جایگزین کنید.
          </p>
        </div>
      </div>

      <div className="metric-card tone-cold" style={{ marginBottom: 18 }}>
        <span className="label">دریافت خودکار</span>
        <p style={{ margin: "8px 0 12px" }}>
          شهر پروژه: <strong>{city ?? "تعیین‌نشده"}</strong>
        </p>
        <button className="btn btn-primary" onClick={autoFetch} disabled={busy}>
          {busy ? "در حال دریافت..." : "دریافت خودکار آب‌وهوای یک سال اخیر"}
        </button>
      </div>

      <div className="metric-card tone-mid">
        <span className="label">جایگزین: بارگذاری فایل اکسل</span>
        <p style={{ margin: "8px 0 12px" }}>ستون‌های لازم: Date, Temp Min, Temp Max, Mean/Avg Temp, Humidity (اختیاری)</p>
        <input ref={fileRef} type="file" accept=".xlsx,.xls" onChange={handleFile} disabled={busy} />
      </div>

      {status && <p className={`alert ${status.includes("ناموفق") ? "error" : ""}`} style={{ marginTop: 16 }}>{status}</p>}
      {rowCount != null && <p style={{ marginTop: 8 }}>تعداد رکوردهای ذخیره‌شده: <span className="ltr-num">{rowCount}</span></p>}
    </section>
  );
}
