import { useParams, Navigate } from 'react-router-dom'
import { findWheelOfferBySlug, getWheelRedirectPath } from '../lib/productUrls'
import { ProductNotFound, ProductOfferPage } from './ProductOfferPage'

export function WheelProductPage() {
  const { id = '' } = useParams()
  const redirectTo = getWheelRedirectPath(id)
  if (redirectTo) {
    return <Navigate to={redirectTo} replace />
  }

  const offer = findWheelOfferBySlug(id)

  if (!offer) {
    return (
      <ProductNotFound
        title="Диск не найден"
        backTo="/wheels"
        backLabel="К каталогу дисков"
      />
    )
  }

  return (
    <ProductOfferPage
      offer={offer}
      notFoundPath="/wheels"
      notFoundLabel="Диски"
    />
  )
}
