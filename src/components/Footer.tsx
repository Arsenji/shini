import { Logo } from './Logo'

export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div className="footer__brand">
          <a href="#" className="footer__logo-link">
            <Logo size="footer" showTagline />
          </a>
          <p className="footer__copy">© КОЛЁСА ДЁШЕВО, все права защищены.</p>
        </div>

        <nav className="footer__nav">
          <a href="#catalog">Каталог</a>
          <a href="#services">Услуги</a>
          <a href="#about">Компания</a>
          <a href="#contact">Контакты</a>
        </nav>

        <div className="footer__socials">
          <a href="https://t.me/" target="_blank" rel="noreferrer" aria-label="Telegram">
            Telegram
          </a>
          <a href="tel:+79120133223" aria-label="Phone">
            Phone
          </a>
          <a href="https://wa.me/" target="_blank" rel="noreferrer" aria-label="WhatsApp">
            WhatsApp
          </a>
        </div>
      </div>
    </footer>
  )
}
