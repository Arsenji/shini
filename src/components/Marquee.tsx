import { marqueeItems } from '../data'

export function Marquee() {
  const items = [...marqueeItems, ...marqueeItems]

  return (
    <div className="marquee">
      <div className="marquee__track">
        {items.map((item, i) => (
          <span key={i} className="marquee__item">
            {item}
            <span className="marquee__dot">•</span>
          </span>
        ))}
      </div>
    </div>
  )
}
