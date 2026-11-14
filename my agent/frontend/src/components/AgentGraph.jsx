import React, { useState } from 'react'
import {
  IconCpu,
  IconZap,
  IconNetwork,
  IconShieldCheck,
  IconAlertTriangle,
  IconFileText,
  IconSearch,
  IconCheckCircle,
  IconRefreshCw,
  IconSparkles,
  IconInfo
} from './icons'

const nodeMeta = {
  TASK: { label: 'TASK', role: 'Input Intake', icon: IconZap, desc: 'Accepts requirements & verifies Definition of Done.' },
  PLANNER: { label: 'PLANNER', role: 'DAG Orchestrator', icon: IconCpu, desc: 'Constructs sub-agent dependencies & execution plan.' },
  RESEARCH: { label: 'RESEARCH AGENT', role: 'Web Scraper', icon: IconSearch, desc: 'Finds authoritative sources & extracts claims.' },
  DOCUMENT: { label: 'DOCUMENT AGENT', role: 'PDF Engine', icon: IconFileText, desc: 'Parses local PDFs, spreadsheets, and documents.' },
  DATA: { label: 'DATA AGENT', role: 'Cross-Check', icon: IconNetwork, desc: 'Validates quantitative claims and correlations.' },
  VERIFY: { label: 'VERIFY', role: 'Evidence Gate', icon: IconShieldCheck, desc: 'Enforces truth rules and flags hallucinations.' },
  PASSED: { label: 'PASSED', role: 'Verified Gate', icon: IconCheckCircle, desc: 'Directs validated findings to document synthesis.' },
  FAILED: { label: 'FAILED', role: 'Exception Gate', icon: IconAlertTriangle, desc: 'Detects broken tools, bad APIs, or conflicting data.' },
  RECOVERY: { label: 'RECOVERY', role: 'Self-Heal Agent', icon: IconRefreshCw, desc: 'Autonomous fallback discovery & retry protocols.' },
  COMPLETION: { label: 'COMPLETION', role: 'Truth Proof', icon: IconSparkles, desc: 'Produces immutable audit trail & finalized documents.' },
}

export default function AgentGraph({ taskResult, activeNodeId = 'VERIFY', onSelectNode }) {
  const [hoveredNode, setHoveredNode] = useState(null)

  // Dynamic node status mapping based on active execution state
  const getNodeStatus = (id) => {
    if (!taskResult || !taskResult.steps) {
      if (id === 'TASK') return 'active'
      return 'waiting'
    }

    const steps = taskResult.steps
    const s1 = steps['S1']?.status === 'COMPLETED'
    const s2 = steps['S2']?.status === 'COMPLETED'
    const s3 = steps['S3']?.status === 'COMPLETED'
    const s4 = steps['S4']?.status === 'COMPLETED'
    const s5 = steps['S5']?.status === 'COMPLETED'
    const s6 = steps['S6']
    const s7 = steps['S7']?.status === 'COMPLETED'
    const s8 = steps['S8']?.status === 'COMPLETED'
    const isDone = taskResult.verdict === 'DONE' || taskResult.status === 'COMPLETED'
    const isHuman = taskResult.verdict === 'WAITING_FOR_HUMAN' || taskResult.status === 'WAITING_FOR_HUMAN'
    const isPartial = taskResult.verdict === 'PARTIALLY_DONE' || taskResult.status === 'PARTIALLY_COMPLETED'
    const isFailed = taskResult.verdict === 'FAILED' || taskResult.status === 'FAILED'

    if (id === 'TASK') return 'completed'
    if (id === 'PLANNER') return (s1 && s2) ? 'completed' : 'active'
    if (id === 'DOCUMENT') return s3 ? 'completed' : (s2 ? 'active' : 'waiting')
    if (id === 'RESEARCH') return s4 ? 'completed' : (s3 ? 'active' : 'waiting')
    if (id === 'DATA') return s5 ? 'completed' : (s4 ? 'active' : 'waiting')
    if (id === 'VERIFY') {
      if (s5) return 'completed'
      if (s4) return 'active'
      return 'waiting'
    }
    if (id === 'FAILED') {
      if (isFailed || isHuman || (s6 && s6.status === 'FAILED')) return 'warning'
      return 'waiting'
    }
    if (id === 'RECOVERY') {
      if (s6 && (s6.recovery_action || s6.status === 'RECOVERING' || s6.attempts > 1)) return 'completed'
      if (isHuman) return 'warning'
      return 'waiting'
    }
    if (id === 'PASSED') {
      if (isDone || isPartial) return 'completed'
      if (s5 && !isFailed) return 'active'
      return 'waiting'
    }
    if (id === 'COMPLETION') {
      if (isDone) return 'completed'
      if (isPartial) return 'warning'
      if (isFailed) return 'waiting'
      if (s7 && s8) return 'completed'
      if (s7) return 'active'
      return 'waiting'
    }
    return 'waiting'
  }

  return (
    <div className="glass-panel p-5 rounded-xl relative overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00] animate-ping" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              Live Agent Execution Graph
            </span>
          </div>
          <h3 className="text-base font-bold text-white mt-0.5">
            Autonomous Multi-Agent DAG Orchestration
          </h3>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5 text-zinc-400">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FF6A00] shadow-[0_0_8px_#FF6A00]" />
            Active Node
          </span>
          <span className="flex items-center gap-1.5 text-zinc-400">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
            Completed
          </span>
          <span className="flex items-center gap-1.5 text-zinc-400">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            Exception / Recovery
          </span>
        </div>
      </div>

      {/* SVG Canvas for graph with high-tech glowing laser paths */}
      <div className="relative w-full overflow-x-auto py-2">
        <div className="min-w-[840px] h-[340px] relative">
          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 840 340">
            <defs>
              <linearGradient id="laserGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#FF6A00" stopOpacity="0.8" />
                <stop offset="50%" stopColor="#FF8A00" stopOpacity="1" />
                <stop offset="100%" stopColor="#FF6A00" stopOpacity="0.4" />
              </linearGradient>
              <filter id="laserGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Static background lines */}
            {/* TASK -> PLANNER */}
            <line x1="85" y1="170" x2="160" y2="170" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />
            
            {/* PLANNER -> Branch (RESEARCH, DOCUMENT, DATA) */}
            <path d="M 230 170 L 265 170 L 265 75 L 300 75" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />
            <path d="M 230 170 L 300 170" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />
            <path d="M 230 170 L 265 170 L 265 265 L 300 265" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />

            {/* Branch -> VERIFY */}
            <path d="M 410 75 L 445 75 L 445 170 L 480 170" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />
            <path d="M 410 170 L 480 170" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />
            <path d="M 410 265 L 445 265 L 445 170 L 480 170" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />

            {/* VERIFY -> PASSED / FAILED */}
            <path d="M 550 170 L 575 170 L 575 110 L 600 110" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />
            <path d="M 550 170 L 575 170 L 575 230 L 600 230" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />

            {/* FAILED -> RECOVERY */}
            <path d="M 670 230 L 700 230" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />

            {/* RECOVERY -> Loopback to VERIFY */}
            <path d="M 735 265 L 735 305 L 515 305 L 515 205" fill="none" stroke="rgba(255,106,0,0.4)" strokeWidth="2" strokeDasharray="4 4" className="laser-path" />

            {/* PASSED -> COMPLETION */}
            <path d="M 670 110 L 735 110 L 735 170 L 760 170" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />

            {/* Glowing Active Laser Paths with Moving Energy Particles */}
            <path d="M 85 170 L 160 170" stroke="#10B981" strokeWidth="2" opacity="0.8" />
            <path d="M 230 170 L 265 170 L 265 75 L 300 75" fill="none" stroke="#10B981" strokeWidth="2" opacity="0.8" />
            <path d="M 230 170 L 300 170" fill="none" stroke="#10B981" strokeWidth="2" opacity="0.8" />
            <path d="M 230 170 L 265 170 L 265 265 L 300 265" fill="none" stroke="#FF6A00" strokeWidth="2" opacity="0.9" className="laser-path" />

            <path d="M 410 75 L 445 75 L 445 170 L 480 170" fill="none" stroke="#10B981" strokeWidth="2" opacity="0.8" />
            <path d="M 410 170 L 480 170" fill="none" stroke="#10B981" strokeWidth="2" opacity="0.8" />
            <path d="M 410 265 L 445 265 L 445 170 L 480 170" fill="none" stroke="#FF6A00" strokeWidth="2" opacity="0.9" className="laser-path" />

            <path d="M 550 170 L 575 170 L 575 230 L 600 230" fill="none" stroke="#FF8A00" strokeWidth="2" opacity="0.9" className="laser-path" />
            <path d="M 670 230 L 700 230" fill="none" stroke="#FF6A00" strokeWidth="2" opacity="0.9" className="laser-path" />

            {/* Traveling Laser Energy Beacons along the line */}
            <circle cx="200" cy="170" r="3.5" fill="#FF8A00" filter="url(#laserGlow)">
              <animate attributeName="cx" from="160" to="230" dur="1.8s" repeatCount="indefinite" />
            </circle>
            <circle cx="360" cy="265" r="3.5" fill="#FF8A00" filter="url(#laserGlow)">
              <animate attributeName="cx" from="300" to="410" dur="2.2s" repeatCount="indefinite" />
            </circle>
            <circle cx="635" cy="230" r="3.5" fill="#FF8A00" filter="url(#laserGlow)">
              <animate attributeName="cx" from="600" to="670" dur="1.4s" repeatCount="indefinite" />
            </circle>
          </svg>

          {/* Render Graph Nodes */}
          {/* Column 1: TASK */}
          <NodeItem
            id="TASK"
            meta={nodeMeta.TASK}
            status="completed"
            left={15}
            top={135}
            onClick={() => onSelectNode?.(nodeMeta.TASK)}
            onHover={setHoveredNode}
          />

          {/* Column 2: PLANNER */}
          <NodeItem
            id="PLANNER"
            meta={nodeMeta.PLANNER}
            status="completed"
            left={160}
            top={135}
            onClick={() => onSelectNode?.(nodeMeta.PLANNER)}
            onHover={setHoveredNode}
          />

          {/* Column 3: Parallel Agents (RESEARCH, DOCUMENT, DATA) */}
          <NodeItem
            id="RESEARCH"
            meta={nodeMeta.RESEARCH}
            status="completed"
            left={300}
            top={40}
            onClick={() => onSelectNode?.(nodeMeta.RESEARCH)}
            onHover={setHoveredNode}
          />
          <NodeItem
            id="DOCUMENT"
            meta={nodeMeta.DOCUMENT}
            status="completed"
            left={300}
            top={135}
            onClick={() => onSelectNode?.(nodeMeta.DOCUMENT)}
            onHover={setHoveredNode}
          />
          <NodeItem
            id="DATA"
            meta={nodeMeta.DATA}
            status="active"
            left={300}
            top={230}
            onClick={() => onSelectNode?.(nodeMeta.DATA)}
            onHover={setHoveredNode}
          />

          {/* Column 4: VERIFY */}
          <NodeItem
            id="VERIFY"
            meta={nodeMeta.VERIFY}
            status="active"
            left={480}
            top={135}
            onClick={() => onSelectNode?.(nodeMeta.VERIFY)}
            onHover={setHoveredNode}
          />

          {/* Column 5: Split Gates (PASSED, FAILED) */}
          <NodeItem
            id="PASSED"
            meta={nodeMeta.PASSED}
            status="waiting"
            left={600}
            top={75}
            onClick={() => onSelectNode?.(nodeMeta.PASSED)}
            onHover={setHoveredNode}
          />
          <NodeItem
            id="FAILED"
            meta={nodeMeta.FAILED}
            status="warning"
            left={600}
            top={195}
            onClick={() => onSelectNode?.(nodeMeta.FAILED)}
            onHover={setHoveredNode}
          />

          {/* Column 6: RECOVERY */}
          <NodeItem
            id="RECOVERY"
            meta={nodeMeta.RECOVERY}
            status="active"
            left={700}
            top={195}
            onClick={() => onSelectNode?.(nodeMeta.RECOVERY)}
            onHover={setHoveredNode}
          />

          {/* Column 7: COMPLETION */}
          <NodeItem
            id="COMPLETION"
            meta={nodeMeta.COMPLETION}
            status="waiting"
            left={760}
            top={135}
            onClick={() => onSelectNode?.(nodeMeta.COMPLETION)}
            onHover={setHoveredNode}
          />
        </div>
      </div>

      {/* Node Inspector Bar at bottom if hovered */}
      {hoveredNode && (
        <div className="mt-2 pt-2.5 border-t border-white/5 flex items-center justify-between text-xs text-zinc-300 transition-all">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[#FF8A00] font-bold">[{hoveredNode.label}]</span>
            <span className="text-zinc-400">{hoveredNode.role}:</span>
            <span className="text-white">{hoveredNode.desc}</span>
          </div>
          <span className="text-zinc-500 font-mono text-[11px]">Click to inspect agent telemetry</span>
        </div>
      )}
    </div>
  )
}

function NodeItem({ id, meta, status, left, top, onClick, onHover }) {
  const Icon = meta.icon

  let borderStyle = 'border-white/10 bg-[#121212]'
  let textStyle = 'text-zinc-400'
  let badgeStyle = 'bg-zinc-800 text-zinc-400'
  let isPulsing = false

  if (status === 'active') {
    borderStyle = 'border-[#FF6A00] bg-[#1a120b] shadow-[0_0_16px_rgba(255,106,0,0.3)]'
    textStyle = 'text-white'
    badgeStyle = 'bg-[#FF6A00]/20 text-[#FF8A00] border border-[#FF6A00]/40'
    isPulsing = true
  } else if (status === 'completed') {
    borderStyle = 'border-emerald-500/40 bg-[#0d1612]'
    textStyle = 'text-zinc-200'
    badgeStyle = 'bg-emerald-500/20 text-emerald-400'
  } else if (status === 'warning') {
    borderStyle = 'border-amber-500/50 bg-[#19150b]'
    textStyle = 'text-amber-300'
    badgeStyle = 'bg-amber-500/20 text-amber-400'
  }

  return (
    <div
      style={{ left: `${left}px`, top: `${top}px` }}
      onClick={onClick}
      onMouseEnter={() => onHover(meta)}
      onMouseLeave={() => onHover(null)}
      className={`absolute w-[110px] p-2.5 rounded-lg border transition-all duration-200 cursor-pointer select-none hover:scale-105 hover:z-20 ${borderStyle}`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <div className={`p-1 rounded bg-black/40 ${status === 'active' ? 'text-[#FF8A00]' : status === 'completed' ? 'text-emerald-400' : 'text-zinc-400'}`}>
          <Icon className="w-3.5 h-3.5" />
        </div>
        <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded uppercase ${badgeStyle}`}>
          {status}
        </span>
      </div>

      <div className="font-bold text-[11px] truncate tracking-tight text-white">
        {meta.label}
      </div>
      <div className="text-[9px] text-zinc-500 truncate font-mono">
        {meta.role}
      </div>

      {isPulsing && (
        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#FF6A00] animate-ping" />
      )}
    </div>
  )
}
