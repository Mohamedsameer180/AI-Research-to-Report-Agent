import React, { useState } from 'react'
import {
  IconAlertTriangle,
  IconBarChart,
  IconCheck,
  IconCheckCircle,
  IconChevronRight,
  IconCpu,
  IconFileText,
  IconPlay,
  IconRefreshCw,
  IconSearch,
  IconShieldCheck,
  IconUpload,
  IconZap,
} from '../components/icons'

const EXAMPLE_PROMPTS = [
  'Research this topic across reliable sources, verify every claim, recover from any failed sources, and produce a completion report.',
  'Read the attached PDFs, extract the key findings, cross-check them online, and generate a verified report.',
  'Compare multiple sources, identify conflicts, ask for human approval if needed, and only mark the task complete after final verification.',
]

const DEPTH_OPTIONS = [
  { id: 'Quick', label: 'Quick', desc: 'Focused run with core verification gates.' },
  { id: 'Standard', label: 'Standard', desc: 'Balanced multi-source research and report generation.' },
  { id: 'Deep Research', label: 'Deep Research', desc: 'Broader evidence gathering with stricter conflict checks.' },
]

const OUTPUT_OPTIONS = ['DOCX', 'PDF', 'Both']

const PIPELINE_STEPS = [
  { label: 'USER TASK', detail: 'Capture the multi-step request and desired artifact.', icon: IconZap },
  { label: 'PLAN', detail: 'Break the task into executable steps and success criteria.', icon: IconCpu },
  { label: 'READ 5 PDFs', detail: 'Inspect uploaded PDFs/files and record extraction evidence.', icon: IconFileText },
  { label: 'RESEARCH WEB', detail: 'Gather reliable web sources with URLs and metadata.', icon: IconSearch },
  { label: 'VERIFY INFORMATION', detail: 'Cross-check claims against collected evidence.', icon: IconShieldCheck },
  { label: 'FAILURE?', detail: 'If a step fails, retry or recover. If judgment is needed, ask a human.', icon: IconAlertTriangle, branch: true },
  { label: 'GENERATE REPORT', detail: 'Create the requested final artifact from verified state.', icon: IconFileText },
  { label: 'FINAL VERIFICATION', detail: 'Confirm each required step succeeded before completion.', icon: IconCheckCircle },
  { label: 'COMPLETION REPORT', detail: 'Return the artifact, evidence trail, status, and honest verdict.', icon: IconBarChart },
]

const DEFINITION_OF_DONE = [
  'The user task is converted into a concrete plan.',
  'Files and PDFs are read when provided.',
  'Web research collects reliable sources instead of invented claims.',
  'Each important claim is verified against evidence.',
  'Failures trigger retry or recovery before moving on.',
  'Human approval is requested for ambiguity, conflicts, or permission-sensitive decisions.',
  'The report is generated only after the work is checked.',
  'Final verification decides the honest status: complete, partial, failed, or waiting for human input.',
]

export default function TasksView({
  loading,
  onSubmitTask,
  onRunDemo,
  onPlaySound
}) {
  const [taskPrompt, setTaskPrompt] = useState('')
  const [depth, setDepth] = useState('Standard')
  const [outputFormat, setOutputFormat] = useState('Both')
  const [selectedFiles, setSelectedFiles] = useState([])

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files || [])
    if (files.length) {
      setSelectedFiles(prev => [
        ...prev,
        ...files.map(file => ({
          file,
          name: file.name,
          type: file.type || 'unknown',
          bytes: file.size,
          size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        })),
      ])
      onPlaySound?.('click')
    }
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!taskPrompt.trim()) return
    onPlaySound?.('click')
    onSubmitTask({
      prompt: [
        taskPrompt.trim(),
        '',
        `Execution contract: Take the user's multi-step task, execute it using tools, verify that each step actually succeeded, recover from failures, ask a human when necessary, and only then declare the task complete.`,
        `Research depth: ${depth}`,
        `Output format: ${outputFormat}`,
      ].join('\n'),
      depth,
      outputFormat,
      files: selectedFiles,
    })
  }

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-4xl">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00]" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              Task Studio & Verification Pipeline
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">
            Finish the task only after the work is proven.
          </h1>
          <p className="text-sm text-zinc-300 leading-relaxed mt-2">
            Take a user's multi-step task, execute it using tools, verify that each step actually succeeded,
            recover from failures, ask a human when necessary, and only then declare the task complete.
          </p>
        </div>

        <span className="badge-status badge-executing">
          Verified execution contract
        </span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-6 space-y-6">
          <form onSubmit={handleSubmit} className="glass-panel p-6 rounded-2xl border border-white/10 space-y-5">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label htmlFor="taskInput" className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold">
                  User Task
                </label>
                <span className="text-[11px] text-zinc-500 font-mono">
                  Multi-step tasks, files, research, and reports
                </span>
              </div>

              <textarea
                id="taskInput"
                rows="7"
                value={taskPrompt}
                onChange={(event) => setTaskPrompt(event.target.value)}
                placeholder="Describe the complete job: what to read, what to research, what to verify, when to ask you, and what final report you need."
                className="w-full bg-[#0A0A0A] border border-white/10 focus:border-[#FF6A00] focus:ring-1 focus:ring-[#FF6A00] rounded-xl p-4 text-sm text-white placeholder:text-zinc-600 outline-none transition-all resize-none font-sans"
              />
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                Quick starters:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {EXAMPLE_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => {
                      onPlaySound?.('hover')
                      setTaskPrompt(prompt)
                    }}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-white/[0.03] hover:bg-white/[0.07] border border-white/5 text-zinc-400 hover:text-white transition-all text-left max-w-full"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-white/5">
              <label className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold block">
                Supporting PDFs / Files
              </label>

              <label className="border-2 border-dashed border-white/10 hover:border-[#FF6A00]/50 rounded-xl p-4 flex flex-col items-center justify-center gap-2 cursor-pointer bg-black/20 hover:bg-[#FF6A00]/[0.02] transition-all group">
                <IconUpload className="w-5 h-5 text-zinc-500 group-hover:text-[#FF8A00] transition-colors" />
                <span className="text-xs text-zinc-300 font-medium group-hover:text-white">
                  Add files for the Document Agent
                </span>
                <span className="text-[10px] text-zinc-500 font-mono">
                  PDF, DOCX, XLSX, CSV, TXT, or MD
                </span>
                <input
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                  className="hidden"
                  accept=".pdf,.docx,.xlsx,.csv,.txt,.md"
                />
              </label>

              {selectedFiles.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {selectedFiles.map((file, index) => (
                    <div key={`${file.name}-${index}`} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#141414] border border-white/10 text-xs text-zinc-200">
                      <IconFileText className="w-3.5 h-3.5 text-[#FF8A00]" />
                      <span className="font-mono">{file.name}</span>
                      <span className="text-[10px] text-zinc-500 font-mono">({file.size})</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-white/5">
              <div className="space-y-2">
                <label className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold block">
                  Research Depth
                </label>
                <div className="space-y-2">
                  {DEPTH_OPTIONS.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => {
                        onPlaySound?.('hover')
                        setDepth(option.id)
                      }}
                      className={`w-full p-3 rounded-xl border text-left transition-all ${
                        depth === option.id
                          ? 'bg-[#FF6A00]/15 border-[#FF6A00] shadow-[0_0_15px_rgba(255,106,0,0.2)]'
                          : 'bg-black/30 border-white/5 hover:border-white/15'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-white">{option.label}</span>
                        {depth === option.id && <span className="w-2 h-2 rounded-full bg-[#FF8A00]" />}
                      </div>
                      <span className="text-[10px] text-zinc-400 block leading-tight">{option.desc}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold block">
                  Final Artifact
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {OUTPUT_OPTIONS.map((format) => (
                    <button
                      key={format}
                      type="button"
                      onClick={() => {
                        onPlaySound?.('hover')
                        setOutputFormat(format)
                      }}
                      className={`px-3 py-2 rounded-xl text-xs font-mono font-semibold border transition-all ${
                        outputFormat === format
                          ? 'bg-[#FF6A00]/20 border-[#FF6A00] text-[#FF8A00]'
                          : 'bg-black/30 border-white/5 text-zinc-400 hover:text-white'
                      }`}
                    >
                      {format}
                    </button>
                  ))}
                </div>

                <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs text-zinc-400 leading-relaxed">
                  The final verifier can return complete, partial, failed, or waiting for human input.
                </div>
              </div>
            </div>

            <div className="pt-4 flex flex-wrap items-center justify-between gap-3 border-t border-white/10">
              <span className="text-xs text-zinc-500 font-mono">
                Verify every step before declaring completion
              </span>

              <button
                type="submit"
                disabled={loading || !taskPrompt.trim()}
                className="btn-primary px-6 py-3 text-sm"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                    EXECUTING TASK
                  </>
                ) : (
                  <>
                    <IconPlay className="w-4 h-4 fill-white" />
                    START TASK
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        <div className="xl:col-span-6 space-y-6">
          <section className="glass-panel-elevated p-6 rounded-2xl border border-white/10 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-white/5">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#FF8A00] font-bold">
                  Autonomous ADK Flow
                </span>
                <h2 className="text-base font-bold text-white">
                  Execution Pipeline
                </h2>
              </div>
              <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                Human-safe completion
              </span>
            </div>

            <div className="space-y-2">
              {PIPELINE_STEPS.map((step, index) => {
                const Icon = step.icon
                return (
                  <div key={step.label}>
                    <div className={`p-3 rounded-xl border flex items-start gap-3 ${
                      step.branch
                        ? 'bg-amber-500/5 border-amber-500/30'
                        : 'bg-black/40 border-white/5'
                    }`}>
                      <div className={`p-2 rounded-lg shrink-0 ${
                        step.branch
                          ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                          : 'bg-[#FF6A00]/15 text-[#FF8A00] border border-[#FF6A00]/25'
                      }`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono text-zinc-500">
                            {String(index + 1).padStart(2, '0')}
                          </span>
                          <h3 className="text-xs font-bold text-white tracking-wide">
                            {step.label}
                          </h3>
                        </div>
                        <p className="text-[11px] text-zinc-400 leading-relaxed mt-0.5">
                          {step.detail}
                        </p>

                        {step.branch && (
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
                            <div className="p-2 rounded-lg bg-black/40 border border-amber-500/20 text-[11px] text-amber-300 font-mono flex items-center gap-2">
                              <IconRefreshCw className="w-3.5 h-3.5" />
                              YES: RETRY / RECOVER
                            </div>
                            <div className="p-2 rounded-lg bg-black/40 border border-emerald-500/20 text-[11px] text-emerald-300 font-mono flex items-center gap-2">
                              <IconChevronRight className="w-3.5 h-3.5" />
                              NO: CONTINUE
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {index < PIPELINE_STEPS.length - 1 && (
                      <div className="ml-6 h-4 border-l border-white/10" />
                    )}
                  </div>
                )
              })}
            </div>
          </section>

          <section className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/5">
              <h2 className="text-base font-bold text-white">Definition Of Done</h2>
              <span className="text-xs text-zinc-500 font-mono">{DEFINITION_OF_DONE.length} checks</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {DEFINITION_OF_DONE.map((item) => (
                <div key={item} className="p-3 rounded-xl bg-black/30 border border-white/5 flex items-start gap-2.5">
                  <div className="p-1 rounded bg-emerald-500/20 text-emerald-400 mt-0.5 shrink-0">
                    <IconCheck className="w-3 h-3" />
                  </div>
                  <span className="text-xs text-zinc-300 leading-relaxed">{item}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { label: 'Planner', value: 'Builds steps', icon: IconCpu },
              { label: 'Verifier', value: 'Checks success', icon: IconShieldCheck },
              { label: 'Recovery', value: 'Retries failures', icon: IconRefreshCw },
            ].map((item) => {
              const Icon = item.icon
              return (
                <div key={item.label} className="p-4 rounded-xl bg-black/40 border border-white/10">
                  <Icon className="w-4 h-4 text-[#FF8A00]" />
                  <div className="text-xs text-zinc-500 font-mono mt-3 uppercase">{item.label}</div>
                  <div className="text-sm font-bold text-white mt-0.5">{item.value}</div>
                </div>
              )
            })}
          </section>
        </div>
      </div>
    </div>
  )
}
