import { services } from '../data'

export function Services() {
  return (
    <section id="services" className="section services">
      <div className="container">
        <div className="section__header">
          <p className="section__tag">Услуги</p>
          <h2 className="section__title">Всё для ваших колёс</h2>
        </div>

        <div className="services__grid">
          {services.map((service) => (
            <article key={service.id} className="service-card">
              <div className="service-card__top">
                <h3 className="service-card__title">{service.title}</h3>
                <span className="service-card__price">{service.subtitle}</span>
              </div>
              <p className="service-card__desc">{service.description}</p>
              <a href="#contact" className="service-card__link">
                Заказать →
              </a>
            </article>
          ))}
        </div>

        <div className="services__cta">
          <a href="#contact" className="btn btn--outline">
            Посмотреть полный прайс
          </a>
        </div>
      </div>
    </section>
  )
}
