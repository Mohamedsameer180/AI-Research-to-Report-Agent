import React from 'react'
import {
  IconCheckCircle,
  IconClock,
  IconRefreshCw,
  IconShieldCheck,
  IconAlertTriangle,
} from '../components/icons'

export default function AnalyticsView({ taskResult }) {
  const steps = Object.values(taskResult?.steps || {})
  const completedSteps = steps.filter((step) => step.status === 'COMPLETED').length
  const retries = steps.reduce((total, step) => total + Math.max((step.attempts || 1) - 1, 0), 0)
  const evidenceCount = taskResult?.evidence?.length || 0
  const agentBreakdown = steps.map((step) => ({
    agent: step.agent,
    share: Math.max(8, Math.round(100 / Math.max(steps.length, 1))),
    avgLatency: `${step.attempts || 1} attempt(s)`,
  }))

  const metrics = [
    { label: 'Tasks Loaded', value: taskResult?.task_id ? '1' : '0', icon: IconCheckCircle, change: 'Current browser session', color: 'text-white' },
    { label: 'Completion', value: `${Math.round(taskResult?.completion_percentage || 0)}%`, icon: IconShieldCheck, change: taskResult?.verdict || 'No active task', color: 'text-emerald-400' },
    { label: 'Steps Completed', value: `${completedSteps}/${steps.length || 0}`, icon: IconClock, change: 'Backend step state', color: 'text-[#FF8A00]' },
    { label: 'Retries', value: String(retries), icon: IconRefreshCw, change: 'Recorded attempts above first run', color: 'text-amber-400' },
    { label: 'Human Interventions', value: taskResult?.requires_human_approval ? '1' : '0', icon: IconAlertTriangle, change: 'Active approval gate', color: 'text-zinc-300' },
    { label: 'Evidence Generated', value: String(evidenceCount), icon: IconShieldCheck, change: 'Backend evidence entries', color: 'text-[#FF8A00]' },
  ]

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00]" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              System Intelligence & Telemetry
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">
            Analytics Dashboard
          </h1>
        </div>

        <div className="text-xs font-mono text-zinc-400 bg-black/40 px-3 py-1.5 rounded-xl border border-white/10">
          Telemetry Source: <strong className="text-white">Active Backend Task</strong>
        </div>
      </div>

      {/* 6 Key Telemetry Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((m, idx) => {
          const Icon = m.icon

          return (
            <div
              key={idx}
              className="glass-panel p-5 rounded-2xl border border-white/10 hover:border-[#FF6A00]/40 transition-all space-y-2 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold">
                  {m.label}
                </span>
                <div className="p-2 rounded-lg bg-black/40 text-[#FF8A00] border border-white/5 group-hover:border-[#FF6A00]/30 transition-colors">
                  <Icon className="w-4 h-4" />
                </div>
              </div>

              <div className={`text-3xl font-extrabold font-mono tracking-tight ${m.color}`}>
                {m.value}
              </div>

              <div className="text-[11px] text-zinc-500 font-mono flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF8A00]" />
                {m.change}
              </div>
            </div>
          )
        })}
      </div>

      {/* High-Tech Black & Orange Minimal Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Daily Execution Workload Chart */}
        <div className="lg:col-span-7 glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <div>
              <h3 className="text-sm font-bold text-white">Daily Agent Execution Volume</h3>
              <p className="text-xs text-zinc-400 font-mono">Tasks Completed vs Autonomous Recoveries</p>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="flex items-center gap-1 text-zinc-300">
                <span className="w-2 h-2 rounded-full bg-[#FF6A00]" /> Completed
              </span>
              <span className="flex items-center gap-1 text-amber-400">
                <span className="w-2 h-2 rounded-full bg-amber-500" /> Recovered
              </span>
            </div>
          </div>

          {/* SVG Bar Chart with Black/Orange Minimal Aesthetic */}
          <div className="h-56 w-full flex items-end justify-between gap-3 pt-6 px-2 font-mono text-xs">
            {(steps.length ? steps : [{ step_id: 'S0', completed: 0, recovered: 0 }]).map((step, index) => {
              const compHeight = step.status === 'COMPLETED' ? 90 : step.status ? 45 : 4
              const recHeight = Math.min(((step.attempts || 1) - 1) * 20, 60)

              return (
                <div key={step.step_id || index} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                  <div className="text-[10px] text-zinc-500 opacity-0 group-hover:opacity-100 transition-opacity">
                    {step.status || 'No data'}
                  </div>

                  <div className="w-full max-w-[32px] bg-black/60 rounded-t-lg overflow-hidden flex flex-col justify-end h-full border border-white/5 group-hover:border-[#FF6A00]/50 transition-colors p-0.5 gap-0.5">
                    {/* Recovery bar component */}
                    {recHeight > 0 && (
                      <div
                        style={{ height: `${recHeight}%` }}
                        className="w-full bg-amber-500/70 rounded-t"
                        title={`${(step.attempts || 1) - 1} retries`}
                      />
                    )}
                    {/* Completed bar component */}
                    <div
                      style={{ height: `${compHeight}%` }}
                      className="w-full bg-gradient-to-t from-[#CC5500] to-[#FF6A00] rounded-t shadow-[0_0_8px_rgba(255,106,0,0.3)]"
                    title={step.description || 'No task data'}
                  />
                  </div>

                  <span className="text-[11px] text-zinc-400 group-hover:text-white transition-colors">
                    {step.step_id || 'S0'}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Agent Role Distribution & Average Latency */}
        <div className="lg:col-span-5 glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <div>
              <h3 className="text-sm font-bold text-white">Agent Workload & Latency</h3>
              <p className="text-xs text-zinc-400 font-mono">ADK Worker Performance</p>
            </div>
            <span className="text-xs font-mono text-[#FF8A00]">12 Workers</span>
          </div>

          <div className="space-y-3.5">
            {(agentBreakdown.length ? agentBreakdown : [{ agent: 'No backend task', share: 0, avgLatency: '0 attempts' }]).map((ag, index) => (
              <div key={`${ag.agent}-${index}`} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-zinc-200 font-medium">{ag.agent}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-zinc-500">Avg: <strong className="text-zinc-300">{ag.avgLatency}</strong></span>
                    <span className="text-[#FF8A00] font-bold">{ag.share}% load</span>
                  </div>
                </div>

                <div className="w-full bg-zinc-900 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-[#FF6A00] to-[#FF8A00] h-full rounded-full"
                    style={{ width: `${ag.share}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
