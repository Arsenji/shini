import {
  formatSizeList,
  shopCategoryLabels,
  shopSeasonLabels,
  type ShopProduct,
} from '../../data/shop'
import { productToOrderInterest, setOrderInterest } from '../../lib/orderInterest'
import { TireIllustration } from './TireIllustration'

type ShopCardProps = {
  product: ShopProduct
}

export function ShopCard({ product }: ShopCardProps) {
  const categoryLabel = shopCategoryLabels[product.category]
  const seasonLabel = product.season ? shopSeasonLabels[product.season] : null
  const sizeHeadline = product.sizeGroup ?? formatSizeList(product.sizes, 3)

  function handleOrderClick() {
    setOrderInterest(productToOrderInterest(product))
  }

  return (
    <article className="shop-card">
      {product.badge && <span className="shop-card__badge">{product.badge}</span>}

      <div className="shop-card__visual">
        <TireIllustration imageKey={product.imageKey} className="shop-card__illustration" />
      </div>

      <div className="shop-card__info">
        <div className="shop-card__meta">
          <span className="shop-card__category">{categoryLabel}</span>
          {seasonLabel && <span className="shop-card__season">{seasonLabel}</span>}
        </div>

        <h3 className="shop-card__brand">{product.brand}</h3>
        <p className="shop-card__model">{product.model}</p>
        <p className="shop-card__size">{sizeHeadline}</p>

        {product.sizes.length > 1 && (
          <details className="shop-card__sizes">
            <summary>Все размеры ({product.sizes.length})</summary>
            <ul>
              {product.sizes.map((size) => (
                <li key={size}>{size}</li>
              ))}
            </ul>
          </details>
        )}

        <div className="shop-card__footer">
          <span className="shop-card__price-note">Цена по запросу</span>
          <a href="#request" className="shop-card__btn" onClick={handleOrderClick}>
            Заказать
          </a>
        </div>
      </div>
    </article>
  )
}
