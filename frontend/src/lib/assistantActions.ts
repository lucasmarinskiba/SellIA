/**
 * Shared `AssistantAction` executor.
 *
 * Extracted from `SellIAAssistant.tsx`'s `handleAction` so both the chat
 * widget and the hands-free voice overlay (`HandsFreeOverlay.tsx`, wired via
 * `SellIABrainShell.tsx`) turn a backend-decided `AssistantAction` into the
 * same real frontend effects (navigate, create an agent conversation, etc.)
 * instead of two divergent copies of this routing logic.
 */
import { AssistantAction } from './assistant'
import { agentsApi } from './agents'

/** Minimal shape needed from Next's router — avoids importing its internal type. */
export interface ActionRouter {
  push: (href: string) => void
}

export interface ExecuteActionContext {
  router: ActionRouter
  businessId?: string
  /** Loaded agent personalities, used to resolve `agent_slug` → id for
   * CREATE_CONVERSATION / MULTI_AGENT_PANEL. Pass `[]` if unavailable —
   * those two action types will just fall back to a plain navigate. */
  personalities: Array<{ id: string; slug: string; name: string }>
  /** Called after any action that navigates away / is otherwise "done" —
   * e.g. close the chat widget or the hands-free overlay. */
  onDone?: () => void
}

export async function executeAssistantAction(
  action: AssistantAction,
  ctx: ExecuteActionContext,
): Promise<void> {
  const { router, businessId, personalities, onDone } = ctx

  if (action.action === 'CREATE_CONVERSATION' && action.conversation_id && action.personality) {
    router.push(`/dashboard/agentes?conversation=${action.conversation_id}`)
    onDone?.()
  } else if (action.action === 'CREATE_CONVERSATION' && action.agent_slug) {
    const personality = personalities.find(p => p.slug === action.agent_slug)
    if (personality && businessId) {
      try {
        const conv = await agentsApi.createConversation({
          business_id: businessId,
          personality_id: personality.id,
          title: `SellIA: ${personality.name}`,
        })
        router.push(`/dashboard/agentes?conversation=${conv.id}`)
        onDone?.()
      } catch {
        router.push('/dashboard/agentes')
        onDone?.()
      }
    } else {
      router.push('/dashboard/agentes')
      onDone?.()
    }
  } else if (action.action === 'NAVIGATE' && action.target) {
    const navMap: Record<string, string> = {
      agentes: '/dashboard/agentes',
      negocios: '/dashboard/negocios',
      catalogo: '/dashboard/catalogo',
      analytics: '/dashboard/analytics',
      conversaciones: '/dashboard/conversaciones',
      automatizaciones: '/dashboard/automatizaciones',
      canales: '/dashboard/canales',
      planes: '/dashboard/planes',
      configuracion: '/dashboard/configuracion',
      pipeline: '/dashboard/pipeline',
      autonomo: '/dashboard/autonomo',
    }
    const target = navMap[action.target.toLowerCase()] || '/dashboard'
    router.push(target)
    onDone?.()
  } else if (action.action === 'ACTIVATE_PIPELINE_AGENT' && action.stage) {
    router.push(`/dashboard/pipeline?stage=${action.stage}${action.deal_id ? `&deal=${action.deal_id}` : ''}`)
    onDone?.()
  } else if (action.action === 'NEGOTIATE') {
    router.push(`/dashboard/agentes?section=negotiate${action.expert ? `&expert=${action.expert}` : ''}`)
    onDone?.()
  } else if (action.action === 'BUILD_OFFER') {
    router.push(`/dashboard/agentes?section=offer${action.product_name ? `&product=${encodeURIComponent(action.product_name)}` : ''}`)
    onDone?.()
  } else if (action.action === 'SYSTEM_HEALTH') {
    router.push('/dashboard/autonomo')
    onDone?.()
  } else if (action.action === 'SETUP_AUTOMATION') {
    router.push('/dashboard/automatizaciones/builder')
    onDone?.()
  } else if (action.action === 'COMPUTER_USE' && action.session_id) {
    router.push(`/dashboard/caja-de-cristal?session=${action.session_id}`)
    onDone?.()
  } else if (action.action === 'MULTI_AGENT_PANEL' && action.agent_slugs && businessId) {
    // Open multiple conversations in sequence
    for (const slug of action.agent_slugs) {
      const personality = personalities.find(p => p.slug === slug)
      if (personality) {
        try {
          await agentsApi.createConversation({
            business_id: businessId,
            personality_id: personality.id,
            title: `SellIA: ${personality.name}`,
          })
        } catch {
          // skip failed ones
        }
      }
    }
    router.push('/dashboard/agentes')
    onDone?.()
  }
}
