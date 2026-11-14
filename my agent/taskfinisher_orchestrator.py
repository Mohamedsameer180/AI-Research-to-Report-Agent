"""Root compatibility proxy for TaskFinisher AI Orchestrator.

Google ADK (Agent Development Kit) multi-agent orchestrator.
Delegates to backend/taskfinisher_orchestrator.py.
"""

import os
import sys

_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from backend.taskfinisher_orchestrator import (
    TaskFinisherOrchestrator,
    TaskStatus,
    VerificationStatus,
    StepResult,
    TaskState,
    MAX_RETRIES,
)
