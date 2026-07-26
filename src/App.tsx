import { useEffect, useState } from 'react'
import { About } from './components/About'
import { Catalog } from './components/Catalog'
import { Contact } from './components/Contact'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { Hero } from './components/Hero'
import { Marquee } from './components/Marquee'
import { PublicOffer } from './components/PublicOffer'
import { RequestForm } from './components/RequestForm'
import { Services } from './components/Services'
import { Stats } from './components/Stats'

function getRoute(): 'home' | 'offer' {
  return window.location.hash === '#public-offer' ? 'offer' : 'home'
}

export default function App() {
  const [route, setRoute] = useState<'home' | 'offer'>(getRoute)

  useEffect(() => {
    const onHashChange = () => setRoute(getRoute())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  useEffect(() => {
    if (route !== 'home') {
      window.scrollTo(0, 0)
      return
    }
    const id = window.location.hash.replace(/^#/, '')
    if (!id || id === 'public-offer') {
      window.scrollTo(0, 0)
      return
    }
    requestAnimationFrame(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
    })
  }, [route])

  return (
    <>
      <Header />
      <main>
        {route === 'offer' ? (
          <PublicOffer />
        ) : (
          <>
            <Hero />
            <Marquee />
            <Services />
            <Stats />
            <Catalog />
            <RequestForm />
            <About />
            <Contact />
          </>
        )}
      </main>
      <Footer />
    </>
  )
}
