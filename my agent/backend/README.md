# TASKFINISHER AI - Backend

The core intelligence and persistence engine for TASKFINISHER AI, built with **FastAPI**, **Google ADK** (Agent Development Kit), and **SQLite** (with optional Firebase mirroring).

## Architecture

```
backend/
├── main.py                      # FastAPI entrypoint, WebSocket, and REST endpoints
├── taskfinisher_orchestrator.py # 8-step state machine orchestrator (Google ADK)
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration (API keys, ports)
├── start_backend.bat            # Quick start batch script
└── start_backend.ps1            # Quick start PowerShell script
```

### Shared Engine Components
- `../database/`: SQLite database manager (`db_manager.py`), SHA-256 document integrity ledger (`document_integrity.py`), and optional Firebase sync (`firebase_service.py`).
- `../tools/`: Google ADK tools including web search (`web_search_tool.py`), file processor (`file_processor_tool.py`), and web scraper (`web_scraper_tool.py`).
- `../agents/`: Specialized agent roles.

## Google ADK Agents & Flow
1. **PlannerAgent (`S1`-`S2`)**: Converts user intent into an auditable 8-step plan.
2. **DocumentAgent (`S3`)**: Ingests uploaded documents with SHA-256 hash validation.
3. **ResearchAgent (`S4`)**: Collects evidence from reliable web sources.
4. **VerificationAgent (`S5`)**: Audits evidence for credibility against the verification floor.
5. **RecoveryAgent (`S6`)**: Recovers from search or tool failures with automated retries.
6. **HumanApprovalController (`S6`)**: Pauses execution when human decision is needed for conflicts.
7. **ReportAgent (`S7`)**: Compiles comprehensive markdown and Word (`.docx`) reports.
8. **FinalVerifierAgent (`S8`)**: Truthfully computes final status (`DONE`, `PARTIALLY_DONE`, or `FAILED`).

## Getting Started

### Prerequisites
- Python 3.10+
- Dependencies: `pip install -r requirements.txt`

### Running the Backend
```bash
python main.py
```
Or from the project root:
```bash
python main.py
```
- API Server: `http://127.0.0.1:8000`
- Interactive Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `GET /health`

