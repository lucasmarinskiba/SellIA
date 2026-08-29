interface BadgeProps {
  children: React.ReactNode
  variant?:
    | 'default'
    | 'secondary'
    | 'destructive'
    | 'outline'
    | 'success'
    | 'warning'
    | 'info'
    | 'orange'
    | 'teal'
    | 'violet'
  className?: string
  onClick?: () => void
}

export const Badge = ({ children, variant = 'default', className = '', onClick }: BadgeProps) => {
  const variantClass = {
    default: 'bg-blue-100 text-blue-800',
    secondary: 'bg-gray-100 text-gray-800',
    destructive: 'bg-red-100 text-red-800',
    outline: 'border border-gray-300 text-gray-700',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    info: 'bg-sky-100 text-sky-800',
    orange: 'bg-orange-100 text-orange-800',
    teal: 'bg-teal-100 text-teal-800',
    violet: 'bg-violet-100 text-violet-800',
  }[variant]

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium ${variantClass} ${className}`}
      onClick={onClick}
    >
      {children}
    </span>
  )
}

export default Badge

