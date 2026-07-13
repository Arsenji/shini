export function Contact() {
  return (
    <section id="contact" className="section contact">
      <div className="container contact__inner">
        <p className="section__tag section__tag--highlight">Контакты</p>
        <h2 className="section__title">Запись на шиномонтаж</h2>
        <div className="contact__details">
          <div className="contact__detail">
            <span className="contact__detail-label">Телефон</span>
            <a href="tel:+79127653018" className="contact__detail-value">
              +7 912 765 30 18
            </a>
          </div>
          <div className="contact__detail">
            <span className="contact__detail-label">Адрес</span>
            <span className="contact__detail-value">Воткинское шоссе, 7</span>
          </div>
          <div className="contact__detail">
            <span className="contact__detail-label">Режим работы</span>
            <div className="contact__schedule">
              <span className="contact__detail-value">Будни — 9:00–18:00</span>
              <span className="contact__detail-value">Суббота — 9:00–16:00</span>
              <span className="contact__detail-value">Воскресенье — 10:00–16:00</span>
              <p className="contact__schedule-note">
                С октября по декабрь и с марта по май работу шиномонтажа уточняйте по телефону
              </p>
            </div>
          </div>
        </div>
        <a
          href="https://yandex.ru/maps/?text=Воткинское+шоссе,+7"
          className="btn btn--outline"
          target="_blank"
          rel="noreferrer"
        >
          Посмотреть на карте
        </a>
      </div>
    </section>
  )
}
