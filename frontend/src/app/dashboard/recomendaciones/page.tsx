'use client'

/**
 * Recomendaciones — lo que haría crecer el negocio.
 *
 * Esta página leía /alerts/recommendations y sus acciones apply/dismiss, que no
 * existen en este backend (404): mostraba siempre "no hay recomendaciones".
 *
 * Ahora muestra lo que sí se puede deducir de los datos: canales que tu rubro
 * necesita y no tenés, clientes que dejaron de comprar, órdenes sin contacto
 * (que impiden medir recompra), configuración que le falta a la IA y hasta dónde
 * podrías vender. Nada promete un porcentaje de mejora, porque nada de eso se
 * puede medir por adelantado.
 */

import React from 'react'
import ActionList from '@/components/next-steps/ActionList'

export default function RecomendacionesPage(): React.JSX.Element {
  return (
    <ActionList
      title="Recomendaciones"
      subtitle="Lo que puede hacer crecer tu negocio, deducido de tus propios datos. Nada acá es urgente: son decisiones, no incendios."
      urgencies={['media', 'baja']}
      emptyTitle="No hay recomendaciones pendientes."
      emptyBody="Tu configuración está completa, tus canales conectados y tus clientes con contacto cargado."
    />
  )
}
