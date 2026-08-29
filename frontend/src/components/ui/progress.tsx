interface ProgressProps {
  value: number
  className?: string
}

export const Progress = ({ value, className = '' }: ProgressProps) => {
  const clamped = Math.min(100, Math.max(0, value))
  return (
    <div className={`w-full overflow-hidden rounded-full bg-gray-200 ${className}`}>
      <div
        className="h-full rounded-full bg-blue-600 transition-all"
        style={{ width: `${clamped}%` }}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  )
}

export default Progress
