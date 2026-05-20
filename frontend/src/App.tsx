import { useEffect, useState } from "react";
import { api } from "./api/client";
import { Analysis } from "./pages/Analysis";
import { BillsInput } from "./pages/BillsInput";
import { CreateProject } from "./pages/CreateProject";
import { Dashboard } from "./pages/Dashboard";
import { Reports } from "./pages/Reports";
import { WeatherInput } from "./pages/WeatherInput";
import { Building } from "./types/audit";
import "./styles.css";

const steps = ["Dashboard", "Project", "Bills", "Weather", "Analysis", "Reports"];

export default function App() {
  const [activeStep, setActiveStep] = useState("Dashboard");
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selected, setSelected] = useState<Building | null>(null);

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
          <p className="eyebrow">Iran Residential Energy Audit Platform</p>
          <h1>ممیزی انرژی ساختمان‌های مسکونی مطابق مبحث ۱۹</h1>
          <p>Guided Level 1 and Level 2 audit workflow for Jajarm, North Khorasan climate analysis.</p>
        </div>
      </header>
      <nav className="stepper">
        {steps.map((step) => (
          <button key={step} className={activeStep === step ? "active" : ""} onClick={() => setActiveStep(step)}>
            {step}
          </button>
        ))}
      </nav>
      {selected && <p className="selected">Selected: {selected.project_name} · {selected.city}</p>}
      {activeStep === "Dashboard" && <Dashboard buildings={buildings} onSelect={(building) => { setSelected(building); setActiveStep("Analysis"); }} />}
      {activeStep === "Project" && <CreateProject onCreated={(building) => { setSelected(building); loadBuildings(); setActiveStep("Bills"); }} />}
      {activeStep === "Bills" && selected && <BillsInput buildingId={selected.id} />}
      {activeStep === "Weather" && selected && <WeatherInput buildingId={selected.id} />}
      {activeStep === "Analysis" && selected && <Analysis buildingId={selected.id} />}
      {activeStep === "Reports" && selected && <Reports buildingId={selected.id} />}
      {!selected && !["Dashboard", "Project"].includes(activeStep) && (
        <section className="panel">Select or create a project first.</section>
      )}
    </main>
  );
}
