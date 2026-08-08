import { Catalog } from '../components/Catalog'
import { SeoHead } from '../components/seo/SeoHead'

export function WheelsPage() {
  return (
    <>
      <SeoHead
        title="Каталог дисков — КОЛЁСА ДЁШЕВО"
        description="Штампованные, литые и грузовые диски в наличии. Подбор по ширине, диаметру и цвету."
        path="/wheels"
      />
      <Catalog mode="wheels" title="Каталог дисков" headingLevel="h1" id="wheels-catalog" />
    </>
  )
}
