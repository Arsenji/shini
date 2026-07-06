import { stats } from '../data'

export function Stats() {
  return (
    <section className="stats">
      <div className="container stats__inner">
        {stats.map((stat) => (
          <div key={stat.label} className="stats__item">
            <span className="stats__value">{stat.value}</span>
            <span className="stats__label">{stat.label}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
