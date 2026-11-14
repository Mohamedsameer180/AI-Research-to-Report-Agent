import React, { useState } from 'react'

const examples = [
  'Analyze uploaded research papers, extract methodologies and findings, and compare cross-document agreements and contradictions.',
  'Investigate empirical results across multi-paper PDF literature with page-level citations.',
  'Identify research gaps and synthesize findings from uploaded academic publications.',
]

const scenarios = [
  { id: 'success', label: 'Success' },
  { id: 'recovery', label: 'Recovery' },
  { id: 'partial', label: 'Partial' },
  { id: 'human', label: 'Human Decision' },
]

const depths = ['Quick', 'Standard', 'Deep Research']
const outputs = ['DOCX', 'PDF', 'Both']

function TaskForm({ activeScenario, loading, onDemo, onScenarioChange, onSubmit }) {
  const [userRequest, setUserRequest] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [selectedFiles, setSelectedFiles] = useState([])
  const [depth, setDepth] = useState('Standard')
  const [output, setOutput] = useState('DOCX')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSubmitError('')

    if (!userRequest.trim()) {
      setSubmitError('Describe the task before starting execution.')
      return
    }

    try {
      await onSubmit(`${userRequest}\n\nResearch depth: ${depth}\nOutput format: ${output}`, selectedFiles)
      setUserRequest('')
      setSelectedFiles([])
    } catch (error) {
      setSubmitError('Failed to submit task. Please try again.')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="task-card">
      <div className="card-heading">
        <div>
          <p className="kicker">Task Creation</p>
          <h2>What should I finish for you?</h2>
        </div>
        <span className="mode-badge">Autonomous</span>
      </div>

      <label htmlFor="userRequest">Describe your task</label>
      <textarea
        id="userRequest"
        value={userRequest}
        onChange={(event) => setUserRequest(event.target.value)}
        rows="8"
        placeholder="Analyze uploaded research papers, extract methodologies and findings, and compare cross-document agreements and contradictions."
        disabled={loading}
      />

      {submitError && <p className="form-error">{submitError}</p>}

      <div className="upload-drop">
        <div>
          <label htmlFor="taskFiles">Attach files</label>
          <span>PDF, DOCX, XLSX, CSV, TXT</span>
        </div>
        <input
          id="taskFiles"
          type="file"
          multiple
          disabled={loading}
          onChange={(event) => setSelectedFiles(Array.from(event.target.files || []))}
        />
        <p>{selectedFiles.length ? `${selectedFiles.length} file(s) queued for document analysis` : '+ Add files for document agents'}</p>
      </div>

      {selectedFiles.length > 0 && (
        <div className="file-list">
          {selectedFiles.map((file) => <span key={`${file.name}-${file.size}`}>{file.name}</span>)}
        </div>
      )}

      <fieldset className="segmented-control">
        <legend>Research depth</legend>
        {depths.map((item) => (
          <button type="button" key={item} className={depth === item ? 'active' : ''} onClick={() => setDepth(item)} disabled={loading}>
            {item}
          </button>
        ))}
      </fieldset>

      <fieldset className="segmented-control">
        <legend>Output</legend>
        {outputs.map((item) => (
          <button type="button" key={item} className={output === item ? 'active' : ''} onClick={() => setOutput(item)} disabled={loading}>
            {item}
          </button>
        ))}
      </fieldset>

      <div className="scenario-tabs" aria-label="Demo scenario">
        {scenarios.map((scenario) => (
          <button
            type="button"
            key={scenario.id}
            className={activeScenario === scenario.id ? 'active' : ''}
            onClick={() => onScenarioChange(scenario.id)}
            disabled={loading}
          >
            {scenario.label}
          </button>
        ))}
      </div>

      <div className="example-row">
        {examples.map((example) => (
          <button type="button" key={example} onClick={() => setUserRequest(example)} disabled={loading}>
            {example}
          </button>
        ))}
      </div>

      <button type="submit" className="primary-button" disabled={loading || !userRequest.trim()}>
        {loading ? 'EXECUTING...' : 'START TASK ->'}
      </button>

      <button type="button" className="secondary-button" disabled={loading} onClick={() => onDemo(activeScenario)}>
        Run selected demo
      </button>
    </form>
  )
}

export default TaskForm
