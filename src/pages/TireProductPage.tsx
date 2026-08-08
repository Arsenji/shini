import { useParams, Navigate } from 'react-router-dom'
import { findTireOfferBySlug, getTireRedirectPath } from '../lib/productUrls'
import { ProductNotFound, ProductOfferPage } from './ProductOfferPage'

export function TireProductPage() {
  const { id = '' } = useParams()
  const redirectTo = getTireRedirectPath(id)
  if (redirectTo) {
    return <Navigate to={redirectTo} replace />
  }

  const offer = findTireOfferBySlug(id)

  if (!offer) {
    return (
      <ProductNotFound
        title="Шина не найдена"
        backTo="/tires"
        backLabel="К каталогу шин"
      />
    )
  }

  return (
    <ProductOfferPage
      offer={offer}
      notFoundPath="/tires"
      notFoundLabel="Шины"
    />
  )
}
