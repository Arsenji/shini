import { useEffect, useMemo, useState } from 'react'
import {
  filterShopProducts,
  getCatalogSizeChips,
  getShopStats,
  getSizeFilterOptions,
  productMatchesSizeChip,
  shopCategoryLabels,
  shopProducts,
  type ShopCategoryFilter,
  type ShopSeason,
  type ShopSizeFilters,
} from '../data/shop'
import { ShopCard } from './shop/ShopCard'

const categoryFilters: ShopCategoryFilter[] = ['all', 'passenger', 'lcv', 'truck']
const PAGE_SIZE = 12
/** Сколько номеров страниц показывать; окна: 1–10 ↔ 10–19 ↔ 19–28… */
const PAGE_WINDOW = 10
const SIZE_GROUP_PREVIEW = 6

const emptySizeFilters: ShopSizeFilters = {
  width: '',
  profile: '',
  diameter: '',
}

export function Catalog() {
  const [category, setCategory] = useState<ShopCategoryFilter>('all')
  const [season, setSeason] = useState<ShopSeason>('summer')
  const [sizeFilters, setSizeFilters] = useState<ShopSizeFilters>(emptySizeFilters)
  const [sizeGroup, setSizeGroup] = useState('')
  const [sizeGroupsExpanded, setSizeGroupsExpanded] = useState(false)
  const [page, setPage] = useState(1)
  const [pageWindowStart, setPageWindowStart] = useState(1)

  const stats = useMemo(() => getShopStats(shopProducts), [])

  const categoryProducts = useMemo(
    () => filterShopProducts(shopProducts, category, season, emptySizeFilters),
    [category, season],
  )

  const sizeOptions = useMemo(
    () => getSizeFilterOptions(categoryProducts, sizeFilters),
    [categoryProducts, sizeFilters],
  )

  const filtered = useMemo(() => {
    const byFilters = filterShopProducts(shopProducts, category, season, sizeFilters)
    if (!sizeGroup) return byFilters
    return byFilters.filter((p) => productMatchesSizeChip(p, sizeGroup))
  }, [category, season, sizeFilters, sizeGroup])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))

  const visibleSizeGroups = useMemo(
    () => getCatalogSizeChips(categoryProducts),
    [categoryProducts],
  )

  const hasMoreSizeGroups = visibleSizeGroups.length > SIZE_GROUP_PREVIEW
  const previewSizeGroups = useMemo(() => {
    if (sizeGroupsExpanded || !hasMoreSizeGroups) return visibleSizeGroups
    const preview = visibleSizeGroups.slice(0, SIZE_GROUP_PREVIEW)
    if (sizeGroup && !preview.includes(sizeGroup)) {
      return [...preview.slice(0, Math.max(0, SIZE_GROUP_PREVIEW - 1)), sizeGroup]
    }
    return preview
  }, [visibleSizeGroups, sizeGroupsExpanded, hasMoreSizeGroups, sizeGroup])

  useEffect(() => {
    setPage(1)
    setPageWindowStart(1)
  }, [category, season, sizeFilters, sizeGroup])

  useEffect(() => {
    setSizeGroupsExpanded(false)
  }, [category, season])

  useEffect(() => {
    if (sizeGroup && !visibleSizeGroups.includes(sizeGroup)) {
      setSizeGroup('')
    }
  }, [visibleSizeGroups, sizeGroup])

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  useEffect(() => {
    if (totalPages <= PAGE_WINDOW) {
      setPageWindowStart(1)
      return
    }
    setPageWindowStart((start) => Math.min(start, Math.max(1, totalPages - PAGE_WINDOW + 1)))
  }, [totalPages])

  useEffect(() => {
    setSizeFilters((prev) => {
      const next = { ...prev }
      if (prev.width && !sizeOptions.widths.includes(prev.width)) next.width = ''
      if (prev.profile && !sizeOptions.profiles.includes(prev.profile)) next.profile = ''
      if (prev.diameter && !sizeOptions.diameters.includes(prev.diameter)) next.diameter = ''
      if (
        next.width === prev.width &&
        next.profile === prev.profile &&
        next.diameter === prev.diameter
      ) {
        return prev
      }
      return next
    })
  }, [sizeOptions])

  const pageItems = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE
    return filtered.slice(start, start + PAGE_SIZE)
  }, [filtered, page])

  const visiblePages = useMemo(() => {
    if (totalPages <= PAGE_WINDOW) {
      return Array.from({ length: totalPages }, (_, index) => index + 1)
    }

    const windowEnd = Math.min(totalPages, pageWindowStart + PAGE_WINDOW - 1)
    return Array.from({ length: windowEnd - pageWindowStart + 1 }, (_, index) => pageWindowStart + index)
  }, [pageWindowStart, totalPages])

  function goToPage(next: number) {
    const target = Math.min(totalPages, Math.max(1, next))
    const step = PAGE_WINDOW - 1

    if (totalPages > PAGE_WINDOW) {
      const windowEnd = Math.min(totalPages, pageWindowStart + PAGE_WINDOW - 1)
      const isFirstInWindow = target === pageWindowStart
      const isLastInWindow = target === windowEnd

      if (isFirstInWindow && pageWindowStart > 1) {
        // 10–19 → клик 10 → окно 1–10
        setPageWindowStart(Math.max(1, pageWindowStart - step))
      } else if (isLastInWindow && target < totalPages) {
        // 1–10 → клик 10 → окно 10–19
        setPageWindowStart(target)
      } else if (target < pageWindowStart) {
        setPageWindowStart(Math.max(1, pageWindowStart - step))
      } else if (target > windowEnd) {
        setPageWindowStart(Math.min(pageWindowStart + step, Math.max(1, totalPages - PAGE_WINDOW + 1)))
      }
    }

    setPage(target)
    document.getElementById('catalog')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  function updateSizeFilter(key: keyof ShopSizeFilters, value: string) {
    setSizeFilters((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <section id="catalog" className="section catalog">
      <div className="container">
        <div className="section__header section__header--row">
          <div>
            <p className="section__tag section__tag--highlight">Каталог</p>
            <h2 className="section__title">Шины в наличии</h2>
            <p className="catalog__subtitle">
              {stats.total} моделей · {stats.brands} брендов · {stats.sizes} размеров
            </p>
          </div>
        </div>

        <div className="catalog__size-panel">
          <div className="catalog__category">
            <span className="catalog__field-label">Тип</span>
            <div className="catalog__filters" role="tablist" aria-label="Категория шин">
              {categoryFilters.map((filter) => (
                <button
                  key={filter}
                  type="button"
                  className={`catalog__filter ${category === filter ? 'catalog__filter--active' : ''}`}
                  onClick={() => {
                    setCategory(filter)
                    setSizeGroup('')
                  }}
                >
                  {shopCategoryLabels[filter]}
                </button>
              ))}
            </div>
          </div>

          <div className="catalog__season">
            <span className="catalog__field-label">Сезон</span>
            <div className="catalog__season-toggle" role="group" aria-label="Сезон">
              <button
                type="button"
                className={`catalog__season-btn ${season === 'summer' ? 'catalog__season-btn--active' : ''}`}
                onClick={() => setSeason('summer')}
              >
                <span className="catalog__season-icon catalog__season-icon--summer" aria-hidden="true">
                 ☀
                </span>
                Летние
              </button>
              <button
                type="button"
                className={`catalog__season-btn ${season === 'winter' ? 'catalog__season-btn--active' : ''}`}
                onClick={() => setSeason('winter')}
              >
                <span className="catalog__season-icon catalog__season-icon--winter" aria-hidden="true">
                 ❄
                </span>
                Зимние
              </button>
            </div>
          </div>

          <div className="catalog__dims">
            <label className="catalog__dim">
              <span className="catalog__field-label">Ширина, мм</span>
              <select
                className="catalog__select"
                value={sizeFilters.width}
                onChange={(e) => updateSizeFilter('width', e.target.value)}
              >
                <option value="">Все</option>
                {sizeOptions.widths.map((width) => (
                  <option key={width} value={width}>
                    {width}
                  </option>
                ))}
              </select>
            </label>

            <label className="catalog__dim">
              <span className="catalog__field-label">Профиль</span>
              <select
                className="catalog__select"
                value={sizeFilters.profile}
                onChange={(e) => updateSizeFilter('profile', e.target.value)}
              >
                <option value="">Все</option>
                {sizeOptions.profiles.map((profile) => (
                  <option key={profile} value={profile}>
                    {profile}
                  </option>
                ))}
              </select>
            </label>

            <label className="catalog__dim">
              <span className="catalog__field-label">Диаметр</span>
              <select
                className="catalog__select"
                value={sizeFilters.diameter}
                onChange={(e) => updateSizeFilter('diameter', e.target.value)}
              >
                <option value="">Все</option>
                {sizeOptions.diameters.map((diameter) => (
                  <option key={diameter} value={diameter}>
                    {diameter}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {visibleSizeGroups.length > 0 && (
            <div className="catalog__size-groups-block">
              <span className="catalog__field-label">Размеры</span>
              <div className="catalog__size-groups">
                <button
                  type="button"
                  className={`catalog__chip ${sizeGroup === '' ? 'catalog__chip--active' : ''}`}
                  onClick={() => setSizeGroup('')}
                >
                  Все размеры
                </button>
                {previewSizeGroups.map((group) => (
                  <button
                    key={group}
                    type="button"
                    className={`catalog__chip catalog__chip--group ${sizeGroup === group ? 'catalog__chip--active' : ''}`}
                    onClick={() => setSizeGroup(group)}
                  >
                    {group}
                  </button>
                ))}
                {hasMoreSizeGroups && (
                  <button
                    type="button"
                    className="catalog__chip catalog__chip--more"
                    onClick={() => setSizeGroupsExpanded((open) => !open)}
                    aria-expanded={sizeGroupsExpanded}
                  >
                    {sizeGroupsExpanded
                      ? 'Свернуть'
                      : `Все размеры (${visibleSizeGroups.length})`}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {filtered.length === 0 ? (
          <p className="catalog__empty">Ничего не найдено. Попробуйте другой размер или категорию.</p>
        ) : (
          <>
            <div className="catalog__grid catalog__grid--shop">
              {pageItems.map((product) => (
                <ShopCard key={product.id} product={product} />
              ))}
            </div>

            <div className="catalog__pagination">
              <div className="catalog__pagination-controls" role="navigation" aria-label="Страницы каталога">
                <button
                  type="button"
                  className="catalog__page-btn"
                  onClick={() => goToPage(page - 1)}
                  disabled={page <= 1}
                  aria-label="Предыдущая страница"
                >
                  ←
                </button>

                {visiblePages.map((pageNumber) => (
                  <button
                    key={pageNumber}
                    type="button"
                    className={`catalog__page-btn ${page === pageNumber ? 'catalog__page-btn--active' : ''}`}
                    onClick={() => goToPage(pageNumber)}
                    aria-current={page === pageNumber ? 'page' : undefined}
                  >
                    {pageNumber}
                  </button>
                ))}

                <button
                  type="button"
                  className="catalog__page-btn"
                  onClick={() => goToPage(page + 1)}
                  disabled={page >= totalPages}
                  aria-label="Следующая страница"
                >
                  →
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  )
}
