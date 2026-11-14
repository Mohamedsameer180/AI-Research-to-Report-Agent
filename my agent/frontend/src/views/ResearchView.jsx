import React, { useState, useRef, useEffect } from 'react'
import {
  IconSearch,
  IconShieldCheck,
  IconExternalLink,
  IconCheck,
  IconFileText,
  IconFilter,
  IconBookOpen,
  IconRefreshCw,
  IconZap,
  IconChevronDown,
} from '../components/icons'

const SECTIONS = [
  { id: 'all', label: 'All Sections' },
  { id: 'abstract', label: 'Abstract' },
  { id: 'introduction', label: 'Introduction' },
  { id: 'methodology', label: 'Methodology' },
  { id: 'experiments', label: 'Experiments' },
  { id: 'results', label: 'Results' },
  { id: 'limitations', label: 'Limitations' },
  { id: 'conclusion', label: 'Conclusion' },
]

const SAMPLE_QUERIES = [
  'What are the primary limitations reported by the authors?',
  'What empirical methodology and datasets were evaluated?',
  'How do the results compare against previous baseline models?',
  'What theoretical claims or mathematical frameworks are proposed?',
]

export default function ResearchView({
  taskResult,
  apiBaseUrl = 'http://127.0.0.1:8000',
  workspaceId = 'default_workspace',
  setWorkspaceId,
  onNavigate,
  onPlaySound,
}) {
  const [activeTab, setActiveTab] = useState('search') // 'search' | 'evidence'
  const [query, setQuery] = useState('')
  const [selectedSection, setSelectedSection] = useState('all')
  const [useReranker, setUseReranker] = useState(true)
  const [expandParent, setExpandParent] = useState(true)
  const [topK, setTopK] = useState(5)
  const [searching, setSearching] = useState(false)
  const [searchResults, setSearchResults] = useState(null)
  const [searchError, setSearchError] = useState('')
  const [expandedChunkId, setExpandedChunkId] = useState(null)
  const [sectionDropdownOpen, setSectionDropdownOpen] = useState(false)
  const sectionMenuRef = useRef(null)

  // Close section dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (sectionMenuRef.current && !sectionMenuRef.current.contains(event.target)) {
        setSectionDropdownOpen(false)
      }
    }
    if (sectionDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [sectionDropdownOpen])

  const currentWorkspace = workspaceId || 'default_workspace'

  // Execute Hybrid RAG Search
  const handleSearch = async (searchQuery = query) => {
    const q = searchQuery.trim()
    if (!q) return
    setSearching(true)
    setSearchError('')
    onPlaySound?.('click')

    try {
      const payload = {
        query: q,
        workspace_id: currentWorkspace,
        top_k: Number(topK),
        candidate_k: 20,
        sections: selectedSection !== 'all' ? [selectedSection] : null,
        expand_parent: expandParent,
        use_reranker: useReranker,
      }

      const cleanBaseUrl = (apiBaseUrl || '').trim().replace(/\/+$/, '')
      const searchUrl = cleanBaseUrl ? `${cleanBaseUrl}/api/retrieval/search` : '/api/retrieval/search'

      let res = await fetch(searchUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).catch(() => null)

      // Fallback to relative endpoint if absolute URL failed or 404'd
      if ((!res || res.status === 404) && cleanBaseUrl) {
        const fallback = await fetch('/api/retrieval/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }).catch(() => null)
        if (fallback && fallback.ok) {
          res = fallback
        }
      }

      if (!res) {
        throw new Error('Cannot connect to backend server. Please verify the backend is running on http://127.0.0.1:8000')
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        if (res.status === 404) {
          throw new Error('Retrieval endpoint not found (HTTP 404). Please ensure the backend server is running and restarted with the latest TP01 routes.')
        }
        throw new Error(err.detail || `Search request failed (HTTP ${res.status})`)
      }

      const data = await res.json()
      setSearchResults(data)
      onPlaySound?.('complete')
    } catch (err) {
      setSearchError(err.message || 'Error executing hybrid search')
    } finally {
      setSearching(false)
    }
  }

  // Legacy task evidence sources
  const evidenceList = taskResult?.evidence || []

  return (
    <div className="space-y-6 pb-12">
      {/* View Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00]" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              TP01 Hybrid Intelligence
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1 flex items-center gap-3">
            <IconSearch className="w-6 h-6 text-[#FF6A00]" />
            Hybrid Retrieval & Cross-Encoder Deep Search
          </h1>
          <p className="text-sm text-zinc-400 mt-0.5">
            Query across workspace papers with dense embeddings, BM25Plus, and MS-MARCO Cross-Encoder reranking.
          </p>
        </div>

        {/* Workspace & Sub-tab switcher */}
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
              onClick={() => setActiveTab('search')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'search'
                  ? 'bg-[#FF6A00] text-white shadow'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              Hybrid Search
            </button>
            <button
              onClick={() => setActiveTab('evidence')}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'evidence'
                  ? 'bg-[#FF6A00] text-white shadow'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              Task Evidence ({evidenceList.length})
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'search' ? (
        <div className="space-y-5">
          {/* Main Search Bar Card */}
          <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-5 space-y-4 shadow-xl">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSearch()
              }}
              className="flex gap-2"
            >
              <div className="relative flex-1">
                <IconSearch className="w-5 h-5 absolute left-3.5 top-3.5 text-zinc-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask any research question across workspace papers (e.g. 'What are the reported limitations in scaling?')..."
                  className="w-full bg-black/50 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-[#FF6A00] transition-all font-sans"
                />
              </div>

              <button
                type="submit"
                disabled={searching || !query.trim()}
                className="px-6 py-3 rounded-xl bg-[#FF6A00] hover:bg-[#FF8A00] disabled:opacity-50 text-white font-semibold text-sm transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(255,106,0,0.3)] shrink-0"
              >
                {searching ? (
                  <IconRefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <IconZap className="w-4 h-4" />
                )}
                <span>Search Papers</span>
              </button>
            </form>

            {/* Quick Query Pills */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="text-zinc-500 font-mono text-[11px]">Suggested Questions:</span>
              {SAMPLE_QUERIES.map((sq, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setQuery(sq)
                    handleSearch(sq)
                  }}
                  className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-zinc-300 hover:text-white transition-colors border border-white/5 truncate max-w-xs"
                >
                  {sq}
                </button>
              ))}
            </div>

            {/* Controls Bar: Section filter, Reranker toggle, Parent expansion */}
            <div className="pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-4 text-xs">
              {/* Section Filter Popover Dropdown */}
              <div className="relative" ref={sectionMenuRef}>
                <div className="flex items-center gap-2">
                  <span className="text-zinc-500 font-mono text-[11px]">Section:</span>
                  <button
                    type="button"
                    onClick={() => setSectionDropdownOpen((prev) => !prev)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white font-mono text-xs transition-all shadow-sm focus:outline-none focus:border-[#FF6A00]"
                  >
                    <IconFilter className="w-3.5 h-3.5 text-[#FF6A00]" />
                    <span className="font-semibold text-zinc-200">
                      {SECTIONS.find((s) => s.id === selectedSection)?.label || 'All Sections'}
                    </span>
                    <IconChevronDown
                      className={`w-3.5 h-3.5 text-zinc-400 transition-transform duration-200 ${
                        sectionDropdownOpen ? 'rotate-180 text-white' : ''
                      }`}
                    />
                  </button>
                </div>

                {/* Popover Menu */}
                {sectionDropdownOpen && (
                  <div className="absolute left-14 top-full mt-2 w-52 bg-zinc-900/95 backdrop-blur-xl border border-white/15 rounded-xl shadow-2xl p-1.5 z-40 animate-in fade-in zoom-in-95 duration-150">
                    <div className="px-2.5 py-1 text-[10px] font-mono text-zinc-400 uppercase tracking-wider border-b border-white/5 mb-1">
                      Filter Target Section
                    </div>
                    {SECTIONS.map((sec) => {
                      const isSelected = selectedSection === sec.id
                      return (
                        <button
                          key={sec.id}
                          type="button"
                          onClick={() => {
                            setSelectedSection(sec.id)
                            setSectionDropdownOpen(false)
                          }}
                          className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all text-left ${
                            isSelected
                              ? 'bg-[#FF6A00] text-white font-bold shadow'
                              : 'text-zinc-300 hover:text-white hover:bg-white/10'
                          }`}
                        >
                          <span>{sec.label}</span>
                          {isSelected && <IconCheck className="w-3.5 h-3.5 shrink-0" />}
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* Toggles */}
              <div className="flex items-center gap-4 font-mono text-[11px]">
                <label className="flex items-center gap-2 cursor-pointer select-none text-zinc-300 hover:text-white">
                  <input
                    type="checkbox"
                    checked={useReranker}
                    onChange={(e) => setUseReranker(e.target.checked)}
                    className="accent-[#FF6A00] rounded"
                  />
                  <span>Cross-Encoder (ms-marco)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none text-zinc-300 hover:text-white">
                  <input
                    type="checkbox"
                    checked={expandParent}
                    onChange={(e) => setExpandParent(e.target.checked)}
                    className="accent-[#FF6A00] rounded"
                  />
                  <span>Parent Section Context</span>
                </label>

                <div className="flex items-center gap-1 text-zinc-400">
                  <span>Top K:</span>
                  <select
                    value={topK}
                    onChange={(e) => setTopK(e.target.value)}
                    className="bg-black/50 border border-white/10 text-white rounded px-1.5 py-0.5 text-xs focus:outline-none"
                  >
                    <option value="3">3</option>
                    <option value="5">5</option>
                    <option value="10">10</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {searchError && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-xl">
              {searchError}
            </div>
          )}

          {/* Results Feed */}
          {searchResults && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-zinc-400">
                <span>Found {searchResults.total_found} verified citation passages</span>
                <span>Workspace: {searchResults.workspace_id}</span>
              </div>

              {searchResults.results.length === 0 ? (
                <div className="p-8 text-center bg-white/[0.02] border border-white/10 rounded-2xl text-zinc-400 text-xs">
                  No matching passages found. Ensure research papers are uploaded to workspace "{currentWorkspace}".
                </div>
              ) : (
                searchResults.results.map((r, idx) => {
                  const isExpanded = expandedChunkId === r.chunk_id
                  return (
                    <div
                      key={r.chunk_id || idx}
                      className="bg-white/[0.03] border border-white/10 rounded-2xl p-5 space-y-3 transition-all hover:border-white/20"
                    >
                      {/* Result Top Metadata Bar */}
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-lg bg-[#FF6A00]/20 text-[#FF6A00] font-mono text-xs font-bold flex items-center justify-center">
                            #{idx + 1}
                          </span>
                          <span className="text-xs font-bold text-white tracking-wide">
                            {r.title || r.filename}
                          </span>
                          <span className="text-zinc-500 font-mono text-[11px]">({r.filename})</span>
                        </div>

                        {/* Page & Section Badges */}
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded-lg text-xs font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            PDF Page {r.pdf_page} {r.printed_page !== String(r.pdf_page) && `(p. ${r.printed_page})`}
                          </span>
                          <span className="px-2 py-0.5 rounded-lg text-xs font-mono uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20">
                            {r.section}
                          </span>
                        </div>
                      </div>

                      {/* Verbatim Quote Excerpt */}
                      <div className="bg-black/40 border border-white/5 rounded-xl p-3.5 text-xs text-zinc-200 font-mono leading-relaxed select-text">
                        <span className="text-[#FF8A00] font-bold mr-1.5">“</span>
                        {r.text}
                        <span className="text-[#FF8A00] font-bold ml-1.5">”</span>
                      </div>

                      {/* Parent Section Context if Expanded */}
                      {isExpanded && r.parent_text && (
                        <div className="mt-3 p-4 bg-black/60 border border-[#FF6A00]/20 rounded-xl text-xs text-zinc-300 font-sans space-y-1">
                          <span className="text-[11px] font-mono text-[#FF8A00] font-semibold block uppercase">
                            Expanded Section Context:
                          </span>
                          <p className="whitespace-pre-wrap leading-relaxed">{r.parent_text}</p>
                        </div>
                      )}

                      {/* Bottom Metrics Bar */}
                      <div className="flex items-center justify-between pt-2 border-t border-white/5 text-xs font-mono text-zinc-400">
                        <div className="flex items-center gap-4">
                          {r.rerank_score !== null && (
                            <span className="text-zinc-300">
                              Cross-Encoder Logit:{' '}
                              <strong className="text-emerald-400">{r.rerank_score.toFixed(3)}</strong>
                            </span>
                          )}
                          {r.rrf_score && (
                            <span className="text-zinc-400">
                              RRF Score: <strong className="text-blue-400">{r.rrf_score.toFixed(4)}</strong>
                            </span>
                          )}
                        </div>

                        {r.parent_text && (
                          <button
                            onClick={() => setExpandedChunkId(isExpanded ? null : r.chunk_id)}
                            className="text-[#FF8A00] hover:underline font-mono text-[11px]"
                          >
                            {isExpanded ? 'Hide Full Section Context' : 'View Full Section Context'}
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          )}
        </div>
      ) : (
        /* Legacy Task Evidence View */
        <div className="space-y-4">
          <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-6">
            <h2 className="text-base font-bold text-white mb-3 flex items-center gap-2">
              <IconShieldCheck className="w-5 h-5 text-emerald-400" />
              Active Task Evidence Trail ({evidenceList.length})
            </h2>
            {evidenceList.length === 0 ? (
              <p className="text-xs text-zinc-500 italic">No evidence collected for the current task.</p>
            ) : (
              <div className="space-y-2">
                {evidenceList.map((e, idx) => (
                  <div key={idx} className="p-3 bg-black/40 rounded-xl border border-white/5 text-xs text-zinc-300 font-mono">
                    <span className="text-[#FF8A00] font-bold mr-2">[{e.source || 'Evidence'}]:</span>
                    <span>{e.content || JSON.stringify(e)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
