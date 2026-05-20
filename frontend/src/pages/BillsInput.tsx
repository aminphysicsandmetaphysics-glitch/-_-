import { useMemo, useState } from "react";
import { api } from "../api/client";

const months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];

export function BillsInput({ buildingId }: { buildingId: number }) {
  const [year, setYear] = useState(1402);
  const [rows, setRows] = useState(() =>
    months.map((_, index) => ({
      year,
      month: index + 1,
      electricity_kwh: index > 3 && index < 8 ? 420 : 210,
      gas_m3: index > 8 || index < 3 ? 260 : 35,
      electricity_cost: 0,
      gas_cost: 0,
    })),
  );
  const totalPreview = useMemo(
    () => rows.reduce((sum, row) => sum + row.electricity_kwh * 3.6 + row.gas_m3 * 38, 0),
    [rows],
  );

  async function save() {
    await api.saveBills(buildingId, rows.map((row) => ({ ...row, year })));
    alert("Bills saved");
  }

  return (
    <section className="panel">
      <p className="eyebrow">Step 2 | Energy Bills Input</p>
      <h2>Monthly Utility Bills | قبض برق و گاز</h2>
      <label className="year-field">
        Audit year
        <input type="number" value={year} onChange={(event) => setYear(Number(event.target.value))} />
      </label>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Month</th>
              <th>Electricity kWh</th>
              <th>Gas m³</th>
              <th>Electricity Cost</th>
              <th>Gas Cost</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={row.month}>
                <td>{months[index]}</td>
                {(["electricity_kwh", "gas_m3", "electricity_cost", "gas_cost"] as const).map((key) => (
                  <td key={key}>
                    <input
                      type="number"
                      value={row[key]}
                      onChange={(event) => {
                        const next = [...rows];
                        next[index] = { ...row, [key]: Number(event.target.value) };
                        setRows(next);
                      }}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>Preview annual total: {totalPreview.toLocaleString()} MJ</p>
      <button className="primary" onClick={save}>Save bills</button>
    </section>
  );
}
