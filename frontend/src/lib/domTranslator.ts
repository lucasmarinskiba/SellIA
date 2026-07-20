'use client'

/**
 * DOM TRANSLATOR
 *
 * Walks the DOM, collects unique Spanish text nodes + input placeholders +
 * aria-labels + titles, translates via `/api/translate` (MyMemory proxy),
 * and swaps them in place.
 *
 * Coverage:
 *   - Text nodes inside elements
 *   - input/textarea placeholder attrs
 *   - aria-label attrs
 *   - title attrs (tooltips)
 *
 * Triggers:
 *   - On language change (called from SettingsProvider)
 *   - MutationObserver: re-translates added nodes + attribute changes + characterData
 *
 * Cache: localStorage `sellia_translations_v1` { lang: { sourceText: translated } }
 *
 * Skips: <script>, <style>, <code>, <pre>, contenteditable, monospace short text,
 *        very short strings (< 3 chars), pure numbers/symbols.
 */

import type { Lang } from './settings'

const CACHE_KEY = 'sellia_translations_v1'
const BATCH_SIZE = 30
const ORIG_TEXT_KEY = '__sellia_orig_text__'
const ORIG_ATTR_KEY = '__sellia_orig_attr__'
const ATTRS_TO_TRANSLATE = ['placeholder', 'aria-label', 'title'] as const
type AttrName = typeof ATTRS_TO_TRANSLATE[number]

interface TranslationCache {
  [lang: string]: { [src: string]: string }
}

// ── STATIC DICTIONARY — INSTANT translation (no API roundtrip) ─────────────────
// All common visible Spanish strings hard-mapped for zero-latency switching.
// API fallback only fires for dynamic / uncovered strings.
const STATIC_DICT: Record<'en' | 'pt' | 'fr', Record<string, string>> = {
  en: {
    // ── Nav / shell ──
    'Dashboard':'Dashboard','Escuadrones':'Squads','Pipeline de Ventas':'Sales Pipeline',
    'Agent Audit Log':'Agent Audit Log','Handoff · Slack IA':'Handoff · AI Slack',
    'Aprobaciones':'Approvals','Cerebro Neuronal':'Neural Brain',
    'SellIA · Command Center':'SellIA · Command Center','Súper Agente de Ventas B2B':'Super B2B Sales Agent',
    'AGENTE ACTIVO':'ACTIVE AGENT','capacidades':'capabilities','salud':'health',
    'vista':'view','Inicializando command center…':'Initializing command center…',
    // ── KPIs ──
    'ROI GLOBAL':'GLOBAL ROI','LEADS PROCESADOS':'LEADS PROCESSED',
    'TASA DE CONVERSIÓN':'CONVERSION RATE','TICKET PROMEDIO':'AVERAGE TICKET',
    // ── Mission bar ──
    'Buscar herramienta…':'Search tool…','Computer Use':'Computer Use','VOZ':'VOICE',
    'ESCUCHANDO':'LISTENING','PERMISO…':'PERMISSION…','MIC OFF':'MIC OFF','N/A':'N/A',
    'Entrar':'Sign in','Cerrar sesión':'Sign out','Eliminar cuenta':'Delete account',
    'Crear cuenta gratis':'Create free account','Iniciar sesión':'Log in','Cuenta desde':'Account since',
    'Modo Computer Use':'Computer Use Mode','Abrir sesión':'Open session',
    'Manos libres activo':'Hands-free active','Activar voz':'Activate voice',
    'Tu navegador no soporta voz':'Your browser does not support voice',
    'Permiso de mic denegado · revisar settings':'Mic permission denied · check settings',
    'Pidiendo permiso de micrófono…':'Requesting microphone permission…',
    'Escuchando · decí "Hola SellIA"':'Listening · say "Hola SellIA"',
    // ── Squads ──
    'Escuadrones SellIA':'SellIA Squads','ejecutando':'executing','telemetría en vivo':'live telemetry',
    'EJECUTANDO':'EXECUTING','EN REPOSO':'IDLE','PAUSADO':'PAUSED','ATENCIÓN':'ATTENTION',
    'SDR':'SDR','Prospección & ventas':'Prospecting & sales','Growth & Ads':'Growth & Ads',
    'Pauta paga · scaling':'Paid media · scaling','PR & Reputación':'PR & Reputation',
    'Social listening · brand':'Social listening · brand','Customer Success':'Customer Success',
    'Retención · soporte':'Retention · support','Operaciones · navegador':'Operations · browser',
    'Enviando secuencia outbound':'Sending outbound sequence','Optimizando 3 campañas':'Optimizing 3 campaigns',
    'Monitoreando 45 menciones LinkedIn':'Monitoring 45 LinkedIn mentions',
    'En reposo · sin tickets nuevos':'Idle · no new tickets','Esperando aprobación humana':'Waiting for human approval',
    'EMAILS 24H':'EMAILS 24H','RESPUESTAS':'REPLIES','REPLY RATE':'REPLY RATE',
    'DEMOS BOOK':'DEMOS BOOKED','ROAS':'ROAS','SPEND HOY':'SPEND TODAY','CPC PROMEDIO':'AVG CPC',
    'CONVERSIONES':'CONVERSIONS','MENCIONES 7D':'MENTIONS 7D','SENTIMIENTO':'SENTIMENT',
    'REACH TOTAL':'TOTAL REACH','RESPONDIDAS':'ANSWERED','TICKETS OPEN':'OPEN TICKETS',
    'TTR AVG':'AVG TTR','NPS ROLLING':'NPS ROLLING','CSAT 7D':'CSAT 7D',
    'PIPELINE ACTIVO':'ACTIVE PIPELINE','PIPELINE ACTIF':'ACTIVE PIPELINE',
    'Croissance & Ads':'Growth & Ads','Croissance':'Growth',
    'Crecimiento & Ads':'Growth & Ads','Crecimiento':'Growth',
    'Vente':'Sale','Vendas':'Sales','Ventas':'Sales',
    'TAREAS HOY':'TASKS TODAY','ÉXITO RATE':'SUCCESS RATE','PENDING HIL':'PENDING HIL',
    'TIEMPO AHORR':'TIME SAVED','crítico':'critical','positivo':'positive',
    // ── Approvals ──
    'Centro de Aprobaciones':'Approvals Center','Human-in-the-Loop · {n} pendientes':'Human-in-the-Loop · {n} pending',
    'Todas':'All','Crítico':'Critical','Alto':'High','Medio':'Medium','Bajo':'Low',
    'Aprobar':'Approve','Rechazar':'Reject','Procesando…':'Processing…',
    'Expandir todo':'Expand all','Colapsar todo':'Collapse all',
    'Sin decisiones pendientes':'No pending decisions',
    'IA operando dentro de parámetros aprobados':'AI operating within approved parameters',
    'Justificación IA':'AI Rationale','restante':'remaining','expirado':'expired',
    'Aumento de presupuesto':'Budget increase','Descuento al cliente':'Customer discount',
    'Envío masivo':'Mass send','Exportación de datos':'Data export',
    'Nueva integración / API':'New integration / API','Cambio de precio':'Price change',
    'Compra autónoma':'Autonomous purchase',
    // ── Handoff Log ──
    'Handoff Log · Slack IA':'Handoff Log · AI Slack','eventos':'events','departamentos':'departments',
    'TODOS':'ALL','HANDOFF':'HANDOFF','STATUS':'STATUS','ALERT':'ALERT','WIN':'WIN',
    'Sin eventos para este filtro':'No events for this filter',
    // ── Notifications ──
    'Notificaciones':'Notifications','sin leer':'unread','total':'total',
    'Sin notificaciones nuevas':'No new notifications','Marcar todas':'Mark all',
    'Ver todas':'View all','offline':'offline',
    'modo local · backend offline':'local mode · backend offline','live · polling 15s':'live · polling 15s',
    'Acción':'Action','Aprobación':'Approval','Alerta':'Alert','Info':'Info','Logro':'Win',
    // ── Settings ──
    'Configuración':'Settings','Tema':'Theme','Modo oscuro':'Dark mode','Modo claro':'Light mode',
    'Idioma':'Language','Español':'Spanish','Inglés':'English','Portugués':'Portuguese','Francés':'French',
    'Cambios aplicados globalmente · guardados en este dispositivo':'Changes applied globally · saved on this device',
    // ── Neural ──
    'Cerebro Neuronal en Vivo':'Live Neural Brain','SINAPSIS ACTIVAS':'ACTIVE SYNAPSES',
    'Cerebro offline · reintentando…':'Brain offline · retrying…','Cerebro en reposo':'Brain idle',
    'sin nodos cargados · grafo se activará con la primera interacción real':'no nodes loaded · graph will activate on first real interaction',
    'sin conexión con /api/v1/brain · polling activo':'no connection to /api/v1/brain · polling active',
    'nodos':'nodes','edges':'edges','Skills':'Skills','Agentes':'Agents','Automatizaciones':'Automations',
    'arrastrá para mover · scroll para zoom':'drag to move · scroll to zoom','último':'latest',
    // ── Pipeline / Audit ──
    'Gestionado por el agente · {n} prospectos':'Managed by agent · {n} prospects',
    'Buscar empresa, contacto, industria…':'Search company, contact, industry…',
    'Todos los estados':'All statuses','Ordenar':'Sort','Lead Score':'Lead Score',
    'Prob. Cierre':'Close Prob.','Valor':'Value','Empresa / Contacto':'Company / Contact',
    'Estado IA':'AI Status','Razonamiento en tiempo real':'Real-time reasoning',
    'Sin prospectos para los filtros aplicados.':'No prospects for the applied filters.',
    'Prospectando':'Prospecting','Calificando':'Qualifying','Outreach':'Outreach',
    'Negociando':'Negotiating','Propuesta enviada':'Proposal sent','Cierre':'Closing',
    'Ganado':'Won','En riesgo':'At risk',
  },
  pt: {
    'Dashboard':'Painel','Escuadrones':'Esquadrões','Pipeline de Ventas':'Pipeline de Vendas',
    'Agent Audit Log':'Agent Audit Log','Handoff · Slack IA':'Handoff · Slack IA',
    'Aprobaciones':'Aprovações','Cerebro Neuronal':'Cérebro Neural',
    'SellIA · Command Center':'SellIA · Command Center','Súper Agente de Ventas B2B':'Super Agente de Vendas B2B',
    'AGENTE ACTIVO':'AGENTE ATIVO','capacidades':'capacidades','salud':'saúde',
    'vista':'visão','Inicializando command center…':'Inicializando command center…',
    'ROI GLOBAL':'ROI GLOBAL','LEADS PROCESADOS':'LEADS PROCESSADOS',
    'TASA DE CONVERSIÓN':'TAXA DE CONVERSÃO','TICKET PROMEDIO':'TICKET MÉDIO',
    'Buscar herramienta…':'Buscar ferramenta…','Computer Use':'Computer Use','VOZ':'VOZ',
    'ESCUCHANDO':'OUVINDO','PERMISO…':'PERMISSÃO…','MIC OFF':'MIC OFF','N/A':'N/D',
    'Entrar':'Entrar','Cerrar sesión':'Sair','Eliminar cuenta':'Excluir conta',
    'Crear cuenta gratis':'Criar conta grátis','Iniciar sesión':'Entrar','Cuenta desde':'Conta desde',
    'Modo Computer Use':'Modo Computer Use','Abrir sesión':'Abrir sessão',
    'Manos libres activo':'Mãos livres ativo','Activar voz':'Ativar voz',
    'Tu navegador no soporta voz':'Seu navegador não suporta voz',
    'Permiso de mic denegado · revisar settings':'Permissão de mic negada · revisar settings',
    'Pidiendo permiso de micrófono…':'Pedindo permissão de microfone…',
    'Escuchando · decí "Hola SellIA"':'Ouvindo · diga "Olá SellIA"',
    'Escuadrones SellIA':'Esquadrões SellIA','ejecutando':'executando','telemetría en vivo':'telemetria ao vivo',
    'EJECUTANDO':'EXECUTANDO','EN REPOSO':'EM REPOUSO','PAUSADO':'PAUSADO','ATENCIÓN':'ATENÇÃO',
    'SDR':'SDR','Prospección & ventas':'Prospecção & vendas','Growth & Ads':'Growth & Ads',
    'Pauta paga · scaling':'Mídia paga · scaling','PR & Reputación':'PR & Reputação',
    'Social listening · brand':'Social listening · marca','Customer Success':'Customer Success',
    'Retención · soporte':'Retenção · suporte','Operaciones · navegador':'Operações · navegador',
    'Enviando secuencia outbound':'Enviando sequência outbound','Optimizando 3 campañas':'Otimizando 3 campanhas',
    'Monitoreando 45 menciones LinkedIn':'Monitorando 45 menções no LinkedIn',
    'En reposo · sin tickets nuevos':'Em repouso · sem tickets novos','Esperando aprobación humana':'Aguardando aprovação humana',
    'EMAILS 24H':'EMAILS 24H','RESPUESTAS':'RESPOSTAS','REPLY RATE':'TAXA DE RESPOSTA',
    'DEMOS BOOK':'DEMOS AGENDADAS','ROAS':'ROAS','SPEND HOY':'GASTO HOJE','CPC PROMEDIO':'CPC MÉDIO',
    'CONVERSIONES':'CONVERSÕES','MENCIONES 7D':'MENÇÕES 7D','SENTIMIENTO':'SENTIMENTO',
    'REACH TOTAL':'ALCANCE TOTAL','RESPONDIDAS':'RESPONDIDAS','TICKETS OPEN':'TICKETS ABERTOS',
    'TTR AVG':'TTR MÉDIO','NPS ROLLING':'NPS MÓVEL','CSAT 7D':'CSAT 7D',
    'PIPELINE ACTIVO':'PIPELINE ATIVO','PIPELINE ACTIF':'PIPELINE ATIVO',
    'TICKET MOYEN':'TICKET MÉDIO',
    'Crecimiento & Ads':'Crescimento & Ads','Crecimiento':'Crescimento','Croissance & Ads':'Crescimento & Ads',
    'TASA DE RESPUESTA':'TAXA DE RESPOSTA',
    'TAREAS HOY':'TAREFAS HOJE','ÉXITO RATE':'TAXA SUCESSO','PENDING HIL':'PENDENTE HIL',
    'TIEMPO AHORR':'TEMPO POUPADO','crítico':'crítico','positivo':'positivo',
    'Centro de Aprobaciones':'Central de Aprovações','Todas':'Todas','Crítico':'Crítico',
    'Alto':'Alto','Medio':'Médio','Bajo':'Baixo','Aprobar':'Aprovar','Rechazar':'Rejeitar',
    'Procesando…':'Processando…','Expandir todo':'Expandir tudo','Colapsar todo':'Recolher tudo',
    'Sin decisiones pendientes':'Sem decisões pendentes',
    'IA operando dentro de parámetros aprobados':'IA operando dentro de parâmetros aprovados',
    'Justificación IA':'Justificativa IA','restante':'restante','expirado':'expirado',
    'Aumento de presupuesto':'Aumento de orçamento','Descuento al cliente':'Desconto ao cliente',
    'Envío masivo':'Envio em massa','Exportación de datos':'Exportação de dados',
    'Nueva integración / API':'Nova integração / API','Cambio de precio':'Mudança de preço',
    'Compra autónoma':'Compra autônoma',
    'Handoff Log · Slack IA':'Handoff Log · Slack IA','eventos':'eventos','departamentos':'departamentos',
    'TODOS':'TODOS','Sin eventos para este filtro':'Sem eventos para este filtro',
    'Notificaciones':'Notificações','sin leer':'não lidas','total':'total',
    'Sin notificaciones nuevas':'Sem notificações novas','Marcar todas':'Marcar todas',
    'Ver todas':'Ver todas','offline':'offline',
    'modo local · backend offline':'modo local · backend offline','live · polling 15s':'live · polling 15s',
    'Acción':'Ação','Aprobación':'Aprovação','Alerta':'Alerta','Info':'Info','Logro':'Conquista',
    'Configuración':'Configurações','Tema':'Tema','Modo oscuro':'Modo escuro','Modo claro':'Modo claro',
    'Idioma':'Idioma','Español':'Espanhol','Inglés':'Inglês','Portugués':'Português','Francés':'Francês',
    'Cambios aplicados globalmente · guardados en este dispositivo':'Mudanças aplicadas globalmente · salvas neste dispositivo',
    'Cerebro Neuronal en Vivo':'Cérebro Neural Ao Vivo','SINAPSIS ACTIVAS':'SINAPSES ATIVAS',
    'Cerebro offline · reintentando…':'Cérebro offline · tentando…','Cerebro en reposo':'Cérebro em repouso',
    'nodos':'nós','Skills':'Skills','Agentes':'Agentes','Automatizaciones':'Automatizações',
    'arrastrá para mover · scroll para zoom':'arraste para mover · scroll para zoom','último':'último',
    'Buscar empresa, contacto, industria…':'Buscar empresa, contato, indústria…',
    'Todos los estados':'Todos os status','Ordenar':'Ordenar','Lead Score':'Lead Score',
    'Prob. Cierre':'Prob. Fechar','Valor':'Valor','Empresa / Contacto':'Empresa / Contato',
    'Estado IA':'Status IA','Razonamiento en tiempo real':'Raciocínio em tempo real',
    'Prospectando':'Prospectando','Calificando':'Qualificando','Outreach':'Outreach',
    'Negociando':'Negociando','Propuesta enviada':'Proposta enviada','Cierre':'Fechamento',
    'Ganado':'Ganho','En riesgo':'Em risco',
  },
  fr: {
    'Dashboard':'Tableau de bord','Escuadrones':'Escouades','Pipeline de Ventas':'Pipeline des ventes',
    'Agent Audit Log':'Agent Audit Log','Handoff · Slack IA':'Handoff · Slack IA',
    'Aprobaciones':'Approbations','Cerebro Neuronal':'Cerveau Neuronal',
    'SellIA · Command Center':'SellIA · Command Center','Súper Agente de Ventas B2B':'Super Agent Commercial B2B',
    'AGENTE ACTIVO':'AGENT ACTIF','capacidades':'capacités','salud':'santé',
    'vista':'vue','Inicializando command center…':'Initialisation command center…',
    'ROI GLOBAL':'ROI GLOBAL','LEADS PROCESADOS':'LEADS TRAITÉS',
    'TASA DE CONVERSIÓN':'TAUX DE CONVERSION','TICKET PROMEDIO':'TICKET MOYEN',
    'Buscar herramienta…':'Chercher outil…','Computer Use':'Computer Use','VOZ':'VOIX',
    'ESCUCHANDO':'À L\'ÉCOUTE','PERMISO…':'PERMISSION…','MIC OFF':'MIC OFF','N/A':'N/D',
    'Entrar':'Connexion','Cerrar sesión':'Déconnexion','Eliminar cuenta':'Supprimer le compte',
    'Crear cuenta gratis':'Créer compte gratuit','Iniciar sesión':'Se connecter','Cuenta desde':'Compte depuis',
    'Modo Computer Use':'Mode Computer Use','Abrir sesión':'Ouvrir session',
    'Manos libres activo':'Mains libres actif','Activar voz':'Activer voix',
    'Tu navegador no soporta voz':'Votre navigateur ne supporte pas la voix',
    'Permiso de mic denegado · revisar settings':'Permission micro refusée · vérifier paramètres',
    'Pidiendo permiso de micrófono…':'Demande de permission du microphone…',
    'Escuchando · decí "Hola SellIA"':'À l\'écoute · dites "Hola SellIA"',
    'Escuadrones SellIA':'Escouades SellIA','ejecutando':'en exécution','telemetría en vivo':'télémétrie en direct',
    'EJECUTANDO':'EN EXÉCUTION','EN REPOSO':'AU REPOS','PAUSADO':'EN PAUSE','ATENCIÓN':'ATTENTION',
    'SDR':'SDR','Prospección & ventas':'Prospection & ventes','Growth & Ads':'Growth & Ads',
    'Pauta paga · scaling':'Média payante · scaling','PR & Reputación':'PR & Réputation',
    'Social listening · brand':'Social listening · marque','Customer Success':'Customer Success',
    'Retención · soporte':'Rétention · support','Operaciones · navegador':'Opérations · navigateur',
    'Enviando secuencia outbound':'Envoi séquence outbound','Optimizando 3 campañas':'Optimisation de 3 campagnes',
    'Monitoreando 45 menciones LinkedIn':'Surveillance de 45 mentions LinkedIn',
    'En reposo · sin tickets nuevos':'Au repos · pas de nouveaux tickets','Esperando aprobación humana':'En attente d\'approbation humaine',
    'EMAILS 24H':'COURRIELS 24H','RESPUESTAS':'RÉPONSES','REPLY RATE':'TAUX DE RÉPONSE',
    'DEMOS BOOK':'DÉMOS RÉSERVÉES','ROAS':'ROAS','SPEND HOY':'DÉPENSES JOUR','CPC PROMEDIO':'CPC MOYEN',
    'CONVERSIONES':'CONVERSIONS','MENCIONES 7D':'MENTIONS 7J','SENTIMIENTO':'SENTIMENT',
    'REACH TOTAL':'PORTÉE TOTALE','RESPONDIDAS':'RÉPONDUES','TICKETS OPEN':'TICKETS OUVERTS',
    'TTR AVG':'TTR MOYEN','NPS ROLLING':'NPS GLISSANT','CSAT 7D':'CSAT 7J',
    'PIPELINE ACTIVO':'PIPELINE ACTIF',
    'TICKET MEDIO':'TICKET MOYEN',
    'Crecimiento & Ads':'Croissance & Ads','Crecimiento':'Croissance',
    'BILLETS OUVERTS':'TICKETS OUVERTS',
    'AVG':'MOY','PROMEDIO':'MOYEN',
    'TASA DE RESPUESTA':'TAUX DE RÉPONSE','TASA RESPUESTA':'TAUX RÉPONSE',
    'TAREAS HOY':'TÂCHES AUJOURD\'HUI','ÉXITO RATE':'TAUX SUCCÈS','PENDING HIL':'EN ATTENTE HIL',
    'TIEMPO AHORR':'TEMPS ÉCONOMISÉ','crítico':'critique','positivo':'positif',
    'Centro de Aprobaciones':'Centre d\'Approbations','Todas':'Toutes','Crítico':'Critique',
    'Alto':'Haute','Medio':'Moyenne','Bajo':'Basse','Aprobar':'Approuver','Rechazar':'Rejeter',
    'Procesando…':'Traitement…','Expandir todo':'Tout déplier','Colapsar todo':'Tout replier',
    'Sin decisiones pendientes':'Aucune décision en attente',
    'IA operando dentro de parámetros aprobados':'IA opérant dans les paramètres approuvés',
    'Justificación IA':'Justification IA','restante':'restant','expirado':'expiré',
    'Aumento de presupuesto':'Augmentation de budget','Descuento al cliente':'Remise client',
    'Envío masivo':'Envoi en masse','Exportación de datos':'Export de données',
    'Nueva integración / API':'Nouvelle intégration / API','Cambio de precio':'Changement de prix',
    'Compra autónoma':'Achat autonome',
    'Handoff Log · Slack IA':'Handoff Log · Slack IA','eventos':'événements','departamentos':'départements',
    'TODOS':'TOUS','Sin eventos para este filtro':'Aucun événement pour ce filtre',
    'Notificaciones':'Notifications','sin leer':'non lues','total':'total',
    'Sin notificaciones nuevas':'Aucune nouvelle notification','Marcar todas':'Tout marquer',
    'Ver todas':'Voir toutes','offline':'hors ligne',
    'modo local · backend offline':'mode local · backend hors ligne','live · polling 15s':'live · polling 15s',
    'Acción':'Action','Aprobación':'Approbation','Alerta':'Alerte','Info':'Info','Logro':'Réussite',
    'Configuración':'Paramètres','Tema':'Thème','Modo oscuro':'Mode sombre','Modo claro':'Mode clair',
    'Idioma':'Langue','Español':'Espagnol','Inglés':'Anglais','Portugués':'Portugais','Francés':'Français',
    'Cambios aplicados globalmente · guardados en este dispositivo':'Modifications appliquées globalement · sauvegardées sur cet appareil',
    'Cerebro Neuronal en Vivo':'Cerveau Neuronal en Direct','SINAPSIS ACTIVAS':'SYNAPSES ACTIVES',
    'Cerebro offline · reintentando…':'Cerveau hors ligne · nouvel essai…','Cerebro en reposo':'Cerveau au repos',
    'nodos':'nœuds','Skills':'Compétences','Agentes':'Agents','Automatizaciones':'Automatisations',
    'arrastrá para mover · scroll para zoom':'glisser pour déplacer · défilement pour zoom','último':'dernier',
    'Buscar empresa, contacto, industria…':'Chercher entreprise, contact, industrie…',
    'Todos los estados':'Tous les statuts','Ordenar':'Trier','Lead Score':'Score Lead',
    'Prob. Cierre':'Prob. Clôture','Valor':'Valeur','Empresa / Contacto':'Entreprise / Contact',
    'Estado IA':'Statut IA','Razonamiento en tiempo real':'Raisonnement en temps réel',
    'Prospectando':'Prospection','Calificando':'Qualification','Outreach':'Outreach',
    'Negociando':'Négociation','Propuesta enviada':'Proposition envoyée','Cierre':'Clôture',
    'Ganado':'Gagné','En riesgo':'À risque',
  },
}

// ── Cache helpers ──────────────────────────────────────────────────────────────
const loadCache = (): TranslationCache => {
  if (typeof window === 'undefined') return {}
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    return raw ? JSON.parse(raw) as TranslationCache : {}
  } catch { return {} }
}

const saveCache = (cache: TranslationCache): void => {
  try { localStorage.setItem(CACHE_KEY, JSON.stringify(cache)) } catch { /* noop */ }
}

// ── Translation guard (prevents observer loops from our own writes) ────────────
let writing = false

// ── Should translate this text node? ───────────────────────────────────────────
// Aggressive: translate almost everything. Only skip:
//   - pure numbers / symbols / whitespace
//   - timestamps (HH:MM, ISO dates)
//   - currency / percentages with only digits
//   - 1-char strings
//   - script/style content
const shouldSkipNode = (node: Text): boolean => {
  const text = node.nodeValue?.trim() ?? ''
  if (text.length < 2) return true
  // Pure numbers / symbols
  if (/^[\d\s\W_]+$/.test(text)) return true
  // Timestamps like 14:32 / 14:32:08 / 2026-06-01
  if (/^\d{1,4}([:\-/]\d{1,4})+$/.test(text)) return true
  // Currency / percentages / measurements with no letters
  if (/^[$€£¥]?[\d,.]+[%kKmMxX×]?$/.test(text)) return true
  // Standalone hex codes
  if (/^#[0-9a-fA-F]{3,8}$/.test(text)) return true

  const parent = node.parentElement
  if (!parent) return true

  const tag = parent.tagName.toLowerCase()
  if (['script', 'style', 'noscript'].includes(tag)) return true
  if (parent.isContentEditable) return true
  if (parent.closest('[data-no-translate]')) return true

  return false
}

// ── Walk DOM, collect text nodes ──────────────────────────────────────────────
const collectTextNodes = (root: Element): Text[] => {
  if (typeof document === 'undefined') return []
  const walker = document.createTreeWalker(
    root,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: (node: Node): number => {
        const t = node as Text
        return shouldSkipNode(t) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
      },
    },
  )
  const out: Text[] = []
  let n = walker.nextNode()
  while (n) {
    out.push(n as Text)
    n = walker.nextNode()
  }
  return out
}

// ── Walk DOM, collect elements with translatable attributes ───────────────────
interface AttrTarget { el: Element; attr: AttrName; value: string }

const collectAttrTargets = (root: Element): AttrTarget[] => {
  if (typeof document === 'undefined') return []
  const out: AttrTarget[] = []
  const isValid = (v: string): boolean => {
    if (v.length < 2) return false
    if (/^[\d\s\W_]+$/.test(v)) return false
    if (/^\d{1,4}([:\-/]\d{1,4})+$/.test(v)) return false
    return true
  }
  // Use querySelectorAll for each attr — fast
  for (const attr of ATTRS_TO_TRANSLATE) {
    const els = root.querySelectorAll(`[${attr}]`)
    els.forEach(el => {
      const v = el.getAttribute(attr) ?? ''
      if (!isValid(v)) return
      if (el.closest('[data-no-translate]')) return
      out.push({ el, attr, value: v })
    })
  }
  // Also check root element itself
  for (const attr of ATTRS_TO_TRANSLATE) {
    if (root.hasAttribute(attr)) {
      const v = root.getAttribute(attr) ?? ''
      if (isValid(v) && !root.closest('[data-no-translate]')) {
        out.push({ el: root, attr, value: v })
      }
    }
  }
  return out
}

// ── Stash originals for restoration ───────────────────────────────────────────
const stashTextOriginal = (node: Text): string => {
  const el = node as Text & { [ORIG_TEXT_KEY]?: string }
  if (el[ORIG_TEXT_KEY] === undefined) el[ORIG_TEXT_KEY] = node.nodeValue ?? ''
  return el[ORIG_TEXT_KEY]
}

const stashAttrOriginal = (el: Element, attr: AttrName, current: string): string => {
  const e = el as Element & { [ORIG_ATTR_KEY]?: Record<string, string> }
  if (!e[ORIG_ATTR_KEY]) e[ORIG_ATTR_KEY] = {}
  if (e[ORIG_ATTR_KEY][attr] === undefined) e[ORIG_ATTR_KEY][attr] = current
  return e[ORIG_ATTR_KEY][attr]
}

// ── Apply translations ────────────────────────────────────────────────────────
const applyTextTranslations = (
  nodeMap: Map<Text, string>,
  cache: { [src: string]: string },
): void => {
  writing = true
  try {
    for (const [node, orig] of nodeMap.entries()) {
      const t = cache[orig]
      if (t && t !== orig) {
        const lead = (node.nodeValue ?? '').match(/^\s*/)?.[0] ?? ''
        const tail = (node.nodeValue ?? '').match(/\s*$/)?.[0] ?? ''
        node.nodeValue = `${lead}${t}${tail}`
      }
    }
  } finally { writing = false }
}

const applyAttrTranslations = (
  attrTargets: AttrTarget[],
  cache: { [src: string]: string },
): void => {
  writing = true
  try {
    for (const { el, attr, value } of attrTargets) {
      const t = cache[value.trim()]
      if (t && t !== value.trim()) {
        el.setAttribute(attr, t)
      }
    }
  } finally { writing = false }
}

// ── Restore originals (lang back to es) ───────────────────────────────────────
const restoreOriginals = (root: Element): void => {
  writing = true
  try {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null)
    let n = walker.nextNode()
    while (n) {
      const el = n as Text & { [ORIG_TEXT_KEY]?: string }
      if (el[ORIG_TEXT_KEY] !== undefined) {
        n.nodeValue = el[ORIG_TEXT_KEY]
      }
      n = walker.nextNode()
    }
    // Restore attrs
    const elWalker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null)
    let e = elWalker.nextNode() as Element | null
    while (e) {
      const ee = e as Element & { [ORIG_ATTR_KEY]?: Record<string, string> }
      if (ee[ORIG_ATTR_KEY]) {
        for (const attr of ATTRS_TO_TRANSLATE) {
          if (ee[ORIG_ATTR_KEY][attr] !== undefined) {
            e.setAttribute(attr, ee[ORIG_ATTR_KEY][attr])
          }
        }
      }
      e = elWalker.nextNode() as Element | null
    }
  } finally { writing = false }
}

// ── Batch-translate via API ───────────────────────────────────────────────────
const translateBatch = async (lang: Lang, strings: string[]): Promise<string[]> => {
  try {
    const r = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lang, strings }),
    })
    if (!r.ok) return strings
    const data = (await r.json()) as { translations?: string[] }
    return data.translations ?? strings
  } catch {
    return strings
  }
}

const fetchMissing = async (
  lang: Lang,
  toTranslate: string[],
  langCache: { [src: string]: string },
  cache: TranslationCache,
  onProgress: () => void,
): Promise<void> => {
  for (let i = 0; i < toTranslate.length; i += BATCH_SIZE) {
    const batch = toTranslate.slice(i, i + BATCH_SIZE)
    const translated = await translateBatch(lang, batch)
    for (let j = 0; j < batch.length; j++) {
      langCache[batch[j]] = translated[j] ?? batch[j]
    }
    cache[lang] = langCache
    saveCache(cache)
    onProgress()
  }
}

// ── Translate subtree (used by both initial pass + observer) ──────────────────
const translateSubtree = async (lang: Lang, root: Element): Promise<void> => {
  const textNodes = collectTextNodes(root)
  const attrTargets = collectAttrTargets(root)

  if (textNodes.length === 0 && attrTargets.length === 0) return

  // Build text node map
  const nodeMap = new Map<Text, string>()
  const uniqueStrings = new Set<string>()

  for (const node of textNodes) {
    const orig = stashTextOriginal(node).trim()
    if (!orig) continue
    nodeMap.set(node, orig)
    uniqueStrings.add(orig)
  }

  // Build attr target list (stash originals)
  const trimmedAttrTargets: AttrTarget[] = []
  for (const t of attrTargets) {
    const orig = stashAttrOriginal(t.el, t.attr, t.value).trim()
    if (!orig) continue
    trimmedAttrTargets.push({ ...t, value: orig })
    uniqueStrings.add(orig)
  }

  const cache = loadCache()
  const langCache = cache[lang] ?? {}

  // Hydrate langCache with STATIC_DICT — authoritative, overwrites bad API caches
  const staticDict = lang === 'es' ? {} : (STATIC_DICT[lang as 'en' | 'pt' | 'fr'] ?? {})
  for (const [src, tgt] of Object.entries(staticDict)) {
    langCache[src] = tgt
  }

  const toTranslate: string[] = []
  for (const s of uniqueStrings) {
    if (!(s in langCache)) toTranslate.push(s)
  }

  // Apply cached first (fast paint — STATIC_DICT hits are instant)
  applyTextTranslations(nodeMap, langCache)
  applyAttrTranslations(trimmedAttrTargets, langCache)

  // Fetch missing
  if (toTranslate.length > 0) {
    await fetchMissing(lang, toTranslate, langCache, cache, () => {
      applyTextTranslations(nodeMap, langCache)
      applyAttrTranslations(trimmedAttrTargets, langCache)
    })
  }
}

// ── Main translate function ───────────────────────────────────────────────────
let observer: MutationObserver | null = null
let running = false

export const translateDocument = async (lang: Lang, root: Element = document.body): Promise<void> => {
  if (lang === 'es') {
    restoreOriginals(root)
    teardownObserver()
    return
  }

  if (running) return
  running = true
  try {
    await translateSubtree(lang, root)
    document.documentElement.lang = lang
    setupObserver(lang)
  } finally {
    running = false
  }
}

// ── MutationObserver for dynamic content ──────────────────────────────────────
const setupObserver = (lang: Lang): void => {
  if (typeof window === 'undefined') return
  teardownObserver()

  const pendingRoots = new Set<Element>()
  let debounceId: number | null = null

  const flush = (): void => {
    if (pendingRoots.size === 0) return
    const roots = [...pendingRoots]
    pendingRoots.clear()
    Promise.all(roots.map(r => translateSubtree(lang, r))).catch(() => { /* noop */ })
  }

  observer = new MutationObserver((mutations) => {
    if (writing) return // ignore our own writes

    for (const m of mutations) {
      // Added nodes → translate their subtree
      m.addedNodes.forEach(n => {
        if (n.nodeType === Node.ELEMENT_NODE) {
          pendingRoots.add(n as Element)
        } else if (n.nodeType === Node.TEXT_NODE && n.parentElement) {
          pendingRoots.add(n.parentElement)
        }
      })
      // Attribute changes (e.g. React setting a new placeholder)
      if (m.type === 'attributes' && m.target.nodeType === Node.ELEMENT_NODE) {
        pendingRoots.add(m.target as Element)
      }
      // Character data changes (React re-rendering existing text)
      if (m.type === 'characterData' && m.target.parentElement) {
        pendingRoots.add(m.target.parentElement)
      }
    }

    if (debounceId) window.clearTimeout(debounceId)
    debounceId = window.setTimeout(flush, 220)
  })

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: [...ATTRS_TO_TRANSLATE],
  })
}

const teardownObserver = (): void => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
}
