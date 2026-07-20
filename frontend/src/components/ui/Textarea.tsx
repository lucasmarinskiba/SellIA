import * as React from "react"
import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-white shadow-sm transition-all duration-200",
          "placeholder:text-white/20",
          "focus:outline-none focus:bg-white/[0.05] focus:border-brand-orange/30 focus:shadow-[0_0_0_3px_rgba(255,107,53,0.08)]",
          "hover:border-white/[0.12]",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "resize-y",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
