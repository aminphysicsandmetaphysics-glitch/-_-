import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { ElectricEquipment, EquipmentPreset, GasEquipment } from "../types/audit";

const electricDefaults: ElectricEquipment[] = [
  { name: "یخچال‌فریزر", category: "refrigeration", quantity: 1, power_w: 120, hours_per_day: 24, days_per_year: 365, usage_period: "year-round" },
];

const gasDefaults: GasEquipment[] = [
  { name: "پکیج گازی", category: "heating", quantity: 1, gas_m3_per_hour: 1.3, hours_per_day: 6, days_per_year: 150, usage_period: "winter" },
];

export function EquipmentInput({ buildingId }: { buildingId: number }) {
  const [electricRows, setElectricRows] = useState(electricDefaults);
  const [gasRows, setGasRows] = useState(gasDefaults);
  const [savedElectric, setSavedElectric] = useState<ElectricEquipment[]>([]);
  const [savedGas, setSavedGas] = useState<GasEquipment[]>([]);
  const [electricPresets, setElectricPresets] = useState<EquipmentPreset[]>([]);
  const [gasPresets, setGasPresets] = useState<EquipmentPreset[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    api.equipmentCatalog("electric").then(setElectricPresets).catch(() => {});
    api.equipmentCatalog("gas").then(setGasPresets).catch(() => {});
  }, []);

  async function save() {
    setStatus(null);
    try {
      setSavedElectric(await api.saveElectricEquipment(buildingId, electricRows));
      setSavedGas(await api.saveGasEquipment(buildingId, gasRows));
      setStatus("تجهیزات ذخیره شد.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "ذخیره تجهیزات ناموفق بود");
    }
  }

  function updateElectric(index: number, key: keyof ElectricEquipment, value: string) {
    const next = [...electricRows];
    next[index] = { ...next[index], [key]: ["quantity", "power_w", "hours_per_day", "days_per_year"].includes(String(key)) ? Number(value) : value };
    setElectricRows(next);
  }

  function updateGas(index: number, key: keyof GasEquipment, value: string) {
    const next = [...gasRows];
    next[index] = { ...next[index], [key]: ["quantity", "gas_m3_per_hour", "hours_per_day", "days_per_year"].includes(String(key)) ? Number(value) : value };
    setGasRows(next);
  }

  function addFromElectricPreset(key: string) {
    const preset = electricPresets.find((p) => p.key === key);
    if (!preset) return;
    setElectricRows([
      ...electricRows,
      {
        name: preset.label_fa,
        category: preset.category,
        quantity: 1,
        power_w: preset.typical_power_w,
        hours_per_day: preset.typical_hours_per_day,
        days_per_year: preset.typical_days_per_year,
        usage_period: "",
      },
    ]);
  }

  function addFromGasPreset(key: string) {
    const preset = gasPresets.find((p) => p.key === key);
    if (!preset) return;
    setGasRows([
      ...gasRows,
      {
        name: preset.label_fa,
        category: preset.category,
        quantity: 1,
        gas_m3_per_hour: preset.typical_gas_m3_per_hour,
        hours_per_day: preset.typical_hours_per_day,
        days_per_year: preset.typical_days_per_year,
        usage_period: "",
      },
    ]);
  }

  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">مرحله ۴ از ۶</p>
          <h2>تجهیزات برقی و گازسوز</h2>
          <p>یک دستگاه را از فهرست انتخاب کنید تا توان مصرفی و ساعات کارکرد نمونه آن به‌طور خودکار پر شود؛ سپس در صورت نیاز مقادیر را ویرایش کنید.</p>
        </div>
      </div>

      <h3>تجهیزات برقی</h3>
      <div className="field" style={{ maxWidth: 360, marginBottom: 12 }}>
        <label>افزودن از فهرست دستگاه‌های برقی رایج</label>
        <select className="select" defaultValue="" onChange={(e) => { if (e.target.value) addFromElectricPreset(e.target.value); e.target.value = ""; }}>
          <option value="" disabled>انتخاب دستگاه...</option>
          {electricPresets.map((p) => <option key={p.key} value={p.key}>{p.label_fa}</option>)}
        </select>
      </div>
      <div className="table-scroll">
        <table className="data-table">
          <thead><tr><th>نام</th><th className="num">تعداد</th><th className="num">توان (W)</th><th className="num">ساعت/روز</th><th className="num">روز/سال</th></tr></thead>
          <tbody>
            {electricRows.map((row, index) => (
              <tr key={index}>
                <td><input className="input" style={{ minWidth: 160 }} value={row.name} onChange={(e) => updateElectric(index, "name", e.target.value)} /></td>
                <td className="num"><input className="input ltr-num" style={{ width: 70 }} type="number" value={row.quantity} onChange={(e) => updateElectric(index, "quantity", e.target.value)} /></td>
                <td className="num"><input className="input ltr-num" style={{ width: 90 }} type="number" value={row.power_w} onChange={(e) => updateElectric(index, "power_w", e.target.value)} /></td>
                <td className="num"><input className="input ltr-num" style={{ width: 80 }} type="number" value={row.hours_per_day} onChange={(e) => updateElectric(index, "hours_per_day", e.target.value)} /></td>
                <td className="num"><input className="input ltr-num" style={{ width: 90 }} type="number" value={row.days_per_year} onChange={(e) => updateElectric(index, "days_per_year", e.target.value)} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button className="btn btn-sm" style={{ marginTop: 10 }} onClick={() => setElectricRows([...electricRows, { name: "دستگاه جدید", quantity: 1, power_w: 0, hours_per_day: 0, days_per_year: 365 }])}>+ افزودن دستی</button>

      <h3 style={{ marginTop: 28 }}>تجهیزات گازسوز</h3>
      <div className="field" style={{ maxWidth: 360, marginBottom: 12 }}>
        <label>افزودن از فهرست دستگاه‌های گازسوز رایج</label>
        <select className="select" defaultValue="" onChange={(e) => { if (e.target.value) addFromGasPreset(e.target.value); e.target.value = ""; }}>
          <option value="" disabled>انتخاب دستگاه...</option>
          {gasPresets.map((p) => <option key={p.key} value={p.key}>{p.label_fa}</option>)}
        </select>
      </div>
      <div className="table-scroll">
        <table className="data-table">
          <thead><tr><th>نام</th><th className="num">تعداد</th><th className="num">m³/ساعت</th><th className="num">ساعت/روز</th><th className="num">روز/سال</th></tr></thead>
          <tbody>
            {gasRows.map((row, index) => (
              <tr key={index}>
                <td><input className="input" style={{ minWidth: 160 }} value={row.name} onChange={(e) => updateGas(index, "name", e.target.value)} /></td>
                <td className="num"><input className="input ltr-num" style={{ width: 70 }} type="number" value={row.quantity} onChange={(e) => updateGas(index, "quantity", e.target.value)} /></td>
                <td className="num"><input className="input ltr-num" style={{ width: 90 }} type="number" step="0.1" value={row.gas_m3_per_hour} onChange={(e) => updateGas(index, "gas_m3_per_hour", e.target.value)} /></td>
                <td className="num"><input className="input ltr-num" style={{ width: 80 }} type="number" value={row.hours_per_day} onChange={(e) => updateGas(index, "hours_per_day", e.target.value)} /></td>
                <td className="num"><input className="input ltr-num" style={{ width: 90 }} type="number" value={row.days_per_year} onChange={(e) => updateGas(index, "days_per_year", e.target.value)} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button className="btn btn-sm" style={{ marginTop: 10 }} onClick={() => setGasRows([...gasRows, { name: "دستگاه گازسوز جدید", quantity: 1, gas_m3_per_hour: 0, hours_per_day: 0, days_per_year: 365 }])}>+ افزودن دستی</button>

      <div className="form-actions">
        <button className="btn btn-primary" onClick={save}>ذخیره تجهیزات</button>
      </div>
      {status && <p className="alert" style={{ marginTop: 12 }}>{status}</p>}

      {(savedElectric.length > 0 || savedGas.length > 0) && (
        <div className="card-grid" style={{ marginTop: 24, gridTemplateColumns: "1fr 1fr" }}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={savedElectric}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="annual_kwh" fill="#1e3a5f" name="kWh/سال" />
            </BarChart>
          </ResponsiveContainer>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={savedGas}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="annual_m3" fill="#d6772f" name="m³/سال" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
