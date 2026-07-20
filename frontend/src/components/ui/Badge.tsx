import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-brand-orange/20 focus:ring-offset-2 focus:ring-offset-[#060812]",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-brand-orange/10 text-brand-orange hover:bg-brand-orange/20",
        secondary:
          "border-transparent bg-white/5 text-white/60 hover:bg-white/10",
        destructive:
          "border-transparent bg-red-500/10 text-red-400 hover:bg-red-500/20",
        outline:
          "border-white/10 text-white/60 hover:bg-white/5",
        success:
          "border-transparent bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20",
        warning:
          "border-transparent bg-amber-500/10 text-amber-400 hover:bg-amber-500/20",
        info:
          "border-transparent bg-blue-500/10 text-blue-400 hover:bg-blue-500/20",
        orange:
          "border-transparent bg-brand-orange/10 text-brand-orange hover:bg-brand-orange/20",
        teal:
          "border-transparent bg-brand-teal/10 text-brand-teal hover:bg-brand-teal/20",
        violet:
          "border-transparent bg-brand-violet/10 text-brand-violet hover:bg-brand-violet/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export default Badge
export { Badge, badgeVariants }
