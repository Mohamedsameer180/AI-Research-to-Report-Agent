# TASKFINISHER AI - Frontend UI Dashboard

A modern React 18 single-page dashboard built with Vite, Tailwind CSS, and Lucide React icons.

## Features
- **Overview Dashboard**: Active task tracking, live progress percentage, status indicators, and prompt presets.
- **Interactive Agent Graph**: Dynamic node visualization of the 8 Google ADK agents (Planner, Research, Document, Verification, Recovery, Report, Human in the Loop, Final Verifier).
- **Execution History**: Searchable and filterable task history fetched directly from SQLite/FastAPI.
- **Audit & Evidence Viewer**: Cryptographic integrity hashes (SHA-256), step-by-step audit logs, and downloaded document artifacts (`.docx` / `.md`).
- **Human Decision Modal**: Interactive decision-point interface allowing users to resolve conflicts and resume paused agent execution.

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation
```bash
npm install
```

### Development
```bash
npm run dev
```
The application will be served at `http://localhost:5173`.

### Production Build
```bash
npm run build
```
Build artifacts will be generated in `dist/`.

### Preview Build
```bash
npm run preview
```

