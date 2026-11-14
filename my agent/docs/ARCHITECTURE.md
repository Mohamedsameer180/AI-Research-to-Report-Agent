# TASKFINISHER AI System Architecture

## Overview
TASKFINISHER AI is an autonomous agentic system built with Google ADK (Agent Development Kit), FastAPI, React 18, and SQLite.

## Core Flow
1. **Plan (`S1`-`S2`)**: The PlannerAgent parses user intent into discrete steps with verifiable outputs.
2. **Execute (`S3`-`S4`)**: The DocumentAgent and ResearchAgent gather verified facts using specialized tools.
3. **Verify (`S5`)**: The VerificationAgent checks every claim and document hash against strict criteria.
4. **Recover (`S6`)**: The RecoveryAgent automatically switches strategies if tools fail.
5. **Human Decision (`S6`)**: The HumanApprovalController pauses the engine if subjective conflicts arise.
6. **Artifact Generation (`S7`)**: The ReportAgent formats the findings into `.docx` and `.md`.
7. **Final Verification (`S8`)**: The FinalVerifierAgent ensures all steps truly succeeded before reporting `DONE`.

## Layer Separation
- **`frontend/`**: Modern React 18 SPA powered by Vite, Tailwind CSS, and Lucide icons.
- **`backend/`**: FastAPI REST & WebSocket server orchestrating Google ADK agents.
- **`database/`**: Persistent SQLite database and SHA-256 document registry.
- **`tools/`**: Reusable ADK tool definitions.

