import {
  getOfferPrice,
  getProductOffers,
  shopCategoryLabels,
  shopProducts,
  shopSeasonLabels,
  type ShopCategory,
  type ShopProduct,
} from '../data/shop'
import { absoluteUrl } from './seo'

export const TIRE_CATEGORIES: ShopCategory[] = ['passenger', 'lcv', 'truck']
export const WHEEL_CATEGORIES: ShopCategory[] = ['disk']

export type CatalogOffer = {
  product: ShopProduct
  size: string
  price: number | null
  slug: string
  path: string
  kind: 'tire' | 'wheel'
}

export type ProductRedirect = {
  from: string
  to: string
}

/** Нормализация фрагмента размера в URL-slug */
export function sizeToSlug(size: string): string {
  return size
    .toLowerCase()
    .replace(/,/g, '.')
    .replace(/[х×]/gi, 'x')
    .replace(/\//g, '-')
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9.j-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
}

function normalizeComparable(value: string): string {
  return value.toLowerCase().replace(/\s+/g, '').replace(/,/g, '.')
}

/** Дубли прайса помечены суффиксом `-2` в id */
export function isDuplicateProductId(id: string): boolean {
  return /-2$/.test(id)
}

export function isTireProduct(product: ShopProduct): boolean {
  return TIRE_CATEGORIES.includes(product.category)
}

export function isWheelProduct(product: ShopProduct): boolean {
  return WHEEL_CATEGORIES.includes(product.category)
}

export function getTireProducts(): ShopProduct[] {
  return shopProducts.filter(isTireProduct)
}

export function getWheelProducts(): ShopProduct[] {
  return shopProducts.filter(isWheelProduct)
}

export function tireOfferPath(product: ShopProduct, size: string): string {
  return `/tires/${product.id}-${sizeToSlug(size)}`
}

export function wheelOfferPath(product: ShopProduct, size: string): string {
  return `/wheels/${product.id}-${sizeToSlug(size)}`
}

export function productOfferPath(product: ShopProduct, size: string): string | null {
  if (isTireProduct(product)) return tireOfferPath(product, size)
  if (isWheelProduct(product)) return wheelOfferPath(product, size)
  return null
}

function buildOffers(
  products: ShopProduct[],
  kind: 'tire' | 'wheel',
  pathFn: (product: ShopProduct, size: string) => string,
): CatalogOffer[] {
  const offers: CatalogOffer[] = []
  for (const product of products) {
    for (const offer of getProductOffers(product)) {
      const size = offer.size
      const slug = `${product.id}-${sizeToSlug(size)}`
      offers.push({
        product,
        size,
        price: offer.price > 0 ? offer.price : getOfferPrice(product, size),
        slug,
        path: pathFn(product, size),
        kind,
      })
    }
  }
  return offers
}

export function getTireOffers(): CatalogOffer[] {
  return buildOffers(getTireProducts(), 'tire', tireOfferPath)
}

export function getWheelOffers(): CatalogOffer[] {
  return buildOffers(getWheelProducts(), 'wheel', wheelOfferPath)
}

function offerIdentityKey(offer: CatalogOffer): string {
  return [
    offer.kind,
    offer.product.brand,
    offer.product.model,
    offer.size,
    offer.product.category,
    offer.product.season ?? '',
    offer.product.color ?? '',
    offer.price ?? '',
    JSON.stringify(getProductOffers(offer.product)),
  ].join('\u0001')
}

function pickCanonicalOffer(offers: CatalogOffer[]): CatalogOffer {
  return [...offers].sort((a, b) => {
    const aDup = isDuplicateProductId(a.product.id) ? 1 : 0
    const bDup = isDuplicateProductId(b.product.id) ? 1 : 0
    if (aDup !== bDup) return aDup - bDup
    if (a.product.id.length !== b.product.id.length) {
      return a.product.id.length - b.product.id.length
    }
    return a.path.localeCompare(b.path, 'en')
  })[0]!
}

function buildRedirectMap(offers: CatalogOffer[]): Map<string, string> {
  const groups = new Map<string, CatalogOffer[]>()
  for (const offer of offers) {
    const key = offerIdentityKey(offer)
    const list = groups.get(key)
    if (list) list.push(offer)
    else groups.set(key, [offer])
  }

  const redirects = new Map<string, string>()
  for (const group of groups.values()) {
    if (group.length < 2) continue
    const canonical = pickCanonicalOffer(group)
    for (const offer of group) {
      if (offer.path !== canonical.path) {
        redirects.set(offer.path, canonical.path)
      }
    }
  }
  return redirects
}

let cachedRedirects: Map<string, string> | null = null

function getRedirectMap(): Map<string, string> {
  if (!cachedRedirects) {
    cachedRedirects = buildRedirectMap([...getTireOffers(), ...getWheelOffers()])
  }
  return cachedRedirects
}

/** Пары 301: дубль → канонический URL */
export function getProductRedirects(): ProductRedirect[] {
  return [...getRedirectMap().entries()]
    .map(([from, to]) => ({ from, to }))
    .sort((a, b) => a.from.localeCompare(b.from, 'en'))
}

export function resolveCanonicalPath(path: string): string {
  return getRedirectMap().get(path) ?? path
}

/** Канонический путь оффера (для ссылок и sitemap) */
export function canonicalProductOfferPath(
  product: ShopProduct,
  size: string,
): string | null {
  const path = productOfferPath(product, size)
  if (!path) return null
  return resolveCanonicalPath(path)
}

export function getCanonicalTireOffers(): CatalogOffer[] {
  const redirects = getRedirectMap()
  return getTireOffers().filter((offer) => !redirects.has(offer.path))
}

export function getCanonicalWheelOffers(): CatalogOffer[] {
  const redirects = getRedirectMap()
  return getWheelOffers().filter((offer) => !redirects.has(offer.path))
}

export function findTireOfferBySlug(slug: string): CatalogOffer | null {
  return getTireOffers().find((offer) => offer.slug === slug) ?? null
}

export function findWheelOfferBySlug(slug: string): CatalogOffer | null {
  return getWheelOffers().find((offer) => offer.slug === slug) ?? null
}

/** Если slug — дубль, вернуть канонический path для redirect */
export function getTireRedirectPath(slug: string): string | null {
  const offer = findTireOfferBySlug(slug)
  if (!offer) return null
  const canonical = resolveCanonicalPath(offer.path)
  return canonical !== offer.path ? canonical : null
}

export function getWheelRedirectPath(slug: string): string | null {
  const offer = findWheelOfferBySlug(slug)
  if (!offer) return null
  const canonical = resolveCanonicalPath(offer.path)
  return canonical !== offer.path ? canonical : null
}

/**
 * H1 / title: бренд + модель + размер, без повтора размера,
 * цвет диска — если есть в данных.
 */
export function formatOfferTitle(offer: CatalogOffer): string {
  const { product, size } = offer
  const parts: string[] = []
  if (product.brand) parts.push(product.brand)

  const model = product.model?.trim() ?? ''
  const sizeValue = size?.trim() ?? ''
  const modelNorm = normalizeComparable(model)
  const sizeNorm = normalizeComparable(sizeValue)

  if (model && sizeValue && modelNorm === sizeNorm) {
    parts.push(model)
  } else {
    if (model) parts.push(model)
    if (sizeValue) parts.push(sizeValue)
  }

  if (product.color) {
    parts.push(`(${product.color})`)
  }

  return parts.join(' ')
}

const tireCategoryAdjective: Partial<Record<ShopCategory, string>> = {
  passenger: 'Легковая',
  lcv: 'Легкогрузовая',
  truck: 'Грузовая',
}

const seasonAdjective: Record<string, string> = {
  summer: 'летняя',
  winter: 'зимняя',
  allseason: 'всесезонная',
}

export function formatOfferDescription(offer: CatalogOffer): string {
  const { product, price } = offer
  const title = formatOfferTitle(offer)
  const priceText =
    typeof price === 'number' && price > 0
      ? `Цена ${price.toLocaleString('ru-RU')} ₽.`
      : 'Цена по запросу.'

  if (isTireProduct(product)) {
    const cat = tireCategoryAdjective[product.category]
    const season = product.season ? seasonAdjective[product.season] : null
    let typeSentence = 'Шина.'
    if (cat && season) typeSentence = `${cat} ${season} шина.`
    else if (cat) typeSentence = `${cat} шина.`
    else if (season) typeSentence = `${season[0]!.toUpperCase()}${season.slice(1)} шина.`

    return `Купить шину ${title}. ${typeSentence} ${priceText} В наличии в магазине «КОЛЁСА ДЁШЕВО».`
  }

  if (isWheelProduct(product)) {
    return `Купить диск ${title}. ${priceText} В наличии в магазине «КОЛЁСА ДЁШЕВО».`
  }

  return `Купить ${title}. ${priceText} В наличии в магазине «КОЛЁСА ДЁШЕВО».`
}

export function buildProductJsonLd(offer: CatalogOffer): Record<string, unknown> {
  const { product, size, price, path } = offer
  const canonicalPath = resolveCanonicalPath(path)
  const data: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: formatOfferTitle(offer),
    sku: offer.slug,
    brand: {
      '@type': 'Brand',
      name: product.brand,
    },
    category: shopCategoryLabels[product.category],
    url: absoluteUrl(canonicalPath),
    description: formatOfferDescription(offer),
  }

  if (product.image) {
    data.image = absoluteUrl(product.image)
  }

  if (typeof price === 'number' && price > 0) {
    data.offers = {
      '@type': 'Offer',
      url: absoluteUrl(canonicalPath),
      priceCurrency: 'RUB',
      price: String(price),
      availability: 'https://schema.org/InStock',
    }
  }

  data.additionalProperty = [
    { '@type': 'PropertyValue', name: 'Размер', value: size },
    product.season
      ? { '@type': 'PropertyValue', name: 'Сезон', value: shopSeasonLabels[product.season] }
      : null,
    product.color
      ? { '@type': 'PropertyValue', name: 'Цвет', value: product.color }
      : null,
  ].filter(Boolean)

  return data
}
