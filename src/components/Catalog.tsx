import { useState } from 'react'
import { seasonLabels, tires } from '../data'

type Season = 'all' | 'summer' | 'winter' | 'allseason'

const filters: Season[] = ['all', 'summer', 'winter', 'allseason']

export function Catalog() {
  const [season, setSeason] = useState<Season>('all')

  const filtered =
    season === 'all' ? tires : tires.filter((t) => t.season === season)

  return (
    <section id="catalog" className="section catalog">
      <div className="container">
        <div className="section__header section__header--row">
          <div>
            <p className="section__tag section__tag--highlight">Каталог</p>
            <h2 className="section__title">Популярные модели</h2>
          </div>
          <div className="catalog__filters">
            {filters.map((f) => (
              <button
                key={f}
                className={`catalog__filter ${season === f ? 'catalog__filter--active' : ''}`}
                onClick={() => setSeason(f)}
              >
                {seasonLabels[f]}
              </button>
            ))}
          </div>
        </div>

        <div className="catalog__grid">
          {filtered.map((tire) => (
            <article key={tire.id} className="tire-card">
              {tire.badge && <span className="tire-card__badge">{tire.badge}</span>}
              <div className="tire-card__visual">
                <div className="tire-card__tire">
                  <div className="tire-card__tire-outer" />
                  <div className="tire-card__tire-inner" />
                </div>
              </div>
              <div className="tire-card__info">
                <span className="tire-card__season">{seasonLabels[tire.season]}</span>
                <h3 className="tire-card__brand">{tire.brand}</h3>
                <p className="tire-card__model">{tire.model}</p>
                <p className="tire-card__size">{tire.size}</p>
                <div className="tire-card__footer">
                  <span className="tire-card__price">
                    {tire.price.toLocaleString('ru-RU')} ₽
                  </span>
                  <a href="#contact" className="tire-card__btn">
                    Заказать
                  </a>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
