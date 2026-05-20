import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { RatingBadge } from "../components/RatingBadge";
import { StatCard } from "../components/StatCard";
import { AuditResult } from "../types/audit";

const months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];

export function Analysis({ buildingId }: { buildingId: number }) {
  const [result, setResult] = useState<AuditResult | null>(null);

  async function run() {
    setResult(await api.runAudit(buildingId));
  }

  const chartData = result?.monthly.map((item) => ({ ...item, name: months[item.month - 1] })) ?? [];

  return (
    <section className="panel">
      <p className="eyebrow">Steps 4-6 | Energy Analysis, Rating, Recommendations</p>
      <div className="section-header">
        <h2>Audit Results | نتایج ممیزی</h2>
        <button className="primary" onClick={run}>Run analysis</button>
      </div>
      {result && (
        <>
          <div className="stats-grid">
            <StatCard label="Annual Energy" value={`${result.total_energy_mj.toFixed(0)} MJ`} />
            <StatCard label="EUI" value={`${result.eui.toFixed(1)} MJ/m².year`} tone={result.high_consumption_flag ? "danger" : "success"} />
            <StatCard label="Energy/person" value={`${result.energy_per_person.toFixed(0)} MJ/person.year`} />
            <StatCard label="HDD / CDD" value={`${result.hdd.toFixed(0)} / ${result.cdd.toFixed(0)}`} />
          </div>
          <div className="rating-row">
            <RatingBadge rating={result.energy_rating} />
            <span>Benchmark مبحث ۱۹: {result.standard_eui} MJ/m².year</span>
            {result.high_consumption_flag && <strong className="danger-text">مصرف انرژی بالاتر از استاندارد</strong>}
          </div>
          <div className="charts">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="electricity_kwh" fill="#2563eb" name="Electricity kWh" />
                <Bar dataKey="gas_m3" fill="#f97316" name="Gas m³" />
              </BarChart>
            </ResponsiveContainer>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line dataKey="total_mj" stroke="#0f766e" name="Total MJ" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <h3>Recommendations | راهکارهای بهینه‌سازی</h3>
          <div className="recommendations">
            {result.recommendations.map((item) => (
              <article key={item.id}>
                <span>{item.category}</span>
                <p>{item.recommendation}</p>
                <strong>{item.impact_level}</strong>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
