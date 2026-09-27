import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import { Language, useT } from "../i18n";
import { Building, EnvelopeMaterial } from "../types/audit";

const freeTextOptions = {
  climate_zone: [
    { value: "very_cold", label: "بسیار سرد" },
    { value: "cold", label: "سرد" },
    { value: "moderate_dry", label: "معتدل خشک" },
    { value: "moderate_humid", label: "معتدل مرطوب" },
    { value: "hot_dry", label: "گرم و خشک" },
    { value: "hot_humid", label: "گرم و مرطوب" },
    { value: "mild", label: "ملایم" },
    { value: "coastal", label: "ساحلی" },
  ],
  airtightness: [
    { value: "leaky", label: "نشتی هوا زیاد (بدون آب‌بندی)" },
    { value: "medium", label: "متوسط (وضعیت رایج)" },
    { value: "tight", label: "آب‌بندی‌شده / پنجره و درز مدرن" },
  ],
  orientation: [
    { value: "south", label: "جنوبی" },
    { value: "south-west", label: "جنوب غربی" },
    { value: "north", label: "شمالی" },
    { value: "east-west", label: "شرقی-غربی" },
  ],
  heating_system: ["پکیج گازی معمولی", "پکیج گازی چگالشی", "بخاری گازی", "شوفاژ برقی"],
  cooling_system: ["کولر آبی", "اسپلیت معمولی", "اسپلیت اینورتر"],
  lighting_type: ["لامپ رشته‌ای/هالوژن", "لامپ کم‌مصرف (CFL)", "LED"],
};

const initialForm: Record<string, unknown> = {
  project_name: "پروژه ممیزی جاجرم",
  city: "جاجرم",
  address: "",
  area_m2: 150,
  floors: 1,
  year_built: 2005,
  occupants: 4,
  building_type: "Residential",
  climate_zone: "moderate_dry",
  heating_system: "پکیج گازی معمولی",
  cooling_system: "اسپلیت معمولی",
  lighting_type: "لامپ رشته‌ای/هالوژن",
  has_insulation: false,
  has_thermostat: false,
  has_shading: false,
  orientation: "south-west",
  wall_material_key: "wall_brick_single_wythe",
  roof_material_key: "roof_flat_uninsulated",
  floor_material_key: "floor_slab_on_grade",
  window_material_key: "window_single_aluminum",
  airtightness: "medium",
};

const fieldOrder = [
  "project_name", "city", "address", "area_m2", "floors", "year_built", "occupants",
  "climate_zone", "orientation",
  "heating_system", "cooling_system", "lighting_type",
  "wall_material_key", "roof_material_key", "floor_material_key", "window_material_key", "airtightness",
  "has_insulation", "has_thermostat", "has_shading",
];

const labels: Record<string, string> = {
  project_name: "نام پروژه",
  city: "شهر",
  address: "آدرس (برای دریافت خودکار آب‌وهوا)",
  area_m2: "متراژ (m²)",
  floors: "تعداد طبقات",
  year_built: "سال ساخت",
  occupants: "تعداد نفرات",
  climate_zone: "اقلیم (مبحث ۱۹)",
  orientation: "جهت‌گیری اصلی ساختمان",
  heating_system: "سیستم گرمایش",
  cooling_system: "سیستم سرمایش",
  lighting_type: "نوع روشنایی غالب",
  wall_material_key: "جنس دیوار خارجی",
  roof_material_key: "جنس سقف/پشت‌بام",
  floor_material_key: "جنس کف (تماس با زمین)",
  window_material_key: "نوع پنجره",
  airtightness: "میزان آب‌بندی/نفوذ هوا",
  has_insulation: "عایق حرارتی اضافی نصب شده",
  has_thermostat: "ترموستات هوشمند دارد",
  has_shading: "سایه‌بان/پرده در پنجره‌ها دارد",
};

export function CreateProject({ onCreated, language }: { onCreated: (building: Building) => void; language: Language }) {
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [envelopeCatalog, setEnvelopeCatalog] = useState<EnvelopeMaterial[]>([]);
  const t = useT(language);

  useEffect(() => {
    api.envelopeCatalog().then(setEnvelopeCatalog).catch(() => setEnvelopeCatalog([]));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const building = await api.createBuilding(form as Partial<Building>);
      onCreated(building);
    } catch (err) {
      setError(err instanceof Error ? err.message : "ذخیره پروژه ناموفق بود");
    }
  }

  function envelopeOptionsFor(category: string) {
    return envelopeCatalog.filter((m) => m.category === category).map((m) => ({ value: m.key, label: m.label_fa }));
  }

  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">مرحله ۱ از ۶</p>
          <h2>اطلاعات ساختمان و پوسته حرارتی</h2>
        </div>
      </div>
      {error && <p className="alert error">{error}</p>}
      <form onSubmit={submit}>
        <div className="form-grid">
          {fieldOrder.map((key) => {
            const value = form[key];
            if (typeof value === "boolean") {
              return (
                <div key={key} className="checkbox-row" style={{ alignSelf: "end", paddingBottom: 9 }}>
                  <input type="checkbox" checked={value} onChange={(e) => setForm({ ...form, [key]: e.target.checked })} id={key} />
                  <label htmlFor={key} style={{ fontWeight: 400 }}>{labels[key]}</label>
                </div>
              );
            }
            if (key.endsWith("_material_key")) {
              const category = key.replace("_material_key", "");
              return (
                <div className="field" key={key}>
                  <label>{labels[key]}</label>
                  <select className="select" value={String(value ?? "")} onChange={(e) => setForm({ ...form, [key]: e.target.value })}>
                    {envelopeOptionsFor(category).map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                  <span className="catalog-hint">U-value این گزینه به‌صورت خودکار در محاسبه اعمال می‌شود</span>
                </div>
              );
            }
            if (key in freeTextOptions) {
              const opts = freeTextOptions[key as keyof typeof freeTextOptions];
              const normalized = opts.map((o) => (typeof o === "string" ? { value: o, label: o } : o));
              return (
                <div className="field" key={key}>
                  <label>{labels[key]}</label>
                  <select className="select" value={String(value ?? "")} onChange={(e) => setForm({ ...form, [key]: e.target.value })}>
                    {normalized.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              );
            }
            return (
              <div className="field" key={key}>
                <label>{labels[key] ?? key}</label>
                <input
                  className="input"
                  value={String(value ?? "")}
                  type={typeof value === "number" ? "number" : "text"}
                  onChange={(e) => setForm({ ...form, [key]: typeof value === "number" ? Number(e.target.value) : e.target.value })}
                />
              </div>
            );
          })}
        </div>
        <div className="form-actions">
          <button className="btn btn-primary" type="submit">ذخیره و ادامه</button>
        </div>
      </form>
    </section>
  );
}
