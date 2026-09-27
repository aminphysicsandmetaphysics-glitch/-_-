import { useMemo, useState } from "react";
import { api } from "../api/client";
import { formatMJ } from "../lib/format";

const months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];

export function BillsInput({ buildingId }: { buildingId: number }) {
  const [year, setYear] = useState(1403);
  const [status, setStatus] = useState<string | null>(null);
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
    setStatus(null);
    try {
      await api.saveBills(buildingId, rows.map((row) => ({ ...row, year })));
      setStatus("قبض‌های ماهانه با موفقیت ذخیره شد.");
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "ذخیره قبض‌ها ناموفق بود");
    }
  }

  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">مرحله ۲ از ۶</p>
          <h2>قبض‌های ماهانه برق و گاز</h2>
          <p>حداقل ۱۲ ماه پیوسته لازم است تا رگرسیون آب‌وهوایی و تحلیل دقیق ممکن شود.</p>
        </div>
        <div className="field" style={{ minWidth: 140 }}>
          <label>سال ممیزی</label>
          <input className="input ltr-num" type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} />
        </div>
      </div>
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>ماه</th>
              <th className="num">برق (kWh)</th>
              <th className="num">گاز (m³)</th>
              <th className="num">هزینه برق</th>
              <th className="num">هزینه گاز</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={row.month}>
                <td>{months[index]}</td>
                {(["electricity_kwh", "gas_m3", "electricity_cost", "gas_cost"] as const).map((key) => (
                  <td key={key} className="num">
                    <input
                      className="input ltr-num"
                      style={{ width: 100, padding: "4px 8px" }}
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
      <p style={{ marginTop: 14 }}>
        مجموع پیش‌نمایش سالانه: <strong className="ltr-num">{formatMJ(totalPreview, "en")}</strong>
      </p>
      {status && <p className="alert">{status}</p>}
      <div className="form-actions">
        <button className="btn btn-primary" onClick={save}>ذخیره قبض‌ها</button>
      </div>
    </section>
  );
}
