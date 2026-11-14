import React from 'react'
import { IconX, IconCpu, IconShieldCheck, IconTerminal, IconCheckCircle, IconZap } from './icons'

export default function NodeInspectorModal({ node, onClose }) {
  if (!node) return null

  const Icon = node.icon || IconCpu

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg glass-panel-elevated rounded-2xl border border-[#FF6A00]/40 shadow-[0_0_40px_rgba(255,106,0,0.2)] overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="p-5 border-b border-white/10 bg-[#0E0E0E] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#FF6A00]/15 text-[#FF8A00] border border-[#FF6A00]/30 shadow-[0_0_12px_rgba(255,106,0,0.25)]">
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-extrabold text-white font-mono">{node.label}</h3>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono font-bold">
                  ACTIVE AGENT
                </span>
              </div>
              <p className="text-xs text-[#A1A1AA]">{node.role}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
          >
            <IconX className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-4 text-xs font-sans">
          <div>
            <span className="text-zinc-500 uppercase tracking-wider font-mono text-[10px]">
              Agent Responsibility
            </span>
            <p className="text-zinc-200 mt-1 text-sm font-medium leading-relaxed">
              {node.desc}
            </p>
          </div>

          {/* Telemetry Stats Grid */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="p-3 rounded-xl bg-black/40 border border-white/5">
              <div className="text-[10px] font-mono text-zinc-500 uppercase">Framework</div>
              <div className="text-sm font-bold text-white mt-0.5">Google ADK Agent</div>
            </div>
            <div className="p-3 rounded-xl bg-black/40 border border-white/5">
              <div className="text-[10px] font-mono text-zinc-500 uppercase">Average Latency</div>
              <div className="text-sm font-bold text-[#FF8A00] mt-0.5">3.8 ms</div>
            </div>
            <div className="p-3 rounded-xl bg-black/40 border border-white/5">
              <div className="text-[10px] font-mono text-zinc-500 uppercase">Memory Protocol</div>
              <div className="text-sm font-bold text-white mt-0.5">InMemorySessionService</div>
            </div>
            <div className="p-3 rounded-xl bg-black/40 border border-white/5">
              <div className="text-[10px] font-mono text-zinc-500 uppercase">Verification Rule</div>
              <div className="text-sm font-bold text-emerald-400 mt-0.5">Cryptographic Hash</div>
            </div>
          </div>

          {/* Active Tools */}
          <div>
            <span className="text-zinc-500 uppercase tracking-wider font-mono text-[10px]">
              Bound Tool APIs
            </span>
            <div className="flex flex-wrap gap-2 mt-1.5">
              {['web_search_tool', 'web_scraper_tool', 'file_processor_tool', 'evidence_verifier'].map((t) => (
                <span key={t} className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-zinc-300 font-mono text-[11px]">
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-white/10 bg-[#0A0A0A] flex items-center justify-between">
          <span className="text-[11px] text-zinc-500 font-mono">Status: Standby / Ready</span>
          <button
            type="button"
            onClick={onClose}
            className="btn-primary text-xs py-1.5 px-4"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  )
}
