'use client'

import { useEffect, useCallback, useRef } from 'react'
import { useMissionWebSocket } from './useMissionWebSocket'

/**
 * Extends SellIA voice system to approve missions by voice.
 * 
 * Trigger phrases:
 * - "SellIA, aprueba la misión" → approves current proposed mission
 * - "SellIA, ejecuta la misión" → runs current approved mission  
 * - "SellIA, cancela la misión" → cancels current running mission
 * - "SellIA, nueva misión [playbook name]" → creates new mission
 */

const APPROVAL_PHRASES = [
  'aprueba la misión', 'aprueba la mision',
  'acepta la misión', 'acepta la mision',
  'dale a la misión', 'dale a la mision',
  'sí a la misión', 'si a la mision',
]

const RUN_PHRASES = [
  'ejecuta la misión', 'ejecuta la mision',
  'corre la misión', 'corre la mision',
  'inicia la misión', 'inicia la mision',
  'empezar misión', 'empezar mision',
]

const CANCEL_PHRASES = [
  'cancela la misión', 'cancela la mision',
  'para la misión', 'para la mision',
  'detén la misión', 'deten la mision',
]

export function useVoiceMissionApproval(
  missions: Array<{ id: string; status: string; title: string }>,
  onApprove: (id: string) => void,
  onRun: (id: string) => void,
  onCancel: (id: string) => void,
  onCreate?: (playbookSlug: string) => void,
) {
  const { lastMessage } = useMissionWebSocket()
  const pendingApprovalRef = useRef<string | null>(null)

  // Track which mission is waiting for approval from WS
  useEffect(() => {
    if (lastMessage?.type === 'step_approval_request') {
      pendingApprovalRef.current = lastMessage.mission_id
    }
  }, [lastMessage])

  const handleVoiceCommand = useCallback((transcript: string) => {
    const lower = transcript.toLowerCase().trim()

    // Find most relevant mission
    const proposed = missions.find(m => m.status === 'proposed')
    const approved = missions.find(m => m.status === 'approved')
    const running = missions.find(m => m.status === 'running')

    // Approval
    if (APPROVAL_PHRASES.some(p => lower.includes(p))) {
      if (proposed) {
        onApprove(proposed.id)
        return { action: 'approve', missionId: proposed.id, title: proposed.title }
      }
      return { action: 'approve', error: 'No hay misiones para aprobar' }
    }

    // Run
    if (RUN_PHRASES.some(p => lower.includes(p))) {
      if (approved) {
        onRun(approved.id)
        return { action: 'run', missionId: approved.id, title: approved.title }
      }
      return { action: 'run', error: 'No hay misiones aprobadas para ejecutar' }
    }

    // Cancel
    if (CANCEL_PHRASES.some(p => lower.includes(p))) {
      if (running) {
        onCancel(running.id)
        return { action: 'cancel', missionId: running.id, title: running.title }
      }
      return { action: 'cancel', error: 'No hay misiones en ejecución para cancelar' }
    }

    // Create new mission by name (simplified matching)
    if (lower.includes('nueva misión') || lower.includes('nueva mision') || lower.includes('crear misión') || lower.includes('crear mision')) {
      const playbookKeywords: Record<string, string> = {
        'instagram': 'instagram_launch',
        'seo': 'seo_technical_audit',
        'google ads': 'google_ads_search',
        'meta ads': 'meta_ads_funnel',
        'facebook ads': 'meta_ads_funnel',
        'tiktok': 'tiktok_viral_launch',
        'carritos': 'cart_recovery_sequence',
        'recuperación': 'cart_recovery_sequence',
        'recuperacion': 'cart_recovery_sequence',
        'email': 'email_marketing_setup',
        'branding': 'brand_identity_refresh',
        'local': 'google_local_seo',
        'envíos': 'shipping_carriers_full',
        'envios': 'shipping_carriers_full',
      }
      for (const [keyword, slug] of Object.entries(playbookKeywords)) {
        if (lower.includes(keyword) && onCreate) {
          onCreate(slug)
          return { action: 'create', playbookSlug: slug }
        }
      }
    }

    return null
  }, [missions, onApprove, onRun, onCancel, onCreate])

  return { handleVoiceCommand, pendingApprovalId: pendingApprovalRef.current }
}
