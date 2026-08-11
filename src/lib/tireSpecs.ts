import type { ShopProduct } from '../data/shop'

const PLY_LAYERS_RE = /\b(\d{1,2})\s*сл\b/i
const PLY_PR_RE = /\b(?:PR\s*(\d{1,2})|(\d{1,2})\s*PR)\b/i
const LOAD_INDEX_RE = /\b(\d{2,3}(?:\/\d{2,3})?[A-ZА-Я])\b/i

function normalizeLetter(value: string): string {
  return value.toUpperCase().replace('К', 'K')
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
