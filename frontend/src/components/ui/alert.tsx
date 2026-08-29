interface AlertProps {
  children: React.ReactNode
  className?: string
}

export const Alert = ({ children, className = '' }: AlertProps) => (
  <div className={`rounded-lg border px-4 py-3 ${className}`} role="alert">
    {children}
  </div>
)

export const AlertTitle = ({ children, className = '' }: AlertProps) => (
  <h5 className={`font-medium leading-none mb-1 ${className}`}>{children}</h5>
)

export const AlertDescription = ({ children, className = '' }: AlertProps) => (
  <div className={`text-sm ${className}`}>{children}</div>
)

export default Alert
