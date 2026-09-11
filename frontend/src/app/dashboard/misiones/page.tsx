'use client'

/**
 * Próximos pasos — todo lo que hay para hacer, en orden.
 *
 * Esta página era "Misiones": pedía /missions, /missions/diagnostics/list y
 * /missions/from-playbook, rutas que no existen en este backend. Lo único vivo
 * que tenía eran los análisis de /business-context (canales que faltan y
 * alcance), y esos volvieron al motor: ahora aparecen priorizados junto al
 * resto en vez de en una pestaña aparte.
 *
 * Alertas muestra sólo lo urgente y Recomendaciones lo que hace crecer; acá está
 * todo junto, en orden de prioridad.
 */

import React from 'react'
import ActionList from '@/components/next-steps/ActionList'

export default function ProximosPasosPage(): React.JSX.Element {
  return (
    <ActionList
      title="Próximos pasos"
      subtitle="Calculado sobre tus propias conversaciones, órdenes y clientes. Si no hay nada acá, no hay nada pendiente que se pueda medir."
      urgencies={['alta', 'media', 'baja']}
      emptyTitle="No hay nada pendiente de lo que se puede medir."
      emptyBody="Ninguna consulta sin responder, ninguna orden trabada, ningún cliente sin contacto."
    />
  )
}
