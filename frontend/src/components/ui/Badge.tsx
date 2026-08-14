export const Badge = ({ children, variant = 'default', className }: { children: React.ReactNode; variant?: string; className?: string }) => {
  const baseClass = 'px-2 py-1 text-xs rounded';
  const variantClass = variant === 'outline' ? 'border' : 'bg-blue-200 text-blue-900';
  return <span className={`${baseClass} ${variantClass} ${className || ''}`}>{children}</span>;
};
