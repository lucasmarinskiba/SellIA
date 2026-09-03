'use client'

/**
 * Deep-view renderers for each transformation stage artifact.
 * A tailored layout per stage; anything not explicitly handled falls through
 * to a raw key/value dump so nothing is hidden.
 */
import { Fragment } from 'react'

const box = 'rounded-lg border border-white/10 bg-white/[0.03] p-3'
const label = 'text-[11px] font-semibold uppercase tracking-wide text-white/40'
const chip = 'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium'

const S = (v: any): string =>
  v == null ? '—' : typeof v === 'string' ? v : Array.isArray(v) ? v.map(S).join(', ') : JSON.stringify(v)

function KV({ k, v }: { k: string; v: any }) {
  if (v == null || (Array.isArray(v) && !v.length)) return null
  return (
    <div>
      <p className={label}>{k.replace(/_/g, ' ')}</p>
      <div className="text-sm text-white/80">{typeof v === 'object' && !Array.isArray(v) ? <Raw data={v} /> : Array.isArray(v) ? <Bullets items={v} /> : String(v)}</div>
    </div>
  )
}

function Bullets({ items }: { items: any[] }) {
  return (
    <ul className="space-y-1">
      {items.map((it, i) => (
        <li key={i} className="flex gap-2 text-sm text-white/80">
          <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-white/30" />
          <span>{typeof it === 'object' ? <Raw data={it} /> : String(it)}</span>
        </li>
      ))}
    </ul>
  )
}

function Raw({ data }: { data: any }) {
  if (data == null) return <span className="text-white/40">—</span>
  if (typeof data !== 'object') return <span>{String(data)}</span>
  if (Array.isArray(data)) return <Bullets items={data} />
  return (
    <div className="space-y-1.5">
      {Object.entries(data).map(([k, v]) => (
        <KV key={k} k={k} v={v} />
      ))}
    </div>
  )
}

function Table({ rows, cols }: { rows: any[]; cols: string[] }) {
  if (!rows?.length) return null
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="text-white/40">
            {cols.map((c) => (
              <th key={c} className="px-2 py-1 font-semibold uppercase tracking-wide">
                {c.replace(/_/g, ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-white/10 align-top text-white/80">
              {cols.map((c) => (
                <td key={c} className="px-2 py-1.5">
                  {typeof r?.[c] === 'object' ? <Raw data={r[c]} /> : S(r?.[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Bars({ scores }: { scores: Record<string, any> }) {
  const entries = Object.entries(scores || {}).filter(([, v]) => typeof v === 'number')
  if (!entries.length) return null
  return (
    <div className="space-y-1.5">
      {entries.map(([k, v]) => (
        <div key={k} className="flex items-center gap-2 text-xs">
          <span className="w-32 shrink-0 text-white/50">{k.replace(/_/g, ' ')}</span>
          <div className="h-2 flex-1 rounded-full bg-white/10">
            <div
              className="h-2 rounded-full bg-primary"
              style={{ width: `${(Number(v) / 5) * 100}%` }}
            />
          </div>
          <span className="w-6 text-right text-white/60">{v}</span>
        </div>
      ))}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  if (!children) return null
  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold text-white/80">{title}</p>
      {children}
    </div>
  )
}

const HANDLED: Record<string, string[]> = {
  positioning: [
    'positioning_statement', 'one_liner', 'elevator_pitch', 'the_enemy', 'enemy_analysis',
    'point_of_view', 'pov_validation', 'category_decision', 'reframe', 'messaging_pillars',
    'alternatives_matrix', 'attribute_value_proof', 'migration_risks', 'alternative_angles',
    'best_fit_customers', 'market_category', 'new_category_name', 'competitive_alternatives',
    'unique_attributes', 'value_themes', 'confidence', 'frameworks_applied', 'generated_by',
    'id', 'business_id', 'created_at', 'deployed_competitive',
  ],
  brand_identity: [
    'primary_archetype', 'secondary_archetype', 'archetype_analysis', 'tagline', 'taglines_alt',
    'manifesto', 'story_spine', 'verbal_identity', 'sample_rewrites', 'naming', 'visual_brief',
    'brand_architecture', 'identity_consistency_rules', 'alternative_angles', 'rename_recommended',
    'name_candidates', 'voice_attributes', 'voice_do', 'voice_dont',
    'confidence', 'frameworks_applied', 'generated_by', 'id', 'business_id', 'created_at', 'deployed_assets',
  ],
  business_model: [
    'model_diagnosis', 'pattern_evaluation', 'applied_patterns', 'canvas', 'canvas_changes',
    'value_equation', 'grand_slam_offer', 'pricing_architecture', 'pricing_migration',
    'unit_economics_targets', 'errc_grid', 'rollout', 'risks', 'new_revenue_streams', 'rationale',
    'alternative_angles', 'confidence', 'frameworks_applied', 'generated_by', 'id', 'business_id', 'created_at',
  ],
  fomo_engine: [
    'lever_selection', 'mechanisms', 'ethics_review', 'activation_sequence', 'launch_ritual',
    'cadence', 'content_hooks', 'measurement', 'integration_notes', 'risk_matrix', 'risk_notes',
    'alternative_angles', 'deployed_campaigns', 'confidence', 'frameworks_applied', 'generated_by',
    'id', 'business_id', 'created_at',
  ],
  gtm: [
    'loop_evaluation', 'primary_growth_loop', 'channel_plan', 'channels', 'lightning_strike',
    'content_engine', 'content_pillars', 'funnel', 'plan_90_days', 'week_1_actions', 'budget_shape',
    'north_star_metric', 'anti_goals', 'alternative_angles', 'confidence', 'frameworks_applied',
    'generated_by', 'id', 'business_id', 'created_at',
  ],
  restructuring: [
    'kill', 'keep', 'scale', 'capability_gaps', 'the_one_hire', 'org_redesign', 'decision_rights',
    'core_processes', 'operating_rhythm', 'promise_kpis', 'unit_economics_gate', 'unit_economics_notes',
    'operating_plan_90d', 'transition_risks', 'alternative_angles', 'confidence', 'frameworks_applied',
    'generated_by', 'id', 'business_id', 'created_at',
  ],
}

export function StageArtifact({ stageKey, artifact }: { stageKey: string; artifact: Record<string, any> }) {
  const a = artifact || {}
  const rest = Object.entries(a).filter(([k]) => !(HANDLED[stageKey] || []).includes(k) && a[k] != null)

  return (
    <div className="space-y-4">
      {(a.confidence != null || a.generated_by) && (
        <div className="flex flex-wrap gap-2">
          {a.generated_by && (
            <span className={`${chip} ${a.generated_by === 'llm' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-white/10 text-white/50'}`}>
              {a.generated_by === 'llm' ? 'IA' : a.generated_by} · conf {a.confidence ?? '—'}
            </span>
          )}
          {(a.frameworks_applied || []).map((f: string, i: number) => (
            <span key={i} className={`${chip} bg-white/10 text-white/50`}>{f}</span>
          ))}
        </div>
      )}

      {stageKey === 'positioning' && (
        <>
          {a.positioning_statement && (
            <div className={box}>
              <p className="text-base font-medium text-white">{a.positioning_statement}</p>
              {a.one_liner && <p className="mt-1 text-sm text-primary">“{a.one_liner}”</p>}
              {a.elevator_pitch && <p className="mt-2 text-sm text-white/60">{a.elevator_pitch}</p>}
            </div>
          )}
          <Section title="El enemigo">
            <div className={box}>
              <p className="text-sm text-white/85">{(a.enemy_analysis?.enemy) || a.the_enemy}</p>
              {a.enemy_analysis?.passes != null && (
                <span className={`${chip} mt-2 ${a.enemy_analysis.passes ? 'bg-emerald-500/15 text-emerald-300' : 'bg-amber-500/15 text-amber-300'}`}>
                  enemy test: {a.enemy_analysis.passes ? 'pasa' : 'no pasa'}
                </span>
              )}
              {a.point_of_view && <p className="mt-2 text-sm text-white/60">{a.point_of_view}</p>}
            </div>
          </Section>
          {a.pov_validation?.scores && (
            <Section title="Validación del POV"><div className={box}><Bars scores={a.pov_validation.scores} /></div></Section>
          )}
          {a.reframe && (
            <Section title="Reframe">
              <div className={`${box} flex flex-col gap-1 text-sm sm:flex-row sm:items-center sm:gap-3`}>
                <span className="text-white/50 line-through">{a.reframe.from}</span>
                <span className="text-white/30">→</span>
                <span className="font-medium text-white">{a.reframe.to}</span>
              </div>
            </Section>
          )}
          {a.category_decision && (
            <Section title="Decisión de categoría">
              <div className={box}>
                <span className={`${chip} bg-primary/15 text-primary`}>{a.category_decision.recommendation}</span>
                <KV k="rationale" v={a.category_decision.rationale} />
                <KV k="name candidates" v={a.category_decision.name_candidates} />
              </div>
            </Section>
          )}
          {!!a.messaging_pillars?.length && (
            <Section title="Pilares de mensaje"><Table rows={a.messaging_pillars} cols={['pillar', 'proof']} /></Section>
          )}
          {!!a.alternatives_matrix?.length && (
            <Section title="Matriz de alternativas">
              <Table rows={a.alternatives_matrix} cols={['alternative', 'why_tolerated', 'what_customer_keeps', 'what_they_lose']} />
            </Section>
          )}
          {!!a.attribute_value_proof?.length && (
            <Section title="Atributo → valor → prueba"><Table rows={a.attribute_value_proof} cols={['attribute', 'value', 'proof_point']} /></Section>
          )}
          <KV k="migration_risks" v={a.migration_risks} />
          <KV k="alternative_angles" v={a.alternative_angles} />
        </>
      )}

      {stageKey === 'brand_identity' && (
        <>
          <div className={box}>
            <div className="flex flex-wrap items-center gap-2">
              <span className={`${chip} bg-primary/15 text-primary`}>{a.primary_archetype}</span>
              {a.secondary_archetype && <span className={`${chip} bg-white/10 text-white/60`}>+ {a.secondary_archetype}</span>}
              {a.archetype_analysis?.blend && <span className="text-xs text-white/40">{a.archetype_analysis.blend}</span>}
            </div>
            {a.tagline && <p className="mt-2 text-lg font-semibold text-white">{a.tagline}</p>}
            {!!a.taglines_alt?.length && <p className="text-xs text-white/40">alt: {a.taglines_alt.join(' · ')}</p>}
          </div>
          {a.manifesto && <div className={`${box} text-sm italic leading-relaxed text-white/80`}>{a.manifesto}</div>}
          {a.story_spine && (
            <Section title="Story spine">
              <div className="grid gap-2 sm:grid-cols-2">
                {['world', 'problem', 'insight', 'mission'].map((b) => (
                  <div key={b} className={box}>
                    <p className={label}>{b}</p>
                    <p className="text-sm text-white/80">{a.story_spine[b]}</p>
                  </div>
                ))}
              </div>
            </Section>
          )}
          {a.verbal_identity && (
            <Section title="Identidad verbal">
              <div className={box}>
                {!!a.verbal_identity.attributes?.length && (
                  <Table rows={a.verbal_identity.attributes} cols={['adj', 'sounds_like', 'not']} />
                )}
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {(a.verbal_identity.lexicon?.use || []).map((w: string, i: number) => (
                    <span key={`u${i}`} className={`${chip} bg-emerald-500/15 text-emerald-300`}>{w}</span>
                  ))}
                  {(a.verbal_identity.lexicon?.ban || []).slice(0, 12).map((w: string, i: number) => (
                    <span key={`b${i}`} className={`${chip} bg-red-500/15 text-red-300 line-through`}>{w}</span>
                  ))}
                </div>
                <KV k="rhythm" v={a.verbal_identity.rhythm} />
                <KV k="humor" v={a.verbal_identity.humor} />
                <KV k="first line rule" v={a.verbal_identity.first_line_rule} />
              </div>
            </Section>
          )}
          {!!a.sample_rewrites?.length && (
            <Section title="Reescrituras de ejemplo">
              <div className="grid gap-2 sm:grid-cols-2">
                {a.sample_rewrites.map((sr: any, i: number) => (
                  <div key={i} className={box}>
                    <p className={label}>{sr.context}</p>
                    <p className="text-sm text-white/80">{sr.text}</p>
                  </div>
                ))}
              </div>
            </Section>
          )}
          {a.naming && (
            <Section title="Naming">
              <div className={box}>
                <span className={`${chip} bg-white/10 text-white/70`}>{a.naming.decision}</span>
                <KV k="rationale" v={a.naming.rationale} />
                {!!a.naming.candidates?.length && <Table rows={a.naming.candidates} cols={['name', 'idea', 'scores']} />}
              </div>
            </Section>
          )}
          {a.visual_brief && <Section title="Brief visual"><div className={box}><Raw data={a.visual_brief} /></div></Section>}
          <KV k="identity_consistency_rules" v={a.identity_consistency_rules} />
          <KV k="alternative_angles" v={a.alternative_angles} />
        </>
      )}

      {stageKey === 'business_model' && (
        <>
          <KV k="model_diagnosis" v={a.model_diagnosis} />
          {!!a.pattern_evaluation?.length && (
            <Section title="Evaluación de patrones"><Table rows={a.pattern_evaluation} cols={['pattern', 'scores', 'verdict', 'how_it_transfers_here', 'precedent']} /></Section>
          )}
          {a.canvas && (
            <Section title="Business Model Canvas">
              <div className="grid gap-2 sm:grid-cols-3">
                {Object.entries(a.canvas).map(([k, v]) => (
                  <div key={k} className={box}>
                    <p className={label}>{k.replace(/_/g, ' ')}</p>
                    <div className="text-xs text-white/75">{Array.isArray(v) ? <Bullets items={v} /> : S(v)}</div>
                  </div>
                ))}
              </div>
            </Section>
          )}
          {!!a.canvas_changes?.length && (
            <Section title="Cambios en el canvas"><Table rows={a.canvas_changes} cols={['block', 'from', 'to', 'why', 'forces_change_in']} /></Section>
          )}
          {a.value_equation && <Section title="Ecuación de valor"><div className={box}><Raw data={a.value_equation} /></div></Section>}
          {a.grand_slam_offer && <Section title="Grand-slam offer"><div className={box}><Raw data={a.grand_slam_offer} /></div></Section>}
          {a.pricing_architecture?.tiers && (
            <Section title="Pricing">
              <Table rows={a.pricing_architecture.tiers} cols={['name', 'price', 'for', 'the_trick', 'expected_mix_pct']} />
              <KV k="anchor" v={a.pricing_architecture.anchor} />
              <KV k="psych tactics" v={a.pricing_architecture.psych_tactics} />
            </Section>
          )}
          <KV k="pricing_migration" v={a.pricing_migration} />
          {a.unit_economics_targets && (
            <Section title="Unit economics objetivo"><div className={box}><Raw data={a.unit_economics_targets} /></div></Section>
          )}
          {a.errc_grid && (
            <Section title="ERRC">
              <div className="grid gap-2 sm:grid-cols-2">
                {['eliminate', 'reduce', 'raise', 'create'].map((q) => (
                  <div key={q} className={box}>
                    <p className={label}>{q}</p>
                    <Bullets items={a.errc_grid[q] || []} />
                  </div>
                ))}
              </div>
            </Section>
          )}
          <KV k="rollout" v={a.rollout} />
          <KV k="risks" v={a.risks} />
          <KV k="rationale" v={a.rationale} />
        </>
      )}

      {stageKey === 'fomo_engine' && (
        <>
          {!!a.lever_selection?.length && (
            <Section title="Selección de palancas"><Table rows={a.lever_selection} cols={['lever', 'scores', 'chosen', 'note']} /></Section>
          )}
          {!!a.mechanisms?.length && (
            <Section title="Mecanismos">
              <div className="space-y-2">
                {a.mechanisms.map((m: any, i: number) => (
                  <div key={i} className={box}>
                    <div className="flex items-center gap-2">
                      <span className={`${chip} bg-orange-500/15 text-orange-300`}>{m.lever}</span>
                      {m.trigger && <span className="text-xs text-white/40">{m.trigger}</span>}
                    </div>
                    <KV k="implementation" v={m.implementation} />
                    <KV k="anti-fake guardrail" v={m.anti_fake_guardrail} />
                    <KV k="honest alternative" v={m.honest_alternative} />
                    <KV k="kpi" v={m.kpi} />
                  </div>
                ))}
              </div>
            </Section>
          )}
          {a.ethics_review && <Section title="Revisión ética"><div className={box}><Raw data={a.ethics_review} /></div></Section>}
          <KV k="activation_sequence" v={a.activation_sequence} />
          <KV k="launch_ritual" v={a.launch_ritual} />
          <KV k="cadence" v={a.cadence} />
          {!!a.content_hooks?.length && <Section title="Hooks de copy"><Table rows={a.content_hooks} cols={['mechanism', 'copy_angle']} /></Section>}
          <KV k="measurement" v={a.measurement} />
          {!!a.integration_notes?.length && (
            <Section title="Integración SellIA"><Table rows={a.integration_notes} cols={['mechanism', 'sellia_domain_action']} /></Section>
          )}
          {!!a.risk_matrix?.length && <Section title="Matriz de riesgo"><Table rows={a.risk_matrix} cols={['mechanism', 'backfire_mode', 'early_warning', 'kill_switch']} /></Section>}
          {!!a.deployed_campaigns?.length && (
            <Section title="Campañas creadas"><Table rows={a.deployed_campaigns} cols={['lever', 'campaign_type', 'status', 'campaign_id', 'error']} /></Section>
          )}
        </>
      )}

      {stageKey === 'gtm' && (
        <>
          {!!a.loop_evaluation?.length && <Section title="Evaluación de loops"><Table rows={a.loop_evaluation} cols={['loop', 'scores', 'verdict', 'note']} /></Section>}
          {a.primary_growth_loop && (
            <Section title="Growth loop primario">
              <div className={box}>
                <span className={`${chip} bg-primary/15 text-primary`}>{a.primary_growth_loop.type}</span>
                <KV k="the variable it turns" v={a.primary_growth_loop.the_variable_it_turns} />
                <KV k="turning metric" v={a.primary_growth_loop.turning_metric} />
                <KV k="cycle time" v={a.primary_growth_loop.cycle_time} />
                <KV k="why not the others" v={a.primary_growth_loop.why_not_the_others} />
              </div>
            </Section>
          )}
          {!!(a.channel_plan || a.channels)?.length && (
            <Section title="Canales"><Table rows={a.channel_plan || a.channels} cols={['channel', 'role', 'hypothesis', 'first_action', 'effort', 'kill_signal']} /></Section>
          )}
          <KV k="lightning_strike" v={a.lightning_strike} />
          {a.content_engine && <Section title="Motor de contenido"><div className={box}><Raw data={a.content_engine} /></div></Section>}
          {Array.isArray(a.funnel) && <Section title="Funnel"><Table rows={a.funnel} cols={['stage', 'the_job', 'asset', 'metric', 'top_dropoff_risk']} /></Section>}
          {!!a.plan_90_days?.length && <Section title="Plan 90 días"><Table rows={a.plan_90_days} cols={['milestone', 'weeks', 'focus', 'owner', 'success_metric', 'depends_on']} /></Section>}
          {a.north_star_metric && (
            <div className={`${box} border-primary/20 bg-primary/5`}>
              <p className={label}>north star metric</p>
              <p className="text-sm text-white/85">{a.north_star_metric}</p>
            </div>
          )}
          <KV k="week_1_actions" v={a.week_1_actions} />
          <KV k="budget_shape" v={a.budget_shape} />
          <KV k="anti_goals" v={a.anti_goals} />
        </>
      )}

      {stageKey === 'restructuring' && (
        <>
          <div className="grid gap-2 sm:grid-cols-3">
            {(['kill', 'keep', 'scale'] as const).map((c) => (
              <div key={c} className={box}>
                <p className={`${label} ${c === 'kill' ? 'text-red-300' : c === 'scale' ? 'text-emerald-300' : ''}`}>{c}</p>
                <Bullets items={a[c] || []} />
              </div>
            ))}
          </div>
          {!!a.capability_gaps?.length && <Section title="Gaps de capacidad"><Table rows={a.capability_gaps} cols={['gap', 'build_buy_borrow', 'reason']} /></Section>}
          {a.the_one_hire && <KV k="the one hire" v={a.the_one_hire} />}
          {!!a.decision_rights?.length && <Section title="Derechos de decisión"><Table rows={a.decision_rights} cols={['decision', 'owner', 'consulted', 'informed']} /></Section>}
          {!!a.core_processes?.length && <Section title="Procesos núcleo"><Table rows={a.core_processes} cols={['name', 'owner', 'trigger', 'sla', 'promise_protected', 'failure_mode']} /></Section>}
          {a.operating_rhythm && <Section title="Ritmo operativo"><div className={box}><Raw data={a.operating_rhythm} /></div></Section>}
          {!!a.promise_kpis?.length && <Section title="Promise KPIs"><Table rows={a.promise_kpis} cols={['kpi', 'target', 'proves', 'replaces_vanity_metric', 'source', 'baseline']} /></Section>}
          {a.unit_economics_gate && <Section title="Gate de unit economics"><div className={box}><Raw data={a.unit_economics_gate} /></div></Section>}
          {!!a.operating_plan_90d?.length && <Section title="Plan operativo 90d"><Table rows={a.operating_plan_90d} cols={['change', 'owner', 'done_looks_like', 'depends_on']} /></Section>}
          <KV k="transition_risks" v={a.transition_risks} />
        </>
      )}

      {rest.length > 0 && (
        <details className="text-sm">
          <summary className="cursor-pointer text-white/40">Campos adicionales ({rest.length})</summary>
          <div className="mt-2 space-y-2">
            {rest.map(([k, v]) => (
              <KV key={k} k={k} v={v} />
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
