import { Link } from 'react-router-dom'
import {
  getOfferPrice,
  getProductOffers,
  shopCategoryLabels,
  shopSeasonLabels,
} from '../data/shop'
import { productToOrderInterest, setOrderInterest } from '../lib/orderInterest'
import {
  formatOfferDescription,
  formatOfferTitle,
  buildProductJsonLd,
  canonicalProductOfferPath,
  resolveCanonicalPath,
  type CatalogOffer,
} from '../lib/productUrls'
import { SeoHead } from '../components/seo/SeoHead'
import { TireIllustration } from '../components/shop/TireIllustration'

function formatPrice(price: number): string {
  return `${price.toLocaleString('ru-RU')} ₽`
}

type ProductOfferPageProps = {
  offer: CatalogOffer
  notFoundPath: string
  notFoundLabel: string
}

export function ProductOfferPage({ offer, notFoundPath, notFoundLabel }: ProductOfferPageProps) {
  const { product, size, price } = offer
  const offers = getProductOffers(product)
  const hasPrice = typeof price === 'number' && price > 0
  const title = `${formatOfferTitle(offer)} — купить в КОЛЁСА ДЁШЕВО`
  const description = formatOfferDescription(offer)
  const categoryLabel = shopCategoryLabels[product.category]
  const seasonLabel = product.season ? shopSeasonLabels[product.season] : null
  const canonicalPath = resolveCanonicalPath(offer.path)

  function handleOrderClick() {
    setOrderInterest(productToOrderInterest(product, size))
  }

  return (
    <section className="section product-page">
      <SeoHead
        title={title}
        description={description}
        path={canonicalPath}
        image={product.image || '/logo.png'}
        type="product"
        jsonLd={buildProductJsonLd(offer)}
      />

      <div className="container product-page__inner">
        <nav className="product-page__crumbs" aria-label="Навигация">
          <Link to="/">Главная</Link>
          <span aria-hidden="true">/</span>
          <Link to={notFoundPath}>{notFoundLabel}</Link>
          <span aria-hidden="true">/</span>
          <span>{product.brand}</span>
        </nav>

        <div className="product-page__layout">
          <div className="product-page__visual">
            {product.image ? (
              <img
                src={product.image}
                alt={formatOfferTitle(offer)}
                className="product-page__photo"
              />
            ) : (
              <TireIllustration imageKey={product.imageKey} className="product-page__illustration" />
            )}
          </div>

          <div className="product-page__content">
            <p className="product-page__meta">
              {[categoryLabel, seasonLabel, product.badge, product.color].filter(Boolean).join(' · ')}
            </p>
            <h1 className="product-page__title">{formatOfferTitle(offer)}</h1>
            <p className="product-page__price">
              {hasPrice ? formatPrice(price!) : 'Цена по запросу'}
            </p>

            {offers.length > 1 && (
              <div className="product-page__sizes" role="group" aria-label="Другие размеры">
                <p className="product-page__sizes-label">Размеры</p>
                <div className="product-page__size-list">
                  {offers.map((item) => {
                    const path = canonicalProductOfferPath(product, item.size)
                    if (!path) return null
                    const active = item.size === size
                    const itemPrice = getOfferPrice(product, item.size)
                    return (
                      <Link
                        key={item.size}
                        to={path}
                        className={`product-page__size-chip${active ? ' product-page__size-chip--active' : ''}`}
                        aria-current={active ? 'page' : undefined}
                      >
                        <span>{item.size}</span>
                        {typeof itemPrice === 'number' && itemPrice > 0 && (
                          <span className="product-page__size-price">
                            {formatPrice(itemPrice)}
                          </span>
                        )}
                      </Link>
                    )
                  })}
                </div>
              </div>
            )}

            <div className="product-page__actions">
              <Link to={{ pathname: '/', hash: 'request' }} className="btn btn--primary" onClick={handleOrderClick}>
                Заказать
              </Link>
              <Link to={notFoundPath} className="btn btn--outline">
                Назад в каталог
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export function ProductNotFound({
  title,
  backTo,
  backLabel,
}: {
  title: string
  backTo: string
  backLabel: string
}) {
  return (
    <section className="section product-page">
      <SeoHead
        title={`${title} — КОЛЁСА ДЁШЕВО`}
        description="Товар не найден. Смотрите актуальный каталог шин и дисков."
        path={backTo}
      />
      <div className="container">
        <h1 className="section__title">{title}</h1>
        <p className="catalog__empty">Такой позиции нет в каталоге.</p>
        <Link to={backTo} className="btn btn--primary">
          {backLabel}
        </Link>
      </div>
    </section>
  )
}
