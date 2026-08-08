import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from './Logo'
import { VK_URL, VkIcon } from './VkIcon'

const navLinks = [
  { to: { pathname: '/', hash: 'catalog' }, label: 'Каталог' },
  { to: '/tires', label: 'Шины' },
  { to: '/wheels', label: 'Диски' },
  { to: { pathname: '/', hash: 'services' }, label: 'Услуги' },
  { to: { pathname: '/', hash: 'about' }, label: 'Компания' },
  { to: { pathname: '/', hash: 'contact' }, label: 'Контакты' },
] as const

export function Header() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [menuOpen])

  const closeMenu = () => setMenuOpen(false)

  return (
    <header className={`header ${scrolled ? 'header--scrolled' : ''}`}>
      <div className="container header__inner">
        <Link to="/" className="header__logo-link" onClick={closeMenu}>
          <Logo />
        </Link>

        <nav className={`header__nav ${menuOpen ? 'header__nav--open' : ''}`}>
          {navLinks.map((link) => (
            <Link
              key={link.label}
              to={link.to}
              className="header__link"
              onClick={closeMenu}
            >
              {link.label}
            </Link>
          ))}
          <div className="header__nav-actions">
            <a
              href={VK_URL}
              className="header__social header__social--menu"
              aria-label="ВКонтакте"
              target="_blank"
              rel="noreferrer"
            >
              <VkIcon />
            </a>
            <Link
              to={{ pathname: '/', hash: 'contact' }}
              className="btn btn--primary"
              onClick={closeMenu}
            >
              Подобрать шины
            </Link>
          </div>
        </nav>

        <div className="header__actions">
          <a
            href={VK_URL}
            className="header__social"
            aria-label="ВКонтакте"
            target="_blank"
            rel="noreferrer"
          >
            <VkIcon />
          </a>
          <Link to={{ pathname: '/', hash: 'contact' }} className="btn btn--primary btn--sm">
            Подобрать шины
          </Link>
        </div>

        <button
          className={`header__burger ${menuOpen ? 'header__burger--open' : ''}`}
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label={menuOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={menuOpen}
        >
          <span />
          <span />
        </button>
      </div>
    </header>
  )
}
