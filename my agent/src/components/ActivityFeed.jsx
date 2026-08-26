import React, { useState } from 'react'
import { IconCpu, IconTerminal, IconShieldCheck, IconAlertTriangle, IconRefreshCw, IconSearch, IconFileText } from './icons'

export default function ActivityFeed({ events = [] }) {
  const [filter, setFilter] = useState('ALL')

  const displayEvents = events.map((e, idx) => {
    if (typeof e === 'object' && e.message) {
      return {
        time: e.timestamp || e.time || '',
        agent: e.agent || (e.event?.includes('PLAN') ? 'Planner' : e.event?.includes('RECOVERY') ? 'Recovery' : e.event?.includes('VERIFY') ? 'Verifier' : 'Research'),
        message: e.message,
        event: e.event || 'EVENT',
        level: e.event?.includes('RECOVERY') ? 'recovery' : e.event?.includes('FAIL') || e.event?.includes('CONFLICT') || e.event?.includes('WARN') ? 'warning' : e.event?.includes('VERIF') || e.event?.includes('LOCKED') ? 'success' : 'info',
        isNew: idx === events.length - 1,
      }
    }
    return {
      time: Array.isArray(e) ? e[0] : '',
      agent: 'Agent',
      message: Array.isArray(e) ? e[1] : String(e),
      event: 'EVENT',
      level: 'info',
      isNew: false,
    }
  })

  const filteredEvents = displayEvents.filter(item => {
    if (filter === 'ALL') return true
    if (filter === 'RECOVERY') return item.level === 'recovery'
    if (filter === 'WARNING') return item.level === 'warning'
    if (filter === 'SUCCESS') return item.level === 'success'
    return true
  })

  const getAgentIcon = (agent) => {
    switch (agent) {
      case 'Planner': return <IconCpu className="w-3.5 h-3.5" />
      case 'Research': return <IconSearch className="w-3.5 h-3.5" />
      case 'Document': return <IconFileText className="w-3.5 h-3.5" />
      case 'Verifier': return <IconShieldCheck className="w-3.5 h-3.5" />
      case 'Recovery': return <IconRefreshCw className="w-3.5 h-3.5" />
      default: return <IconTerminal className="w-3.5 h-3.5" />
    }
  }

  return (
    <div className="glass-panel p-5 rounded-xl flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <IconTerminal className="w-4 h-4 text-[#FF8A00]" />
          <h3 className="text-sm font-bold tracking-wider text-white uppercase font-mono">
            Live Agent Activity
          </h3>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-1 bg-black/40 p-0.5 rounded-lg border border-white/5 text-[11px] font-mono">
          {['ALL', 'RECOVERY', 'WARNING', 'SUCCESS'].map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setFilter(tab)}
              className={`px-2 py-0.5 rounded transition-colors ${filter === tab ? 'bg-[#FF6A00]/20 text-[#FF8A00] font-semibold border border-[#FF6A00]/40' : 'text-zinc-400 hover:text-white'}`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Feed list */}
      <div className="flex-1 overflow-y-auto space-y-2.5 max-h-[290px] pr-1.5 font-mono text-xs">
        {filteredEvents.length === 0 ? (
          <div className="text-zinc-500 text-center py-8">No matching agent events found.</div>
        ) : (
          filteredEvents.map((evt, idx) => {
            let levelBorder = 'border-white/5'
            let levelBadge = 'text-zinc-400 bg-zinc-900/60'

            if (evt.level === 'recovery') {
              levelBorder = 'border-amber-500/40 bg-amber-500/5'
              levelBadge = 'text-amber-400 bg-amber-500/20'
            } else if (evt.level === 'warning') {
              levelBorder = 'border-red-500/40 bg-red-500/5'
              levelBadge = 'text-red-400 bg-red-500/20'
            } else if (evt.level === 'success') {
              levelBorder = 'border-emerald-500/40 bg-emerald-500/5'
              levelBadge = 'text-emerald-400 bg-emerald-500/20'
            }

            return (
              <div
                key={`${evt.time}-${idx}`}
                className={`p-2.5 rounded-lg border flex items-start gap-3 transition-all ${levelBorder} ${evt.isNew ? 'fresh-event-anim' : 'bg-black/30'}`}
              >
                <div className="flex items-center gap-1.5 text-zinc-500 font-mono text-[11px] shrink-0 pt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#FF6A00]/70" />
                  {evt.time}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="flex items-center gap-1 font-bold text-white text-[11px]">
                      {getAgentIcon(evt.agent)}
                      {evt.agent}
                    </span>
                    <span className={`text-[9px] px-1.5 py-0.2 rounded uppercase font-semibold ${levelBadge}`}>
                      {evt.event}
                    </span>
                  </div>
                  <p className="text-zinc-300 font-sans text-xs leading-relaxed">
                    {evt.message}
                  </p>
                </div>
              </div>
            )
          })
        )}
      </div>

      <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] text-zinc-500">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          Event Stream Active
        </span>
        <span className="font-mono text-zinc-400">{filteredEvents.length} events recorded</span>
      </div>
    </div>
  )
}
