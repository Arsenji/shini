import { useEffect, useState } from 'react'
import { Logo } from './Logo'
import { VK_URL, VkIcon } from './VkIcon'

const navLinks = [
  { href: '#catalog', label: 'Каталог' },
  { href: '#services', label: 'Услуги' },
  { href: '#about', label: 'Компания' },
  { href: '#contact', label: 'Контакты' },
]

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
        <a href="#" className="header__logo-link" onClick={closeMenu}>
          <Logo />
        </a>

        <nav className={`header__nav ${menuOpen ? 'header__nav--open' : ''}`}>
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="header__link"
              onClick={closeMenu}
            >
              {link.label}
            </a>
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
            <a href="#contact" className="btn btn--primary" onClick={closeMenu}>
              Подобрать шины
            </a>
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
          <a href="#contact" className="btn btn--primary btn--sm">
            Подобрать шины
          </a>
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
