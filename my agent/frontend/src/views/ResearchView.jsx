import React, { useMemo, useState } from 'react'
import {
  IconShieldCheck,
  IconExternalLink,
  IconCheck,
  IconFileText,
} from '../components/icons'

const getEvidence = (taskResult) => taskResult?.evidence || []

const buildSources = (taskResult) => {
  const sourceMap = new Map()

  getEvidence(taskResult).forEach((item) => {
    const metadata = item.metadata || {}
    const key = metadata.url || item.source || item.id
    const existing = sourceMap.get(key) || {
      id: key,
      name: item.source || metadata.title || item.type || 'Evidence source',
      organization: metadata.domain || metadata.organization || item.source || 'TaskFinisher backend',
      type: item.type || 'evidence',
      url: metadata.url || '',
      reliability: metadata.reliability || metadata.confidence || 100,
      relevance: metadata.relevance || 'Collected by backend agent',
      hash: item.id,
      claims: [],
    }

    existing.claims.push(item.content)
    sourceMap.set(key, existing)
  })

  return Array.from(sourceMap.values())
}

export default function ResearchView({ taskResult, onNavigate, onPlaySound }) {
  const sources = useMemo(() => buildSources(taskResult), [taskResult])
  const evidence = getEvidence(taskResult)
  const [selectedSourceId, setSelectedSourceId] = useState(null)
  const selectedSource = sources.find((source) => source.id === selectedSourceId) || sources[0]

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00]" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              Intelligence Workspace
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">
            Research & Source Verification
          </h1>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 bg-black/40 px-3 py-1.5 rounded-xl border border-white/10">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>{sources.length} source(s) from the active backend task</span>
        </div>
      </div>

      {!taskResult || sources.length === 0 ? (
        <section className="glass-panel p-6 rounded-2xl border border-white/10">
          <h2 className="text-base font-bold text-white">No research evidence yet</h2>
          <p className="text-sm text-zinc-400 mt-2">
            Run a task through the backend to populate real sources, claims, and verification evidence.
          </p>
        </section>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-4 space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold">
                Source Catalog
              </span>
              <span className="text-[10px] font-mono text-zinc-500">Backend Evidence</span>
            </div>

            <div className="space-y-3 max-h-[720px] overflow-y-auto pr-1">
              {sources.map((source, index) => {
                const isSelected = selectedSource?.id === source.id

                return (
                  <article
                    key={source.id}
                    onClick={() => {
                      onPlaySound?.('hover')
                      setSelectedSourceId(source.id)
                    }}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[#FF6A00]/10 border-[#FF6A00] shadow-[0_0_20px_rgba(255,106,0,0.15)]'
                        : 'bg-black/40 border-white/10 hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-mono font-bold text-[#FF8A00]">
                        SOURCE #{String(index + 1).padStart(2, '0')}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-bold flex items-center gap-1">
                        <IconCheck className="w-3 h-3" />
                        CAPTURED
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-white leading-snug">
                      {source.name}
                    </h4>
                    <p className="text-[11px] text-zinc-400 font-mono mt-0.5">
                      {source.organization}
                    </p>

                    <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px]">
                      <span className="text-zinc-500 font-mono">
                        Evidence items: <strong className="text-zinc-300">{source.claims.length}</strong>
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          onPlaySound?.('click')
                          onNavigate('evidence')
                        }}
                        className="text-[#FF8A00] hover:text-white font-mono text-[10px] font-semibold underline flex items-center gap-1"
                      >
                        View Evidence
                      </button>
                    </div>
                  </article>
                )
              })}
            </div>
          </div>

          <div className="lg:col-span-5 space-y-4">
            <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-4 h-full">
              <div className="flex items-center justify-between pb-3 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <IconFileText className="w-4 h-4 text-[#FF8A00]" />
                  <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                    Source Inspection & Claims
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-zinc-500">
                  {selectedSource?.hash}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-black/50 border border-white/5 space-y-2">
                <h2 className="text-base font-bold text-white">{selectedSource.name}</h2>
                <div className="flex items-center gap-3 text-xs font-mono text-zinc-400">
                  <span>Source: <strong className="text-zinc-200">{selectedSource.organization}</strong></span>
                  <span>Type: <strong className="text-zinc-200">{selectedSource.type}</strong></span>
                </div>
                {selectedSource.url && (
                  <div className="text-[11px] font-mono text-[#FF8A00] truncate flex items-center gap-1">
                    <IconExternalLink className="w-3 h-3 shrink-0" />
                    <span className="truncate">{selectedSource.url}</span>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold block">
                  Captured Claims:
                </span>

                <div className="space-y-2">
                  {selectedSource.claims.map((claim, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-black/30 border border-white/5 flex items-start gap-2.5 text-xs text-zinc-200 leading-relaxed">
                      <span className="text-[#FF8A00] font-mono font-bold mt-0.5">[{idx + 1}]</span>
                      <span>{claim}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2 text-emerald-400">
                  <IconShieldCheck className="w-4 h-4" />
                  <span>Evidence ID:</span>
                </div>
                <span className="text-zinc-400 text-[11px]">{selectedSource.hash}</span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-3 space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold">
                Evidence Rail
              </span>
              <span className="text-[10px] font-mono text-[#FF8A00]">{evidence.length} items</span>
            </div>

            <div className="space-y-2 max-h-[720px] overflow-y-auto pr-1">
              {evidence.map((ev) => (
                <div
                  key={ev.id}
                  onClick={() => {
                    onPlaySound?.('hover')
                    onNavigate('evidence')
                  }}
                  className="p-3 rounded-xl bg-black/40 border border-white/5 hover:border-[#FF6A00]/40 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-mono font-bold text-white group-hover:text-[#FF8A00]">
                      {ev.id}
                    </span>
                    <span className="text-[9px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded">
                      {ev.type}
                    </span>
                  </div>
                  <div className="text-xs font-bold text-zinc-300 truncate">
                    {ev.source}
                  </div>
                  <p className="text-[11px] text-zinc-500 truncate mt-1">
                    {ev.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
