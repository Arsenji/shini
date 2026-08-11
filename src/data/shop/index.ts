import { shopProducts } from './products'
import type { ShopCategory, ShopCategoryFilter, ShopProduct, ShopSeason } from './types'
import { shopCategoryLabels } from './types'

export * from './types'
export { shopProducts } from './products'

export type ParsedTireSize = {
  width: string
  profile: string
  diameter: string
}

/** Разбор размера диска: ширина из 5x14 / 4x114, диаметр из R15 или 5x15 → R15 */
export type ParsedDiskSize = {
  widths: string[]
  diameters: string[]
}

/** Разбор размера камеры / ободной ленты: 11.00-20, 6.95R16, УК15 */
export type ParsedAccessorySize = {
  widths: string[]
  diameters: string[]
}

export type ShopSizeFilters = {
  width: string
  profile: string
  diameter: string
}

/** Нормализация размера для поиска: 205/55 R16 → 205/55r16 */
export function normalizeSize(value: string): string {
  return value.toLowerCase().replace(/\s+/g, '').replace(/,/g, '.')
}

/** Разбор 205/55R16, 215/75R17.5, 185/75R16C, 8.25R20, 12R22.5, 14.00-20 */
export function parseTireSize(value: string): ParsedTireSize | null {
  const normalized = normalizeSize(value)
  const metric = normalized.match(/^(\d{3})\/(\d{2,3})r?(\d{2}(?:\.\d)?)(c)?$/)
  if (metric) {
    return {
      width: metric[1],
      profile: metric[2],
      diameter: metric[4] ? `${metric[3]}C` : metric[3],
    }
  }

  // Грузовые форматы без профиля: 8.25R20, 12R22.5
  const truck = normalized.match(/^(\d{1,2}(?:\.\d+)?)r(\d{2}(?:\.\d)?)(c)?$/)
  if (truck) {
    return {
      width: truck[1],
      profile: '',
      diameter: truck[3] ? `${truck[2]}C` : truck[2],
    }
  }

  // Диагональные грузовые: 14.00-20, 11.2-20
  const diagonal = normalized.match(/^(\d{1,2}(?:\.\d+)?)-(\d{2}(?:\.\d+)?)(c)?$/)
  if (diagonal) {
    return {
      width: diagonal[1],
      profile: '',
      diameter: diagonal[3] ? `${diagonal[2]}C` : diagonal[2],
    }
  }

  return null
}

function formatDiskNumber(value: string): string {
  const normalized = value.replace(',', '.')
  const num = Number(normalized)
  if (!Number.isFinite(num)) return normalized
  return String(num)
}

/** Из «5x14 4x100 ET45» → widths [5, 4], diameters [R14] */
export function parseDiskSize(value: string): ParsedDiskSize {
  const text = value.replace(/,/g, '.').replace(/[х×*]/gi, 'x')
  const widths = new Set<string>()
  const diameters = new Set<string>()

  for (const match of text.matchAll(/(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)/gi)) {
    widths.add(formatDiskNumber(match[1]))
    const second = Number(match[2].replace(',', '.'))
    // Диаметр обода: 5x14 → R14 (не путать с PCD 4x100 / 5x114.3)
    if (second >= 12 && second <= 25) {
      diameters.add(`R${formatDiskNumber(match[2])}`)
    }
  }

  for (const match of text.matchAll(/\bR\s*(\d{2}(?:\.\d)?)\b/gi)) {
    diameters.add(`R${formatDiskNumber(match[1])}`)
  }

  return {
    widths: Array.from(widths),
    diameters: Array.from(diameters),
  }
}

/** Из «11.00-20», «6.95R16», «УК15», «15.5/65-18» → ширина + R-диаметр */
export function parseAccessorySize(value: string): ParsedAccessorySize {
  const text = value.trim().replace(/,/g, '.')
  const widths = new Set<string>()
  const diameters = new Set<string>()

  const uk = text.match(/^УК\s*(\d{2})$/i)
  if (uk) {
    diameters.add(`R${uk[1]}`)
    return { widths: [], diameters: Array.from(diameters) }
  }

  const rOnly = text.match(/^R\s*(\d{2}(?:\.\d)?)$/i)
  if (rOnly) {
    diameters.add(`R${formatDiskNumber(rOnly[1])}`)
    return { widths: [], diameters: Array.from(diameters) }
  }

  const slash = text.match(/^(\d+(?:\.\d+)?)\/(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/i)
  if (slash) {
    widths.add(formatDiskNumber(slash[1]))
    diameters.add(`R${formatDiskNumber(slash[3])}`)
    return { widths: Array.from(widths), diameters: Array.from(diameters) }
  }

  const wr = text.match(/^(\d+(?:\.\d+)?)\s*R\s*(\d{2}(?:\.\d)?)$/i)
  if (wr) {
    widths.add(formatDiskNumber(wr[1]))
    diameters.add(`R${formatDiskNumber(wr[2])}`)
    return { widths: Array.from(widths), diameters: Array.from(diameters) }
  }

  const dash = text.match(/^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/)
  if (dash) {
    widths.add(formatDiskNumber(dash[1]))
    const diameter = Number(dash[2])
    if (diameter <= 50) {
      diameters.add(`R${formatDiskNumber(dash[2])}`)
    } else {
      diameters.add(formatDiskNumber(dash[2]))
    }
    return { widths: Array.from(widths), diameters: Array.from(diameters) }
  }

  const triple = text.match(/^(\d+)-(\d+)-(\d+)$/)
  if (triple) {
    widths.add(formatDiskNumber(triple[1]))
    diameters.add(formatDiskNumber(triple[3]))
    return { widths: Array.from(widths), diameters: Array.from(diameters) }
  }

  return { widths: [], diameters: [] }
}

export function getProductSizeParts(product: ShopProduct): ParsedTireSize[] {
  return product.sizes
    .map(parseTireSize)
    .filter((part): part is ParsedTireSize => part !== null)
}

export function getProductDiskSizeParts(product: ShopProduct): ParsedDiskSize[] {
  return product.sizes.map(parseDiskSize)
}

export function getProductAccessorySizeParts(product: ShopProduct): ParsedAccessorySize[] {
  return product.sizes.map(parseAccessorySize)
}

function isAccessoryCategory(category: ShopCategory): boolean {
  return category === 'tube' || category === 'rimTape'
}

function matchesSeason(product: ShopProduct, season: ShopSeason | 'all'): boolean {
  if (season === 'all') return true
  // Диски / камеры / ленты / грузовые без сезона — показываем при любом сезоне
  if (!product.season) return true
  if (product.season === 'allseason') return true
  return product.season === season
}

function matchesWidthDiameterFilters(
  parts: { widths: string[]; diameters: string[] }[],
  sizeFilters: ShopSizeFilters,
): boolean {
  const { width, diameter } = sizeFilters
  if (!width && !diameter) return true

  return parts.some((part) => {
    if (width && !part.widths.includes(width)) return false
    if (diameter && !part.diameters.includes(diameter)) return false
    return true
  })
}

function matchesSizeFilters(product: ShopProduct, sizeFilters: ShopSizeFilters): boolean {
  const { width, profile, diameter } = sizeFilters
  if (!width && !profile && !diameter) return true

  if (product.category === 'disk') {
    return matchesWidthDiameterFilters(getProductDiskSizeParts(product), sizeFilters)
  }

  if (isAccessoryCategory(product.category)) {
    return matchesWidthDiameterFilters(getProductAccessorySizeParts(product), sizeFilters)
  }

  return getProductSizeParts(product).some((part) => {
    if (width && part.width !== width) return false
    if (profile && part.profile !== profile) return false
    if (diameter && part.diameter !== diameter) return false
    return true
  })
}

export function filterShopProducts(
  products: ShopProduct[],
  category: ShopCategoryFilter,
  season: ShopSeason | 'all',
  sizeFilters: ShopSizeFilters,
  color = '',
): ShopProduct[] {
  return products.filter((product) => {
    if (category !== 'all' && product.category !== category) return false
    if (!matchesSeason(product, season)) return false
    if (color && product.color !== color) return false
    return matchesSizeFilters(product, sizeFilters)
  })
}

/** Уникальные цвета дисков (для фильтра каталога) */
export function getDiskColors(products: ShopProduct[]): string[] {
  const colors = new Set<string>()
  for (const product of products) {
    if (product.category === 'disk' && product.color) {
      colors.add(product.color)
    }
  }
  return Array.from(colors).sort((a, b) => a.localeCompare(b, 'ru'))
}

function getWidthDiameterFilterOptions(
  partsList: { widths: string[]; diameters: string[] }[],
  sizeFilters: ShopSizeFilters,
): { widths: string[]; profiles: string[]; diameters: string[] } {
  const widths = new Set<string>()
  const diameters = new Set<string>()

  for (const part of partsList) {
    const widthOk = !sizeFilters.width || part.widths.includes(sizeFilters.width)
    const diameterOk = !sizeFilters.diameter || part.diameters.includes(sizeFilters.diameter)

    if (diameterOk) {
      for (const width of part.widths) widths.add(width)
    }
    if (widthOk) {
      for (const diameter of part.diameters) diameters.add(diameter)
    }
  }

  const byNumber = (a: string, b: string) => parseFloat(a.replace(/^R/i, '')) - parseFloat(b.replace(/^R/i, ''))

  return {
    widths: Array.from(widths).sort(byNumber),
    profiles: [],
    diameters: Array.from(diameters).sort(byNumber),
  }
}

/** Уникальные значения ширины/профиля/диаметра с учётом уже выбранных фильтров */
export function getSizeFilterOptions(
  products: ShopProduct[],
  sizeFilters: ShopSizeFilters,
): { widths: string[]; profiles: string[]; diameters: string[] } {
  const onlyDisks = products.length > 0 && products.every((product) => product.category === 'disk')
  if (onlyDisks) {
    return getWidthDiameterFilterOptions(
      products.flatMap((product) => getProductDiskSizeParts(product)),
      sizeFilters,
    )
  }

  const onlyAccessories =
    products.length > 0 && products.every((product) => isAccessoryCategory(product.category))
  if (onlyAccessories) {
    return getWidthDiameterFilterOptions(
      products.flatMap((product) => getProductAccessorySizeParts(product)),
      sizeFilters,
    )
  }

  const widths = new Set<string>()
  const profiles = new Set<string>()
  const diameters = new Set<string>()

  for (const product of products) {
    for (const part of getProductSizeParts(product)) {
      const widthOk = !sizeFilters.width || part.width === sizeFilters.width
      const profileOk = !sizeFilters.profile || part.profile === sizeFilters.profile
      const diameterOk = !sizeFilters.diameter || part.diameter === sizeFilters.diameter

      if (profileOk && diameterOk) widths.add(part.width)
      if (widthOk && diameterOk && part.profile) profiles.add(part.profile)
      if (widthOk && profileOk) diameters.add(part.diameter)
    }
  }

  const byNumber = (a: string, b: string) => parseFloat(a) - parseFloat(b)

  return {
    widths: Array.from(widths).sort(byNumber),
    profiles: Array.from(profiles).sort(byNumber),
    diameters: Array.from(diameters).sort(byNumber),
  }
}

export function getUniqueSizeGroups(products: ShopProduct[]): string[] {
  const groups = new Set<string>()
  for (const product of products) {
    if (product.sizeGroup) groups.add(product.sizeGroup)
  }
  return Array.from(groups).sort(compareTireSizes)
}

/**
 * Чипы размерной сетки: sizeGroup (если есть) или все sizes товара.
 * У дисков sizeGroup / sizes — полная спецификация (5x13 4x98 ET35 58,6).
 * Уже отфильтрованный список (категория + сезон) передавайте снаружи.
 */
export function getCatalogSizeChips(products: ShopProduct[]): string[] {
  const chips = new Set<string>()
  for (const product of products) {
    if (product.category === 'disk') {
      for (const size of product.sizes) {
        chips.add(size)
      }
      continue
    }
    if (product.sizeGroup) {
      chips.add(product.sizeGroup)
      continue
    }
    for (const size of product.sizes) {
      chips.add(size)
    }
  }
  return Array.from(chips).sort(compareTireSizes)
}

const SIZE_CHIP_CATEGORY_ORDER: ShopCategory[] = [
  'passenger',
  'lcv',
  'truck',
  'disk',
  'tube',
  'rimTape',
]

/** Размеры, сгруппированные по типу товара (для режима «Все») */
export function getCatalogSizeChipsGrouped(
  products: ShopProduct[],
): { category: ShopCategory; label: string; chips: string[] }[] {
  const byCategory = new Map<ShopCategory, ShopProduct[]>()
  for (const product of products) {
    const list = byCategory.get(product.category)
    if (list) list.push(product)
    else byCategory.set(product.category, [product])
  }

  return SIZE_CHIP_CATEGORY_ORDER.flatMap((category) => {
    const groupProducts = byCategory.get(category)
    if (!groupProducts?.length) return []
    const chips = getCatalogSizeChips(groupProducts)
    if (!chips.length) return []
    return [{ category, label: shopCategoryLabels[category], chips }]
  })
}

export function productMatchesSizeChip(product: ShopProduct, chip: string): boolean {
  if (!chip) return true
  if (product.sizeGroup === chip) return true
  return product.sizes.includes(chip)
}

function compareTireSizes(a: string, b: string): number {
  const parse = (value: string) => {
    const metric = value.match(/^(\d+)\/(\d+)R([\d.]+)(C)?$/i)
    if (metric) {
      return [0, Number(metric[1]), Number(metric[2]), Number(metric[3]), metric[4] ? 1 : 0] as const
    }
    // Диски: 5x13 4x98… / R15 4x100… / 6.75x19.5…
    const disk = value.match(
      /^(?:R\s*)?(\d+(?:\.\d+)?)\s*[xх×-]?\s*(\d+(?:\.\d+)?)?/i,
    )
    if (disk && /[xх×Rr-]|\d+\s+\d/.test(value)) {
      return [1, Number(disk[1]), Number(disk[2] || 0), 0, 0] as const
    }
    const alt = value.match(/^([\d.]+)[Rr-]([\d.]+)$/)
    if (alt) {
      return [1, Number(alt[1]), Number(alt[2]), 0, 0] as const
    }
    return [2, 0, 0, 0, 0] as const
  }
  const left = parse(a)
  const right = parse(b)
  for (let i = 0; i < left.length; i += 1) {
    if (left[i] !== right[i]) return left[i] - right[i]
  }
  return a.localeCompare(b, 'ru')
}

export function formatSizeList(sizes: string[], limit = 4): string {
  if (sizes.length <= limit) return sizes.join(' · ')
  return `${sizes.slice(0, limit).join(' · ')} +${sizes.length - limit}`
}

export function getShopStats(products: ShopProduct[] = shopProducts) {
  return {
    total: products.length,
    brands: new Set(products.map((p) => p.brand)).size,
    sizes: new Set(products.flatMap((p) => p.sizes)).size,
  }
}
