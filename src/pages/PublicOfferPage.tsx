import { PublicOffer } from '../components/PublicOffer'
import { SeoHead } from '../components/seo/SeoHead'

export function PublicOfferPage() {
  return (
    <>
      <SeoHead
        title="Публичная оферта — КОЛЁСА ДЁШЕВО"
        description="Публичная оферта интернет-магазина КОЛЁСА ДЁШЕВО на покупку шин, дисков и сопутствующих товаров."
        path="/public-offer"
      />
      <PublicOffer />
    </>
  )
}
