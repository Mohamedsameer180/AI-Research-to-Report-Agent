"""Compatibility wrapper for the canonical root orchestrator."""

from pathlib import Path
import importlib.util
import sys

_ROOT_ORCHESTRATOR = Path(__file__).resolve().parent.parent / "taskfinisher_orchestrator.py"
_ROOT_DIR = str(_ROOT_ORCHESTRATOR.parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
_SPEC = importlib.util.spec_from_file_location("_taskfinisher_root_orchestrator", _ROOT_ORCHESTRATOR)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MODULE)

TaskStatus = _MODULE.TaskStatus
VerificationStatus = _MODULE.VerificationStatus
StepResult = _MODULE.StepResult
TaskState = _MODULE.TaskState
TaskFinisherOrchestrator = _MODULE.TaskFinisherOrchestrator
MAX_RETRIES = _MODULE.MAX_RETRIES
