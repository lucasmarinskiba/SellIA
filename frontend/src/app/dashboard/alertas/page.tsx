'use client'

/**
 * Alertas — lo que está perdiendo plata ahora.
 *
 * Esta página leía /alerts, /alerts/rules, /alerts/stats y
 * /alerts/recommendations. Las cuatro devuelven 404 en este backend, así que
 * mostraba una bandeja vacía: el usuario concluía "no tengo alertas" cuando en
 * realidad nadie las estaba calculando.
 *
 * Ahora muestra las acciones urgentes que sí se calculan sobre sus datos:
 * consultas sin responder, órdenes sin cobrar, órdenes cobradas sin despachar,
 * y la IA sin clave configurada. Cada una con el número que la justifica.
 */

import React from 'react'
import ActionList from '@/components/next-steps/ActionList'

export default function AlertasPage(): React.JSX.Element {
  return (
    <ActionList
      title="Alertas"
      subtitle="Lo que está costando plata o clientes en este momento, calculado sobre tus órdenes y conversaciones reales."
      urgencies={['alta']}
      emptyTitle="No hay nada urgente."
      emptyBody="Ninguna consulta sin responder hace horas, ninguna orden trabada, ninguna venta sin cobrar."
    />
  )
}
