import React, { useState } from 'react'
import {
  IconAlertTriangle,
  IconRefreshCw,
} from '../components/icons'

export default function AgentActivityView({
  taskResult,
  onRunDemo,
  onHumanDecision,
  onPlaySound
}) {
  const [selectedStep, setSelectedStep] = useState(null)
  const stepsTimeline = Object.values(taskResult?.steps || {})
  const isWaitingHuman = taskResult?.requires_human_approval || taskResult?.verdict === 'WAITING_FOR_HUMAN'
  const recoverySteps = stepsTimeline.filter((step) => step.recovery_action || step.attempts > 1 || step.status === 'RECOVERING')

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00] animate-ping" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              Agent Orchestrator Monitor
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">
            Real-Time Agent Execution & Recovery
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              onPlaySound?.('click')
              onRunDemo('recovery')
            }}
            className="btn-secondary text-xs"
          >
            <IconRefreshCw className="w-3.5 h-3.5 text-amber-400" />
            Run Recovery Scenario
          </button>

          <button
            type="button"
            onClick={() => {
              onPlaySound?.('click')
              onRunDemo('human')
            }}
            className="btn-secondary text-xs"
          >
            <IconAlertTriangle className="w-3.5 h-3.5 text-[#FF8A00]" />
            Run Human Gate Scenario
          </button>
        </div>
      </div>

      {!taskResult && (
        <section className="glass-panel p-6 rounded-2xl border border-white/10">
          <h2 className="text-base font-bold text-white">No active execution</h2>
          <p className="text-sm text-zinc-400 mt-2">
            Start a task to stream real agent steps, retries, approvals, and verification status.
          </p>
        </section>
      )}

      {taskResult?.error && (
        <section className="glass-panel p-6 rounded-2xl border border-red-500/30 bg-red-500/5">
          <h2 className="text-base font-bold text-red-300">Backend task error</h2>
          <p className="text-sm text-zinc-300 mt-2">{taskResult.error}</p>
        </section>
      )}

      {isWaitingHuman && (
        <section className="glass-panel-elevated p-6 rounded-2xl border-2 border-[#FF6A00] shadow-[0_0_40px_rgba(255,106,0,0.3)] bg-gradient-to-br from-[#1c1208] to-[#121212] animate-in fade-in zoom-in-95 duration-200">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-[#FF6A00]/20">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-[#FF6A00]/20 text-[#FF8A00] border border-[#FF6A00]/40 animate-pulse">
                <IconAlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-mono uppercase tracking-widest text-[#FF8A00] font-bold">
                  INTERVENTION PROTOCOL
                </span>
                <h2 className="text-lg sm:text-xl font-extrabold text-white">
                  HUMAN DECISION REQUIRED
                </h2>
              </div>
            </div>

            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-xs font-bold">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
              EXECUTION PAUSED
            </div>
          </div>

          <p className="text-sm text-zinc-200 leading-relaxed font-medium">
            {taskResult.human_decision_point || 'The backend paused because human judgment is required.'}
          </p>

          <div className="pt-5 flex flex-wrap items-center gap-3">
            {(taskResult.human_options || []).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => {
                  onPlaySound?.('click')
                  onHumanDecision?.(option)
                }}
                className="btn-primary text-xs py-2.5 px-4"
              >
                {option}
              </button>
            ))}
          </div>
        </section>
      )}

      {recoverySteps.length > 0 && (
        <section className="glass-panel p-6 rounded-2xl border border-amber-500/30 bg-gradient-to-br from-[#151109] to-[#101010]">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-white/5">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <IconRefreshCw className="w-5 h-5 animate-spin-slow" />
              </div>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-amber-400 font-bold">
                  AUTONOMOUS RECOVERY
                </span>
                <h2 className="text-base sm:text-lg font-bold text-white">
                  Recorded Failure Recovery
                </h2>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            {recoverySteps.map((step) => (
              <div key={step.step_id} className="p-3.5 rounded-xl bg-black/40 border border-amber-500/20">
                <div className="text-xs font-bold text-white">{step.description}</div>
                <p className="text-xs text-zinc-400 mt-1">{step.recovery_action || step.error || step.output_summary}</p>
                <div className="text-[11px] font-mono text-amber-400 mt-2">Attempts: {step.attempts}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="glass-panel p-6 rounded-2xl border border-white/10">
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-white/5">
          <h2 className="text-base font-bold text-white">
            Sequential Execution & Agent Audit Trail
          </h2>
          <span className="text-xs text-zinc-400 font-mono">{stepsTimeline.length} step(s) monitored</span>
        </div>

        <div className="space-y-2">
          {stepsTimeline.length === 0 ? (
            <div className="text-zinc-500 text-sm py-6">No backend step data available.</div>
          ) : stepsTimeline.map((st) => (
            <div
              key={st.step_id}
              onClick={() => {
                onPlaySound?.('hover')
                setSelectedStep(st.step_id)
              }}
              className={`p-3.5 rounded-xl border flex items-center justify-between gap-4 cursor-pointer transition-all ${
                selectedStep === st.step_id
                  ? 'bg-[#FF6A00]/10 border-[#FF6A00]/50 shadow-[0_0_15px_rgba(255,106,0,0.15)]'
                  : 'bg-black/30 border-white/5 hover:border-white/15'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="font-mono text-xs font-bold text-[#FF8A00] w-8">
                  {st.step_id}
                </span>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white">{st.description}</span>
                    <span className="text-[10px] font-mono text-zinc-400 bg-white/5 px-2 py-0.2 rounded">
                      {st.agent}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 truncate max-w-xl mt-0.5">
                    {st.output_summary || st.error || st.verification_reason || 'Waiting for backend output.'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0 font-mono text-xs">
                <span className="text-zinc-500 hidden sm:inline">{st.completed_at || st.started_at}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  st.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400' :
                  st.status === 'RUNNING' ? 'bg-[#FF6A00]/20 text-[#FF8A00]' :
                  'bg-zinc-800 text-zinc-400'
                }`}>
                  {st.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
