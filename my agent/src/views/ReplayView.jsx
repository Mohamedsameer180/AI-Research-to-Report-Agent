import React, { useState, useEffect } from 'react'
import {
  IconPlay,
  IconPause,
  IconRotateCcw,
  IconCpu,
} from '../components/icons'

const buildTimeline = (taskResult) => {
  const steps = Object.values(taskResult?.steps || {})
  if (!steps.length) return []

  return steps.map((step, index) => ({
    time: step.completed_at || step.started_at || taskResult.updated_at || '',
    agent: step.agent,
    action: step.description,
    status: step.status,
    input: step.input_summary || taskResult.user_request,
    tool: step.tool_used?.length ? step.tool_used.join(', ') : 'No external tool recorded',
    output: step.output_summary || step.error || 'No output summary recorded.',
    evidence: `${step.evidence?.length || 0} evidence item(s)`,
    decision: step.verification_reason || step.verification_status || 'Pending verification detail',
    step_id: step.step_id || `S${index + 1}`,
  }))
}

export default function ReplayView({ taskResult, onPlaySound }) {
  const timelineSteps = buildTimeline(taskResult)
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)

  const activeStep = timelineSteps[currentStepIndex]

  useEffect(() => {
    if (currentStepIndex >= timelineSteps.length) {
      setCurrentStepIndex(0)
    }
  }, [currentStepIndex, timelineSteps.length])

  useEffect(() => {
    let interval = null
    if (isPlaying && timelineSteps.length > 0) {
      interval = setInterval(() => {
        setCurrentStepIndex((prev) => {
          if (prev >= timelineSteps.length - 1) {
            setIsPlaying(false)
            onPlaySound?.('complete')
            return prev
          }
          onPlaySound?.('hover')
          return prev + 1
        })
      }, 2400 / playbackSpeed)
    }
    return () => clearInterval(interval)
  }, [isPlaying, playbackSpeed, timelineSteps.length, onPlaySound])

  const togglePlay = () => {
    onPlaySound?.('click')
    if (currentStepIndex >= timelineSteps.length - 1) {
      setCurrentStepIndex(0)
    }
    setIsPlaying(!isPlaying)
  }

  const handleReset = () => {
    onPlaySound?.('click')
    setIsPlaying(false)
    setCurrentStepIndex(0)
  }

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00]" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              Backend Step Replay
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">
            Execution Replay & Time Scrubber
          </h1>
        </div>

        <div className="flex items-center gap-2 bg-black/60 p-1.5 rounded-xl border border-white/10">
          <button
            type="button"
            onClick={handleReset}
            className="p-2 rounded-lg hover:bg-white/10 text-zinc-400 hover:text-white transition-colors"
            title="Reset Replay"
            disabled={timelineSteps.length === 0}
          >
            <IconRotateCcw className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={togglePlay}
            className="btn-primary text-xs py-1.5 px-3.5"
            disabled={timelineSteps.length === 0}
          >
            {isPlaying ? (
              <>
                <IconPause className="w-3.5 h-3.5" />
                Pause
              </>
            ) : (
              <>
                <IconPlay className="w-3.5 h-3.5 fill-white" />
                Play Replay
              </>
            )}
          </button>

          <div className="flex items-center gap-1 border-l border-white/10 pl-2">
            {[1, 2, 5].map((spd) => (
              <button
                key={spd}
                type="button"
                onClick={() => {
                  onPlaySound?.('hover')
                  setPlaybackSpeed(spd)
                }}
                className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold transition-colors ${
                  playbackSpeed === spd
                    ? 'bg-[#FF6A00]/20 text-[#FF8A00] border border-[#FF6A00]/40'
                    : 'text-zinc-500 hover:text-white'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {timelineSteps.length === 0 ? (
        <section className="glass-panel p-6 rounded-2xl border border-white/10">
          <h2 className="text-base font-bold text-white">No replay data yet</h2>
          <p className="text-sm text-zinc-400 mt-2">
            Run a task through the backend to replay actual execution steps.
          </p>
        </section>
      ) : (
        <>
          <section className="glass-panel p-5 rounded-2xl border border-white/10 space-y-4">
            <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
              <span>Execution Timeline:</span>
              <span className="text-[#FF8A00] font-bold">
                Step {currentStepIndex + 1} of {timelineSteps.length} ({activeStep.time})
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
              {timelineSteps.map((st, idx) => {
                const isActive = idx === currentStepIndex
                const isPassed = idx < currentStepIndex

                return (
                  <button
                    key={st.step_id}
                    type="button"
                    onClick={() => {
                      onPlaySound?.('hover')
                      setCurrentStepIndex(idx)
                      setIsPlaying(false)
                    }}
                    className={`p-2.5 rounded-xl border text-left transition-all ${
                      isActive
                        ? 'bg-[#FF6A00]/15 border-[#FF6A00] shadow-[0_0_15px_rgba(255,106,0,0.3)]'
                        : isPassed
                        ? 'bg-emerald-500/5 border-emerald-500/30 text-zinc-300'
                        : 'bg-black/40 border-white/5 text-zinc-500'
                    }`}
                  >
                    <div className="flex items-center justify-between font-mono text-[10px] mb-1">
                      <span className={isActive ? 'text-[#FF8A00] font-bold' : ''}>{st.step_id}</span>
                    </div>
                    <div className="text-[11px] font-bold truncate text-white">
                      {st.agent}
                    </div>
                  </button>
                )
              })}
            </div>
          </section>

          <section className="glass-panel-elevated p-6 rounded-2xl border border-white/10 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-white/5">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[#FF6A00]/15 text-[#FF8A00] border border-[#FF6A00]/30">
                  <IconCpu className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-widest text-[#FF8A00] font-bold">
                    {activeStep.step_id} - {activeStep.agent}
                  </span>
                  <h2 className="text-base sm:text-lg font-bold text-white">
                    {activeStep.action}
                  </h2>
                </div>
              </div>

              <span className="px-2.5 py-1 rounded text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {activeStep.status}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-4 rounded-xl bg-black/50 border border-white/5 space-y-1.5">
                <span className="text-zinc-500 text-[10px] uppercase font-bold">Input Payload:</span>
                <p className="text-zinc-200 font-sans leading-relaxed">{activeStep.input}</p>
              </div>

              <div className="p-4 rounded-xl bg-black/50 border border-white/5 space-y-1.5">
                <span className="text-zinc-500 text-[10px] uppercase font-bold">Tool Utilized:</span>
                <div className="text-[#FF8A00] font-bold text-xs bg-[#FF6A00]/10 p-2 rounded border border-[#FF6A00]/20">
                  {activeStep.tool}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-black/50 border border-white/5 space-y-1.5">
                <span className="text-zinc-500 text-[10px] uppercase font-bold">Agent Output & Result:</span>
                <p className="text-zinc-200 font-sans leading-relaxed">{activeStep.output}</p>
              </div>

              <div className="p-4 rounded-xl bg-black/50 border border-white/5 space-y-2">
                <div>
                  <span className="text-zinc-500 text-[10px] uppercase font-bold">Verified Evidence:</span>
                  <div className="text-emerald-400 font-semibold mt-0.5">{activeStep.evidence}</div>
                </div>
                <div>
                  <span className="text-zinc-500 text-[10px] uppercase font-bold">Autonomous Decision:</span>
                  <div className="text-white font-semibold mt-0.5">{activeStep.decision}</div>
                </div>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
