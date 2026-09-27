const colors: Record<string, string> = {
  A: "var(--rating-a)",
  B: "var(--rating-b)",
  C: "var(--rating-c)",
  D: "var(--rating-d)",
  E: "var(--rating-e)",
};

export function RatingBadge({ rating, label }: { rating: string; label?: string }) {
  return (
    <span className="rating-badge" style={{ backgroundColor: colors[rating] ?? "#475569" }}>
      {label ?? `Rating ${rating}`}
    </span>
  );
}
