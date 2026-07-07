import { team } from '../data'

export function About() {
  return (
    <section id="about" className="section about">
      <div className="container about__inner">
        <div className="about__content">
          <p className="section__tag">О нас</p>
          <h2 className="section__title">Надёжные колёса — доступные цены</h2>
          <p className="about__text">
            КОЛЁСА ДЁШЕВО — это магазин шин и дисков, который предлагает полный спектр услуг
            по подбору, продаже и обслуживанию автомобильных покрышек. Мы не просто продаём
            резину — мы подбираем оптимальное решение под ваш стиль вождения, климат и бюджет.
          </p>
          <p className="about__text">
            В нашей работе сочетаются технологии, точность и страсть к деталям: от подбора
            по VIN и размеру до профессионального шиномонтажа, балансировки и сезонного хранения.
            Работаем с машинами всех классов — от компактных хэтчбеков до премиальных внедорожников.
          </p>
          <div className="about__number">
            <span className="about__number-value">12 000</span>
            <span className="about__number-label">комплектов продано</span>
          </div>
        </div>

        <div className="about__team">
          {team.map((member) => (
            <article key={member.name} className="team-card">
              <div className="team-card__avatar">
                {member.name.split(' ').map((n) => n[0]).join('')}
              </div>
              <h3 className="team-card__name">{member.name}</h3>
              <p className="team-card__role">{member.role}</p>
              <p className="team-card__exp">{member.experience}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
