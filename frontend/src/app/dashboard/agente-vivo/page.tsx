'use client'

/**
 * AGENTE EN VIVO — SellIA Brain Hub
 *
 * Interfaz central de mando donde todos los agentes de IA convergen.
 * Eje principal: Computer Use Agents (ojos y manos virtuales).
 * Activación por voz: "Hola SellIA"
 */

import SellIAHub from '@/components/sellia-hub/SellIAHub'
import { useAuth } from '@/hooks/useAuth'

export default function AgenteVivoPage() {
  const { user } = useAuth()

  return (
    <div className="-m-6">
      <SellIAHub
        userName={user?.full_name || user?.email?.split('@')[0] || 'Usuario'}
        userEmail={user?.email}
      />
    </div>
  )
}
