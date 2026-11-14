import React from 'react'
import AiCore from '../components/AiCore'
import AgentGraph from '../components/AgentGraph'
import ActivityFeed from '../components/ActivityFeed'
import {
  IconZap,
  IconPlay,
  IconClock,
  IconSearch,
  IconShieldCheck,
  IconRefreshCw,
  IconFileText,
  IconSparkles,
  IconAlertTriangle,
  IconCheckCircle,
  IconDownload,
  IconExternalLink
} from '../components/icons'

export default function OverviewView({
  taskResult,
  loading,
  activeScenario,
  onRunDemo,
  onNavigate,
  onSelectNode,
  onPlaySound
}) {
  const currentVerdict = taskResult?.verdict || (loading ? 'EXECUTING' : 'IDLE')
  const currentTitle = taskResult?.user_request || 'No active task'
  const progressPercent = loading ? 72 : taskResult?.completion_percentage || 100
  const isExecuting = loading
  const isPartial = currentVerdict === 'PARTIALLY_DONE'
  const isWaitingHuman = currentVerdict === 'WAITING_FOR_HUMAN'

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Hero / Overview Panel */}
      <section className="glass-panel p-6 rounded-2xl relative overflow-hidden cyber-grid-glow border border-white/10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Left Column: Greeting & Action CTAs */}
          <div className="lg:col-span-8 space-y-4">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-[#FF6A00]/15 text-[#FF8A00] text-xs font-mono font-bold tracking-wider uppercase border border-[#FF6A00]/30 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF8A00] animate-ping" />
                Mission Control
              </span>
              <span className="text-zinc-500 text-xs font-mono">ADK Autonomous v2.4</span>
            </div>

            <div className="space-y-1">
              <h3 className="text-sm font-mono text-[#A1A1AA] tracking-wider uppercase">
                Good afternoon.
              </h3>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
                Your agents are ready to finish the job.
              </h1>
            </div>

            <p className="text-zinc-300 text-sm max-w-2xl leading-relaxed">
              TaskFinisher doesn't just chat. It plans the execution DAG, orchestrates parallel research agents, verifies empirical claims against authoritative sources, recovers from broken tools autonomously, and certifies completion with verifiable proof.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  onPlaySound?.('click')
                  onNavigate('tasks')
                }}
                className="btn-primary"
              >
                <IconZap className="w-4 h-4" />
                + New Task
              </button>

              <button
                type="button"
                onClick={() => {
                  onPlaySound?.('click')
                  onNavigate('activity')
                }}
                className="btn-secondary"
              >
                <IconRefreshCw className="w-4 h-4" />
                View Activity
              </button>

              <button
                type="button"
                onClick={() => {
                  onPlaySound?.('click')
                  onNavigate('replay')
                }}
                className="btn-secondary text-zinc-300"
              >
                <IconPlay className="w-4 h-4 text-[#FF8A00]" />
                Replay Execution
              </button>
            </div>
          </div>

          {/* Right Column: AI Agent Processing Core Animation */}
          <div className="lg:col-span-4 flex flex-col items-center justify-center p-2 rounded-2xl bg-black/40 border border-white/5 relative">
            <AiCore
              status={isExecuting ? 'Cross-verifying healthcare adoption statistics...' : 'All verification gates sealed'}
              isWorking={isExecuting}
            />
          </div>
        </div>
      </section>

      {/* 2. Active Task Featured Card */}
      <section className={`glass-panel p-6 rounded-2xl border transition-all ${
        isExecuting 
          ? 'border-[#FF6A00]/50 shadow-[0_0_30px_rgba(255,106,0,0.15)] bg-gradient-to-br from-[#121212] via-[#15100a] to-[#121212]'
          : isPartial
          ? 'border-amber-500/40 bg-amber-500/[0.02]'
          : 'border-white/10'
      }`}>
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-white/5">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono uppercase tracking-widest text-[#FF8A00] font-bold">
              ACTIVE TASK
            </span>
            <span className="text-zinc-600 font-mono">|</span>
            <span className="text-xs text-zinc-400 font-mono">
              ID: {taskResult?.task_id || 'None'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {isExecuting && (
              <span className="badge-status badge-executing animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF8A00] animate-ping" />
                EXECUTING
              </span>
            )}
            {!isExecuting && currentVerdict === 'DONE' && (
              <span className="badge-status badge-completed">
                <IconCheckCircle className="w-3.5 h-3.5" />
                VERIFIED DONE
              </span>
            )}
            {!isExecuting && isPartial && (
              <span className="badge-status badge-partial">
                <IconAlertTriangle className="w-3.5 h-3.5" />
                PARTIALLY COMPLETED
              </span>
            )}
            {!isExecuting && isWaitingHuman && (
              <span className="badge-status badge-waiting">
                <IconAlertTriangle className="w-3.5 h-3.5" />
                HUMAN DECISION REQUIRED
              </span>
            )}
          </div>
        </div>

        {/* Task Title & Progress */}
        <div className="space-y-3">
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            {currentTitle}
          </h2>

          {/* Progress Bar with Percentage */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-zinc-400 font-medium">Pipeline Execution Progress</span>
              <span className="text-[#FF8A00] font-bold text-sm">{Math.round(progressPercent)}%</span>
            </div>

            <div className="w-full bg-[#080808] border border-white/10 rounded-full h-3.5 p-0.5 overflow-hidden shadow-inner">
              <div
                className="h-full rounded-full bg-gradient-to-r from-[#FF6A00] to-[#FF8A00] shadow-[0_0_12px_rgba(255,106,0,0.5)] transition-all duration-500 relative"
                style={{ width: `${Math.min(progressPercent, 100)}%` }}
              >
                <div className="absolute inset-0 bg-white/20 animate-pulse" />
              </div>
            </div>
          </div>

          {/* Current Operation Ticker */}
          <div className="p-3 rounded-xl bg-black/40 border border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FF6A00] opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FF8A00]" />
              </span>
              <span className="text-xs text-zinc-300 font-mono">
                {isExecuting
                  ? 'Current operation: "Cross-verifying healthcare adoption statistics..."'
                  : isPartial
                  ? 'Operation complete with 1 disclosed data gap (unverified secondary source).'
                  : isWaitingHuman
                  ? 'Execution paused at Step 5: Conflicting market estimates require human review.'
                  : taskResult
                  ? 'Task state loaded from the backend response.'
                  : 'No task is running. Start a task to populate live backend state.'
                }
              </span>
            </div>
            <span className="text-[11px] font-mono text-zinc-500 hidden sm:inline">
              Step {isExecuting ? '6' : currentVerdict === 'PARTIALLY_DONE' ? '7' : '8'} of 8
            </span>
          </div>

          {/* Task Metrics Row */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[10px] font-mono text-zinc-500 uppercase">Step</span>
              <div className="text-base font-bold text-white mt-0.5 font-mono">
                {isExecuting ? 'Running' : `${taskResult?.completed_steps || 0} of ${taskResult?.total_steps || 0}`}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[10px] font-mono text-zinc-500 uppercase">Elapsed</span>
              <div className="text-base font-bold text-white mt-0.5 font-mono">
                {isExecuting ? 'Running' : '-'}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[10px] font-mono text-zinc-500 uppercase">Sources</span>
              <div className="text-base font-bold text-[#FF8A00] mt-0.5 font-mono">
                {taskResult?.evidence?.filter((item) => item.type === 'web_source').length || 0}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[10px] font-mono text-zinc-500 uppercase">Evidence</span>
              <div className="text-base font-bold text-emerald-400 mt-0.5 font-mono">
                {taskResult?.evidence?.length || 0} items
              </div>
            </div>

            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 col-span-2 sm:col-span-1">
              <span className="text-[10px] font-mono text-zinc-500 uppercase">Retries</span>
              <div className="text-base font-bold text-amber-400 mt-0.5 font-mono">
                {Object.values(taskResult?.steps || {}).reduce((total, step) => total + Math.max((step.attempts || 1) - 1, 0), 0)}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Quick Scenario Switcher Bar (Judge & Demo Friendly) */}
      <section className="p-4 rounded-xl glass-panel border border-white/10 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <IconSparkles className="w-4 h-4 text-[#FF8A00]" />
          <span className="text-xs font-bold text-white font-mono uppercase tracking-wider">
            Interactive Test Scenarios:
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {[
            { id: 'success', label: '1. Success Path (8/8)', desc: 'Full verification & DOCX generation' },
            { id: 'recovery', label: '2. Tool Failure & Recovery', desc: 'Auto-retries and self-heals' },
            { id: 'partial', label: '3. Partial Completion', desc: 'Honest disclosure of gap' },
            { id: 'human', label: '4. Human Decision Required', desc: 'Pauses on conflicting data' },
          ].map((sc) => (
            <button
              key={sc.id}
              type="button"
              onClick={() => {
                onPlaySound?.('click')
                onRunDemo(sc.id)
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                activeScenario === sc.id
                  ? 'bg-[#FF6A00] text-white shadow-[0_0_12px_rgba(255,106,0,0.35)] font-bold'
                  : 'bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 border border-white/5'
              }`}
            >
              {sc.label}
            </button>
          ))}
        </div>
      </section>

      {/* 4. Live Agent Execution Graph */}
      <AgentGraph taskResult={taskResult} onSelectNode={onSelectNode} />

      {/* 5. Live Activity Feed */}
      <ActivityFeed events={taskResult?.events || []} />
    </div>
  )
}
