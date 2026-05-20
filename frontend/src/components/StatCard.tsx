type Props = {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "danger" | "success";
};

export function StatCard({ label, value, hint, tone = "default" }: Props) {
  return (
    <div className={`stat-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {hint && <small>{hint}</small>}
    </div>
  );
}
