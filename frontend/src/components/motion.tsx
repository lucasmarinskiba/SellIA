"use client"

import { motion, type Variants, type HTMLMotionProps } from "framer-motion"
import { cn } from "@/lib/utils"

/* ============================================================
   MOTION COMPONENTS — Reusable Framer Motion wrappers
   ============================================================ */

// Fade in from bottom
export function FadeIn({
  children,
  className,
  delay = 0,
  duration = 0.5,
  y = 24,
  ...props
}: {
  children: React.ReactNode
  className?: string
  delay?: number
  duration?: number
  y?: number
} & Omit<HTMLMotionProps<"div">, "children" | "className">) {
  return (
    <motion.div
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// Fade in with scale
export function FadeScale({
  children,
  className,
  delay = 0,
  duration = 0.5,
  ...props
}: {
  children: React.ReactNode
  className?: string
  delay?: number
  duration?: number
} & Omit<HTMLMotionProps<"div">, "children" | "className">) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// Stagger children container
export function StaggerContainer({
  children,
  className,
  staggerDelay = 0.08,
  ...props
}: {
  children: React.ReactNode
  className?: string
  staggerDelay?: number
} & Omit<HTMLMotionProps<"div">, "children" | "className">) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-50px" }}
      variants={{
        hidden: {},
        visible: {
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// Stagger child item
export function StaggerItem({
  children,
  className,
  ...props
}: {
  children: React.ReactNode
  className?: string
} & Omit<HTMLMotionProps<"div">, "children" | "className">) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] } },
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// Hover scale effect
export function HoverScale({
  children,
  className,
  scale = 1.02,
  ...props
}: {
  children: React.ReactNode
  className?: string
  scale?: number
} & Omit<HTMLMotionProps<"div">, "children" | "className">) {
  return (
    <motion.div
      whileHover={{ scale }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// Slide in from direction
export function SlideIn({
  children,
  className,
  direction = "left",
  delay = 0,
  duration = 0.6,
  ...props
}: {
  children: React.ReactNode
  className?: string
  direction?: "left" | "right" | "up" | "down"
  delay?: number
  duration?: number
} & Omit<HTMLMotionProps<"div">, "children" | "className">) {
  const directions = {
    left: { x: -40, y: 0 },
    right: { x: 40, y: 0 },
    up: { x: 0, y: -40 },
    down: { x: 0, y: 40 },
  }
  const { x, y } = directions[direction]

  return (
    <motion.div
      initial={{ opacity: 0, x, y }}
      whileInView={{ opacity: 1, x: 0, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// Page transition wrapper
export function PageTransition({
  children,
  className,
  ...props
}: {
  children: React.ReactNode
  className?: string
} & Omit<HTMLMotionProps<"div">, "children" | "className">) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// Animated number counter
export function MotionCounter({
  target,
  suffix = "",
  className,
}: {
  target: number
  suffix?: string
  className?: string
}) {
  return (
    <motion.span
      className={className}
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
    >
      <motion.span
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
      >
        {target.toLocaleString()}{suffix}
      </motion.span>
    </motion.span>
  )
}
