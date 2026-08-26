import React, { useCallback, useEffect, useRef, useState } from 'react'
import {
  IconSettings,
  IconCpu,
  IconShieldCheck,
  IconRefreshCw,
  IconTerminal,
  IconCheck
} from '../components/icons'

export default function SettingsView({ apiBaseUrl, onPlaySound }) {
  const resolvedApiBaseUrl = apiBaseUrl || 'http://127.0.0.1:8000'
  const [model, setModel] = useState('Gemini 2.0 Flash')
  const [verificationFloor, setVerificationFloor] = useState(90)
  const [maxRetries, setMaxRetries] = useState(2)
  const [autoRecovery, setAutoRecovery] = useState(true)
  const [cryptographicSeal, setCryptographicSeal] = useState(true)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [liveStatus, setLiveStatus] = useState('Loading backend configuration')
  const [lastSavedSettings, setLastSavedSettings] = useState(null)
  const skipNextAutoSave = useRef(true)

  useEffect(() => {
    let cancelled = false

    const loadSettings = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`${resolvedApiBaseUrl}/api/settings/engine`)
        if (!response.ok) {
          throw new Error(`Settings load failed with HTTP ${response.status}.`)
        }
        const data = await response.json()
        if (cancelled) return
        setModel(data.model_label || data.model || 'Gemini 2.0 Flash')
        setVerificationFloor(Number(data.verification_floor ?? 90))
        setMaxRetries(Number(data.max_retries ?? 2))
        setAutoRecovery(Boolean(data.auto_recovery ?? true))
        setCryptographicSeal(Boolean(data.cryptographic_seal ?? true))
        setLiveStatus('Live configuration loaded')
      } catch (settingsError) {
        if (!cancelled) {
          setError(settingsError.message || 'Could not load backend settings.')
          setLiveStatus('Backend configuration unavailable')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadSettings()
    return () => {
      cancelled = true
    }
  }, [resolvedApiBaseUrl])

  const persistSettings = useCallback(async ({ announce = false } = {}) => {
    setSaving(true)
    setSaved(false)
    setError('')
    setLiveStatus('Applying settings to backend runtime...')

    try {
      const response = await fetch(`${resolvedApiBaseUrl}/api/settings/engine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          verification_floor: verificationFloor,
          max_retries: maxRetries,
          auto_recovery: autoRecovery,
          cryptographic_seal: cryptographicSeal,
          output_format: 'docx',
        }),
      })
      if (!response.ok) {
        throw new Error(`Save failed with HTTP ${response.status}.`)
      }
      const data = await response.json()
      const settings = data.settings || data
      setModel(settings.model_label || settings.model || model)
      setVerificationFloor(Number(settings.verification_floor ?? verificationFloor))
      setMaxRetries(Number(settings.max_retries ?? maxRetries))
      setAutoRecovery(Boolean(settings.auto_recovery ?? autoRecovery))
      setCryptographicSeal(Boolean(settings.cryptographic_seal ?? cryptographicSeal))
      setLastSavedSettings(settings)
      if (announce) onPlaySound?.('complete')
      setLiveStatus('Saved and applied to backend runtime')
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (saveError) {
      if (announce) onPlaySound?.('alert')
      setError(saveError.message || 'Could not save backend settings.')
      setLiveStatus('Live sync failed')
    } finally {
      setSaving(false)
    }
  }, [resolvedApiBaseUrl, autoRecovery, cryptographicSeal, maxRetries, model, onPlaySound, verificationFloor])

  useEffect(() => {
    if (loading) return undefined
    if (skipNextAutoSave.current) {
      skipNextAutoSave.current = false
      return undefined
    }

    setLiveStatus('Waiting to sync latest change...')
    const timeoutId = window.setTimeout(() => {
      persistSettings()
    }, 650)

    return () => window.clearTimeout(timeoutId)
  }, [autoRecovery, cryptographicSeal, loading, maxRetries, model, persistSettings, verificationFloor])

  const handleSave = async (e) => {
    e?.preventDefault()
    await persistSettings({ announce: true })
  }

  return (
    <div className="space-y-6 pb-12 max-w-4xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#FF6A00]" />
            <span className="text-xs font-semibold tracking-wider text-[#FF8A00] uppercase font-mono">
              Engine Parameters
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">
            System Settings & Autonomous Agent Controls
          </h1>
          <p className="text-xs text-zinc-400 font-mono mt-1">
            {liveStatus}
          </p>
        </div>

        {saved && (
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/20 flex items-center gap-1.5">
            <IconCheck className="w-3.5 h-3.5" />
            Parameters Synchronized
          </span>
        )}
      </div>

      {error && (
        <div className="text-xs font-mono text-red-300 bg-red-500/10 px-3 py-2 rounded-xl border border-red-500/20">
          {error}
        </div>
      )}

      {lastSavedSettings && (
        <div className="text-xs font-mono text-emerald-300 bg-emerald-500/10 px-3 py-2 rounded-xl border border-emerald-500/20">
          Runtime applied: {lastSavedSettings.model_label || lastSavedSettings.model} · reliability {lastSavedSettings.verification_floor}% · retries {lastSavedSettings.max_retries} · SHA-256 {lastSavedSettings.cryptographic_seal ? 'enabled' : 'disabled'}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* LLM & Model Engine Selector */}
        <section className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-white/5">
            <IconCpu className="w-5 h-5 text-[#FF8A00]" />
            <div>
              <h2 className="text-sm font-bold text-white">Foundation LLM Model</h2>
              <p className="text-xs text-zinc-400 font-mono">Select the reasoning core for DAG planning and code tools.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { id: 'Gemini 2.5 Pro (Recommended)', desc: 'High-speed reasoning, full ADK support' },
              { id: 'Gemini 2.0 Flash', desc: 'Sub-second tool calling and fast extraction' },
              { id: 'Claude 3.7 Sonnet', desc: 'Extended mathematical proofing and audit' },
              { id: 'GPT-4o Enterprise', desc: 'Standard enterprise API endpoint' },
            ].map((m) => (
              <div
                key={m.id}
                onClick={() => {
                  onPlaySound?.('hover')
                  setModel(m.id)
                }}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  model === m.id
                    ? 'bg-[#FF6A00]/15 border-[#FF6A00] shadow-[0_0_15px_rgba(255,106,0,0.2)]'
                    : 'bg-black/30 border-white/5 hover:border-white/15'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white font-mono">{m.id}</span>
                  {model === m.id && <span className="w-2 h-2 rounded-full bg-[#FF8A00]" />}
                </div>
                <p className="text-[11px] text-zinc-400 mt-1">{m.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Verification & Self-Recovery Thresholds */}
        <section className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-white/5">
            <IconShieldCheck className="w-5 h-5 text-emerald-400" />
            <div>
              <h2 className="text-sm font-bold text-white">Verification & Self-Recovery Thresholds</h2>
              <p className="text-xs text-zinc-400 font-mono">Control truth enforcement and autonomous retry limits.</p>
            </div>
          </div>

          <div className="space-y-4 text-xs font-mono">
            {/* Slider: Confidence Floor */}
            <div className="space-y-1.5">
              <div className="flex justify-between">
                <span className="text-zinc-300">Minimum Source Reliability Floor:</span>
                <span className="text-[#FF8A00] font-bold">{verificationFloor}%</span>
              </div>
              <input
                type="range"
                min="70"
                max="98"
                value={verificationFloor}
                onChange={(e) => setVerificationFloor(Number(e.target.value))}
                className="w-full accent-[#FF6A00] bg-zinc-800 h-2 rounded-lg cursor-pointer"
              />
              <span className="text-[10px] text-zinc-500">Sources below this threshold are flagged for manual review or dropped.</span>
            </div>

            {/* Max Recovery Retries */}
            <div className="space-y-1.5 pt-2 border-t border-white/5">
              <div className="flex justify-between">
                <span className="text-zinc-300">Max Autonomous Recovery Retries:</span>
                <span className="text-white font-bold">{maxRetries} attempts</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                value={maxRetries}
                onChange={(e) => setMaxRetries(Number(e.target.value))}
                className="w-full accent-[#FF6A00] bg-zinc-800 h-2 rounded-lg cursor-pointer"
              />
            </div>

            {/* Checkbox Toggles */}
            <div className="space-y-3 pt-3 border-t border-white/5">
              <label className="flex items-center gap-3 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={autoRecovery}
                  onChange={(e) => setAutoRecovery(e.target.checked)}
                  className="w-4 h-4 accent-[#FF6A00] rounded"
                />
                <div>
                  <div className="text-white font-semibold">Enable Autonomous Tool Failure Recovery</div>
                  <div className="text-[10px] text-zinc-500 font-sans">Allows Recovery Agent to discover alternative mirror sources automatically.</div>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={cryptographicSeal}
                  onChange={(e) => setCryptographicSeal(e.target.checked)}
                  className="w-4 h-4 accent-[#FF6A00] rounded"
                />
                <div>
                  <div className="text-white font-semibold">Generate Cryptographic Evidence Signatures (SHA-256)</div>
                  <div className="text-[10px] text-zinc-500 font-sans">Appends immutable proof hashes to all deliverable DOCX reports.</div>
                </div>
              </label>
            </div>
          </div>
        </section>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="btn-primary py-2.5 px-6 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving Configuration...' : loading ? 'Loading Configuration...' : 'Save Engine Configuration'}
          </button>
        </div>
      </form>
    </div>
  )
}
