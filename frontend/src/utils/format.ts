/** Round to 2 decimals and drop floating-point noise (e.g. 1.3900000000000001 -> 1.39). */
export function formatValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-'
  return String(Math.round(value * 100) / 100)
}
