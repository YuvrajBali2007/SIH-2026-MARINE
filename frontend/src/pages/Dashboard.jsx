import { useEffect, useState } from 'react'
import { Streamlit } from 'streamlit-component-lib'
import {
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  ShieldCheck,
  Waves,
} from 'lucide-react'

import AppNavigation from '../components/AppNavigation'
import BarGraphs from '../components/BarGraphs'
import Header from '../components/Header'
import KPICards from '../components/KPICards'
import EmptyState from '../components/EmptyState'
import RecommendationCard from '../components/RecommendationCard'
import CharteringPage from './CharteringPage'
import OperationsPage from './OperationsPage'
import ExecutivePage from './ExecutivePage'
import Sidebar from '../components/Sidebar'
import { checkApiHealth, runOptimization } from '../services/api'


const defaults = {
  route: 'Dampier, Australia - Visakhapatnam',
  cargo_type: 'Coal Ore',
  vessel_class: 'Supramax',
  market_event: 'None',
  vessel_dwt: 60000,
  distance_nm: 3570,
  baltic_style_index: 1550,
  bunker_fuel_price: 640,
  port_congestion_days: 1.5,
  port: 'Vizag',
  cargo_tonnes: 55000,
  required_days: 30,
  wind_speed: 12,
  wave_height: 2,
  speed: 14,
  vessel_age: 8,
  inventory_hold_cost_per_day: 12000,
}


const Dashboard = ({ args }) => {
  const [parameters, setParameters] = useState(defaults)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [apiOnline, setApiOnline] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [activePage, setActivePage] = useState('dashboard')
  const [audit, setAudit] = useState({
    market: false,
    port: false,
    commercial: false,
  })


  // Receive optimization result from Streamlit
  useEffect(() => {
    const result = args?.optimization_result

    if (!result) {
      return
    }

    if (result.success) {
      setData(result.data)
      setApiOnline(true)
      setLoading(false)
      setError('')
    } else {
      setError(result.error || 'Optimization failed')
      setApiOnline(false)
      setLoading(false)
    }

    Streamlit.setFrameHeight()
  }, [args])


  // Initial API/component health state
  useEffect(() => {
    checkApiHealth()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false))
  }, [])


  const execute = async () => {
    setLoading(true)
    setError('')

    try {
      await runOptimization(parameters)
      setApiOnline(true)
      setMobileOpen(false)
    } catch (e) {
      setError(e.message || 'Optimization request failed')
      setApiOnline(false)
      setLoading(false)
    }
  }


  const page =
    activePage === 'chartering' ? (
      <CharteringPage data={data} />
    ) : activePage === 'operations' ? (
      <OperationsPage
        data={data}
        parameters={parameters}
      />
    ) : activePage === 'executive' ? (
      <ExecutivePage
        data={data}
        parameters={parameters}
      />
    ) : (
      <DashboardHome
        data={data}
        loading={loading}
        error={error}
        execute={execute}
        parameters={parameters}
        audit={audit}
        setAudit={setAudit}
      />
    )


  return (
    <div className="min-h-screen bg-[#edf4f8] text-slate-900">
      <Header
        onMenuClick={() => setMobileOpen(true)}
        onDesktopToggle={() =>
          setSidebarCollapsed((value) => !value)
        }
        sidebarCollapsed={sidebarCollapsed}
        apiOnline={apiOnline}
      />

      <div className="flex">
        <Sidebar
          parameters={parameters}
          setParameters={setParameters}
          onRunOptimization={execute}
          loading={loading}
          mobileOpen={mobileOpen}
          onClose={() => setMobileOpen(false)}
          collapsed={sidebarCollapsed}
          onCollapse={() => {
            setSidebarCollapsed(true)
            setMobileOpen(false)
          }}
        />

        <main className="min-w-0 flex-1">
          <div className="mx-auto max-w-[1700px] p-4 sm:p-6 lg:p-8">
            <AppNavigation
              activePage={activePage}
              onChange={setActivePage}
            />

            {page}
          </div>
        </main>
      </div>
    </div>
  )
}


const DashboardHome = ({
  data,
  loading,
  error,
  execute,
  parameters,
  audit,
  setAudit,
}) => (
  <>
    <section className="relative mb-6 min-h-[300px] overflow-hidden rounded-3xl bg-[#08233c] shadow-xl">
      <img
        src="/maritime-hero.jpg"
        alt="Cargo vessel at sea"
        className="absolute inset-0 h-full w-full object-cover opacity-70"
      />

      <div className="absolute inset-0 bg-gradient-to-r from-[#06182a] via-[#08233c]/75 to-[#08233c]/20" />

      <div className="relative flex min-h-[300px] flex-col justify-between p-6 sm:p-8 lg:p-10">
        <div className="flex items-center justify-between">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-wider text-white">
            <Waves size={13} />
            Maritime Operations
          </div>

          <div className="hidden items-center gap-2 rounded-full border border-white/15 bg-black/20 px-3 py-1.5 text-[10px] font-bold text-white/80 sm:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            AI-enabled procurement
          </div>
        </div>

        <div className="max-w-3xl">
          <p className="text-xs font-extrabold uppercase tracking-[0.22em] text-sky-200">
            Steel Authority of India Limited
          </p>

          <h1 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-5xl">
            Maritime Procurement
            <br className="hidden sm:block" />
            Intelligence Dashboard
          </h1>

          <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-200 sm:text-base">
            A single decision workspace for freight forecasting,
            vessel chartering, fuel economics and port operations.
          </p>
        </div>
      </div>
    </section>


    {error && (
      <div className="mb-5 flex gap-3 rounded-2xl border border-red-200 bg-red-50 p-4">
        <AlertCircle
          size={19}
          className="shrink-0 text-red-600"
        />

        <div>
          <p className="text-sm font-black text-red-800">
            Optimization Error
          </p>

          <p className="mt-1 break-words text-xs text-red-700">
            {error}
          </p>
        </div>
      </div>
    )}


    {loading && (
      <div className="mb-6 rounded-2xl border border-sky-200 bg-white p-8 text-center shadow-sm">
        <RefreshCw
          size={27}
          className="mx-auto animate-spin text-sky-600"
        />

        <p className="mt-4 text-lg font-black text-[#0a2440]">
          Running Maritime AI Models
        </p>

        <p className="mt-1 text-xs text-slate-500">
          Freight · Fuel · Charter Timing · Vessel Allocation · Port Constraints
        </p>
      </div>
    )}


    {!data && !loading && (
      <div className="mb-6">
        <EmptyState
          onRunOptimization={execute}
          loading={loading}
        />
      </div>
    )}


    {data && !loading && (
      <>
        <div className="mb-6">
          <RecommendationCard data={data} />
        </div>

        <div className="mb-6">
          <KPICards data={data} />
        </div>

        <div className="mb-6">
          <BarGraphs data={data} />
        </div>


        <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <p className="text-sm font-black text-[#0a2440]">
                Procurement Control & Audit Readiness
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Mark review gates after validating live quotes
                and operational confirmations.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              {Object.entries(audit).map(([key, value]) => (
                <button
                  type="button"
                  key={key}
                  onClick={() =>
                    setAudit((current) => ({
                      ...current,
                      [key]: !current[key],
                    }))
                  }
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-2 text-[10px] font-extrabold uppercase tracking-wide ${
                    value
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 bg-slate-50 text-slate-500'
                  }`}
                >
                  {value ? (
                    <CheckCircle2 size={13} />
                  ) : (
                    <ShieldCheck size={13} />
                  )}

                  {key} review
                </button>
              ))}
            </div>
          </div>
        </section>


        <div className="rounded-2xl border border-slate-200 bg-white p-4 text-xs text-slate-500">
          Current scenario:{' '}
          <span className="font-bold text-[#0a2440]">
            {parameters.cargo_type}
          </span>{' '}
          ·{' '}
          <span className="font-bold text-[#0a2440]">
            {parameters.vessel_class}
          </span>{' '}
          ·{' '}
          <span className="font-bold text-[#0a2440]">
            {parameters.port}
          </span>{' '}
          ·{' '}
          {Number(parameters.cargo_tonnes).toLocaleString()} MT
        </div>
      </>
    )}
  </>
)


export default Dashboard