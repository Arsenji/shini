import type { ShopProduct } from '../data/shop'

export const ORDER_INTEREST_EVENT = 'kolesa:order-interest'
const STORAGE_KEY = 'kolesa_order_interest'

export type OrderInterest = {
  productId: string
  brand: string
  model: string
  category: string
  season?: string
  sizeGroup?: string
  sizes: string[]
  /** Размер для поля формы (группа или первый размер) */
  preferredSize: string
}

export function productToOrderInterest(product: ShopProduct): OrderInterest {
  const preferredSize = product.sizeGroup ?? product.sizes[0] ?? ''
  return {
    productId: product.id,
    brand: product.brand,
    model: product.model,
    category: product.category,
    season: product.season,
    sizeGroup: product.sizeGroup,
    sizes: product.sizes,
    preferredSize,
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
