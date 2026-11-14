import React from 'react'
import {
  IconCpu,
  IconZap,
  IconFileText,
  IconSearch,
  IconShieldCheck,
  IconHistory,
  IconBarChart,
  IconSettings,
  IconLayers,
  IconRefreshCw,
  IconSparkles,
  IconBookOpen,
} from './icons'

export const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: IconCpu, kicker: 'Mission Control' },
  { id: 'tasks', label: 'Tasks', icon: IconZap, kicker: 'Plan & Create' },
  { id: 'activity', label: 'Agent Activity', icon: IconRefreshCw, kicker: 'Live Execution' },
  { id: 'research', label: 'Deep Search', icon: IconSearch, kicker: 'Hybrid RAG & Rerank' },
  { id: 'documents', label: 'Paper Hub', icon: IconBookOpen, kicker: 'Ingest & Grounding' },
  { id: 'evidence', label: 'Evidence', icon: IconShieldCheck, kicker: 'Audit Ledger' },
  { id: 'history', label: 'Execution History', icon: IconHistory, kicker: 'Archive & Replay' },
  { id: 'analytics', label: 'Analytics', icon: IconBarChart, kicker: 'Telemetry' },
  { id: 'settings', label: 'Settings', icon: IconSettings, kicker: 'Configuration' },
]

export default function Sidebar({ activePage, setActivePage, onPlaySound }) {
  return (
    <aside className="w-64 bg-[#0A0A0A] border-r border-white/10 flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none z-30">
      {/* Brand Header */}
      <div>
        <div className="p-5 border-b border-white/5 flex items-center justify-between">
          <div 
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => {
              onPlaySound?.('click')
              setActivePage('overview')
            }}
          >
            {/* Glowing Orange AI Symbol */}
            <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF6A00] to-[#CC5500] flex items-center justify-center shadow-[0_0_16px_rgba(255,106,0,0.4)] group-hover:shadow-[0_0_24px_rgba(255,106,0,0.6)] transition-all">
              <IconSparkles className="w-5 h-5 text-white animate-pulse-glow" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-white animate-ping" />
            </div>

            <div>
              <div className="text-[13px] font-extrabold tracking-widest text-white leading-tight font-mono">
                TASK<br />FINISHER
              </div>
              <div className="text-[9px] text-[#FF8A00] font-semibold tracking-wider uppercase font-mono">
                Autonomous Engine
              </div>
            </div>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const isActive = activePage === item.id

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  onPlaySound?.('click')
                  setActivePage(item.id)
                }}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all group ${
                  isActive
                    ? 'bg-[#FF6A00]/15 text-[#FF8A00] border border-[#FF6A00]/30 shadow-[0_0_15px_rgba(255,106,0,0.15)] font-semibold'
                    : 'text-zinc-400 hover:text-white hover:bg-white/[0.04] border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className={`transition-colors ${isActive ? 'text-[#FF8A00]' : 'text-zinc-500 group-hover:text-zinc-300'}`}>
                    <Icon className="w-4 h-4" />
                  </span>
                  <span className="tracking-wide">{item.label}</span>
                </div>

                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#FF8A00] shadow-[0_0_6px_#FF8A00]" />
                )}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Bottom System Status */}
      <div className="p-4 border-t border-white/5 bg-[#070707]/80">
        <div className="glass-panel p-3 rounded-xl border border-white/5 flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-zinc-500">
            <span>AI SYSTEM</span>
            <span className="text-[#FF8A00] font-bold">v2.4 ADK</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-xs font-semibold text-zinc-200">
              All systems operational
            </span>
          </div>

          <div className="w-full bg-zinc-900 rounded-full h-1 mt-1 overflow-hidden">
            <div className="bg-gradient-to-r from-emerald-500 to-[#FF6A00] h-full rounded-full w-full" />
          </div>
        </div>
      </div>
    </aside>
  )
}
