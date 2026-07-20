import { api } from './api'

export interface Address {
  name: string
  company?: string
  street: string
  city: string
  state: string
  zip: string
  country: string
  phone?: string
  email?: string
}

export interface PackageItem {
  name: string
  qty: number
  sku?: string
}

export interface Package {
  weight_kg: number
  length_cm?: number
  width_cm?: number
  height_cm?: number
  items: PackageItem[]
  description?: string
}

export interface ShipmentConfig {
  id: string
  business_id: string
  carrier: string
  label: string | null
  is_test_mode: boolean
  is_active: boolean
  default_service_type: string | null
  default_from_address: Address | null
  created_at: string
  updated_at: string
}

export interface ShipmentTrackingEvent {
  id: string
  shipment_id: string
  event_code: string | null
  event_description: string
  location: string | null
  carrier_status: string | null
  event_at: string
  created_at: string
}

export interface Shipment {
  id: string
  business_id: string
  order_id: string
  config_id: string | null
  carrier: string
  service_type: string
  status: string
  tracking_number: string | null
  tracking_url: string | null
  label_url: string | null
  from_address: Address
  to_address: Address
  package: Package
  shipping_cost: number | null
  insurance_amount: number | null
  declared_value: number | null
  estimated_delivery_date: string | null
  actual_delivery_date: string | null
  picked_up_at: string | null
  customer_notified_at: string | null
  notification_channel: string | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ShipmentDetail extends Shipment {
  tracking_events: ShipmentTrackingEvent[]
}

export interface CarrierInfo {
  id: string
  name: string
  label: string
  country: string
  service_types: string[]
  features: string[]
  icon: string | null
}

export interface ShipmentListResponse {
  items: Shipment[]
  total: number
  limit: number
  offset: number
}

export const shipmentsApi = {
  // Carriers
  getCarriers: () => api.get<CarrierInfo[]>('/shipments/carriers').then(r => r.data),

  // Configs
  getConfigs: (businessId: string) =>
    api.get<ShipmentConfig[]>('/shipments/configs', { params: { business_id: businessId } }).then(r => r.data),

  createConfig: (businessId: string, data: Omit<ShipmentConfig, 'id' | 'business_id' | 'created_at' | 'updated_at'>) =>
    api.post<ShipmentConfig>('/shipments/configs', data, { params: { business_id: businessId } }).then(r => r.data),

  updateConfig: (configId: string, data: Partial<ShipmentConfig>) =>
    api.patch<ShipmentConfig>(`/shipments/configs/${configId}`, data).then(r => r.data),

  deleteConfig: (configId: string) =>
    api.delete(`/shipments/configs/${configId}`).then(r => r.data),

  testConfig: (configId: string) =>
    api.post(`/shipments/configs/${configId}/test`).then(r => r.data),

  // Shipments
  getShipments: (businessId: string, params?: { status?: string; carrier?: string; search?: string; limit?: number; offset?: number }) =>
    api.get<ShipmentListResponse>('/shipments', { params: { business_id: businessId, ...params } }).then(r => r.data),

  createShipment: (data: {
    order_id: string;
    config_id?: string;
    carrier: string;
    service_type?: string;
    from_address?: Address;
    to_address?: Address;
    package: Package;
    shipping_cost?: number;
    insurance_amount?: number;
    declared_value?: number;
    estimated_delivery_date?: string;
    notes?: string;
    auto_generate_label?: boolean;
    notify_customer?: boolean;
    notification_channel?: string;
  }) =>
    api.post<Shipment>('/shipments', data).then(r => r.data),

  getShipment: (id: string) =>
    api.get<ShipmentDetail>(`/shipments/${id}`).then(r => r.data),

  updateShipment: (id: string, data: Partial<Shipment>) =>
    api.patch<Shipment>(`/shipments/${id}`, data).then(r => r.data),

  deleteShipment: (id: string) =>
    api.delete(`/shipments/${id}`).then(r => r.data),

  refreshTracking: (id: string) =>
    api.post<{ success: boolean; new_events_count: number; current_status: string; message: string }>(`/shipments/${id}/refresh-tracking`).then(r => r.data),

  notifyCustomer: (id: string, channel?: string) =>
    api.post<{ success: boolean; channel: string | null; message: string }>(`/shipments/${id}/notify-customer`, null, { params: channel ? { channel } : undefined }).then(r => r.data),
}
