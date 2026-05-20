import { Building } from "../types/audit";
import { StatCard } from "../components/StatCard";

type Props = {
  buildings: Building[];
  onSelect: (building: Building) => void;
};

export function Dashboard({ buildings, onSelect }: Props) {
  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">داشبورد | Dashboard</p>
          <h2>Residential Audit Projects</h2>
        </div>
        <span className="alert">مصرف انرژی بالاتر از استاندارد will be highlighted after analysis.</span>
      </div>
      <div className="stats-grid">
        <StatCard label="Projects" value={buildings.length} hint="Buildings in portfolio" />
        <StatCard label="Default city" value="جاجرم" hint="North Khorasan climate case" />
        <StatCard label="Primary index" value="EUI" hint="MJ/m².year" />
      </div>
      <div className="project-list">
        {buildings.map((building) => (
          <button key={building.id} className="project-row" onClick={() => onSelect(building)}>
            <strong>{building.project_name}</strong>
            <span>{building.city} · {building.area_m2} m² · {building.occupants} occupants</span>
          </button>
        ))}
        {buildings.length === 0 && <p>No projects yet. Start with Step 1: Create Audit Project.</p>}
      </div>
    </section>
  );
}
