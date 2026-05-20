const colors: Record<string, string> = {
  A: "#16a34a",
  B: "#65a30d",
  C: "#ca8a04",
  D: "#ea580c",
  E: "#dc2626",
};

export function RatingBadge({ rating }: { rating: string }) {
  return (
    <span className="rating-badge" style={{ backgroundColor: colors[rating] ?? "#475569" }}>
      Rating {rating}
    </span>
  );
}
