import type { ShopProduct } from '../data/shop'

const PLY_LAYERS_RE = /\b(\d{1,2})\s*сл\b/i
const PLY_PR_RE = /\b(?:PR\s*(\d{1,2})|(\d{1,2})\s*PR)\b/i
const LOAD_INDEX_RE = /\b(\d{2,3}(?:\/\d{2,3})?[A-ZА-Я])\b/i
/** «универ.» / «универсальная» / «(унив)» в конце названия */
const APPLICATION_RE =
  /(?:\s*[(\[]?\s*(универсальн(?:ый|ая|ое|ые)|универ\.?|унив)\s*[)\]]?)+$/i
/**
 * Ось в конце названия: руль / рул. / рулевая / вед. / ведущая / ведущ / (руль) / (вед)
 */
const AXLE_RE =
  /(?:\s*[(\[]?\s*(рулевая|руль|рул\.?|ведущая|ведущ\.?|вед\.?)\s*[)\]]?)+$/i

export type AxleLabel = 'рулевая ось' | 'ведущая ось'

function normalizeLetter(value: string): string {
  return value.toUpperCase().replace('К', 'K')
}

function normalizeApplication(raw: string): string {
  const value = raw.trim().toLowerCase().replace(/\.$/, '')
  if (value.startsWith('универсальн')) {
    const match = raw.trim().match(/универсальн(?:ый|ая|ое|ые)/i)
    return match ? match[0] : 'универсальная'
  }
  return 'универ.'
}

function normalizeAxle(raw: string): AxleLabel | null {
  const value = raw.trim().toLowerCase().replace(/\.$/, '')
  if (value.startsWith('рул')) return 'рулевая ось'
  if (value.startsWith('вед')) return 'ведущая ось'
  return null
}

/** Убрать назначение из названия и вернуть нормализованный лейбл. */
export function stripApplication(text: string): { cleaned: string; application: string | null } {
  const match = text.match(APPLICATION_RE)
  if (!match) return { cleaned: text.trim(), application: null }
  const cleaned = text.slice(0, match.index).replace(/[\s,;/\-–—]+$/u, '').trim()
  return { cleaned, application: normalizeApplication(match[1] ?? match[0]) }
}

/** Убрать обозначение оси из названия и вернуть лейбл «рулевая ось» / «ведущая ось». */
export function stripAxle(text: string): { cleaned: string; axle: AxleLabel | null } {
  const match = text.match(AXLE_RE)
  if (!match) return { cleaned: text.trim(), axle: null }
  const cleaned = text.slice(0, match.index).replace(/[\s,;/\-–—]+$/u, '').trim()
  return { cleaned, axle: normalizeAxle(match[1] ?? match[0]) }
}

function cleanTitlePart(text: string): {
  cleaned: string
  application: string | null
  axle: AxleLabel | null
} {
  const app = stripApplication(text)
  const axle = stripAxle(app.cleaned)
  return {
    cleaned: axle.cleaned,
    application: app.application,
    axle: axle.axle,
  }
}

export function resolveApplication(product: ShopProduct): string | null {
  if (product.application?.trim()) return product.application.trim()
  const fromBrand = cleanTitlePart(product.brand).application
  if (fromBrand) return fromBrand
  return cleanTitlePart(product.model).application
}

export function resolveAxle(product: ShopProduct): AxleLabel | null {
  if (product.axle?.trim()) {
    const normalized = normalizeAxle(product.axle)
    if (normalized) return normalized
  }
  const fromBrand = cleanTitlePart(product.brand).axle
  if (fromBrand) return fromBrand
  return cleanTitlePart(product.model).axle
}

function collapseRepeatedTitle(text: string): string {
  const parts = text.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 2 && parts[0] === parts[1]) return parts[0]!
  return text.trim()
}

export function displayProductTitle(product: ShopProduct): { brand: string; model: string } {
  const brand = collapseRepeatedTitle(cleanTitlePart(product.brand).cleaned)
  const model = collapseRepeatedTitle(cleanTitlePart(product.model).cleaned)
  return { brand, model }
}

export function extractPlyRating(text: string | null | undefined): string | null {
  if (!text) return null
  const layers = text.match(PLY_LAYERS_RE)
  if (layers) return `${layers[1]} слоев`

  const pr = text.match(PLY_PR_RE)
  const prValue = pr?.[1] ?? pr?.[2]
  if (prValue) return `${prValue} PR`

  return null
}

export function extractLoadIndex(text: string | null | undefined): string | null {
  if (!text) return null
  const m = text.match(LOAD_INDEX_RE)
  if (!m) return null
  return normalizeLetter(m[1]!)
}

export function resolveTireSpecs(product: ShopProduct): {
  plyRating: string | null
  loadIndex: string | null
} {
  const source = [product.model, product.truckSpecs].filter(Boolean).join(' ')
  return {
    plyRating: product.plyRating ?? extractPlyRating(source),
    loadIndex: product.loadIndex ?? extractLoadIndex(source),
  }
}

/** «R22.5» / «R17.5» уже есть в размере — не показывать отдельно. */
export function isRedundantRimSpec(
  specs: string,
  size: string | null | undefined,
  sizeGroup?: string | null,
): boolean {
  const rim = specs.trim().match(/^R\s*(\d+(?:[.,]\d+)?)$/i)
  if (!rim) return false
  const rimNorm = rim[1].replace(',', '.')
  const hay = `${size ?? ''} ${sizeGroup ?? ''}`
  return new RegExp(`R\\s*${rimNorm.replace('.', '[.,]')}\\b`, 'i').test(hay)
}
