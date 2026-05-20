import { api } from "../api/client";

export function Reports({ buildingId }: { buildingId: number }) {
  return (
    <section className="panel">
      <p className="eyebrow">Step 7 | Report Generation</p>
      <h2>Professional Outputs | خروجی حرفه‌ای</h2>
      <p>PDF includes building description, bills, charts-ready tables, indices, climate analysis, rating, and recommendations.</p>
      <div className="actions">
        <a className="primary link-button" href={api.pdfUrl(buildingId)}>Download PDF Report</a>
        <a className="secondary link-button" href={api.excelUrl(buildingId)}>Download Excel Report</a>
      </div>
    </section>
  );
}
