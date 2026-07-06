import { useTypewriter } from '../hooks/useTypewriter'

export function Hero() {
  const typed = useTypewriter()

  return (
    <section className="hero">
      <div className="hero__bg">
        <div className="hero__glow hero__glow--1" />
        <div className="hero__glow hero__glow--2" />
        <div className="hero__grid" />
      </div>

      <div className="container hero__inner">
        <div className="hero__content">
          <p className="hero__tag">Grip by Design</p>
          <h1 className="hero__title">
            Премиальные
            <br />
            <span className="hero__typed">
              {typed}
              <span className="hero__cursor">|</span>
            </span>
            <br />
            в <strong>Ижевске</strong>
          </h1>
          <p className="hero__desc">
            Подбор, продажа и монтаж шин всех классов — от городских седанов до внедорожников.
            Бесплатная консультация и расчёт за 10 минут.
          </p>
          <div className="hero__actions">
            <a href="#contact" className="btn btn--primary">
              Узнать стоимость
            </a>
            <a href="#catalog" className="btn btn--outline">
              Смотреть каталог
            </a>
          </div>
        </div>

        <div className="hero__card">
          <div className="hero__card-badge">онлайн подбор</div>
          <h2 className="hero__card-title">
            Подбор шин
            <br />
            по размеру
          </h2>
          <form className="hero__form" onSubmit={(e) => e.preventDefault()}>
            <div className="hero__form-row">
              <input type="text" placeholder="Ширина (205)" className="input" />
              <span className="hero__form-sep">/</span>
              <input type="text" placeholder="Профиль (55)" className="input" />
              <span className="hero__form-sep">R</span>
              <input type="text" placeholder="16" className="input input--sm" />
            </div>
            <input type="tel" placeholder="+7 (___) ___-__-__" className="input" />
            <button type="submit" className="btn btn--primary btn--full">
              Получить расчёт
            </button>
          </form>
          <p className="hero__card-note">
            Перезвоним в течение 10 минут и назовём точную цену
          </p>
        </div>
      </div>

      <div className="hero__tire">
        <div className="tire-visual">
          <div className="tire-visual__outer" />
          <div className="tire-visual__inner" />
          <div className="tire-visual__hub" />
        </div>
      </div>
    </section>
  )
}
