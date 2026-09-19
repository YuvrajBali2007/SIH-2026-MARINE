import { BarChart3, FileText, LayoutDashboard, Ship, Waypoints } from 'lucide-react'

const items = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'chartering', label: 'Chartering Desk', icon: Ship },
  { id: 'operations', label: 'Port & Operations', icon: Waypoints },
  { id: 'executive', label: 'Executive Summary', icon: FileText },
]

const AppNavigation = ({ activePage, onChange }) => (
  <nav className="mb-6 overflow-x-auto rounded-2xl border border-slate-200 bg-white p-1.5 shadow-sm">
    <div className="flex min-w-max items-center gap-1">
      {items.map(({ id, label, icon: Icon }) => {
        const active = activePage === id
        return (
          <button
            key={id}
            type="button"
            onClick={() => onChange(id)}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-extrabold transition ${active ? 'bg-[#0b5f93] text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50 hover:text-[#0a2440]'}`}
          >
            <Icon size={15} />
            {label}
          </button>
        )
      })}
    </div>
  </nav>
)

export default AppNavigation
