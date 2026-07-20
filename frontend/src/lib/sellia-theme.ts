/**
 * SELLIA · Paleta corporativa FIJA
 *
 * Única fuente de verdad de color/tipografía para toda la interfaz de SellIA
 * (Command Center, sidebar, NeuralBrain, paneles). Enterprise SaaS dark mode:
 * slate/navy profundo, azul corporativo + verde de éxito. Sobrio, NO videojuego.
 *
 * Importar SIEMPRE desde acá. No hardcodear colores sueltos en componentes.
 */

export const SELLIA = {
  // superficies
  bg: '#0A0F1A', // navy/slate base
  panel: '#0F1722', // card surface
  panelAlt: '#131C2B', // raised / hover
  border: 'rgba(255,255,255,0.10)',
  borderStrong: 'rgba(255,255,255,0.16)',

  // texto
  text: '#E6EAF2',
  text2: '#9AA7BD',
  text3: '#5C6B85',

  // acentos corporativos
  cobalt: '#3B82F6', // azul corporativo (primario)
  cobaltDk: '#2563EB',
  emerald: '#10B981', // éxito / métricas positivas
  amber: '#F59E0B', // atención
  red: '#EF4444', // riesgo

  // tipografía
  mono: "'JetBrains Mono', ui-monospace, monospace",
  sans: "'Inter', ui-sans-serif, system-ui, sans-serif",
} as const

/** Color por tipo de capability en el NeuralBrain (dentro de la paleta fija). */
export const KIND_COLOR: Record<string, string> = {
  agent: SELLIA.cobalt,
  skill: SELLIA.text2,
  knowledge: SELLIA.text2,
  automation: SELLIA.emerald,
  platform: SELLIA.amber,
  computer_use: SELLIA.amber,
  db: SELLIA.cobaltDk,
  function: SELLIA.cobalt,
}

/** Color por capa del grafo (platforms → skills → agents → automations). */
export const LAYER_COLOR: Record<number, string> = {
  0: SELLIA.amber, // platforms (canales/integraciones)
  1: SELLIA.text2, // skills
  2: SELLIA.cobalt, // agents
  3: SELLIA.emerald, // automations
}

/** Color por categoría (group) — mapa de interacciones. Dentro de la paleta fija. */
export const GROUP_COLOR: Record<string, string> = {
  // plataformas
  ventas: '#10B981',        // emerald
  publicacion: '#8B5CF6',   // violet
  anuncios: '#F59E0B',      // amber
  mensajeria: '#3B82F6',    // cobalt
  pagos: '#22D3EE',         // cyan
  fiscal: '#94A3B8',        // slate
  web: '#64748B',
  crm: '#14B8A6',           // teal
  finanzas: '#EAB308',      // gold
  // agentes
  captacion: '#3B82F6',
  conversion: '#6366F1',
  retencion: '#10B981',
  experto: '#0EA5E9',
  leyenda: '#A855F7',
  // automatizaciones
  adquisicion: '#3B82F6',
  core: '#94A3B8',
  // skills / tools
  creatividad: '#EC4899',   // pink
  analisis: '#F59E0B',
  chat: '#3B82F6',
  datos: '#22D3EE',
  seo: '#84CC16',           // lime
  conocimiento: '#9AA7BD',
}

export const GROUP_LABEL: Record<string, string> = {
  ventas: 'Ventas', publicacion: 'Publicación', anuncios: 'Anuncios',
  mensajeria: 'Mensajería', pagos: 'Pagos', fiscal: 'Fiscal', web: 'Web',
  crm: 'CRM/Integraciones', finanzas: 'Finanzas',
  captacion: 'Captación', conversion: 'Conversión', retencion: 'Retención',
  experto: 'Experto', leyenda: 'Leyenda', adquisicion: 'Adquisición', core: 'Core',
  creatividad: 'Creatividad', analisis: 'Análisis', chat: 'Chat',
  datos: 'Datos/CRM', seo: 'SEO', conocimiento: 'Conocimiento',
}

export type SelliaPalette = typeof SELLIA
