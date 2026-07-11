import { Logo } from './Logo'
import { VK_URL } from './VkIcon'

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
          <a href={VK_URL} target="_blank" rel="noreferrer" aria-label="ВКонтакте">
            ВКонтакте
          </a>
        </nav>
      </div>
    </footer>
  )
}
