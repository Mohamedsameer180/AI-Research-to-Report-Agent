import React, { useState, useEffect } from 'react'
import { IconSearch, IconX, IconChevronRight } from './icons'

export default function GlobalSearchModal({ isOpen, taskResult, onClose, onSelectResult }) {
  const [query, setQuery] = useState('')

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        if (isOpen) onClose()
        else onSelectResult?.('OPEN_SEARCH')
      }
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose, onSelectResult])

  if (!isOpen) return null

  const cleanQuery = query.toLowerCase().trim()
  const evidence = taskResult?.evidence || []
  const tasks = taskResult?.task_id ? [taskResult] : []

  const matchedEvidence = evidence.filter(e =>
    !cleanQuery ||
    e.source?.toLowerCase().includes(cleanQuery) ||
    e.content?.toLowerCase().includes(cleanQuery) ||
    e.type?.toLowerCase().includes(cleanQuery)
  ).slice(0, 3)

  const matchedTasks = tasks.filter(t =>
    !cleanQuery || t.user_request.toLowerCase().includes(cleanQuery)
  ).slice(0, 3)

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-start justify-center pt-24 px-4">
      <div className="w-full max-w-2xl glass-panel-elevated rounded-2xl border border-white/20 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="p-4 border-b border-white/10 flex items-center gap-3 bg-[#0A0A0A]">
          <IconSearch className="w-5 h-5 text-[#FF8A00]" />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search active backend task, evidence, and agent events..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder:text-zinc-500 font-sans"
          />
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-zinc-400 hover:text-white"
          >
            <IconX className="w-5 h-5" />
          </button>
        </div>

        <div className="max-h-[60vh] overflow-y-auto p-4 space-y-4">
          {matchedEvidence.length > 0 && (
            <div>
              <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-[#FF8A00] mb-2">
                Evidence Audit Items ({matchedEvidence.length})
              </div>
              <div className="space-y-1.5">
                {matchedEvidence.map(e => (
                  <div
                    key={e.id}
                    onClick={() => {
                      onSelectResult?.('evidence', e)
                      onClose()
                    }}
                    className="p-2.5 rounded-xl bg-black/40 hover:bg-[#FF6A00]/10 border border-white/5 hover:border-[#FF6A00]/40 flex items-center justify-between cursor-pointer group transition-all"
                  >
                    <div>
                      <div className="text-xs font-bold text-white group-hover:text-[#FF8A00] transition-colors">
                        {e.id} - {e.source}
                      </div>
                      <div className="text-[11px] text-zinc-400 truncate max-w-md">
                        {e.content}
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-zinc-400 bg-white/5 px-2 py-0.5 rounded">
                      {e.type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {matchedTasks.length > 0 && (
            <div>
              <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-[#FF8A00] mb-2">
                Execution History ({matchedTasks.length})
              </div>
              <div className="space-y-1.5">
                {matchedTasks.map(t => (
                  <div
                    key={t.task_id}
                    onClick={() => {
                      onSelectResult?.('history', t)
                      onClose()
                    }}
                    className="p-2.5 rounded-xl bg-black/40 hover:bg-[#FF6A00]/10 border border-white/5 hover:border-[#FF6A00]/40 flex items-center justify-between cursor-pointer group transition-all"
                  >
                    <div>
                      <div className="text-xs font-bold text-white group-hover:text-[#FF8A00] transition-colors">
                        {t.user_request}
                      </div>
                      <div className="text-[11px] text-zinc-400">
                        {t.completed_steps || 0}/{t.total_steps || 0} steps - {t.verdict || t.status}
                      </div>
                    </div>
                    <IconChevronRight className="w-4 h-4 text-zinc-500 group-hover:text-white" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {matchedEvidence.length === 0 && matchedTasks.length === 0 && (
            <div className="p-6 text-center text-sm text-zinc-500">
              No backend task data matches this search yet.
            </div>
          )}
        </div>

        <div className="p-3 border-t border-white/10 bg-[#0A0A0A] flex items-center justify-between text-[11px] text-zinc-500 font-mono">
          <span>Press ESC to close</span>
          <span className="text-[#FF8A00]">TaskFinisher Live Index</span>
        </div>
      </div>
    </div>
  )
}
