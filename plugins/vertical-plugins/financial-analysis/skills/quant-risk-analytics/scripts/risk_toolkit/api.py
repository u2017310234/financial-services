from __future__ import annotations

from typing import Any, Dict, Optional

from .errors import RiskPracticeError, TaskNotFoundError, TaskNotImplementedError
from . import registry


def run(task: str, payload: Dict[str, Any], *, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    options = options or {}
    spec = registry.get_task(task)
    if spec is None:
        raise TaskNotFoundError(f"Unknown task: {task}")
    if spec.handler is None:
        raise TaskNotImplementedError(f"Task not implemented: {task}")
    try:
        result = spec.handler(payload, options)
        return {
            "status": "ok",
            "result": result,
            "artifacts": result.get("artifacts", []) if isinstance(result, dict) else [],
            "warnings": result.get("warnings", []) if isinstance(result, dict) else [],
            "meta": {
                "task": spec.name,
                "module": spec.module,
                "schema_version": options.get("schema_version", "1.0"),
            },
        }
    except RiskPracticeError as exc:
        if options.get("raise_on_error"):
            raise
        return {
            "status": "error",
            "error": str(exc),
            "result": None,
            "artifacts": [],
            "warnings": [],
            "meta": {"task": spec.name, "module": spec.module},
        }
    except Exception as exc:
        if options.get("raise_on_error"):
            raise
        return {
            "status": "error",
            "error": f"Unhandled error: {exc}",
            "result": None,
            "artifacts": [],
            "warnings": [],
            "meta": {"task": spec.name, "module": spec.module},
        }

