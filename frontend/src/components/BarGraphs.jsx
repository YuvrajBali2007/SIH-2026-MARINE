import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BarChart3, CircleDollarSign, Ship } from 'lucide-react'

const Card = ({ title, subtitle, icon: Icon, children }) => (
  <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
    <div className="mb-5 flex items-center gap-3">
      <div className="rounded-xl bg-sky-50 p-2.5 text-sky-700"><Icon size={17} /></div>
      <div>
        <h2 className="text-base font-black text-[#0a2440]">{title}</h2>
        <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
      </div>
    </div>
    <div className="h-[300px]">
      {children}
    </div>
  </section>
)

const BarGraphs = ({ data }) => {
  const vessels = Array.isArray(data?.ranked_vessels)
    ? data.ranked_vessels.slice(0, 6).map((v, index) => ({
        name: v.vessel_id || v.candidate_id || `Vessel ${index + 1}`,
        score: Number(v.vessel_score || 0),
      }))
    : []

  const cost = data?.tlc_breakdown || {}
  const costs = [
    { name: 'Freight', value: Number(cost.base_freight || 0) },
    { name: 'Bunker', value: Number(cost.bunker_surcharge || 0) },
    { name: 'Demurrage', value: Number(cost.demurrage_risk || 0) },
    { name: 'Inventory', value: Number(cost.inventory_hold || 0) },
  ]

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <Card title="Vessel Score Comparison" subtitle="Multi-factor allocation score across leading candidates" icon={Ship}>
        {vessels.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={vessels} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis dataKey="name" type="category" width={90} tick={{ fontSize: 10, fill: '#475569' }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}`, 'Score']} contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0' }} />
              <Bar dataKey="score" name="Score" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart />
        )}
      </Card>

      <Card title="Landed Cost Components" subtitle="Relative contribution to the current voyage economics" icon={CircleDollarSign}>
        {data?.tlc_breakdown ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={costs} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} width={65} tickFormatter={(v) => `$${Number(v / 1000).toFixed(0)}k`} />
              <Tooltip formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Cost']} contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0' }} />
              <Bar dataKey="value" name="Cost" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart />
        )}
      </Card>
    </div>
  )
}

const EmptyChart = () => (
  <div className="flex h-full flex-col items-center justify-center rounded-xl bg-slate-50 text-center">
    <BarChart3 size={25} className="text-slate-300" />
    <p className="mt-3 text-sm font-bold text-slate-500">Run optimization to populate analytics</p>
    <p className="mt-1 text-xs text-slate-400">Charts update from the live model response.</p>
  </div>
)

export default BarGraphs
