/** Категория шины — для фильтров и иллюстраций */
export type ShopCategory = 'passenger' | 'lcv' | 'truck'

/** Сезон (для легковых; у коммерческих обычно null) */
export type ShopSeason = 'summer' | 'winter' | 'allseason'

/**
 * Ключ иллюстрации. Добавляйте новые SVG в TireIllustration
 * и прописывайте сюда при появлении новых типов.
 */
export type ShopImageKey = 'passenger' | 'lcv' | 'truck'

/**
 * Товар магазина.
 * Чтобы добавить новую шину — добавьте объект в products.ts.
 */
export type ShopProduct = {
  /** Уникальный slug, например "kumho-es31" */
  id: string
  brand: string
  model: string
  /** Список размеров в формате 205/55R16 или 215/75R17.5 */
  sizes: string[]
  category: ShopCategory
  season?: ShopSeason
  /**
   * Группа размера для коммерческих шин
   * (например "185/75R16C", "215/75R17.5")
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
   * Цена в рублях. Если пусто / null — на карточке «Цена по запросу»
   */
  price?: number | null
  badge?: string | null
}

export type ShopCategoryFilter = 'all' | ShopCategory

export const shopCategoryLabels: Record<ShopCategoryFilter, string> = {
  all: 'Все',
  passenger: 'Легковые',
  lcv: 'Легкогрузовые',
  truck: 'Грузовые',
}

export const shopSeasonLabels: Record<ShopSeason, string> = {
  summer: 'Лето',
  winter: 'Зима',
  allseason: 'Всесезон',
}
