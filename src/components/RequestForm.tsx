export function RequestForm() {
  return (
    <section id="request" className="section request">
      <div className="container request__inner">
        <div className="section__header request__header">
          <p className="section__tag section__tag--highlight">Заявка</p>
          <h2 className="section__title">Оставьте заявку</h2>
          <p className="request__sub">Отправим расчёт в течение 10 минут</p>
        </div>

        <form className="request__form" onSubmit={(e) => e.preventDefault()}>
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
