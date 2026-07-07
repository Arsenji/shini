export function TireTracks() {
  return (
    <div className="tire-tracks" aria-hidden="true">
      <svg className="tire-tracks__svg" viewBox="0 0 800 600" preserveAspectRatio="xMinYMin slice">
        <g opacity="0.18" transform="rotate(-25 200 200)">
          <rect x="40" y="60" width="700" height="50" rx="4" fill="white" />
          <rect x="40" y="130" width="700" height="50" rx="4" fill="#1B2D45" />
          <rect x="40" y="200" width="700" height="50" rx="4" fill="white" opacity="0.6" />
        </g>
        <g opacity="0.12" transform="rotate(-25 350 350)">
          <rect x="100" y="280" width="600" height="40" rx="4" fill="#1B2D45" />
          <rect x="100" y="340" width="600" height="40" rx="4" fill="white" />
        </g>
      </svg>
    </div>
  )
}
