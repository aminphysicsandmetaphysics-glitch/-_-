import { useState } from "react";
import { api } from "../api/client";

export function Reports({ buildingId }: { buildingId: number }) {
  const [busy, setBusy] = useState<"pdf" | "excel" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function download(kind: "pdf" | "excel") {
    setBusy(kind);
    setError(null);
    try {
      const url = kind === "pdf" ? api.pdfUrl(buildingId) : api.excelUrl(buildingId);
      await api.downloadReport(url, `audit-${buildingId}.${kind === "pdf" ? "pdf" : "xlsx"}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "دانلود گزارش ناموفق بود");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">مرحله ۶ از ۶</p>
          <h2>خروجی حرفه‌ای گزارش</h2>
          <p>گزارش PDF شامل مشخصات ساختمان، قبض‌ها، شاخص‌ها، تحلیل آب‌وهوایی، رتبه انرژی، و توصیه‌های کمّی‌شده است.</p>
        </div>
      </div>
      {error && <p className="alert error">{error}</p>}
      <div className="form-actions">
        <button className="btn btn-primary" onClick={() => download("pdf")} disabled={busy !== null}>
          {busy === "pdf" ? "در حال ساخت..." : "دانلود گزارش PDF"}
        </button>
        <button className="btn" onClick={() => download("excel")} disabled={busy !== null}>
          {busy === "excel" ? "در حال ساخت..." : "دانلود گزارش اکسل"}
        </button>
      </div>
    </section>
  );
}
