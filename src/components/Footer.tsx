import { Link } from 'react-router-dom'
import { Logo } from './Logo'
import { VK_URL } from './VkIcon'

export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div className="footer__brand">
          <Link to="/" className="footer__logo-link">
            <Logo size="footer" showTagline />
          </Link>
          <p className="footer__copy">© КОЛЁСА ДЁШЕВО, все права защищены.</p>
        </div>

        <nav className="footer__nav" aria-label="Навигация">
          <div className="footer__nav-row">
            <Link to={{ pathname: '/', hash: 'catalog' }}>Каталог</Link>
            <Link to="/tires">Шины</Link>
            <Link to="/wheels">Диски</Link>
            <Link to={{ pathname: '/', hash: 'services' }}>Услуги</Link>
            <Link to={{ pathname: '/', hash: 'about' }}>Компания</Link>
            <Link to={{ pathname: '/', hash: 'contact' }}>Контакты</Link>
            <a href={VK_URL} target="_blank" rel="noreferrer" aria-label="ВКонтакте">
              ВКонтакте
            </a>
          </div>
          <div className="footer__nav-row">
            <Link to="/personal-data-consent">Согласие на обработку персональных данных</Link>
            <Link to="/privacy-policy">Политика обработки персональных данных</Link>
            <Link to="/public-offer">Публичная оферта</Link>
            <a href="/dogovor-postavki-2026.pdf" download>
              Скачать договор поставки
            </a>
          </div>
        </nav>
      </div>
    </footer>
  )
}
