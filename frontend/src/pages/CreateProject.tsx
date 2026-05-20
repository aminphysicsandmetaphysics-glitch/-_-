import { FormEvent, useState } from "react";
import { api } from "../api/client";
import { Building } from "../types/audit";

const initialForm = {
  project_name: "Jajarm Residential Case Study",
  city: "جاجرم",
  address: "",
  area_m2: 150,
  floors: 2,
  year_built: 2005,
  occupants: 4,
  building_type: "Residential",
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

export function CreateProject({ onCreated }: { onCreated: (building: Building) => void }) {
  const [form, setForm] = useState(initialForm);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const building = await api.createBuilding(form);
    onCreated(building);
  }

  return (
    <section className="panel">
      <p className="eyebrow">Step 1 | Create Audit Project</p>
      <h2>Building Information | اطلاعات ساختمان</h2>
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
          return (
            <label key={key}>
              {key.replaceAll("_", " ")}
              <input
                value={value}
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
        <button className="primary">Save project and continue</button>
      </form>
    </section>
  );
}
