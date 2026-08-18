import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getOfferPrice,
  getProductOffers,
  shopCategoryLabels,
  shopSeasonLabels,
  type ShopProduct,
} from '../../data/shop'
import { productToOrderInterest, setOrderInterest } from '../../lib/orderInterest'
import { canonicalProductOfferPath } from '../../lib/productUrls'
import { resolveTireSpecs } from '../../lib/tireSpecs'
import { TireIllustration } from './TireIllustration'

type ShopCardProps = {
  product: ShopProduct
}

const PREVIEW_SIZES = 2

function getCatalogPreview(image: string | null | undefined): string | null {
  if (!image) return null
  return image.replace(/(\.[a-z0-9]+)$/i, '-thumb$1')
}

function formatPrice(price: number): string {
  return `${price.toLocaleString('ru-RU')} ₽`
}

function compactSpec(value: string): string {
  return value
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/\./g, '')
    .replace(/к/g, 'k')
    .replace(/м/g, 'm')
}

function cleanupTruckSpecs(raw: string, plyRating: string | null, loadIndex: string | null): string {
  let value = raw
  if (plyRating) {
    const m = plyRating.match(/^(\d{1,2})\s*слоев$/i)
    if (m) {
      const n = m[1]
      value = value.replace(new RegExp(`(^|[\\s(])${n}\\s*сл\\.?($|[\\s).,;:/-])`, 'gi'), ' ')
      value = value.replace(new RegExp(`(^|[\\s(])сл\\.?\\s*${n}($|[\\s).,;:/-])`, 'gi'), ' ')
    }
    const pr = plyRating.match(/^(\d{1,2})\s*PR$/i)
    if (pr) {
      const n = pr[1]
      value = value.replace(new RegExp(`(^|[\\s(])${n}\\s*PR($|[\\s).,;:/-])`, 'gi'), ' ')
      value = value.replace(new RegExp(`(^|[\\s(])PR\\s*${n}($|[\\s).,;:/-])`, 'gi'), ' ')
    }
  }
  if (loadIndex) {
    const idx = loadIndex.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    value = value.replace(new RegExp(`\\b${idx}\\b`, 'gi'), ' ')
  }
  return value
    .replace(/^\(([^)]+)\)$/, '$1')
    .replace(/\(\s*\)/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .replace(/[.,;:\-–—]\s*$/g, '')
    .trim()
}

export function ShopCard({ product }: ShopCardProps) {
  const offers = useMemo(() => getProductOffers(product), [product])
  const [selectedSize, setSelectedSize] = useState(offers[0]?.size ?? product.sizes[0] ?? '')
  const [sizesExpanded, setSizesExpanded] = useState(false)
  const [infoOpen, setInfoOpen] = useState(false)

  const categoryLabel = shopCategoryLabels[product.category]
  const seasonLabel = product.season ? shopSeasonLabels[product.season] : null
  const selectedPrice = selectedSize ? getOfferPrice(product, selectedSize) : null
  const hasPrice = typeof selectedPrice === 'number' && selectedPrice > 0
  const hasImage = Boolean(product.image)
  const previewImage = getCatalogPreview(product.image)
  const hasMoreSizes = offers.length > PREVIEW_SIZES
  const visibleOffers =
    sizesExpanded || !hasMoreSizes ? offers : offers.slice(0, PREVIEW_SIZES)
  const detailsPath = selectedSize ? canonicalProductOfferPath(product, selectedSize) : null
  const { plyRating, loadIndex } = resolveTireSpecs(product)
  const plyLabel = plyRating ? `Слойность: ${plyRating}` : ''
  const loadLabel = loadIndex ? `Индекс: ${loadIndex}` : ''
  const truckSpecsRaw = product.truckSpecs?.trim() ?? ''
  const truckSpecsClean = cleanupTruckSpecs(truckSpecsRaw, plyRating, loadIndex)
  const plyVariants = plyRating
    ? [
        compactSpec(plyRating),
        compactSpec(plyRating.replace(' слоев', 'сл')),
        compactSpec(plyRating.replace('слоев', 'сл')),
      ]
    : []
  const loadVariants = loadIndex ? [compactSpec(loadIndex)] : []
  const showTruckSpecs = truckSpecsClean
    ? !plyVariants.includes(compactSpec(truckSpecsRaw)) &&
      !loadVariants.includes(compactSpec(truckSpecsRaw))
    : false
  const detailsLine = product.color ?? (showTruckSpecs ? truckSpecsClean : '')

  useEffect(() => {
    if (!infoOpen) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setInfoOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [infoOpen])

  function handleOrderClick() {
    setOrderInterest(productToOrderInterest(product, selectedSize))
  }

  return (
    <article className="shop-card">
      {product.badge && <span className="shop-card__badge">{product.badge}</span>}

      {detailsPath && (
        <a
          href={detailsPath}
          className="shop-card__info-link"
          aria-label={`Информация: ${product.brand} ${product.model}`}
          title="Информация о товаре"
          onClick={(event) => {
            event.preventDefault()
            setInfoOpen(true)
          }}
        >
          i
        </a>
      )}

      <div className="shop-card__visual">
        {hasImage ? (
          <img
            src={previewImage || product.image!}
            alt={`${product.brand} ${product.model}`}
            className="shop-card__photo"
            loading="lazy"
            decoding="async"
          />
        ) : (
          <TireIllustration imageKey={product.imageKey} className="shop-card__illustration" />
        )}
      </div>

      <div className="shop-card__info">
        <div className="shop-card__meta">
          <span className="shop-card__category">{categoryLabel}</span>
          {seasonLabel && <span className="shop-card__season">{seasonLabel}</span>}
        </div>

        <h3 className="shop-card__brand">{product.brand}</h3>
        <p className="shop-card__model">{product.model}</p>

        {offers.length > 0 && (
          <div className="shop-card__size-picker" role="group" aria-label="Размеры">
            {visibleOffers.map((offer) => (
              <button
                key={offer.size}
                type="button"
                className={`shop-card__size-chip${selectedSize === offer.size ? ' shop-card__size-chip--active' : ''}`}
                onClick={() => setSelectedSize(offer.size)}
                aria-pressed={selectedSize === offer.size}
              >
                {offer.size}
              </button>
            ))}
            {hasMoreSizes && (
              <button
                type="button"
                className="shop-card__size-chip shop-card__size-chip--more"
                onClick={() => setSizesExpanded((open) => !open)}
                aria-expanded={sizesExpanded}
              >
                {sizesExpanded ? 'Свернуть' : `Все размеры (${offers.length})`}
              </button>
            )}
          </div>
        )}
        {detailsLine && <p className="shop-card__color">{detailsLine}</p>}
        {plyLabel && <p className="shop-card__color">{plyLabel}</p>}
        {loadLabel && <p className="shop-card__color">{loadLabel}</p>}

        <div className="shop-card__footer">
          <span className={hasPrice ? 'shop-card__price' : 'shop-card__price-note'}>
            {hasPrice ? formatPrice(selectedPrice!) : 'Цена по запросу'}
          </span>
          <Link
            to={{ pathname: '/', hash: 'request' }}
            className="shop-card__btn"
            onClick={handleOrderClick}
          >
            Заказать
          </Link>
        </div>
      </div>

      {infoOpen && detailsPath && (
        <div
          className="shop-card__popup"
          role="dialog"
          aria-modal="true"
          aria-label="Информация о товаре"
        >
          <button
            type="button"
            className="shop-card__popup-backdrop"
            aria-label="Закрыть"
            onClick={() => setInfoOpen(false)}
          />
          <div className="shop-card__popup-panel">
            <button
              type="button"
              className="shop-card__popup-close"
              aria-label="Закрыть"
              onClick={() => setInfoOpen(false)}
            >
              ×
            </button>
            <p className="shop-card__popup-meta">
              {[categoryLabel, seasonLabel, detailsLine, plyLabel, loadLabel]
                .filter(Boolean)
                .join(' · ')}
            </p>
            <p className="shop-card__popup-title">
              {product.brand} {product.model}
            </p>
            {selectedSize && <p className="shop-card__popup-size">Размер: {selectedSize}</p>}
            <p className="shop-card__popup-price">
              {hasPrice ? formatPrice(selectedPrice!) : 'Цена по запросу'}
            </p>
          </div>
        </div>
      )}
    </article>
  )
}
