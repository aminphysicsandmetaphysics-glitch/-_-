type Props = {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "cold" | "mid" | "warm" | "hot";
  numeric?: boolean;
};

export function StatCard({ label, value, hint, tone = "cold", numeric = true }: Props) {
  return (
    <div className={`metric-card tone-${tone}`}>
      <span className="label">{label}</span>
      <strong className={`value ${numeric ? "ltr-num" : ""}`}>{value}</strong>
      {hint && <small className="hint">{hint}</small>}
    </div>
  );
}
