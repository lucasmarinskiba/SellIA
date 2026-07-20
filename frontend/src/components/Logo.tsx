'use client'

interface LogoProps {
  className?: string
  size?: number
  showText?: boolean
  variant?: 'dark' | 'light' | 'auto'
}

export default function Logo({ className = '', size = 40, showText = true, variant = 'auto' }: LogoProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
      >
        {/* Hexágono base */}
        <path
          d="M50 5L93.3 30V80L50 105L6.7 80V30L50 5Z"
          fill="url(#gradient1)"
          transform="scale(0.95) translate(2.5, 0)"
        />
        <path
          d="M50 15L83.3 34V72L50 91L16.7 72V34L50 15Z"
          fill="url(#gradient2)"
        />
        {/* Burbuja de chat que forma V */}
        <path
          d="M35 38C35 38 42 32 50 32C58 32 65 38 65 46C65 54 58 60 50 60C47 60 44 59 42 57L35 64L37 54C36 52 35 49 35 46C35 44 35 41 35 38Z"
          fill="white"
          fillOpacity="0.95"
        />
        {/* Rayo/brain IA */}
        <path
          d="M52 36L48 44H54L48 52"
          stroke="#FF6B35"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        {/* Puntos de conexión IA */}
        <circle cx="70" cy="28" r="4" fill="#00D4AA" />
        <circle cx="78" cy="38" r="3" fill="#7C3AED" />
        <circle cx="74" cy="50" r="2.5" fill="#FF6B35" />
        <defs>
          <linearGradient id="gradient1" x1="50" y1="5" x2="50" y2="105" gradientUnits="userSpaceOnUse">
            <stop stopColor="#0A2540" />
            <stop offset="1" stopColor="#1E3A5F" />
          </linearGradient>
          <linearGradient id="gradient2" x1="50" y1="15" x2="50" y2="91" gradientUnits="userSpaceOnUse">
            <stop stopColor="#0F2D4A" />
            <stop offset="1" stopColor="#0A2540" />
          </linearGradient>
        </defs>
      </svg>
      {showText && (
        <div className="flex flex-col">
          <span className="text-xl font-bold tracking-tight leading-none logo-text">
            Sell<span className="text-[#FF6B35]">IA</span>
          </span>
          <span className="text-[10px] font-medium tracking-widest uppercase leading-tight logo-subtext">
            Vende mientras duermes
          </span>
        </div>
      )}
    </div>
  )
}
