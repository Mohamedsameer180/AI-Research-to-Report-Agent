import React, { useEffect, useState } from 'react'
import {
  IconDownload,
  IconFileText,
  IconCheck,
} from '../components/icons'

export default function DocumentsView({ taskResult, apiBaseUrl, onPlaySound }) {
  const [copied, setCopied] = useState(false)
  const [integrity, setIntegrity] = useState(null)
  const [verifying, setVerifying] = useState(false)
  const [integrityError, setIntegrityError] = useState('')
  const report = taskResult?.final_report || ''
  const artifacts = taskResult?.artifacts || {}
  const documentId = taskResult?.task_id ? `doc_${taskResult.task_id}` : null
  const reportSteps = Object.values(taskResult?.steps || {}).filter((step) =>
    step.agent === 'ReportAgent' || step.agent === 'FinalVerifierAgent'
  )

  useEffect(() => {
    let cancelled = false
    const loadIntegrity = async () => {
      if (!apiBaseUrl || !documentId) {
        setIntegrity(null)
        return
      }
      setIntegrityError('')
      try {
        const response = await fetch(`${apiBaseUrl}/api/documents/${documentId}/integrity`)
        if (!response.ok) return
        const data = await response.json()
        if (!cancelled) setIntegrity(data)
      } catch (error) {
        if (!cancelled) setIntegrityError('Document integrity metadata is not available yet.')
      }
    }
    loadIntegrity()
    return () => {
      cancelled = true
    }
  }, [apiBaseUrl, documentId])

  const downloadReport = () => {
    if (!taskResult?.task_id && !report) return
    onPlaySound?.('complete')

    if (taskResult?.task_id && apiBaseUrl) {
      window.open(`${apiBaseUrl}/api/tasks/${taskResult.task_id}/report/download`, '_blank', 'noopener,noreferrer')
      return
    }

    if (report) {
      const link = document.createElement('a')
      const blob = new Blob([report], { type: 'text/markdown' })
      link.href = URL.createObjectURL(blob)
      link.download = `taskfinisher-${taskResult?.task_id || 'report'}.md`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
    }
  }

  const downloadImportantPoints = () => {
    if (!taskResult?.task_id || !apiBaseUrl) return
    onPlaySound?.('complete')
    window.open(`${apiBaseUrl}/api/tasks/${taskResult.task_id}/important-points/download`, '_blank', 'noopener,noreferrer')
  }

  const verifyIntegrity = async () => {
    if (!apiBaseUrl || !documentId) return
    setVerifying(true)
    setIntegrityError('')
    onPlaySound?.('click')
    try {
      const response = await fetch(`${apiBaseUrl}/api/documents/${documentId}/verify`)
      if (!response.ok) {
        throw new Error(`Verification failed with HTTP ${response.status}.`)
      }
      const data = await response.json()
      setIntegrity({
        document_id: data.document_id,
        filename: data.filename,
        algorithm: data.algorithm,
        sha256: data.expected_hash,
        file_size: integrity?.file_size,
        created_at: integrity?.created_at,
        status: data.integrity,
        verified_at: data.verified_at,
      })
      onPlaySound?.(data.integrity === 'VERIFIED' ? 'complete' : 'alert')
    } catch (error) {
      setIntegrityError(error.message || 'Could not verify document integrity.')
      onPlaySound?.('alert')
    } finally {
      setVerifying(false)
    }
  }

  const copyReport = async () => {
    if (!report) return
    await navigator.clipboard.writeText(report)
    setCopied(true)
    onPlaySound?.('complete')
    setTimeout(() => setCopied(false), 1800)
  }

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00]" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              Report Generation Engine
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">
            Professional Document Studio
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={downloadReport}
            disabled={!taskResult?.task_id && !report}
            className="btn-primary text-xs py-2 px-4"
          >
            <IconDownload className="w-4 h-4" />
            Download DOCX
          </button>
          <button
            type="button"
            onClick={downloadImportantPoints}
            disabled={!taskResult?.task_id || !report}
            className="btn-secondary text-xs py-2 px-4"
          >
            <IconFileText className="w-4 h-4" />
            Important Points
          </button>
          <button
            type="button"
            onClick={copyReport}
            disabled={!report}
            className="btn-secondary text-xs py-2 px-4"
          >
            <IconFileText className="w-4 h-4" />
            Copy Markdown
          </button>
        </div>
      </div>

      {copied && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono flex items-center gap-2 animate-in fade-in">
          <IconCheck className="w-4 h-4" />
          Report copied from the active backend task.
        </div>
      )}

      {!taskResult ? (
        <section className="glass-panel p-6 rounded-2xl border border-white/10">
          <h2 className="text-base font-bold text-white">No document available</h2>
          <p className="text-sm text-zinc-400 mt-2">
            Run a task to generate a backend report artifact.
          </p>
        </section>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4 space-y-4">
            <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-white/5">
                <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold">
                  Generation Pipeline
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                  {taskResult.status}
                </span>
              </div>

              <div className="space-y-2.5">
                {reportSteps.length === 0 ? (
                  <div className="text-xs text-zinc-500">No report-generation steps recorded yet.</div>
                ) : reportSteps.map((step) => (
                  <div
                    key={step.step_id}
                    className="p-3 rounded-xl bg-black/40 border border-white/5"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs">
                        <IconCheck className="w-3 h-3" />
                      </div>
                      <span className="text-xs font-bold text-zinc-200">{step.description}</span>
                    </div>
                    <p className="text-[11px] text-zinc-500 leading-tight mt-2">
                      {step.output_summary || step.verification_reason || step.status}
                    </p>
                  </div>
                ))}
              </div>

              <div className="p-4 rounded-xl bg-black/50 border border-white/5 space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Task ID:</span>
                  <span className="text-white font-bold">{taskResult.task_id || 'Not created'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Verdict:</span>
                  <span className="text-[#FF8A00]">{taskResult.verdict}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Artifacts:</span>
                  <span className="text-emerald-400">{Object.keys(artifacts).length}</span>
                </div>
              </div>
            </div>

            <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-white/5">
                <div>
                  <span className="text-xs font-mono uppercase tracking-wider text-zinc-400 font-bold">
                    Document Integrity
                  </span>
                  <p className="text-[10px] text-zinc-500 font-mono mt-1">
                    SHA-256 fingerprint, not encryption
                  </p>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                  integrity?.status === 'VERIFIED'
                    ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                    : 'text-amber-300 bg-amber-500/10 border-amber-500/20'
                }`}>
                  {integrity?.status || 'PENDING'}
                </span>
              </div>

              {integrity ? (
                <div className="space-y-3 text-xs font-mono">
                  <div className="flex justify-between gap-3">
                    <span className="text-zinc-500">File:</span>
                    <span className="text-white text-right truncate">{integrity.filename || `${taskResult.task_id}_report.docx`}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Algorithm:</span>
                    <span className="text-[#FF8A00]">{integrity.algorithm}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">File Size:</span>
                    <span className="text-white">{integrity.file_size || 0} bytes</span>
                  </div>
                  <div className="p-3 rounded-xl bg-black/50 border border-white/5">
                    <div className="text-[10px] text-zinc-500 mb-1">SHA-256</div>
                    <div className="text-[11px] text-zinc-200 break-all leading-relaxed">
                      {integrity.sha256}
                    </div>
                  </div>
                  {integrity.verified_at && (
                    <div className="text-[10px] text-zinc-500">
                      Last verified: {integrity.verified_at}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-xs text-zinc-500">
                  Download or generate the report to create an integrity record.
                </div>
              )}

              {integrityError && (
                <div className="text-xs text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                  {integrityError}
                </div>
              )}

              <button
                type="button"
                onClick={verifyIntegrity}
                disabled={!documentId || verifying}
                className="btn-secondary w-full text-xs py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {verifying ? 'Verifying File...' : 'Verify File'}
              </button>
            </div>
          </div>

          <div className="lg:col-span-8 space-y-4">
            <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-white/5">
                <div className="flex items-center gap-3">
                  <IconFileText className="w-5 h-5 text-[#FF8A00]" />
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      {taskResult.task_id ? `${taskResult.task_id}_report.md` : 'Backend report'}
                    </h3>
                    <p className="text-[10px] text-zinc-400 font-mono">
                      Live backend artifact preview
                    </p>
                  </div>
                </div>
              </div>

              {report ? (
                <pre className="bg-[#0A0A0A] border border-white/10 rounded-xl p-6 text-xs text-zinc-300 font-mono whitespace-pre-wrap overflow-x-auto max-h-[620px]">
                  {report}
                </pre>
              ) : (
                <div className="bg-[#0A0A0A] border border-white/10 rounded-xl p-6 text-sm text-zinc-500">
                  The backend has not returned a final report for this task yet.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
