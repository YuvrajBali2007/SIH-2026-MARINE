import BarGraphs from '../components/BarGraphs'
import CharteringDesk from '../components/CharteringDesk'
import ForecastChart from '../components/ForecastChart'
import FuelOptimization from '../components/FuelOptimization'
import RecommendationCard from '../components/RecommendationCard'

const CharteringPage = ({ data }) => (
  <div className="space-y-6">
    <PageIntro title="Commercial Chartering Desk" text="Focus the review on freight outlook, fixture timing and fuel economics." />
    <RecommendationCard data={data} />
    <CharteringDesk data={data} />
    <ForecastChart data={data} />
    <BarGraphs data={data} />
    <FuelOptimization data={data} />
  </div>
)

const PageIntro = ({ title, text }) => <div><p className="text-[10px] font-extrabold uppercase tracking-[0.2em] text-sky-700">Commercial workspace</p><h1 className="mt-1 text-2xl font-black text-[#0a2440]">{title}</h1><p className="mt-1 text-sm text-slate-500">{text}</p></div>
export default CharteringPage
