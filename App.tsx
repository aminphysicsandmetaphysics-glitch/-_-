import { useEffect, useState } from "react";
import { api } from "./api/client";
import { Analysis } from "./pages/Analysis";
import { AuthScreen } from "./pages/Auth";
import { BillsInput } from "./pages/BillsInput";
import { CreateProject } from "./pages/CreateProject";
import { Dashboard } from "./pages/Dashboard";
import { EquipmentInput } from "./pages/EquipmentInput";
import { Reports } from "./pages/Reports";
import { WeatherInput } from "./pages/WeatherInput";
import { Language } from "./i18n";
import { useAuth } from "./lib/auth";
import { Building } from "./types/audit";

const steps = [
  { key: "Dashboard", label: "داشبورد" },
  { key: "Project", label: "۱ · اطلاعات ساختمان" },
  { key: "Bills", label: "۲ · قبض‌های انرژی" },
  { key: "Weather", label: "۳ · آب‌وهوا" },
  { key: "Equipment", label: "۴ · تجهیزات" },
  { key: "Analysis", label: "۵ · تحلیل و رتبه" },
  { key: "Reports", label: "۶ · گزارش خروجی" },
] as const;

export default function App() {
  const { user, loading, logout } = useAuth();
  const [activeStep, setActiveStep] = useState<string>("Dashboard");
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selected, setSelected] = useState<Building | null>(null);
  const [language, setLanguage] = useState<Language>("fa");

  async function loadBuildings() {
    try {
      setBuildings(await api.listBuildings());
    } catch {
      /* not authenticated yet or empty */
    }
  }

  useEffect(() => {
    if (user) loadBuildings();
  }, [user]);

  if (loading) {
    return <div className="auth-shell" />;
  }

  if (!user) {
    return <AuthScreen />;
  }

  const requiresBuilding = !["Dashboard", "Project"].includes(activeStep);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark" />
          <div>
            <strong>ممیزی هوشمند انرژی</strong>
            <span>مبحث ۱۹ · جاجرم</span>
          </div>
        </div>
        {steps.map((step, index) => (
          <button
            key={step.key}
            className={`nav-step ${activeStep === step.key ? "active" : ""}`}
            onClick={() => setActiveStep(step.key)}
            disabled={index > 0 && !selected && step.key !== "Project"}
          >
            {step.key !== "Dashboard" && <span className="nav-index">{index}</span>}
            {step.label}
          </button>
        ))}
        <div className="sidebar-footer">
          <span className="ltr-num" style={{ direction: "ltr", textAlign: "start" }}>{user.email}</span>
          <button className="btn btn-sm btn-ghost" onClick={logout} style={{ padding: 0, justifyContent: "flex-start" }}>
            خروج از حساب
          </button>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <span className="topbar-context">
            {selected ? (
              <>
                پروژه فعال: <strong>{selected.project_name}</strong> · {selected.city}
              </>
            ) : (
              "پروژه‌ای انتخاب نشده"
            )}
          </span>
          <div className="topbar-actions">
            <select className="select" style={{ padding: "6px 10px" }} value={language} onChange={(e) => setLanguage(e.target.value as Language)}>
              <option value="fa">فارسی</option>
              <option value="en">English</option>
            </select>
          </div>
        </header>
        <main className="content">
          {activeStep === "Dashboard" && (
            <Dashboard
              buildings={buildings}
              onSelect={(building) => {
                setSelected(building);
                setActiveStep("Analysis");
              }}
              onNewProject={() => setActiveStep("Project")}
            />
          )}
          {activeStep === "Project" && (
            <CreateProject
              language={language}
              onCreated={(building) => {
                setSelected(building);
                loadBuildings();
                setActiveStep("Bills");
              }}
            />
          )}
          {activeStep === "Bills" && selected && <BillsInput buildingId={selected.id} />}
          {activeStep === "Weather" && selected && <WeatherInput buildingId={selected.id} city={selected.city} />}
          {activeStep === "Equipment" && selected && <EquipmentInput buildingId={selected.id} />}
          {activeStep === "Analysis" && selected && <Analysis buildingId={selected.id} language={language} />}
          {activeStep === "Reports" && selected && <Reports buildingId={selected.id} />}
          {requiresBuilding && !selected && (
            <section className="panel empty-state">ابتدا یک پروژه از داشبورد انتخاب یا ایجاد کنید.</section>
          )}
        </main>
      </div>
    </div>
  );
}
