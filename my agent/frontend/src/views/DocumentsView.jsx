import React, { useEffect, useState, useRef } from 'react'
import {
  IconDownload,
  IconFileText,
  IconCheck,
  IconUpload,
  IconTrash,
  IconSearch,
  IconAlertTriangle,
  IconShieldCheck,
  IconRefreshCw,
  IconExternalLink,
  IconBookOpen,
} from '../components/icons'

export default function DocumentsView({
  taskResult,
  apiBaseUrl = 'http://127.0.0.1:8000',
  workspaceId = 'default_workspace',
  setWorkspaceId,
  onNavigate,
  onPlaySound,
}) {
  const [activeTab, setActiveTab] = useState('library') // 'library' | 'reports'
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [copied, setCopied] = useState(false)
  const [integrity, setIntegrity] = useState(null)
  const [integrityError, setIntegrityError] = useState('')
  const fileInputRef = useRef(null)

  const currentWorkspace = workspaceId || 'default_workspace'
  const cleanBaseUrl = (apiBaseUrl || '').trim().replace(/\/+$/, '')

  // Fetch documents for the active workspace
  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const url = cleanBaseUrl
        ? `${cleanBaseUrl}/api/documents?workspace_id=${encodeURIComponent(currentWorkspace)}`
        : `/api/documents?workspace_id=${encodeURIComponent(currentWorkspace)}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setDocuments(data.documents || [])
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [currentWorkspace, apiBaseUrl])

  // Poll active processing documents
  useEffect(() => {
    const hasProcessing = documents.some(
      (d) => d.processing_status === 'processing' || d.processing_status === 'queued'
    )
    if (!hasProcessing) return

    const interval = setInterval(() => {
      fetchDocuments()
    }, 2500)
    return () => clearInterval(interval)
  }, [documents, currentWorkspace])

  // Upload handler
  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return
    setUploading(true)
    setUploadError('')
    onPlaySound?.('click')

    try {
      const formData = new FormData()
      formData.append('workspace_id', currentWorkspace)
      formData.append('user_id', 'local_user')

      if (files.length === 1) {
        formData.append('file', files[0])
        const uploadUrl = cleanBaseUrl ? `${cleanBaseUrl}/api/documents/upload` : '/api/documents/upload'
        const res = await fetch(uploadUrl, {
          method: 'POST',
          body: formData,
        })
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}))
          throw new Error(errData.detail || 'Upload failed')
        }
      } else {
        Array.from(files).forEach((f) => formData.append('files', f))
        const batchUrl = cleanBaseUrl ? `${cleanBaseUrl}/api/documents/batch-upload` : '/api/documents/batch-upload'
        const res = await fetch(batchUrl, {
          method: 'POST',
          body: formData,
        })
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}))
          throw new Error(errData.detail || 'Batch upload failed')
        }
      }

      onPlaySound?.('complete')
      await fetchDocuments()
    } catch (err) {
      setUploadError(err.message || 'Error uploading files.')
    } finally {
      setUploading(false)
    }
  }

  // Delete handler
  const handleDeleteDocument = async (docId, filename) => {
    if (!window.confirm(`Delete "${filename}" and purge all vector embeddings and chunk indices?`)) {
      return
    }
    onPlaySound?.('click')
    try {
      const delUrl = cleanBaseUrl ? `${cleanBaseUrl}/api/documents/${docId}` : `/api/documents/${docId}`
      const res = await fetch(delUrl, {
        method: 'DELETE',
      })
      if (res.ok) {
        setDocuments((prev) => prev.filter((d) => d.id !== docId))
        if (selectedDoc?.id === docId) setSelectedDoc(null)
      }
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  // Reprocess handler
  const handleReprocess = async (docId) => {
    onPlaySound?.('click')
    try {
      const procUrl = cleanBaseUrl ? `${cleanBaseUrl}/api/documents/${docId}/process` : `/api/documents/${docId}/process`
      await fetch(procUrl, { method: 'POST' })
      fetchDocuments()
    } catch (err) {
      console.error('Reprocess failed:', err)
    }
  }

  // Drag and drop handlers
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files)
    }
  }

  // Legacy report integrity loader
  const report = taskResult?.final_report || ''
  const documentId = taskResult?.task_id ? `doc_${taskResult.task_id}` : null

  useEffect(() => {
    if (activeTab !== 'reports' || !documentId) return
    let cancelled = false
    const loadIntegrity = async () => {
      setIntegrityError('')
      try {
        const response = await fetch(`${apiBaseUrl}/api/documents/${documentId}/integrity`)
        if (!response.ok) return
        const data = await response.json()
        if (!cancelled) setIntegrity(data)
      } catch (error) {
        if (!cancelled) setIntegrityError('Integrity metadata is not available yet.')
      }
    }
    loadIntegrity()
    return () => {
      cancelled = true
    }
  }, [activeTab, documentId, apiBaseUrl])

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00]" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              TP01 Research Platform
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1 flex items-center gap-3">
            <IconBookOpen className="w-6 h-6 text-[#FF6A00]" />
            Academic Paper Hub
          </h1>
          <p className="text-sm text-zinc-400 mt-0.5">
            Ingest, parse, and ground multi-paper PDF corpuses with page-level precision.
          </p>
        </div>

        {/* Tab & Workspace Bar */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-black/40 border border-white/10 px-3 py-1.5 rounded-xl font-mono text-xs">
            <span className="text-zinc-500">Workspace:</span>
            <input
              type="text"
              value={currentWorkspace}
              onChange={(e) => setWorkspaceId && setWorkspaceId(e.target.value)}
              className="bg-transparent text-white font-semibold focus:outline-none w-32 border-b border-transparent focus:border-[#FF6A00]"
              placeholder="workspace_id"
            />
          </div>

          <div className="flex rounded-xl bg-white/5 p-1 border border-white/10">
            <button
              onClick={() => setActiveTab('library')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'library'
                  ? 'bg-[#FF6A00] text-white shadow'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              Paper Library ({documents.length})
            </button>
            <button
              onClick={() => setActiveTab('reports')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'reports'
                  ? 'bg-[#FF6A00] text-white shadow'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              Task Reports & Cryptography
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'library' ? (
        <>
          {/* Upload Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
              dragActive
                ? 'border-[#FF6A00] bg-[#FF6A00]/10 scale-[1.01]'
                : 'border-white/15 bg-white/[0.02] hover:border-white/30 hover:bg-white/[0.04]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf"
              className="hidden"
              onChange={(e) => handleFileUpload(e.target.files)}
            />
            <div className="max-w-md mx-auto space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-[#FF6A00]/10 border border-[#FF6A00]/30 text-[#FF6A00] flex items-center justify-center mx-auto shadow-[0_0_15px_rgba(255,106,0,0.2)]">
                {uploading ? (
                  <IconRefreshCw className="w-6 h-6 animate-spin" />
                ) : (
                  <IconUpload className="w-6 h-6" />
                )}
              </div>
              <h3 className="text-sm font-semibold text-white">
                {uploading ? 'Processing & Indexing PDFs...' : 'Upload Academic Research Papers (PDF)'}
              </h3>
              <p className="text-xs text-zinc-400">
                Drag and drop 3–15 papers, or click to browse. Automatic two-column layout parsing,
                header/footer stripping, and dual ChromaDB + BM25 indexing.
              </p>
            </div>
          </div>

          {uploadError && (
            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl">
              <IconAlertTriangle className="w-4 h-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Paper Grid / Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-wider font-mono">
                Indexed Papers in Workspace ({documents.length})
              </h2>
              <button
                onClick={fetchDocuments}
                className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition-colors"
              >
                <IconRefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>

            {documents.length === 0 ? (
              <div className="p-12 text-center bg-white/[0.02] border border-white/10 rounded-2xl">
                <IconFileText className="w-10 h-10 text-zinc-600 mx-auto mb-2" />
                <h3 className="text-sm font-semibold text-zinc-300">No papers uploaded yet</h3>
                <p className="text-xs text-zinc-500 mt-1">
                  Upload your research papers to start cross-paper analysis and grounded QA.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {documents.map((doc) => {
                  const meta = doc.metadata_extracted || {}
                  const isProcessing =
                    doc.processing_status === 'processing' || doc.processing_status === 'queued'
                  return (
                    <div
                      key={doc.id}
                      className="bg-white/[0.03] hover:bg-white/[0.05] border border-white/10 rounded-2xl p-4 flex flex-col justify-between transition-all group relative"
                    >
                      <div className="space-y-2">
                        {/* Status & Badges */}
                        <div className="flex items-center justify-between gap-2">
                          <span
                            className={`px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold uppercase ${
                              doc.processing_status === 'completed'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : doc.processing_status === 'failed'
                                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                : 'bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse'
                            }`}
                          >
                            {doc.processing_status}
                          </span>

                          <div className="flex items-center gap-1.5">
                            {doc.needs_ocr ? (
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                OCR Scanned
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-blue-500/10 text-blue-300 border border-blue-500/20">
                                Native Text
                              </span>
                            )}
                            <span className="text-[10px] font-mono text-zinc-500">v{doc.version}</span>
                          </div>
                        </div>

                        {/* Title */}
                        <h3 className="text-sm font-semibold text-white line-clamp-2 leading-snug">
                          {doc.title || doc.filename}
                        </h3>

                        {/* File Name & DOI */}
                        <div className="text-xs text-zinc-400 flex flex-wrap items-center gap-2">
                          <span className="font-mono text-zinc-500 text-[11px] truncate max-w-[150px]">
                            {doc.filename}
                          </span>
                          {meta.publication_year && (
                            <span className="bg-white/5 px-1.5 py-0.5 rounded text-[10px] font-mono text-zinc-300">
                              {meta.publication_year}
                            </span>
                          )}
                          {meta.doi && (
                            <a
                              href={`https://doi.org/${meta.doi}`}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[11px] text-[#FF8A00] hover:underline flex items-center gap-1"
                            >
                              <span>DOI</span>
                              <IconExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>

                        {/* Abstract excerpt if available */}
                        {meta.abstract && (
                          <p className="text-xs text-zinc-400 line-clamp-3 bg-black/30 p-2.5 rounded-xl border border-white/5">
                            {meta.abstract}
                          </p>
                        )}
                      </div>

                      {/* Footer Info & Actions */}
                      <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-zinc-400">
                        <div className="flex items-center gap-2 font-mono text-[11px]">
                          <span>{doc.page_count} pages</span>
                          <span>•</span>
                          <span>{(doc.file_size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => {
                              onPlaySound?.('click')
                              onNavigate?.('research')
                            }}
                            title="Search in this paper"
                            className="p-1.5 rounded-lg hover:bg-white/10 text-zinc-300 hover:text-white transition-colors"
                          >
                            <IconSearch className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleReprocess(doc.id)}
                            title="Re-process & Re-index"
                            disabled={isProcessing}
                            className="p-1.5 rounded-lg hover:bg-white/10 text-zinc-300 hover:text-white transition-colors disabled:opacity-40"
                          >
                            <IconRefreshCw className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />
                          </button>
                          <button
                            onClick={() => handleDeleteDocument(doc.id, doc.filename)}
                            title="Delete paper"
                            className="p-1.5 rounded-lg hover:bg-red-500/20 text-zinc-400 hover:text-red-400 transition-colors"
                          >
                            <IconTrash className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </>
      ) : (
        /* Legacy Reports & Cryptographic Verification */
        <div className="space-y-6">
          <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <IconShieldCheck className="w-5 h-5 text-emerald-400" />
                TaskFinisher Intelligence Report & Cryptographic Seal
              </h2>
              {taskResult?.task_id && (
                <a
                  href={`${apiBaseUrl}/api/tasks/${taskResult.task_id}/report/download`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 rounded-xl bg-[#FF6A00] text-white text-xs font-semibold hover:bg-[#FF8A00] transition-all flex items-center gap-1.5 shadow"
                >
                  <IconDownload className="w-4 h-4" />
                  <span>Download DOCX</span>
                </a>
              )}
            </div>

            {integrity && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-4 bg-black/40 rounded-xl border border-white/5 font-mono text-xs">
                <div>
                  <span className="text-zinc-500 block">SHA-256 Digest:</span>
                  <span className="text-emerald-400 truncate block">{integrity.sha256}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block">Integrity Status:</span>
                  <span className="text-emerald-400 font-bold">{integrity.integrity}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block">Verification Timestamp:</span>
                  <span className="text-zinc-300">{integrity.verified_at}</span>
                </div>
              </div>
            )}

            {report ? (
              <pre className="p-4 bg-black/50 rounded-xl text-xs text-zinc-300 font-mono overflow-auto max-h-[500px] border border-white/5 whitespace-pre-wrap">
                {report}
              </pre>
            ) : (
              <p className="text-xs text-zinc-500 italic">No report available for the active task.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
