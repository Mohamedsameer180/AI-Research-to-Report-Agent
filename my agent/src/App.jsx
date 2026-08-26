import React, { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import HeaderTopBar from './components/HeaderTopBar'
import GlobalSearchModal from './components/GlobalSearchModal'
import NodeInspectorModal from './components/NodeInspectorModal'
import { playSound } from './components/SoundEffects'

// View Components
import OverviewView from './views/OverviewView'
import TasksView from './views/TasksView'
import AgentActivityView from './views/AgentActivityView'
import ResearchView from './views/ResearchView'
import DocumentsView from './views/DocumentsView'
import EvidenceView from './views/EvidenceView'
import HistoryView from './views/HistoryView'
import ReplayView from './views/ReplayView'
import AnalyticsView from './views/AnalyticsView'
import SettingsView from './views/SettingsView'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const backendErrorResult = (message, userRequest = '') => ({
  task_id: null,
  user_request: userRequest || 'No active task',
  status: 'FAILED',
  verdict: 'FAILED',
  completion_percentage: 0,
  events: [],
  steps: {},
  final_report: message,
  error: message,
})

export default function App() {
  const [activePage, setActivePage] = useState('overview')
  const [activeScenario, setActiveScenario] = useState('success')
  const [taskResult, setTaskResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [searchOpen, setSearchOpen] = useState(false)
  const [inspectedNode, setInspectedNode] = useState(null)

  // Sound triggering helper
  const handlePlaySound = useCallback((type = 'click', force = false) => {
    playSound(type, force || soundEnabled)
  }, [soundEnabled])

  // Execute demo scenario through the backend only.
  const runScenario = async (scenarioKey) => {
    setActiveScenario(scenarioKey)
    setLoading(true)
    handlePlaySound('click')

    try {
      const response = await fetch(`${API_BASE_URL}/api/demo/${scenarioKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (response.ok) {
        const data = await response.json()
        setTaskResult(data)
      } else {
        setTaskResult(backendErrorResult(`Demo scenario failed with HTTP ${response.status}. Start the backend and retry.`))
      }
    } catch (e) {
      setTaskResult(backendErrorResult('Backend is unavailable. Start the TaskFinisher API to run a real task.'))
    } finally {
      setTimeout(() => {
        setLoading(false)
        if (scenarioKey === 'human') {
          handlePlaySound('alert')
          setActivePage('activity')
        } else if (scenarioKey === 'recovery') {
          handlePlaySound('complete')
          setActivePage('activity')
        } else {
          handlePlaySound('complete')
        }
      }, 1000)
    }
  }

  // Handle task submission from TaskView
  const handleTaskSubmit = async (taskPayload) => {
    setLoading(true)
    handlePlaySound('click')

    try {
      let uploadedFiles = []
      const filesToUpload = (taskPayload.files || [])
        .map((item) => item.file)
        .filter(Boolean)

      if (filesToUpload.length > 0) {
        const formData = new FormData()
        filesToUpload.forEach((file) => formData.append('files', file))

        const uploadResponse = await fetch(`${API_BASE_URL}/api/files/upload`, {
          method: 'POST',
          body: formData,
        })

        if (!uploadResponse.ok) {
          setTaskResult(backendErrorResult(`File upload failed with HTTP ${uploadResponse.status}.`, taskPayload.prompt))
          return
        }

        const uploadData = await uploadResponse.json()
        uploadedFiles = (uploadData.files || []).map((file) => file.file_path)
      }

      const response = await fetch(`${API_BASE_URL}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_request: taskPayload.prompt,
          scenario: activeScenario,
          uploaded_files: uploadedFiles,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setTaskResult(data)
      } else {
        setTaskResult(backendErrorResult(`Task submission failed with HTTP ${response.status}.`, taskPayload.prompt))
      }
    } catch (e) {
      setTaskResult(backendErrorResult('Backend is unavailable. Start the TaskFinisher API to submit real tasks.', taskPayload.prompt))
    } finally {
      setTimeout(() => {
        setLoading(false)
        handlePlaySound('complete')
        setActivePage('overview')
      }, 1200)
    }
  }

  // Handle human intervention choice
  const handleHumanDecision = async (option) => {
    handlePlaySound('click')
    setLoading(true)

    try {
      if (taskResult?.task_id) {
        const response = await fetch(`${API_BASE_URL}/api/tasks/${taskResult.task_id}/human-decision`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ selected_option: option }),
        })
        if (response.ok) {
          setTaskResult(await response.json())
        } else {
          setTaskResult(backendErrorResult(`Human decision failed with HTTP ${response.status}.`, taskResult.user_request))
        }
      } else {
        setTaskResult(backendErrorResult('No active backend task is waiting for a human decision.'))
      }
    } catch (e) {
      setTaskResult(backendErrorResult('Backend is unavailable. The human decision was not recorded.', taskResult?.user_request))
    }

    setTimeout(() => {
      setLoading(false)
      handlePlaySound('complete')
    }, 900)
  }

  // Search selection handler
  const handleSearchSelect = (targetPage, item) => {
    handlePlaySound('click')
    if (targetPage === 'OPEN_SEARCH') {
      setSearchOpen(true)
    } else if (targetPage) {
      setActivePage(targetPage)
    }
  }

  return (
    <div className="flex h-screen bg-[#050505] text-[#FFFFFF] font-sans antialiased overflow-hidden selection:bg-[#FF6A00]/30 selection:text-white">
      {/* 1. Left Cyberpunk Sidebar */}
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
        onPlaySound={handlePlaySound}
      />

      {/* 2. Main Mission Control Workspace */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* Top Header */}
        <HeaderTopBar
          onOpenSearch={() => setSearchOpen(true)}
          soundEnabled={soundEnabled}
          setSoundEnabled={setSoundEnabled}
          onPlaySound={handlePlaySound}
          onOpenProfile={() => setActivePage('settings')}
          pendingNotificationsCount={taskResult?.verdict === 'WAITING_FOR_HUMAN' ? 3 : 2}
        />

        {/* Scrollable View Canvas */}
        <main className="flex-1 overflow-y-auto px-6 py-6 cyber-grid">
          {activePage === 'overview' && (
            <OverviewView
              taskResult={taskResult}
              loading={loading}
              activeScenario={activeScenario}
              onRunDemo={runScenario}
              onNavigate={setActivePage}
              onSelectNode={setInspectedNode}
              onPlaySound={handlePlaySound}
            />
          )}

          {activePage === 'tasks' && (
            <TasksView
              loading={loading}
              onSubmitTask={handleTaskSubmit}
              onRunDemo={runScenario}
              onPlaySound={handlePlaySound}
            />
          )}

          {activePage === 'activity' && (
            <AgentActivityView
              taskResult={taskResult}
              activeScenario={activeScenario}
              onRunDemo={runScenario}
              onHumanDecision={handleHumanDecision}
              onPlaySound={handlePlaySound}
            />
          )}

          {activePage === 'research' && (
            <ResearchView
              taskResult={taskResult}
              onNavigate={setActivePage}
              onPlaySound={handlePlaySound}
            />
          )}

          {activePage === 'documents' && (
            <DocumentsView
              taskResult={taskResult}
              apiBaseUrl={API_BASE_URL}
              onPlaySound={handlePlaySound}
            />
          )}

          {activePage === 'evidence' && (
            <EvidenceView
              taskResult={taskResult}
              onPlaySound={handlePlaySound}
            />
          )}

          {activePage === 'history' && (
            <HistoryView
              taskResult={taskResult}
              onSelectTask={(task) => {
                setActivePage('replay')
              }}
              onPlaySound={handlePlaySound}
            />
          )}

          {activePage === 'replay' && (
            <ReplayView
              taskResult={taskResult}
              onPlaySound={handlePlaySound}
            />
          )}

          {activePage === 'analytics' && (
            <AnalyticsView taskResult={taskResult} />
          )}

          {activePage === 'settings' && (
            <SettingsView
              apiBaseUrl={API_BASE_URL}
              onPlaySound={handlePlaySound}
            />
          )}
        </main>
      </div>

      {/* Global Command-K Search Modal */}
      <GlobalSearchModal
        isOpen={searchOpen}
        taskResult={taskResult}
        onClose={() => setSearchOpen(false)}
        onSelectResult={handleSearchSelect}
      />

      {/* DAG Node Inspector Modal */}
      <NodeInspectorModal
        node={inspectedNode}
        onClose={() => setInspectedNode(null)}
      />
    </div>
  )
}
