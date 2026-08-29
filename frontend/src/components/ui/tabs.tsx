import React, { ReactNode, useState } from 'react'

interface TabsProps {
  children: ReactNode
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
  className?: string
}

interface TabsListProps {
  children: ReactNode
  className?: string
}

interface TabsTriggerProps {
  value: string
  children: ReactNode
  className?: string
}

interface TabsContentProps {
  value: string
  children: ReactNode
  className?: string
}

const TabsContext = React.createContext<{
  activeTab: string
  setActiveTab: (value: string) => void
} | null>(null)

export const Tabs = ({
  children,
  defaultValue = '',
  value: controlledValue,
  onValueChange,
  className = '',
}: TabsProps) => {
  const [uncontrolledTab, setUncontrolledTab] = useState(defaultValue)

  // Controlled (value + onValueChange supplied) or uncontrolled (internal state) —
  // same pattern as the rest of this component set (Card/Badge use plain props).
  const isControlled = controlledValue !== undefined
  const activeTab = isControlled ? controlledValue : uncontrolledTab
  const setActiveTab = isControlled ? (onValueChange ?? (() => {})) : setUncontrolledTab

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

export const TabsList = ({ children, className = '' }: TabsListProps) => (
  <div className={`flex border-b border-gray-200 ${className}`}>{children}</div>
)

export const TabsTrigger = ({ value, children, className = '' }: TabsTriggerProps) => {
  const context = React.useContext(TabsContext)
  if (!context) throw new Error('TabsTrigger must be used within Tabs')

  const isActive = context.activeTab === value

  return (
    <button
      onClick={() => context.setActiveTab(value)}
      className={`px-4 py-2 font-medium text-sm border-b-2 ${
        isActive
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-600 hover:text-gray-900'
      } ${className}`}
    >
      {children}
    </button>
  )
}

export const TabsContent = ({ value, children, className = '' }: TabsContentProps) => {
  const context = React.useContext(TabsContext)
  if (!context) throw new Error('TabsContent must be used within Tabs')

  if (context.activeTab !== value) return null

  return <div className={className}>{children}</div>
}

export default Tabs
