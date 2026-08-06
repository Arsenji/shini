/** Категория товара — для фильтров и иллюстраций */
export type ShopCategory = 'passenger' | 'lcv' | 'truck' | 'disk' | 'tube' | 'rimTape'

/** Сезон (для шин; у дисков/камер/лент обычно null) */
export type ShopSeason = 'summer' | 'winter' | 'allseason'

/**
 * Ключ иллюстрации. Добавляйте новые SVG в TireIllustration
 * и прописывайте сюда при появлении новых типов.
 */
export type ShopImageKey = 'passenger' | 'lcv' | 'truck' | 'disk' | 'tube' | 'rimTape'

/** Размер с ценой — выбирается на карточке */
export type ShopSizeOffer = {
  size: string
  price: number
}

/**
 * Товар магазина.
 * Одна модель может иметь несколько offers (размер + цена).
 */
export type ShopProduct = {
  /** Уникальный slug, например "kumho-es31" */
  id: string
  brand: string
  model: string
  /**
   * Размеры (дублируют offers[].size) — для фильтров каталога
   */
  sizes: string[]
  /** Размеры с ценами; если пусто — используется price / «по запросу» */
  offers: ShopSizeOffer[]
  category: ShopCategory
  season?: ShopSeason
  /**
   * Группа размера для коммерческих шин / дисков
   * (например "185/75R16C", "R15 5х114.3")
   */
  sizeGroup?: string
  /** Какая SVG-иллюстрация показывать, если нет image */
  imageKey: ShopImageKey
  /**
   * Фото шины, например "/tires/kumho-es31.webp"
   * Файлы кладите в public/tires/
   */
  image?: string | null
  /**
   * Минимальная цена (для сортировки / подписи).
   * На карточке показывается цена выбранного размера из offers.
   */
  price?: number | null
  badge?: string | null
  /** Цвет / покрытие диска (из прайса) */
  color?: string | null
}

export type ShopCategoryFilter = 'all' | ShopCategory

export const shopCategoryLabels: Record<ShopCategoryFilter, string> = {
  all: 'Все',
  passenger: 'Легковые',
  lcv: 'Легкогрузовые',
  truck: 'Грузовые',
  disk: 'Диски',
  tube: 'Камеры',
  rimTape: 'Ободные ленты',
}

export const shopSeasonLabels: Record<ShopSeason, string> = {
  summer: 'Лето',
  winter: 'Зима',
  allseason: 'Всесезон',
}

export function getProductOffers(product: ShopProduct): ShopSizeOffer[] {
  if (product.offers?.length) return product.offers
  if (product.sizes?.length && typeof product.price === 'number' && product.price > 0) {
    return product.sizes.map((size) => ({ size, price: product.price! }))
  }
  return product.sizes.map((size) => ({ size, price: 0 }))
}

export function getOfferPrice(product: ShopProduct, size: string): number | null {
  const offer = getProductOffers(product).find((item) => item.size === size)
  if (offer && offer.price > 0) return offer.price
  if (typeof product.price === 'number' && product.price > 0) return product.price
  return null
}
