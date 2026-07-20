"use client"

import * as React from "react"

const DropdownMenuContext = React.createContext<{
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
} | null>(null)

function useDropdownMenu() {
  const ctx = React.useContext(DropdownMenuContext)
  if (!ctx) throw new Error("DropdownMenu components must be used inside DropdownMenu")
  return ctx
}

export function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)
  const ref = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [open])

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen }}>
      <div ref={ref} className="relative inline-block">{children}</div>
    </DropdownMenuContext.Provider>
  )
}

export function DropdownMenuTrigger({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) {
  const { open, setOpen } = useDropdownMenu()
  if (asChild && React.isValidElement(children)) {
    const child = children as React.ReactElement<any>
    return React.cloneElement(child, {
      onClick: (e: React.MouseEvent) => {
        setOpen((prev) => !prev)
        child.props.onClick?.(e)
      },
    })
  }
  return (
    <button type="button" onClick={() => setOpen((prev) => !prev)}>
      {children}
    </button>
  )
}

export function DropdownMenuContent({
  children,
  className,
  align,
}: {
  children: React.ReactNode
  className?: string
  align?: "start" | "end" | "center"
}) {
  const { open } = useDropdownMenu()
  if (!open) return null
  const alignClass =
    align === "end" ? "right-0" : align === "center" ? "left-1/2 -translate-x-1/2" : "left-0"
  return (
    <div
      className={
        "absolute mt-2 w-56 rounded-md border border-gray-200 bg-white shadow-lg z-50 " +
        alignClass +
        " " +
        (className || "")
      }
    >
      {children}
    </div>
  )
}

export function DropdownMenuItem({
  children,
  onClick,
  className,
  disabled,
}: {
  children: React.ReactNode
  onClick?: () => void | Promise<void>
  className?: string
  disabled?: boolean
}) {
  const { setOpen } = useDropdownMenu()
  return (
    <button
      type="button"
      disabled={disabled}
      className={
        "w-full text-left px-4 py-2 text-sm hover:bg-gray-100 focus:bg-gray-100 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed " +
        (className || "")
      }
      onClick={() => {
        onClick?.()
        setOpen(false)
      }}
    >
      {children}
    </button>
  )
}
