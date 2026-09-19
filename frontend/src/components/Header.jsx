import { Bell, Menu, PanelLeftClose, PanelLeftOpen, Ship } from 'lucide-react'

const Header = ({ onMenuClick, onDesktopToggle, sidebarCollapsed, apiOnline }) => (
  <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 text-[#0a2440] shadow-sm backdrop-blur-xl">
    <div className="flex h-[72px] items-center justify-between px-4 sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <button type="button" onClick={onDesktopToggle} className="hidden rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-slate-600 transition hover:bg-slate-100 lg:inline-flex" aria-label={sidebarCollapsed ? 'Open scenario controls' : 'Collapse scenario controls'}>
          {sidebarCollapsed ? <PanelLeftOpen size={19} /> : <PanelLeftClose size={19} />}
        </button>
        <button type="button" onClick={onMenuClick} className="rounded-xl border border-slate-200 bg-slate-50 p-2.5 text-slate-600 lg:hidden" aria-label="Open scenario controls">
          <Menu size={19} />
        </button>
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#0b2137] text-white shadow-lg">
          <Ship size={24} />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-extrabold tracking-wide sm:text-base">STEEL AUTHORITY OF INDIA LIMITED</p>
          <p className="text-xs font-medium text-slate-500">Maritime Procurement Desk</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className={`hidden items-center gap-2 rounded-full border px-3 py-2 text-xs font-bold sm:flex ${apiOnline ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'}`}>
          <span className={`h-2 w-2 rounded-full ${apiOnline ? 'bg-emerald-500' : 'bg-amber-500'}`} />
          {apiOnline ? 'System Operational' : 'Backend Offline'}
        </div>
        <button type="button" className="relative rounded-xl border border-slate-200 p-2.5 text-slate-600">
          <Bell size={18} />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-orange-400" />
        </button>
        <div className="hidden h-8 w-px bg-slate-200 sm:block" />
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#0b5f93] text-xs font-extrabold text-white">SAIL</div>
      </div>
    </div>
  </header>
)

export default Header
