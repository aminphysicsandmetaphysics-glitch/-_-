import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { ElectricEquipment, GasEquipment } from "../types/audit";

const electricDefaults: ElectricEquipment[] = [
  { name: "Refrigerator | یخچال", category: "appliance", quantity: 1, power_w: 120, hours_per_day: 8, days_per_year: 365, usage_period: "year-round" },
  { name: "Lighting | روشنایی", category: "lighting", quantity: 10, power_w: 12, hours_per_day: 5, days_per_year: 365, usage_period: "night" },
  { name: "Split AC | کولر گازی", category: "cooling", quantity: 1, power_w: 1800, hours_per_day: 4, days_per_year: 120, usage_period: "summer" },
];

const gasDefaults: GasEquipment[] = [
  { name: "Gas stove | اجاق گاز", category: "cooking", quantity: 1, gas_m3_per_hour: 0.7, hours_per_day: 2, days_per_year: 365, usage_period: "daily" },
  { name: "Gas heater | بخاری", category: "heating", quantity: 2, gas_m3_per_hour: 0.6, hours_per_day: 6, days_per_year: 120, usage_period: "winter" },
  { name: "Water heater | آبگرمکن", category: "dhw", quantity: 1, gas_m3_per_hour: 1.5, hours_per_day: 0.8, days_per_year: 365, usage_period: "daily" },
];

export function EquipmentInput({ buildingId }: { buildingId: number }) {
  const [electricRows, setElectricRows] = useState(electricDefaults);
  const [gasRows, setGasRows] = useState(gasDefaults);
  const [savedElectric, setSavedElectric] = useState<ElectricEquipment[]>([]);
  const [savedGas, setSavedGas] = useState<GasEquipment[]>([]);

  async function save() {
    setSavedElectric(await api.saveElectricEquipment(buildingId, electricRows) as ElectricEquipment[]);
    setSavedGas(await api.saveGasEquipment(buildingId, gasRows) as GasEquipment[]);
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

  return (
    <section className="panel">
      <p className="eyebrow">Equipment | تجهیزات مصرف‌کننده انرژی</p>
      <h2>Electric and Gas Equipment | تجهیزات برقی و گازسوز</h2>
      <h3>Electric equipment | تجهیزات برقی</h3>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Qty</th><th>Power W</th><th>h/day</th><th>days/year</th><th>Period</th></tr></thead>
          <tbody>
            {electricRows.map((row, index) => (
              <tr key={index}>
                <td><input value={row.name} onChange={(event) => updateElectric(index, "name", event.target.value)} /></td>
                <td><input type="number" value={row.quantity} onChange={(event) => updateElectric(index, "quantity", event.target.value)} /></td>
                <td><input type="number" value={row.power_w} onChange={(event) => updateElectric(index, "power_w", event.target.value)} /></td>
                <td><input type="number" value={row.hours_per_day} onChange={(event) => updateElectric(index, "hours_per_day", event.target.value)} /></td>
                <td><input type="number" value={row.days_per_year} onChange={(event) => updateElectric(index, "days_per_year", event.target.value)} /></td>
                <td><input value={row.usage_period ?? ""} onChange={(event) => updateElectric(index, "usage_period", event.target.value)} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button className="secondary" onClick={() => setElectricRows([...electricRows, { name: "New device", quantity: 1, power_w: 0, hours_per_day: 0, days_per_year: 365 }])}>Add electric device</button>

      <h3>Gas equipment | تجهیزات گازسوز</h3>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Qty</th><th>m³/h</th><th>h/day</th><th>days/year</th><th>Period</th></tr></thead>
          <tbody>
            {gasRows.map((row, index) => (
              <tr key={index}>
                <td><input value={row.name} onChange={(event) => updateGas(index, "name", event.target.value)} /></td>
                <td><input type="number" value={row.quantity} onChange={(event) => updateGas(index, "quantity", event.target.value)} /></td>
                <td><input type="number" value={row.gas_m3_per_hour} onChange={(event) => updateGas(index, "gas_m3_per_hour", event.target.value)} /></td>
                <td><input type="number" value={row.hours_per_day} onChange={(event) => updateGas(index, "hours_per_day", event.target.value)} /></td>
                <td><input type="number" value={row.days_per_year} onChange={(event) => updateGas(index, "days_per_year", event.target.value)} /></td>
                <td><input value={row.usage_period ?? ""} onChange={(event) => updateGas(index, "usage_period", event.target.value)} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button className="secondary" onClick={() => setGasRows([...gasRows, { name: "New gas device", quantity: 1, gas_m3_per_hour: 0, hours_per_day: 0, days_per_year: 365 }])}>Add gas device</button>
      <div className="actions"><button className="primary" onClick={save}>Save equipment</button></div>
      {(savedElectric.length > 0 || savedGas.length > 0) && (
        <div className="charts">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={savedElectric}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Legend /><Bar dataKey="annual_kwh" fill="#2563eb" name="kWh/year" /></BarChart>
          </ResponsiveContainer>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={savedGas}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Legend /><Bar dataKey="annual_m3" fill="#f97316" name="m³/year" /></BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
