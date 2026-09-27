import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { EnergyGauge } from "../components/EnergyGauge";
import { StatCard } from "../components/StatCard";
import { Language } from "../i18n";
import { formatKg, formatMJ, formatNumber, formatToman } from "../lib/format";
import { AuditResult } from "../types/audit";

const months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];

const DIAGNOSIS_TEXT: Record<string, string> = {
  consistent: "مصرف واقعی گاز/گرمایش با تخمین فیزیکی پوسته ساختمان هم‌خوانی دارد — مشکل عمده‌ای در پوسته یا سیستم گرمایش دیده نمی‌شود.",
  system_or_operation: "مصرف واقعی کمی بیشتر از حد انتظار فیزیکی پوسته است؛ احتمالاً سیستم گرمایش کم‌راندمان است یا دمای تنظیمی بالاست، نه لزوماً پوسته ساختمان.",
  envelope_or_system: "فاصله زیادی بین مصرف واقعی و تخمین فیزیکی پوسته دیده می‌شود — هم پوسته ساختمان و هم سیستم گرمایش باید بررسی شوند.",
  insufficient_data: "داده کافی برای مقایسه فیزیکی در دسترس نیست.",
};

const PRECISION_LABEL: Record<string, string> = {
  physics_based_comparison: "محاسبه فیزیکی دقیق",
  measured_equipment_list: "بر اساس تجهیزات ثبت‌شده",
  measured_gas_bill: "بر اساس قبض گاز",
  theoretical_envelope_model: "مدل فیزیکی پوسته",
  assumed_share_of_total: "برآورد تقریبی",
};

export function Analysis({ buildingId, language }: { buildingId: number; language: Language }) {
  const [result, setResult] = useState<AuditResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.runAudit(buildingId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "اجرای تحلیل ناموفق بود (حداقل ۱۲ ماه قبض لازم است)");
    } finally {
      setBusy(false);
    }
  }

  const chartData = result?.monthly.map((item) => ({ ...item, name: months[item.month - 1] })) ?? [];

  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">مرحله ۵ از ۶</p>
          <h2>تحلیل و رتبه‌بندی انرژی</h2>
        </div>
        <button className="btn btn-primary" onClick={run} disabled={busy}>
          {busy ? "در حال تحلیل..." : "اجرای تحلیل"}
        </button>
      </div>
      {error && <p className="alert error">{error}</p>}

      {result && (
        <>
          <div className="panel" style={{ background: "var(--surface-sunken)", border: "none" }}>
            <div className="gauge-wrap" style={{ justifyContent: "space-between" }}>
              <EnergyGauge
                rating={result.energy_rating}
                ratio={result.energy_index_ratio}
                score={result.performance_score}
                bands={result.energy_label_ranges as any}
                language={language}
              />
              {result.confidence && (
                <div>
                  <span className={`confidence-pill ${result.confidence.confidence_level}`}>
                    اطمینان تحلیل: {result.confidence.confidence_level === "high" ? "بالا" : result.confidence.confidence_level === "medium" ? "متوسط" : "پایین"} ({result.confidence.confidence_score}/100)
                  </span>
                  <p style={{ fontSize: "0.78rem", marginTop: 8, maxWidth: 260 }}>
                    بر اساس {result.confidence.bill_months_used} ماه قبض، {result.confidence.weather_days_used} روز داده آب‌وهوا
                    {result.confidence.regression_r_squared != null && ` و برازش آماری R²=${result.confidence.regression_r_squared.toFixed(2)}`}.
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="card-grid">
            <StatCard label="مصرف انرژی سالانه" value={formatMJ(result.total_energy_mj, language)} tone="cold" />
            <StatCard label="شدت مصرف انرژی (EUI)" value={formatMJ(result.eui, language)} hint="بر مترمربع در سال" tone={result.high_consumption_flag ? "hot" : "mid"} />
            <StatCard label="شاخص ایده‌آل (E2)" value={formatMJ(result.ideal_e2 ?? result.standard_eui, language)} tone="mid" />
            <StatCard label="مصرف هر نفر" value={formatMJ(result.energy_per_person, language)} hint="در سال" tone="cold" />
            <StatCard label="درجه‌روز گرمایش/سرمایش" value={`${formatNumber(result.hdd, language)} / ${formatNumber(result.cdd, language)}`} tone="warm" />
            {result.total_co2_kg != null && (
              <StatCard label="ردپای کربن سالانه" value={formatKg(result.total_co2_kg, language)} hint="CO₂ معادل" tone="hot" />
            )}
          </div>

          {result.envelope_diagnosis && (
            <div className="panel" style={{ borderInlineStart: "3px solid var(--thermal-cold)" }}>
              <p className="eyebrow">تشخیص فیزیکی پوسته ساختمان</p>
              <div className="card-grid" style={{ marginBottom: 12 }}>
                <StatCard label="تخمین فیزیکی گرمایش" value={formatMJ(result.theoretical_heating_mj ?? 0, language)} numeric tone="cold" />
                <StatCard label="تخمین فیزیکی سرمایش" value={formatMJ(result.theoretical_cooling_mj ?? 0, language)} numeric tone="mid" />
              </div>
              <p>{DIAGNOSIS_TEXT[result.envelope_diagnosis] ?? result.envelope_diagnosis}</p>
            </div>
          )}

          {result.energy_signature && (
            <div className="panel">
              <p className="eyebrow">امضای انرژی ساختمان (رگرسیون آماری بر مبنای قبض‌ها)</p>
              <div className="card-grid">
                <StatCard label="مصرف پایه (مستقل از آب‌وهوا)" value={formatMJ(result.energy_signature.baseload_mj_per_month * 12, language)} hint="در سال" tone="cold" />
                <StatCard label="ضریب گرمایش" value={`${formatNumber(result.energy_signature.heating_signature_mj_per_hdd, language, 2)} MJ`} hint="به ازای هر درجه‌روز" tone="warm" />
                <StatCard label="ضریب سرمایش" value={`${formatNumber(result.energy_signature.cooling_signature_mj_per_cdd, language, 2)} MJ`} hint="به ازای هر درجه‌روز" tone="mid" />
                <StatCard label="کیفیت برازش (R²)" value={result.energy_signature.r_squared.toFixed(2)} tone="cold" />
              </div>
            </div>
          )}

          <div className="tabs">
            <span style={{ color: "var(--ink-faint)", fontSize: "0.8rem", alignSelf: "center" }}>نمودارها</span>
          </div>
          <div className="card-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="electricity_kwh" fill="#1e3a5f" name="برق kWh" />
                <Bar dataKey="gas_m3" fill="#d6772f" name="گاز m³" />
              </BarChart>
            </ResponsiveContainer>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line dataKey="total_mj" stroke="#2a7f6c" name="مجموع MJ" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={[{ name: "EUI در برابر E2", actual: result.eui, ideal: result.ideal_e2 ?? result.standard_eui }]}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="actual" fill="#b54b3a" name="EUI واقعی" />
                <Bar dataKey="ideal" fill="#2a7f6c" name="E2 ایده‌آل" />
              </BarChart>
            </ResponsiveContainer>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={result.weather_monthly.map((item) => ({ ...item, name: months[item.month - 1] }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line dataKey="temp_avg" stroke="#b54b3a" name="دما °C" />
                <Line dataKey="humidity" stroke="#1e3a5f" name="رطوبت %" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {result.anomalies.length > 0 && (
            <>
              <h3>هشدارهای مصرف</h3>
              <div className="recommendation-list" style={{ marginBottom: 20 }}>
                {result.anomalies.map((item) => (
                  <div key={`${item.month}-${item.type}`} className="recommendation-item" style={{ gridTemplateColumns: "auto 1fr" }}>
                    <span className={`impact-dot ${item.type === "peak" ? "high" : "medium"}`} />
                    <div>
                      <div className="rec-text"><strong>{months[item.month - 1]}</strong> · {item.type === "peak" ? "اوج مصرف غیرمنتظره" : "افت مصرف غیرمنتظره"}</div>
                      <div className="rec-meta">{item.message}</div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          <h3>راهکارهای بهینه‌سازی (به ترتیب صرفه‌جویی مالی)</h3>
          <div className="recommendation-list">
            {result.recommendations.map((item) => (
              <div key={item.id} className="recommendation-item">
                <span className={`impact-dot ${item.impact_level}`} />
                <div>
                  <div className="rec-text">
                    {item.recommendation.split("|")[language === "fa" ? 1 : 0]?.trim() || item.recommendation}
                    {item.precision && <span className="precision-tag">{PRECISION_LABEL[item.precision] ?? item.precision}</span>}
                  </div>
                  {item.savings_base_source && (
                    <div className="rec-meta">مبنای محاسبه: {PRECISION_LABEL[item.savings_base_source] ?? item.savings_base_source}</div>
                  )}
                </div>
                <div className="rec-numbers">
                  {item.quantified ? (
                    <>
                      <strong>{formatToman(item.estimated_annual_savings_toman ?? 0, language)}</strong>
                      <span>صرفه‌جویی سالانه</span>
                      {item.estimated_payback_years_low != null && (
                        <div style={{ marginTop: 4 }}>
                          بازگشت سرمایه: <span className="ltr-num">{item.estimated_payback_years_low}-{item.estimated_payback_years_high}</span> سال
                        </div>
                      )}
                    </>
                  ) : (
                    <span>{item.impact_level}</span>
                  )}
                </div>
              </div>
            ))}
            {result.recommendations.length === 0 && <p>در این تحلیل توصیه‌ای شناسایی نشد.</p>}
          </div>

          <h3 style={{ marginTop: 28 }}>مصرف تجهیزات</h3>
          <div className="card-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={result.electric_equipment}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="annual_kwh" fill="#1e3a5f" name="kWh/سال" />
              </BarChart>
            </ResponsiveContainer>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={result.gas_equipment}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="annual_m3" fill="#d6772f" name="m³/سال" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
      {!result && !error && <p>برای مشاهده نتایج، دکمه «اجرای تحلیل» را بزنید.</p>}
    </section>
  );
}
