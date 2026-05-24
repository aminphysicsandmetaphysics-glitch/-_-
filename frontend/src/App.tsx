import { useEffect, useState } from "react";
import { api } from "./api/client";
import { Analysis } from "./pages/Analysis";
import { BillsInput } from "./pages/BillsInput";
import { CreateProject } from "./pages/CreateProject";
import { Dashboard } from "./pages/Dashboard";
import { EquipmentInput } from "./pages/EquipmentInput";
import { Reports } from "./pages/Reports";
import { WeatherInput } from "./pages/WeatherInput";
import { Language, useT } from "./i18n";
import { Building } from "./types/audit";
import "./styles.css";

const steps = [
  { key: "Dashboard", label: "stepDashboard" },
  { key: "Project", label: "stepProject" },
  { key: "Bills", label: "stepBills" },
  { key: "Weather", label: "stepWeather" },
  { key: "Equipment", label: "stepEquipment" },
  { key: "Analysis", label: "stepAnalysis" },
  { key: "Reports", label: "stepReports" },
] as const;

export default function App() {
  const [activeStep, setActiveStep] = useState("Dashboard");
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selected, setSelected] = useState<Building | null>(null);
  const [language, setLanguage] = useState<Language>("fa");
  const t = useT(language);

  async function loadBuildings() {
    setBuildings(await api.listBuildings());
  }

  useEffect(() => {
    loadBuildings().catch(console.error);
  }, []);

  return (
    <main>
      <header className="hero">
        <div>
          <p className="eyebrow">{t("energyAudit")}</p>
          <h1>ممیزی انرژی ساختمان‌های مسکونی مطابق مبحث ۱۹</h1>
          <p>{t("subtitle")}</p>
        </div>
        <label className="language-toggle">
          {t("language")}
          <select value={language} onChange={(event) => setLanguage(event.target.value as Language)}>
            <option value="fa">فارسی</option>
            <option value="en">English</option>
          </select>
        </label>
      </header>
      <nav className="stepper">
        {steps.map((step) => (
          <button key={step.key} className={activeStep === step.key ? "active" : ""} onClick={() => setActiveStep(step.key)}>
            {t(step.label)}
          </button>
        ))}
      </nav>
      {selected && <p className="selected">{t("selected")}: {selected.project_name} · {selected.city}</p>}
      {activeStep === "Dashboard" && <Dashboard buildings={buildings} onSelect={(building) => { setSelected(building); setActiveStep("Analysis"); }} />}
      {activeStep === "Project" && <CreateProject language={language} onCreated={(building) => { setSelected(building); loadBuildings(); setActiveStep("Bills"); }} />}
      {activeStep === "Bills" && selected && <BillsInput buildingId={selected.id} />}
      {activeStep === "Weather" && selected && <WeatherInput buildingId={selected.id} />}
      {activeStep === "Equipment" && selected && <EquipmentInput buildingId={selected.id} />}
      {activeStep === "Analysis" && selected && <Analysis buildingId={selected.id} />}
      {activeStep === "Reports" && selected && <Reports buildingId={selected.id} />}
      {!selected && !["Dashboard", "Project"].includes(activeStep) && (
        <section className="panel">{t("selectFirst")}</section>
      )}
    </main>
  );
}
