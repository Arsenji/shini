import { useMemo, useState } from 'react'
import {
  getOfferPrice,
  getProductOffers,
  shopCategoryLabels,
  shopSeasonLabels,
  type ShopProduct,
} from '../../data/shop'
import { productToOrderInterest, setOrderInterest } from '../../lib/orderInterest'
import { TireIllustration } from './TireIllustration'

type ShopCardProps = {
  product: ShopProduct
}

const PREVIEW_SIZES = 2

function formatPrice(price: number): string {
  return `${price.toLocaleString('ru-RU')} ₽`
}

export function ShopCard({ product }: ShopCardProps) {
  const offers = useMemo(() => getProductOffers(product), [product])
  const [selectedSize, setSelectedSize] = useState(offers[0]?.size ?? product.sizes[0] ?? '')
  const [sizesExpanded, setSizesExpanded] = useState(false)

  const categoryLabel = shopCategoryLabels[product.category]
  const seasonLabel = product.season ? shopSeasonLabels[product.season] : null
  const selectedPrice = selectedSize ? getOfferPrice(product, selectedSize) : null
  const hasPrice = typeof selectedPrice === 'number' && selectedPrice > 0
  const hasImage = Boolean(product.image)
  const hasMoreSizes = offers.length > PREVIEW_SIZES
  const visibleOffers =
    sizesExpanded || !hasMoreSizes ? offers : offers.slice(0, PREVIEW_SIZES)

  function handleOrderClick() {
    setOrderInterest(productToOrderInterest(product, selectedSize))
  }

  return (
    <article className="shop-card">
      {product.badge && <span className="shop-card__badge">{product.badge}</span>}

      <div className="shop-card__visual">
        {hasImage ? (
          <img
            src={product.image!}
            alt={`${product.brand} ${product.model}`}
            className="shop-card__photo"
            loading="lazy"
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

        <div className="shop-card__footer">
          <span className={hasPrice ? 'shop-card__price' : 'shop-card__price-note'}>
            {hasPrice ? formatPrice(selectedPrice!) : 'Цена по запросу'}
          </span>
          <a href="#request" className="shop-card__btn" onClick={handleOrderClick}>
            Заказать
          </a>
        </div>
      </div>
    </article>
  )
}
