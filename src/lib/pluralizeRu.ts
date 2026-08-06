/** Русское склонение: 1 модель, 2 модели, 5 моделей */
export function pluralizeRu(count: number, one: string, few: string, many: string): string {
  const abs = Math.abs(count) % 100
  const last = abs % 10
  if (abs > 10 && abs < 20) return many
  if (last === 1) return one
  if (last >= 2 && last <= 4) return few
  return many
}

export function formatCountRu(count: number, one: string, few: string, many: string): string {
  return `${count} ${pluralizeRu(count, one, few, many)}`
}
