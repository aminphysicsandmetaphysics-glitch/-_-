import { toPersianDigits } from "../lib/format";
import { Language } from "../i18n";

type Band = { rating: string; min_ratio: number | string; max_ratio: number | string };

type Props = {
  rating: string;
  ratio?: number;
  score?: number | null;
  bands?: Band[];
  language: Language;
};

const RATING_COLOR: Record<string, string> = {
  A: "var(--rating-a)",
  B: "var(--rating-b)",
  C: "var(--rating-c)",
  D: "var(--rating-d)",
  E: "var(--rating-e)",
};

const GAUGE_MIN = 0.4;
const GAUGE_MAX = 1.7;

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const angleRad = ((angleDeg - 180) * Math.PI) / 180;
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

function arcPath(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
}

export function EnergyGauge({ rating, ratio, score, bands, language }: Props) {
  const cx = 110;
  const cy = 110;
  const r = 88;

  const segments = (bands ?? []).map((band) => {
    const min = typeof band.min_ratio === "string" ? parseFloat(band.min_ratio) : band.min_ratio;
    const max = typeof band.max_ratio === "string" ? parseFloat(band.max_ratio) : band.max_ratio;
    const clampedMin = Math.max(min, GAUGE_MIN);
    const clampedMax = Math.min(isFinite(max) ? max : GAUGE_MAX, GAUGE_MAX);
    const startAngle = ((clampedMin - GAUGE_MIN) / (GAUGE_MAX - GAUGE_MIN)) * 180;
    const endAngle = ((clampedMax - GAUGE_MIN) / (GAUGE_MAX - GAUGE_MIN)) * 180;
    return { rating: band.rating, startAngle, endAngle };
  });

  const clampedRatio = Math.min(Math.max(ratio ?? 1, GAUGE_MIN), GAUGE_MAX);
  const needleAngle = ((clampedRatio - GAUGE_MIN) / (GAUGE_MAX - GAUGE_MIN)) * 180;
  const needleTip = polarToCartesian(cx, cy, r - 14, needleAngle);

  const digits = (value: string | number) => (language === "fa" ? toPersianDigits(value) : String(value));

  return (
    <div className="gauge-wrap">
      <svg width="220" height="130" viewBox="0 0 220 130">
        {segments.length > 0 ? (
          segments.map((segment) => (
            <path
              key={segment.rating}
              d={arcPath(cx, cy, r, segment.startAngle, segment.endAngle)}
              stroke={RATING_COLOR[segment.rating] ?? "var(--border-strong)"}
              strokeWidth={16}
              fill="none"
              strokeLinecap="butt"
            />
          ))
        ) : (
          <path d={arcPath(cx, cy, r, 0, 180)} stroke="var(--border-strong)" strokeWidth={16} fill="none" />
        )}
        <line x1={cx} y1={cy} x2={needleTip.x} y2={needleTip.y} stroke="var(--ink)" strokeWidth={3} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={6} fill="var(--ink)" />
      </svg>
      <div className="gauge-readout">
        <span className="rating-badge" style={{ backgroundColor: RATING_COLOR[rating] ?? "#475569" }}>
          {language === "fa" ? `رتبه ${digits(rating)}` : `Rating ${rating}`}
        </span>
        <div className="rating-letter" style={{ color: RATING_COLOR[rating] ?? "var(--ink)" }}>
          {digits(rating)}
        </div>
        {score != null && (
          <div className="rating-sub">
            {language === "fa" ? `امتیاز عملکرد: ${digits(score)}/۱۰۰` : `Performance score: ${score}/100`}
          </div>
        )}
        {ratio != null && (
          <div className="rating-sub">
            {language === "fa" ? `نسبت به مصرف ایده‌آل: ${digits(ratio.toFixed(2))}×` : `Ratio to ideal: ${ratio.toFixed(2)}×`}
          </div>
        )}
      </div>
    </div>
  );
}
