type LogoProps = {
  className?: string
  size?: 'header' | 'footer'
  showTagline?: boolean
}

export function Logo({ className = '', size = 'header', showTagline = false }: LogoProps) {
  return (
    <div className={`logo logo--${size} ${className}`}>
      <img
        src="/logo.png"
        alt="КОЛЁСА ДЁШЕВО — шины, диски, шиномонтаж"
        className="logo__img"
      />
      {showTagline && (
        <span className="logo__tagline">
          Шины, диски
          <br />
          Шиномонтаж
        </span>
      )}
    </div>
  )
}
