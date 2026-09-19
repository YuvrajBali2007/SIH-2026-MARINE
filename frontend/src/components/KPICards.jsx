import { Anchor, CircleDollarSign, Fuel, TrendingDown } from 'lucide-react'

const money = (v) => v == null ? '—' : `$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
const num = (v, d = 2) => v == null ? '—' : Number(v).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })

const KPICards = ({ data }) => {
  const timing = data?.timing_decision || {}
  const tlc = data?.tlc_breakdown || {}
  const freight = data?.freight_forecast?.mean?.[0]
  const bunker = data?.fuel_forecast?.price?.[0]
  const accuracy = timing.directional_accuracy
  const cards = [
    { label: 'Current Charter Rate', value: money(timing.current_rate), sub: 'USD / day', icon: Anchor, tone: 'blue' },
    { label: 'Freight Rate T+0', value: freight == null ? '—' : `$${num(freight)}`, sub: 'USD / tonne', icon: TrendingDown, tone: 'green' },
    { label: 'Bunker Price', value: bunker == null ? '—' : `$${num(bunker, 0)}`, sub: 'USD / tonne', icon: Fuel, tone: 'amber' },
    { label: 'Total Landed Cost', value: money(tlc.total_landed_cost), sub: 'USD', icon: CircleDollarSign, tone: 'green' },
  ]
  return <>
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ label, value, sub, icon: Icon, tone }) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-start justify-between"><div><p className="text-[11px] font-extrabold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-2 text-2xl font-black tracking-tight text-[#0a2440]">{value}</p><p className="mt-1 text-xs text-slate-400">{sub}</p></div><div className={`rounded-xl p-3 ${tone === 'amber' ? 'bg-orange-50 text-orange-500' : tone === 'green' ? 'bg-emerald-50 text-emerald-600' : 'bg-sky-50 text-sky-600'}`}><Icon size={20} /></div></div>
        <div className="mt-4 flex items-center gap-1.5 text-[11px] font-bold text-emerald-600"><TrendingDown size={13} /> Model-derived scenario</div>
      </div>)}
    </div>
    <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm sm:flex-row sm:items-center sm:justify-between"><div><p className="text-[11px] font-extrabold uppercase tracking-wide text-slate-500">Forecast Confidence</p><p className="mt-1 text-xs text-slate-500">Directional accuracy reported by the charter-timing model</p></div><div className="flex items-center gap-3"><div className="h-2 w-40 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.min(100, Math.max(0, accuracy || 0))}%` }} /></div><span className="text-sm font-black text-[#0a2440]">{accuracy == null ? '—' : `${accuracy}%`}</span></div></div>
  </>
}

export default KPICards