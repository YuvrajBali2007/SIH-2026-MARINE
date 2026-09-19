import BarGraphs from '../components/BarGraphs'
import LandedCost from '../components/LandedCost'
import PortOperations from '../components/PortOperations'
import VesselRanking from '../components/VesselRanking'

const OperationsPage = ({ data, parameters }) => (
  <div className="space-y-6">
    <PageIntro title="Port & Operations" text="Review berth constraints, vessel suitability and voyage cost exposure." />
    <PortOperations data={data} parameters={parameters} />
    <VesselRanking data={data} />
    <BarGraphs data={data} />
    <LandedCost data={data} />
  </div>
)

const PageIntro = ({ title, text }) => <div><p className="text-[10px] font-extrabold uppercase tracking-[0.2em] text-sky-700">Operations workspace</p><h1 className="mt-1 text-2xl font-black text-[#0a2440]">{title}</h1><p className="mt-1 text-sm text-slate-500">{text}</p></div>
export default OperationsPage
