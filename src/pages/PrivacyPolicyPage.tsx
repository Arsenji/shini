import { PrivacyPolicy } from '../components/PrivacyPolicy'
import { SeoHead } from '../components/seo/SeoHead'

export function PrivacyPolicyPage() {
  return (
    <>
      <SeoHead
        title="Политика обработки персональных данных — КОЛЁСА ДЁШЕВО"
        description="Политика обработки персональных данных интернет-магазина КОЛЁСА ДЁШЕВО."
        path="/privacy-policy"
      />
      <PrivacyPolicy />
    </>
  )
}
