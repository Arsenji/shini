export function Contact() {
  return (
    <section id="contact" className="section contact">
      <div className="container contact__inner">
        <div className="contact__info">
          <p className="section__tag">Контакты</p>
          <h2 className="section__title">Запись на шиномонтаж</h2>
          <div className="contact__details">
            <div className="contact__detail">
              <span className="contact__detail-label">Телефон</span>
              <a href="tel:+79120133223" className="contact__detail-value">
                +7 912 013 32 23
              </a>
            </div>
            <div className="contact__detail">
              <span className="contact__detail-label">Адрес</span>
              <span className="contact__detail-value">г. Ижевск, ул. Дружбы 5Б</span>
            </div>
            <div className="contact__detail">
              <span className="contact__detail-label">Режим работы</span>
              <span className="contact__detail-value">9:00 — 18:00, ежедневно</span>
            </div>
          </div>
          <a
            href="https://yandex.ru/maps/"
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
          <button type="submit" className="btn btn--primary btn--full">
            Отправить заявку
          </button>
        </form>
      </div>
    </section>
  )
}
