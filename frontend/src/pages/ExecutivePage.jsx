import { CheckCircle2, CircleDollarSign, Gauge, Ship } from 'lucide-react'
import BarGraphs from '../components/BarGraphs'
import ExecutiveSummary from '../components/ExecutiveSummary'
import LandedCost from '../components/LandedCost'
import ModelStatus from '../components/ModelStatus'

const ExecutivePage = ({ data, parameters }) => {
  const t = data?.timing_decision || {}
  const cost = data?.tlc_breakdown || {}
  const allowed = data?.port_constraints?.allowed_classes?.includes(parameters.vessel_class)

  return (
    <div className="space-y-6">
      <div><p className="text-[10px] font-extrabold uppercase tracking-[0.2em] text-sky-700">Leadership workspace</p><h1 className="mt-1 text-2xl font-black text-[#0a2440]">Executive Summary</h1><p className="mt-1 text-sm text-slate-500">A concise view of commercial decision, operational readiness and voyage economics.</p></div>
      <div className="grid gap-4 md:grid-cols-3">
        <Signal icon={Ship} label="Chartering Signal" value={t.decision === 'DEFER' ? 'Defer Fixture' : 'Execute Now'} />
        <Signal icon={CheckCircle2} label="Port Readiness" value={allowed ? 'Class Allowed' : 'Review Required'} />
        <Signal icon={CircleDollarSign} label="Landed Cost" value={cost.total_landed_cost ? `$${Number(cost.total_landed_cost).toLocaleString()}` : '—'} />
      </div>
      <ExecutiveSummary data={data} parameters={parameters} />
      <BarGraphs data={data} />
      <div className="grid gap-6 xl:grid-cols-2"><LandedCost data={data} /><ModelStatus /></div>
    </div>
  )
}

const Signal = ({ icon: Icon, label, value }) => <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><Icon size={18} className="text-sky-600"/><p className="mt-3 text-[10px] font-extrabold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 text-lg font-black text-[#0a2440]">{value}</p></div>
export default ExecutivePage
