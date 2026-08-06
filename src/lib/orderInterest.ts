import { getOfferPrice, getProductOffers, type ShopProduct } from '../data/shop'

export const ORDER_INTEREST_EVENT = 'kolesa:order-interest'
const STORAGE_KEY = 'kolesa_order_interest'

export type OrderInterest = {
  productId: string
  brand: string
  model: string
  category: string
  season?: string
  sizeGroup?: string
  color?: string
  sizes: string[]
  /** Размер для поля формы (выбранный на карточке) */
  preferredSize: string
  /** Цена выбранного размера, если есть */
  price?: number | null
}

export function productToOrderInterest(
  product: ShopProduct,
  selectedSize?: string,
): OrderInterest {
  const offers = getProductOffers(product)
  const preferredSize =
    selectedSize ||
    product.sizeGroup ||
    offers[0]?.size ||
    product.sizes[0] ||
    ''
  const price = preferredSize ? getOfferPrice(product, preferredSize) : product.price ?? null

  return {
    productId: product.id,
    brand: product.brand,
    model: product.model,
    category: product.category,
    season: product.season,
    sizeGroup: product.sizeGroup,
    color: product.color ?? undefined,
    sizes: offers.map((o) => o.size),
    preferredSize,
    price,
  }
}

export function setOrderInterest(interest: OrderInterest): void {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(interest))
  window.dispatchEvent(new CustomEvent(ORDER_INTEREST_EVENT, { detail: interest }))
}

export function getOrderInterest(): OrderInterest | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as OrderInterest
  } catch {
    return null
  }
}

export function clearOrderInterest(): void {
  sessionStorage.removeItem(STORAGE_KEY)
  window.dispatchEvent(new CustomEvent(ORDER_INTEREST_EVENT, { detail: null }))
}
