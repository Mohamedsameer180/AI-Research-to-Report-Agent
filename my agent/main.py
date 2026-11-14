"""Root launcher for TaskFinisher AI Backend.

FastAPI application entrypoint delegating to backend/main.py.
Google ADK orchestrator execute_task compliant.
"""

import os
import sys

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from main import (
    app,
    orchestrator,
    TaskRequest,
    TaskResponse,
    HumanDecisionRequest,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
