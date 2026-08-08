import { Catalog } from '../components/Catalog'
import { SeoHead } from '../components/seo/SeoHead'

export function TiresPage() {
  return (
    <>
      <SeoHead
        title="Каталог шин — КОЛЁСА ДЁШЕВО"
        description="Легковые, легкогрузовые и грузовые шины в наличии. Подбор по размеру, сезону и цене."
        path="/tires"
      />
      <Catalog mode="tires" title="Каталог шин" headingLevel="h1" id="tires-catalog" />
    </>
  )
}
