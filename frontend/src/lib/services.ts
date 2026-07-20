import { api } from './api'

export interface ServiceItemConfig {
  modalities: string[]
  solution_types: string[]
  duration_minutes: number
  buffer_minutes: number
  requires_prep: boolean
  materials_needed: string[]
  prerequisites: string[]
  service_area_km: number | null
  travel_included: boolean
  online_meeting_link: string | null
  cancellation_policy_hours: number
  reschedule_policy_hours: number
}

export interface ServiceDelivery {
  id: string
  business_id: string
  order_id: string
  catalog_item_id: string | null
  conversation_id: string | null
  scheduled_at: string | null
  started_at: string | null
  completed_at: string | null
  cancelled_at: string | null
  modality: string | null
  solution_type: string | null
  status: string
  location_address: Record<string, any>
  meeting_url: string | null
  provider_notes: string | null
  client_feedback: string | null
  client_rating: number | null
  materials_used: Record<string, any>[]
  diagnosis: Record<string, any>
  follow_up_required: boolean
  follow_up_notes: string | null
  reminders_sent: Record<string, any>[]
  estimated_duration_minutes: number | null
  actual_duration_minutes: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Appointment {
  id: string
  business_id: string
  service_delivery_id: string | null
  order_id: string | null
  conversation_id: string | null
  client_name: string | null
  client_email: string | null
  client_phone: string | null
  start_time: string
  end_time: string
  timezone: string
  modality: string | null
  solution_type: string | null
  service_name: string | null
  location_address: Record<string, any>
  meeting_url: string | null
  status: string
  reminder_sent_at: string | null
  confirmation_sent_at: string | null
  confirmation_received_at: string | null
  feedback_sent_at: string | null
  feedback_received_at: string | null
  provider_notes: string | null
  preparation_notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export const MODALITY_LABELS: Record<string, string> = {
  home_office: 'Home Office',
  client_office: 'Oficina del cliente',
  client_home: 'Casa del cliente',
  provider_office: 'Mi oficina',
  hybrid: 'Híbrido',
  remote: 'Remoto / Online',
  on_site: 'En sitio',
}

export const SOLUTION_TYPE_LABELS: Record<string, string> = {
  temporary: 'Temporal',
  definitive: 'Definitiva',
  contingency: 'Contingencia',
  analytical: 'Analítica',
  heuristic: 'Heurística',
  creative: 'Creativa',
  architectural: 'Arquitectónica',
  design: 'Diseño',
  implementation: 'Implementación',
  preventive: 'Preventiva',
  corrective: 'Correctiva',
  structural: 'Estructural',
  installation: 'Instalación',
  diagnostic: 'Diagnóstico',
  protection: 'Protección',
  automation: 'Automatización',
  comfort: 'Confort',
  psychological: 'Psicológica',
  advisory: 'Asesoramiento',
  emotional: 'Emocional',
  behavioral: 'Conductual',
  guidance: 'Orientación',
  relief: 'Alivio',
  causality: 'Causalidad',
  ritual: 'Ritual',
  meaning: 'Sentido',
  community: 'Comunidad',
  moral: 'Moral',
  consolation: 'Consuelo',
}

export const APPOINTMENT_STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  confirmed: 'Confirmada',
  completed: 'Completada',
  cancelled: 'Cancelada',
  no_show: 'No asistió',
}

export const DELIVERY_STATUS_LABELS: Record<string, string> = {
  scheduled: 'Agendada',
  confirmed: 'Confirmada',
  reminded: 'Recordada',
  in_progress: 'En progreso',
  paused: 'Pausada',
  completed: 'Completada',
  cancelled: 'Cancelada',
  no_show: 'No asistió',
  rescheduled: 'Reagendada',
}

export const servicesApi = {
  // Service Deliveries
  getDeliveries: (businessId: string, params?: { status?: string; order_id?: string; limit?: number; offset?: number }) =>
    api.get<{ items: ServiceDelivery[]; total: number }>('/services/deliveries', { params: { business_id: businessId, ...params } }).then(r => r.data),

  createDelivery: (data: { order_id: string; catalog_item_id?: string; conversation_id?: string; scheduled_at?: string; modality?: string; solution_type?: string; location_address?: Record<string, any>; meeting_url?: string; estimated_duration_minutes?: number }) =>
    api.post<ServiceDelivery>('/services/deliveries', data).then(r => r.data),

  updateDelivery: (id: string, data: Partial<ServiceDelivery>) =>
    api.patch<ServiceDelivery>(`/services/deliveries/${id}`, data).then(r => r.data),

  completeDelivery: (id: string) =>
    api.post<{ success: boolean; message: string; service_delivery?: ServiceDelivery }>(`/services/deliveries/${id}/complete`).then(r => r.data),

  cancelDelivery: (id: string) =>
    api.post<{ success: boolean; message: string; service_delivery?: ServiceDelivery }>(`/services/deliveries/${id}/cancel`).then(r => r.data),

  // Appointments
  getAppointments: (businessId: string, params?: { status?: string; from_date?: string; to_date?: string; limit?: number; offset?: number }) =>
    api.get<{ items: Appointment[]; total: number }>('/services/appointments', { params: { business_id: businessId, ...params } }).then(r => r.data),

  getCalendar: (businessId: string, from_date: string, to_date: string) =>
    api.get<{ items: Appointment[]; total: number }>('/services/appointments/calendar', { params: { business_id: businessId, from_date, to_date } }).then(r => r.data),

  createAppointment: (data: { service_delivery_id?: string; order_id?: string; conversation_id?: string; client_name?: string; client_email?: string; client_phone?: string; start_time: string; end_time: string; timezone?: string; modality?: string; solution_type?: string; service_name?: string; location_address?: Record<string, any>; meeting_url?: string; preparation_notes?: string }) =>
    api.post<Appointment>('/services/appointments', data).then(r => r.data),

  updateAppointment: (id: string, data: Partial<Appointment>) =>
    api.patch<Appointment>(`/services/appointments/${id}`, data).then(r => r.data),

  confirmAppointment: (id: string) =>
    api.post<{ success: boolean; message: string; appointment?: Appointment }>(`/services/appointments/${id}/confirm`).then(r => r.data),

  completeAppointment: (id: string) =>
    api.post<{ success: boolean; message: string; appointment?: Appointment }>(`/services/appointments/${id}/complete`).then(r => r.data),

  cancelAppointment: (id: string) =>
    api.post<{ success: boolean; message: string; appointment?: Appointment }>(`/services/appointments/${id}/cancel`).then(r => r.data),

  markNoShow: (id: string) =>
    api.post<{ success: boolean; message: string; appointment?: Appointment }>(`/services/appointments/${id}/no-show`).then(r => r.data),

  sendReminder: (id: string, channel?: string) =>
    api.post(`/services/appointments/${id}/send-reminder`, null, { params: channel ? { channel } : undefined }).then(r => r.data),

  requestConfirmation: (id: string, channel?: string) =>
    api.post(`/services/appointments/${id}/request-confirmation`, null, { params: channel ? { channel } : undefined }).then(r => r.data),

  requestFeedback: (id: string, channel?: string) =>
    api.post(`/services/appointments/${id}/request-feedback`, null, { params: channel ? { channel } : undefined }).then(r => r.data),
}
