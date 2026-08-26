import React, { useState } from 'react'
import {
  IconSearch,
  IconCheck,
  IconChevronDown,
  IconChevronRight
} from '../components/icons'

export default function EvidenceView({ taskResult, onPlaySound }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedId, setExpandedId] = useState(null)
  const evidence = taskResult?.evidence || []

  const filteredEvidence = evidence.filter(ev =>
    !searchTerm ||
    ev.type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ev.source?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ev.content?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const activeEvidence = filteredEvidence.find((ev) => ev.id === expandedId) || filteredEvidence[0]

  const toggleExpand = (id) => {
    onPlaySound?.('hover')
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00]" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              Audit Interface
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">
            Evidence Trail & Verification Ledger
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <IconSearch className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter evidence ledger..."
              className="bg-[#0D0D0D] border border-white/10 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder:text-zinc-600 outline-none focus:border-[#FF6A00] transition-colors font-mono"
            />
          </div>

          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/20 font-bold">
            {evidence.length} backend item(s)
          </span>
        </div>
      </div>

      {!taskResult || filteredEvidence.length === 0 ? (
        <section className="glass-panel p-6 rounded-2xl border border-white/10">
          <h2 className="text-base font-bold text-white">No evidence recorded</h2>
          <p className="text-sm text-zinc-400 mt-2">
            Submit a task and wait for the backend verifier to produce evidence entries.
          </p>
        </section>
      ) : (
        <>
          <section className="glass-panel-elevated p-6 rounded-2xl border border-[#FF6A00]/40 shadow-[0_0_30px_rgba(255,106,0,0.15)] bg-gradient-to-br from-[#18110a] to-[#101010]">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-white/10">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono font-extrabold text-[#FF8A00] bg-[#FF6A00]/20 px-2.5 py-1 rounded-lg border border-[#FF6A00]/30">
                  FEATURED EVIDENCE
                </span>
                <h2 className="text-base sm:text-lg font-bold text-white">
                  {activeEvidence.source}
                </h2>
              </div>

              <div className="flex items-center gap-3 font-mono text-xs">
                <span className="text-zinc-400">Timestamp: <strong className="text-white">{activeEvidence.timestamp}</strong></span>
                <span className="text-emerald-400 font-bold bg-emerald-500/15 px-2.5 py-1 rounded-lg border border-emerald-500/30 flex items-center gap-1">
                  <IconCheck className="w-3.5 h-3.5" />
                  {activeEvidence.type}
                </span>
              </div>
            </div>

            <div className="mt-4 p-3.5 rounded-xl bg-black/50 border border-white/5 text-xs text-zinc-300 font-sans leading-relaxed">
              <strong className="text-white font-mono">{activeEvidence.id}: </strong>
              {activeEvidence.content}
            </div>
          </section>

          <section className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/5">
              <h2 className="text-base font-bold text-white">
                Complete Evidence Ledger
              </h2>
              <span className="text-xs text-zinc-500 font-mono">Click card to expand metadata</span>
            </div>

            <div className="space-y-3">
              {filteredEvidence.map((ev, index) => {
                const isExpanded = expandedId === ev.id
                const metadata = ev.metadata || {}

                return (
                  <article
                    key={ev.id}
                    className={`rounded-xl border transition-all overflow-hidden ${
                      isExpanded
                        ? 'bg-[#151515] border-[#FF6A00]/40 shadow-lg'
                        : 'bg-black/30 border-white/5 hover:border-white/15'
                    }`}
                  >
                    <div
                      onClick={() => toggleExpand(ev.id)}
                      className="p-4 flex items-center justify-between cursor-pointer select-none gap-4"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="font-mono text-xs font-bold text-[#FF8A00] bg-[#FF6A00]/10 px-2 py-1 rounded">
                          #{String(index + 1).padStart(2, '0')}
                        </span>
                        <div className="min-w-0">
                          <h4 className="text-xs sm:text-sm font-bold text-white truncate">
                            {ev.source}
                          </h4>
                          <p className="text-xs text-zinc-400 font-sans truncate mt-0.5">
                            {ev.content}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0 font-mono text-xs">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          {ev.type}
                        </span>
                        {isExpanded ? (
                          <IconChevronDown className="w-4 h-4 text-zinc-400" />
                        ) : (
                          <IconChevronRight className="w-4 h-4 text-zinc-400" />
                        )}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="px-4 pb-4 pt-2 border-t border-white/5 space-y-3 text-xs bg-black/40 animate-in fade-in duration-100">
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono">
                          <div>
                            <span className="text-zinc-500 text-[10px]">EVIDENCE ID:</span>
                            <div className="text-zinc-200 font-semibold">{ev.id}</div>
                          </div>
                          <div>
                            <span className="text-zinc-500 text-[10px]">TIME RECORDED:</span>
                            <div className="text-zinc-200 font-semibold">{ev.timestamp}</div>
                          </div>
                          <div>
                            <span className="text-zinc-500 text-[10px]">URL:</span>
                            <div className="text-[#FF8A00] font-mono text-[11px] truncate">{metadata.url || 'Not provided'}</div>
                          </div>
                        </div>

                        <div className="p-3 rounded-lg bg-[#0E0E0E] border border-white/5 space-y-1 font-sans">
                          <span className="text-zinc-400 font-mono text-[10px] uppercase font-bold">Metadata:</span>
                          <pre className="text-zinc-300 leading-relaxed whitespace-pre-wrap text-[11px]">
                            {JSON.stringify(metadata, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </article>
                )
              })}
            </div>
          </section>
        </>
      )}
    </div>
  )
}
