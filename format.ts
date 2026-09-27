const persianDigits = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

export function toPersianDigits(value: string | number): string {
  return String(value).replace(/[0-9]/g, (digit) => persianDigits[Number(digit)]);
}

export function formatNumber(value: number, locale: "fa" | "en", fractionDigits = 0): string {
  const rounded = value.toFixed(fractionDigits);
  const withSeparators = Number(rounded).toLocaleString("en-US", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
  return locale === "fa" ? toPersianDigits(withSeparators) : withSeparators;
}

export function formatToman(value: number, locale: "fa" | "en"): string {
  const formatted = formatNumber(Math.round(value), locale);
  return locale === "fa" ? `${formatted} تومان` : `${formatted} Toman`;
}

export function formatMJ(value: number, locale: "fa" | "en"): string {
  return `${formatNumber(value, locale)} MJ`;
}

export function formatKg(value: number, locale: "fa" | "en"): string {
  return `${formatNumber(value, locale, 1)} kg`;
}
