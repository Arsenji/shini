export function Contact() {
  return (
    <section id="contact" className="section contact">
      <div className="container contact__inner">
        <div className="contact__info">
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

        <form className="contact__form" onSubmit={(e) => e.preventDefault()}>
          <h3 className="contact__form-title">Оставьте заявку</h3>
          <p className="contact__form-sub">Отправим расчёт в течение 10 минут</p>
          <input type="text" placeholder="Имя" className="input" required />
          <select className="input" defaultValue="">
            <option value="" disabled>
              Выберите услугу
            </option>
            <option>Диски</option>
            <option>Летние шины</option>
            <option>Зимние шины</option>
            <option>Всесезонные шины</option>
            <option>Шиномонтаж</option>
            <option>Сезонное хранение</option>
            <option>Ремонт шин</option>
            <option>Другое</option>
          </select>
          <input type="text" placeholder="Размер (205/55 R16)" className="input" />
          <input type="tel" placeholder="+7 (___) ___-__-__" className="input" required />
          <button type="submit" className="btn btn--gold btn--full">
            Отправить заявку
          </button>
        </form>
      </div>
    </section>
  )
}
