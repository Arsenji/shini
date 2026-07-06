import { About } from './components/About'
import { Catalog } from './components/Catalog'
import { Contact } from './components/Contact'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { Hero } from './components/Hero'
import { Marquee } from './components/Marquee'
import { Services } from './components/Services'
import { Stats } from './components/Stats'

export default function App() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Marquee />
        <Services />
        <Stats />
        <Catalog />
        <About />
        <Contact />
      </main>
      <Footer />
    </>
  )
}
