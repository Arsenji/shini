import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { HomePage } from './pages/HomePage'
import { PublicOfferPage } from './pages/PublicOfferPage'
import { TireProductPage } from './pages/TireProductPage'
import { TiresPage } from './pages/TiresPage'
import { WheelProductPage } from './pages/WheelProductPage'
import { WheelsPage } from './pages/WheelsPage'

function LegacyHashRedirect() {
  const location = useLocation()
  if (location.pathname === '/' && location.hash === '#public-offer') {
    return <Navigate to="/public-offer" replace />
  }
  return null
}

export default function App() {
  return (
    <>
      <LegacyHashRedirect />
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/tires" element={<TiresPage />} />
          <Route path="/tires/:id" element={<TireProductPage />} />
          <Route path="/wheels" element={<WheelsPage />} />
          <Route path="/wheels/:id" element={<WheelProductPage />} />
          <Route path="/public-offer" element={<PublicOfferPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
    </>
  )
}
