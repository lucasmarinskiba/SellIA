'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BusinessContext, WizardState, businessContextApi } from '@/lib/businessContext'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { CheckCircle, ChevronRight, ChevronLeft, Building2, MapPin, Share2, Megaphone, Truck, Sparkles } from 'lucide-react'

interface BusinessContextWizardProps {
  contextId: string
  onComplete: () => void
}

const BUSINESS_TYPES = [
  { value: 'physical_products', label: 'Productos Físicos', icon: '📦' },
  { value: 'digital_products', label: 'Productos Digitales', icon: '💾' },
  { value: 'services', label: 'Servicios Profesionales', icon: '🔧' },
  { value: 'consulting', label: 'Consultoría / Coaching', icon: '🎯' },
  { value: 'software', label: 'Software / Apps / SaaS', icon: '💻' },
  { value: 'food_beverage', label: 'Restaurante / Comida', icon: '🍔' },
  { value: 'fashion_beauty', label: 'Moda / Belleza', icon: '👗' },
  { value: 'health_wellness', label: 'Salud / Bienestar', icon: '💪' },
  { value: 'home_decor', label: 'Hogar / Decoración', icon: '🏠' },
  { value: 'handcraft', label: 'Artesanías / Hecho a mano', icon: '🎨' },
  { value: 'other', label: 'Otro', icon: '❓' },
]

const SALES_MODELS = [
  { value: 'b2c', label: 'B2C — Vendo al consumidor final' },
  { value: 'b2b', label: 'B2B — Vendo a empresas' },
  { value: 'b2b2c', label: 'B2B2C — Híbrido' },
  { value: 'd2c', label: 'D2C — Marca propia directa' },
  { value: 'marketplace', label: 'Marketplace — Vendo en plataformas' },
]

const REACH_OPTIONS = [
  { value: 'local', label: 'Mi barrio / ciudad', desc: 'Vendo localmente' },
  { value: 'regional', label: 'Mi provincia / región', desc: 'Cobertura regional' },
  { value: 'national', label: 'Todo mi país', desc: 'Envío nacional' },
  { value: 'cross_border', label: 'Países vecinos', desc: 'Latam expansion' },
  { value: 'global', label: 'El mundo entero', desc: 'Global shipping' },
]

const PRESENCE_TYPES = [
  { value: 'local_physical', label: 'Tengo local físico', desc: 'Tienda / showroom' },
  { value: 'home_office', label: 'Home office', desc: 'Trabajo desde casa' },
  { value: 'showroom', label: 'Showroom / Atelier', desc: 'Solo exhibición' },
  { value: 'online_only', label: '100% Online', desc: 'Sin presencia física' },
  { value: 'hybrid', label: 'Híbrido', desc: 'Online + físico' },
]

const CHANNEL_OPTIONS = [
  'instagram', 'facebook', 'whatsapp', 'tiktok', 'linkedin',
  'shopify', 'mercadolibre', 'amazon', 'etsy', 'youtube'
]

const ADS_OPTIONS = ['meta_ads', 'google_ads', 'tiktok_ads']

const SHIPPING_OPTIONS = ['andreani', 'dhl', 'fedex', 'ups', 'oca', 'correo_argentino']

export default function BusinessContextWizard({ contextId, onComplete }: BusinessContextWizardProps) {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<Partial<BusinessContext>>({})

  const updateField = (field: string, value: any) => {
    setData(prev => ({ ...prev, [field]: value }))
  }

  const toggleMulti = (field: string, value: string) => {
    setData(prev => {
      const current = (prev as any)[field] as Record<string, boolean> || {}
      return { ...prev, [field]: { ...current, [value]: !current[value] } }
    })
  }

  const handleNext = async () => {
    setLoading(true)
    try {
      await businessContextApi.saveWizardStep(step, data, contextId)
      if (step >= 5) {
        onComplete()
      } else {
        setStep(s => s + 1)
        setData({})
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleBack = () => setStep(s => Math.max(1, s - 1))

  const stepIcons = [Building2, MapPin, Share2, Megaphone, Truck]
  const StepIcon = stepIcons[step - 1]

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
    >
      <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-[#0c0e1a] border border-white/10 rounded-3xl shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-[#0c0e1a]/95 backdrop-blur-md border-b border-white/5 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-orange/10 flex items-center justify-center text-brand-orange">
                <StepIcon className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Configura tu Negocio</h2>
                <p className="text-xs text-white/40">Paso {step} de 5</p>
              </div>
            </div>
            <button onClick={onComplete} className="text-white/30 hover:text-white/60">
              ✕
            </button>
          </div>
          <div className="flex gap-1.5">
            {[1, 2, 3, 4, 5].map(s => (
              <div
                key={s}
                className={`h-1 flex-1 rounded-full transition-all ${
                  s <= step ? 'bg-brand-orange' : 'bg-white/10'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                <h3 className="text-white font-semibold">¿Qué tipo de negocio tenés?</h3>
                <div className="grid grid-cols-2 gap-3">
                  {BUSINESS_TYPES.map(bt => (
                    <button
                      key={bt.value}
                      onClick={() => updateField('business_type', bt.value)}
                      className={`p-3 rounded-xl border text-left transition-all ${
                        data.business_type === bt.value
                          ? 'border-brand-orange/30 bg-brand-orange/10'
                          : 'border-white/5 bg-white/5 hover:bg-white/10'
                      }`}
                    >
                      <span className="text-xl mr-2">{bt.icon}</span>
                      <span className="text-sm text-white/80">{bt.label}</span>
                    </button>
                  ))}
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-white/40">Modelo de venta</label>
                  <select
                    value={data.sales_model || ''}
                    onChange={e => updateField('sales_model', e.target.value)}
                    className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {SALES_MODELS.map(sm => (
                      <option key={sm.value} value={sm.value}>{sm.label}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-white/40">Industria / Nicho</label>
                  <input
                    type="text"
                    placeholder="Ej: Indumentaria femenina, desarrollo web..."
                    value={data.industry || ''}
                    onChange={e => updateField('industry', e.target.value)}
                    className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/20"
                  />
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                <h3 className="text-white font-semibold">¿Dónde operás y a dónde querés llegar?</h3>
                <div className="space-y-2">
                  <label className="text-sm text-white/40">Alcance geográfico objetivo</label>
                  <div className="grid grid-cols-1 gap-2">
                    {REACH_OPTIONS.map(ro => (
                      <button
                        key={ro.value}
                        onClick={() => updateField('geographic_reach', ro.value)}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          data.geographic_reach === ro.value
                            ? 'border-brand-orange/30 bg-brand-orange/10'
                            : 'border-white/5 bg-white/5 hover:bg-white/10'
                        }`}
                      >
                        <div className="text-sm text-white/80 font-medium">{ro.label}</div>
                        <div className="text-xs text-white/30">{ro.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-white/40">Tipo de presencia</label>
                  <div className="grid grid-cols-2 gap-2">
                    {PRESENCE_TYPES.map(pt => (
                      <button
                        key={pt.value}
                        onClick={() => updateField('presence_type', pt.value)}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          data.presence_type === pt.value
                            ? 'border-brand-orange/30 bg-brand-orange/10'
                            : 'border-white/5 bg-white/5 hover:bg-white/10'
                        }`}
                      >
                        <div className="text-sm text-white/80">{pt.label}</div>
                        <div className="text-xs text-white/30">{pt.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <label className="text-sm text-white/40">Ciudad</label>
                    <input
                      type="text"
                      value={data.city || ''}
                      onChange={e => updateField('city', e.target.value)}
                      className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-white/40">País</label>
                    <input
                      type="text"
                      value={data.country || 'Argentina'}
                      onChange={e => updateField('country', e.target.value)}
                      className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm"
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                <h3 className="text-white font-semibold">¿Qué canales ya tenés activos?</h3>
                <div className="flex flex-wrap gap-2">
                  {CHANNEL_OPTIONS.map(ch => (
                    <button
                      key={ch}
                      onClick={() => toggleMulti('channels_configured', ch)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize ${
                        (data.channels_configured as any)?.[ch]
                          ? 'bg-brand-orange/20 text-brand-orange border border-brand-orange/20'
                          : 'bg-white/5 text-white/40 border border-white/5 hover:bg-white/10'
                      }`}
                    >
                      {(data.channels_configured as any)?.[ch] && <CheckCircle className="w-3 h-3 inline mr-1" />}
                      {ch}
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                  <input
                    type="checkbox"
                    id="website"
                    checked={data.website_configured || false}
                    onChange={e => updateField('website_configured', e.target.checked)}
                    className="w-4 h-4 rounded border-white/20"
                  />
                  <label htmlFor="website" className="text-sm text-white/80">Tengo sitio web propio</label>
                </div>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div key="step4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                <h3 className="text-white font-semibold">¿Ya invertís en marketing?</h3>
                <div className="space-y-2">
                  <label className="text-sm text-white/40">Plataformas de ads activas</label>
                  <div className="flex flex-wrap gap-2">
                    {ADS_OPTIONS.map(ad => (
                      <button
                        key={ad}
                        onClick={() => toggleMulti('ads_configured', ad)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize ${
                          (data.ads_configured as any)?.[ad]
                            ? 'bg-brand-violet/20 text-brand-violet border border-brand-violet/20'
                            : 'bg-white/5 text-white/40 border border-white/5 hover:bg-white/10'
                        }`}
                      >
                        {(data.ads_configured as any)?.[ad] && <CheckCircle className="w-3 h-3 inline mr-1" />}
                        {ad.replace('_', ' ')}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                    <input
                      type="checkbox"
                      id="seo"
                      checked={data.seo_configured || false}
                      onChange={e => updateField('seo_configured', e.target.checked)}
                      className="w-4 h-4 rounded border-white/20"
                    />
                    <label htmlFor="seo" className="text-sm text-white/80">SEO configurado</label>
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                    <input
                      type="checkbox"
                      id="email"
                      checked={data.email_marketing_configured || false}
                      onChange={e => updateField('email_marketing_configured', e.target.checked)}
                      className="w-4 h-4 rounded border-white/20"
                    />
                    <label htmlFor="email" className="text-sm text-white/80">Email marketing</label>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-white/40">Objetivo principal</label>
                  <select
                    value={data.primary_goal || ''}
                    onChange={e => updateField('primary_goal', e.target.value)}
                    className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    <option value="more_sales">Más ventas</option>
                    <option value="more_leads">Más leads</option>
                    <option value="more_traffic">Más tráfico</option>
                    <option value="brand_awareness">Posicionar marca</option>
                    <option value="expansion">Expandirme</option>
                  </select>
                </div>
              </motion.div>
            )}

            {step === 5 && (
              <motion.div key="step5" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                <h3 className="text-white font-semibold">¿Cómo entregás?</h3>
                <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                  <input
                    type="checkbox"
                    id="delivery"
                    checked={data.does_delivery || false}
                    onChange={e => updateField('does_delivery', e.target.checked)}
                    className="w-4 h-4 rounded border-white/20"
                  />
                  <label htmlFor="delivery" className="text-sm text-white/80">Hago envíos a domicilio</label>
                </div>
                {data.does_delivery && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-3">
                    <label className="text-sm text-white/40">Carriers configurados</label>
                    <div className="flex flex-wrap gap-2">
                      {SHIPPING_OPTIONS.map(sh => (
                        <button
                          key={sh}
                          onClick={() => toggleMulti('shipping_configured', sh)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize ${
                            (data.shipping_configured as any)?.[sh]
                              ? 'bg-brand-teal/20 text-brand-teal border border-brand-teal/20'
                              : 'bg-white/5 text-white/40 border border-white/5 hover:bg-white/10'
                          }`}
                        >
                          {(data.shipping_configured as any)?.[sh] && <CheckCircle className="w-3 h-3 inline mr-1" />}
                          {sh.replace('_', ' ')}
                        </button>
                      ))}
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm text-white/40">Radio de envío (km)</label>
                      <input
                        type="number"
                        value={data.shipping_radius_km || ''}
                        onChange={e => updateField('shipping_radius_km', parseInt(e.target.value) || 0)}
                        className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm"
                      />
                    </div>
                  </motion.div>
                )}
                <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                  <input
                    type="checkbox"
                    id="pickup"
                    checked={data.does_pickup || false}
                    onChange={e => updateField('does_pickup', e.target.checked)}
                    className="w-4 h-4 rounded border-white/20"
                  />
                  <label htmlFor="pickup" className="text-sm text-white/80">Permito retiro en persona</label>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 z-10 bg-[#0c0e1a]/95 backdrop-blur-md border-t border-white/5 p-6 flex justify-between">
          <Button variant="secondary" onClick={handleBack} disabled={step === 1 || loading}>
            <ChevronLeft className="w-4 h-4 mr-1" />
            Atrás
          </Button>
          <Button onClick={handleNext} disabled={loading}>
            {loading ? (
              <Sparkles className="w-4 h-4 animate-spin mr-2" />
            ) : step === 5 ? (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                Finalizar
              </>
            ) : (
              <>
                Siguiente
                <ChevronRight className="w-4 h-4 ml-1" />
              </>
            )}
          </Button>
        </div>
      </div>
    </motion.div>
  )
}
