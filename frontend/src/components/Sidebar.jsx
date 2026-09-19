import { BarChart3, ChevronDown, Gauge, Map, Settings2, Ship, SlidersHorizontal, X } from 'lucide-react'

const Field = ({ label, suffix, children }) => (
  <label className="block">
    <span className="mb-1.5 flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.13em] text-slate-400">
      <span>{label}</span>
      {suffix && <span className="normal-case tracking-normal text-slate-500">{suffix}</span>}
    </span>
    {children}
  </label>
)

const Sidebar = ({ parameters, setParameters, onRunOptimization, loading, mobileOpen, onClose, collapsed, onCollapse }) => {
  const update = (key, value) => setParameters((p) => ({ ...p, [key]: value }))
  const selectClass = 'w-full appearance-none rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2.5 text-xs font-semibold text-slate-100 outline-none transition focus:border-sky-400/60 focus:bg-white/[0.09]'
  const inputClass = selectClass

  const panel = (
    <div className="flex h-full w-[310px] flex-col bg-[#071d31] text-white shadow-2xl">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div className="flex items-center gap-2"><SlidersHorizontal size={16} className="text-sky-300" /><span className="text-sm font-bold">Scenario Controls</span></div>
        <button type="button" onClick={onCollapse} className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white" aria-label="Collapse sidebar"><X size={17} /></button>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-5">
        <p className="mb-6 text-[11px] leading-4 text-slate-400">Configure voyage, market and vessel assumptions before running the AI optimization.</p>

        <Section icon={Map} title="Fixture Parameters">
          <Field label="Route"><div className="relative"><select value={parameters.route} onChange={(e) => update('route', e.target.value)} className={selectClass}><option>Dampier, Australia - Visakhapatnam</option><option>Dampier, Australia - Paradip</option><option>Newcastle, Australia - Visakhapatnam</option><option>Richards Bay, South Africa - Paradip</option><option>Abbot Point, Australia - Visakhapatnam</option><option>Gladstone, Australia - Visakhapatnam</option></select><ChevronDown className="pointer-events-none absolute right-3 top-3 text-slate-400" size={14} /></div></Field>
          <Field label="Cargo Type"><select value={parameters.cargo_type} onChange={(e) => update('cargo_type', e.target.value)} className={selectClass}><option>Coal Ore</option><option>Iron Ore</option><option>Coking Coal</option><option>Thermal Coal</option></select></Field>
          <Field label="Vessel Class"><select value={parameters.vessel_class} onChange={(e) => update('vessel_class', e.target.value)} className={selectClass}><option>Handysize</option><option>Supramax</option><option>Panamax</option><option>Capesize</option></select></Field>
          <Field label="Destination Port"><select value={parameters.port} onChange={(e) => update('port', e.target.value)} className={selectClass}><option>Vizag</option><option>Paradip</option><option>Haldia</option><option>Ennore</option><option>Kolkata</option><option>Mormugao</option></select></Field>
          <Field label="Cargo Volume" suffix="MT"><input type="number" value={parameters.cargo_tonnes} onChange={(e) => update('cargo_tonnes', Number(e.target.value))} className={inputClass} /></Field>
        </Section>

        <Section icon={BarChart3} title="Market Conditions">
          <Field label="BDI Index"><input type="number" value={parameters.baltic_style_index} onChange={(e) => update('baltic_style_index', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Bunker Price" suffix="USD/t"><input type="number" value={parameters.bunker_fuel_price} onChange={(e) => update('bunker_fuel_price', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Port Congestion" suffix="days"><input type="number" step="0.1" value={parameters.port_congestion_days} onChange={(e) => update('port_congestion_days', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Wind Speed" suffix="kn"><input type="number" step="0.1" value={parameters.wind_speed} onChange={(e) => update('wind_speed', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Wave Height" suffix="m"><input type="number" step="0.1" value={parameters.wave_height} onChange={(e) => update('wave_height', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Market Event"><select value={parameters.market_event} onChange={(e) => update('market_event', e.target.value)} className={selectClass}><option>None</option><option>Port Strike</option><option>Canal Disruption</option><option>Monsoon Season</option><option>High Demand</option></select></Field>
        </Section>

        <Section icon={Settings2} title="Voyage Parameters">
          <Field label="Distance" suffix="NM"><input type="number" value={parameters.distance_nm} onChange={(e) => update('distance_nm', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Vessel Age" suffix="years"><input type="number" step="0.5" value={parameters.vessel_age} onChange={(e) => update('vessel_age', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Vessel DWT" suffix="t"><input type="number" value={parameters.vessel_dwt} onChange={(e) => update('vessel_dwt', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Transit Window" suffix="days"><input type="number" step="0.5" value={parameters.required_days} onChange={(e) => update('required_days', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Speed" suffix="knots"><input type="number" step="0.1" value={parameters.speed} onChange={(e) => update('speed', Number(e.target.value))} className={inputClass} /></Field>
          <Field label="Inventory Hold Cost" suffix="USD/day"><input type="number" value={parameters.inventory_hold_cost_per_day} onChange={(e) => update('inventory_hold_cost_per_day', Number(e.target.value))} className={inputClass} /></Field>
        </Section>
      </div>
      <div className="border-t border-white/10 bg-[#05182a] p-4">
        <button type="button" onClick={onRunOptimization} disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-4 py-3.5 text-sm font-extrabold text-white shadow-lg shadow-sky-900/30 transition hover:from-sky-400 hover:to-blue-500 disabled:opacity-60">
          {loading ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" /> Running AI Models</> : <><Gauge size={18} /> Run Optimization</>}
        </button>
        <p className="mt-2 flex items-center justify-center gap-1.5 text-[10px] text-slate-500"><Ship size={12} /> AI-assisted chartering analysis</p>
      </div>
    </div>
  )

  return (
    <>
      {mobileOpen && <button type="button" onClick={onClose} className="fixed inset-0 z-[60] bg-black/60 lg:hidden" aria-label="Close sidebar" />}
      <div className={`fixed inset-y-0 left-0 z-[70] transition-transform duration-300 lg:hidden ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        {panel}
      </div>
      <aside className={`relative hidden shrink-0 overflow-hidden transition-[width] duration-300 lg:block ${collapsed ? 'w-0' : 'w-[310px]'}`}>
        <div className={`sticky top-[72px] h-[calc(100vh-72px)] w-[310px] transition-transform duration-300 ${collapsed ? '-translate-x-full' : 'translate-x-0'}`}>
          {panel}
        </div>
      </aside>
    </>
  )
}

const Section = ({ icon: Icon, title, children }) => (
  <section className="mb-7 border-t border-white/10 pt-5 first:border-0 first:pt-0">
    <div className="mb-4 flex items-center gap-2 text-slate-200"><Icon size={15} className="text-sky-300" /><h3 className="text-[11px] font-extrabold uppercase tracking-[0.14em]">{title}</h3></div>
    <div className="space-y-3.5">{children}</div>
  </section>
)

export default Sidebar
