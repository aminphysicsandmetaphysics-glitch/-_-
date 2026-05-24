import { FormEvent, useState } from "react";
import { api } from "../api/client";
import { CreatableSelect } from "../components/CreatableSelect";
import { Language, useT } from "../i18n";
import { Building } from "../types/audit";

const options = {
  lighting_type: ["LED", "CFL", "incandescent", "halogen", "لامپ LED", "لامپ رشته‌ای"],
  window_type: ["single", "double glazed", "low-e double glazed", "تک جداره", "دوجداره"],
  wall_type: ["brick wall", "concrete block", "insulated wall", "دیوار آجری", "دیوار عایق‌دار"],
  roof_type: ["flat roof", "pitched roof", "insulated roof", "سقف تخت", "سقف عایق‌دار"],
  heating_system: ["old boiler", "condensing boiler", "package radiator", "gas heater", "پکیج", "بخاری گازی"],
  cooling_system: ["old split / low EER", "inverter split", "evaporative cooler", "کولر آبی", "اسپلیت اینورتر"],
  orientation: ["south", "south-west", "north", "east-west", "جنوبی", "جنوب غربی"],
  climate_zone: ["very_cold", "cold", "moderate_dry", "moderate_humid", "hot_dry", "hot_humid", "mild", "coastal"],
};

const initialForm = {
  project_name: "Jajarm Residential Case Study",
  city: "جاجرم",
  address: "",
  area_m2: 150,
  floors: 2,
  year_built: 2005,
  occupants: 4,
  building_type: "Residential",
  climate_zone: "moderate_dry",
  ideal_e2: 324,
  heating_system: "old boiler",
  cooling_system: "old split / low EER",
  lighting_type: "incandescent",
  window_type: "single",
  wall_type: "brick wall",
  roof_type: "flat roof",
  has_insulation: false,
  has_thermostat: false,
  has_shading: false,
  orientation: "south-west",
};

const labels: Record<string, string> = {
  project_name: "Project name | نام پروژه",
  city: "City | شهر",
  address: "Address | آدرس",
  area_m2: "Area m² | مساحت",
  floors: "Floors | طبقات",
  year_built: "Year built | سال ساخت",
  occupants: "Occupants | نفرات",
  building_type: "Building type | نوع ساختمان",
  climate_zone: "Climate zone | اقلیم ۸گانه",
  ideal_e2: "Ideal E2 MJ/m².year | شاخص ایده‌آل",
  heating_system: "Heating system | سیستم گرمایش",
  cooling_system: "Cooling system | سیستم سرمایش",
  lighting_type: "Lighting type | نوع لامپ",
  window_type: "Window type | نوع پنجره",
  wall_type: "Wall material | مصالح دیوار",
  roof_type: "Roof type | نوع سقف",
  orientation: "Orientation | جهت‌گیری",
};

export function CreateProject({ onCreated, language }: { onCreated: (building: Building) => void; language: Language }) {
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const t = useT(language);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const building = await api.createBuilding(form);
      onCreated(building);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save project");
    }
  }

  return (
    <section className="panel">
      <p className="eyebrow">Step 1 | {t("project")}</p>
      <h2>{t("createProject")} | اطلاعات ساختمان</h2>
      {error && <p className="danger-text">{error}</p>}
      <form className="form-grid" onSubmit={submit}>
        {Object.entries(form).map(([key, value]) => {
          if (typeof value === "boolean") {
            return (
              <label key={key} className="checkbox">
                <input
                  type="checkbox"
                  checked={value}
                  onChange={(event) => setForm({ ...form, [key]: event.target.checked })}
                />
                {key.replaceAll("_", " ")}
              </label>
            );
          }
          if (key in options) {
            return (
              <CreatableSelect
                key={key}
                label={labels[key] ?? key}
                value={String(value ?? "")}
                options={options[key as keyof typeof options]}
                onChange={(nextValue) => setForm({ ...form, [key]: nextValue })}
              />
            );
          }
          return (
            <label key={key}>
              {labels[key] ?? key.replaceAll("_", " ")}
              <input
                value={value ?? ""}
                type={typeof value === "number" ? "number" : "text"}
                onChange={(event) =>
                  setForm({
                    ...form,
                    [key]: typeof value === "number" ? Number(event.target.value) : event.target.value,
                  })
                }
              />
            </label>
          );
        })}
        <button className="primary">{t("saveContinue")}</button>
      </form>
    </section>
  );
}
