export function toMeters(value, unit) {
  const factors = { m: 1, km: 1000, cm: 0.01 };
  return value * factors[unit];
}
