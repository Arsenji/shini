import { useId } from 'react'
import type { ShopImageKey } from '../../data/shop'

type TireIllustrationProps = {
  imageKey: ShopImageKey
  className?: string
}

/**
 * Однотипные SVG-иллюстрации в стиле сайта (navy + gold).
 * Чтобы добавить новый тип — расширьте ShopImageKey и добавьте ветку сюда.
 */
export function TireIllustration({ imageKey, className = '' }: TireIllustrationProps) {
  const uid = useId().replace(/:/g, '')
  const hubId = `hub-${uid}`

  const hubGradient = (
    <defs>
      <linearGradient id={hubId} x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#E8C547" />
        <stop offset="100%" stopColor="#C9A035" />
      </linearGradient>
    </defs>
  )

  if (imageKey === 'lcv') {
    return (
      <svg className={className} viewBox="0 0 160 160" aria-hidden="true">
        {hubGradient}
        <circle cx="80" cy="80" r="68" fill="none" stroke="#1B2D45" strokeWidth="18" />
        <circle cx="80" cy="80" r="48" fill="none" stroke="#1B2D45" strokeWidth="2" strokeDasharray="6 5" opacity="0.35" />
        <circle cx="80" cy="80" r="28" fill={`url(#${hubId})`} stroke="#1B2D45" strokeWidth="2" />
        <rect x="72" y="18" width="16" height="10" rx="2" fill="#1B2D45" />
        <rect x="72" y="132" width="16" height="10" rx="2" fill="#1B2D45" />
        <rect x="18" y="72" width="10" height="16" rx="2" fill="#1B2D45" />
        <rect x="132" y="72" width="10" height="16" rx="2" fill="#1B2D45" />
        <text x="80" y="86" textAnchor="middle" fontSize="11" fontWeight="800" fill="#1B2D45">
          LCV
        </text>
      </svg>
    )
  }

  if (imageKey === 'truck') {
    return (
      <svg className={className} viewBox="0 0 160 160" aria-hidden="true">
        {hubGradient}
        <circle cx="80" cy="80" r="70" fill="none" stroke="#1B2D45" strokeWidth="22" />
        <circle cx="80" cy="80" r="44" fill="none" stroke="#1B2D45" strokeWidth="3" opacity="0.25" />
        <g stroke="#8BA4B4" strokeWidth="3" strokeLinecap="round" opacity="0.7">
          <line x1="80" y1="22" x2="80" y2="36" />
          <line x1="80" y1="124" x2="80" y2="138" />
          <line x1="22" y1="80" x2="36" y2="80" />
          <line x1="124" y1="80" x2="138" y2="80" />
          <line x1="36" y1="36" x2="46" y2="46" />
          <line x1="114" y1="114" x2="124" y2="124" />
          <line x1="124" y1="36" x2="114" y2="46" />
          <line x1="46" y1="114" x2="36" y2="124" />
        </g>
        <circle cx="80" cy="80" r="26" fill={`url(#${hubId})`} stroke="#1B2D45" strokeWidth="2" />
        <text x="80" y="86" textAnchor="middle" fontSize="10" fontWeight="800" fill="#1B2D45">
          TRUCK
        </text>
      </svg>
    )
  }

  return (
    <svg className={className} viewBox="0 0 160 160" aria-hidden="true">
      {hubGradient}
      <circle cx="80" cy="80" r="66" fill="none" stroke="#1B2D45" strokeWidth="16" />
      <circle cx="80" cy="80" r="46" fill="none" stroke="#1B2D45" strokeWidth="2" strokeDasharray="4 6" opacity="0.4" />
      <circle cx="80" cy="80" r="24" fill={`url(#${hubId})`} stroke="#1B2D45" strokeWidth="1.5" />
      <circle cx="80" cy="80" r="8" fill="#1B2D45" opacity="0.15" />
    </svg>
  )
}
