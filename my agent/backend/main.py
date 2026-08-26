"""Compatibility launcher for the canonical root FastAPI app."""

from pathlib import Path
import importlib.util
import sys

import uvicorn

_ROOT_MAIN = Path(__file__).resolve().parent.parent / "main.py"
_ROOT_DIR = str(_ROOT_MAIN.parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
_SPEC = importlib.util.spec_from_file_location("_taskfinisher_root_main", _ROOT_MAIN)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MODULE)

app = _MODULE.app
orchestrator = _MODULE.orchestrator
TaskRequest = _MODULE.TaskRequest
TaskResponse = _MODULE.TaskResponse
HumanDecisionRequest = _MODULE.HumanDecisionRequest


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
