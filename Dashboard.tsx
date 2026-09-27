import { Building } from "../types/audit";
import { StatCard } from "../components/StatCard";

type Props = {
  buildings: Building[];
  onSelect: (building: Building) => void;
  onNewProject: () => void;
};

export function Dashboard({ buildings, onSelect, onNewProject }: Props) {
  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">داشبورد</p>
          <h2>پروژه‌های ممیزی انرژی</h2>
        </div>
        <button className="btn btn-primary" onClick={onNewProject}>+ پروژه ممیزی جدید</button>
      </div>
      <div className="card-grid">
        <StatCard label="تعداد پروژه‌ها" value={buildings.length} hint="ساختمان‌های ثبت‌شده در این حساب" tone="cold" />
        <StatCard label="شاخص اصلی" value="EUI" hint="مگاژول بر مترمربع در سال" tone="mid" numeric={false} />
        <StatCard label="استاندارد مرجع" value="مبحث ۱۹" hint="مقررات ملی ساختمان ایران" tone="warm" numeric={false} />
      </div>
      <div className="project-list">
        {buildings.map((building) => (
          <button key={building.id} className="project-row" onClick={() => onSelect(building)}>
            <div className="project-row-top">
              <strong>{building.project_name}</strong>
            </div>
            <span>
              {building.city} · <span className="ltr-num">{building.area_m2}</span> m² · <span className="ltr-num">{building.occupants}</span> نفر
            </span>
          </button>
        ))}
        {buildings.length === 0 && (
          <div className="empty-state">
            <p>هنوز پروژه‌ای ثبت نشده. با «پروژه ممیزی جدید» شروع کنید.</p>
          </div>
        )}
      </div>
    </section>
  );
}
