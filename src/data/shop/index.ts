import { shopProducts } from './products'
import type { ShopCategoryFilter, ShopProduct, ShopSeason } from './types'

export * from './types'
export { shopProducts } from './products'

export type ParsedTireSize = {
  width: string
  profile: string
  diameter: string
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

/** Разбор 205/55R16, 215/75R17.5, 185/75R16C → width/profile/diameter */
export function parseTireSize(value: string): ParsedTireSize | null {
  const match = normalizeSize(value).match(/^(\d{3})\/(\d{2,3})r?(\d{2}(?:\.\d)?)(c)?$/)
  if (!match) return null
  return {
    width: match[1],
    profile: match[2],
    diameter: match[4] ? `${match[3]}C` : match[3],
  }
}

export function getProductSizeParts(product: ShopProduct): ParsedTireSize[] {
  return product.sizes
    .map(parseTireSize)
    .filter((part): part is ParsedTireSize => part !== null)
}

function matchesSeason(product: ShopProduct, season: ShopSeason | 'all'): boolean {
  if (season === 'all') return true
  // Коммерческие без сезона показываем всегда
  if (!product.season) return true
  if (product.season === 'allseason') return true
  return product.season === season
}

function matchesSizeFilters(product: ShopProduct, sizeFilters: ShopSizeFilters): boolean {
  const { width, profile, diameter } = sizeFilters
  if (!width && !profile && !diameter) return true

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
): ShopProduct[] {
  return products.filter((product) => {
    if (category !== 'all' && product.category !== category) return false
    if (!matchesSeason(product, season)) return false
    return matchesSizeFilters(product, sizeFilters)
  })
}

/** Уникальные значения ширины/профиля/диаметра с учётом уже выбранных фильтров */
export function getSizeFilterOptions(
  products: ShopProduct[],
  sizeFilters: ShopSizeFilters,
): { widths: string[]; profiles: string[]; diameters: string[] } {
  const widths = new Set<string>()
  const profiles = new Set<string>()
  const diameters = new Set<string>()

  for (const product of products) {
    for (const part of getProductSizeParts(product)) {
      const widthOk = !sizeFilters.width || part.width === sizeFilters.width
      const profileOk = !sizeFilters.profile || part.profile === sizeFilters.profile
      const diameterOk = !sizeFilters.diameter || part.diameter === sizeFilters.diameter

      if (profileOk && diameterOk) widths.add(part.width)
      if (widthOk && diameterOk) profiles.add(part.profile)
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
  return Array.from(groups).sort()
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
