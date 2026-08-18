import { PersonalDataConsent } from '../components/PersonalDataConsent'
import { SeoHead } from '../components/seo/SeoHead'

export function PersonalDataConsentPage() {
  return (
    <>
      <SeoHead
        title="Согласие на обработку персональных данных — КОЛЁСА ДЁШЕВО"
        description="Согласие на обработку персональных данных при отправке заявки в магазине КОЛЁСА ДЁШЕВО."
        path="/personal-data-consent"
      />
      <PersonalDataConsent />
    </>
  )
}
