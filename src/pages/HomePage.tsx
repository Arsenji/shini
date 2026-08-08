import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { About } from '../components/About'
import { Catalog } from '../components/Catalog'
import { Contact } from '../components/Contact'
import { Hero } from '../components/Hero'
import { Marquee } from '../components/Marquee'
import { RequestForm } from '../components/RequestForm'
import { Services } from '../components/Services'
import { Stats } from '../components/Stats'
import { SeoHead } from '../components/seo/SeoHead'

export function HomePage() {
  const location = useLocation()

  useEffect(() => {
    const id = location.hash.replace(/^#/, '')
    if (!id) {
      window.scrollTo(0, 0)
      return
    }
    requestAnimationFrame(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
    })
  }, [location.hash])

  return (
    <>
      <SeoHead
        title="КОЛЁСА ДЁШЕВО — шины, диски и шиномонтаж"
        description="Шины, диски и аксессуары в наличии. Подбор, продажа и шиномонтаж по выгодным ценам. Бесплатная консультация и расчёт за 10 минут."
        path="/"
      />
      <Hero />
      <Marquee />
      <Services />
      <Stats />
      <Catalog />
      <RequestForm />
      <About />
      <Contact />
    </>
  )
}
