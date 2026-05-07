from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import importlib
import json
from pathlib import Path


@dataclass(frozen=True)
class TaskSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    module: str
    handler_name: str
    tags: List[str]
    handler: Optional[Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]]


def _resolve_handler(module_name: str, handler_name: str) -> Optional[Callable]:
    if not module_name or not handler_name:
        return None
    try:
        module = importlib.import_module(f"{__package__}.{module_name}")
    except Exception:
        return None
    return getattr(module, handler_name, None)


def _load_specs() -> Dict[str, TaskSpec]:
    spec_path = Path(__file__).resolve().parent / "tool_specs.json"
    if not spec_path.exists():
        return {}
    with spec_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    tasks: Dict[str, TaskSpec] = {}
    for item in data.get("tasks", []):
        name = item.get("name")
        if not name:
            continue
        module = item.get("module", "")
        handler_name = item.get("handler", "")
        handler = _resolve_handler(module, handler_name)
        tasks[name] = TaskSpec(
            name=name,
            description=item.get("description", ""),
            input_schema=item.get("input_schema", {}),
            output_schema=item.get("output_schema", {}),
            module=module,
            handler_name=handler_name,
            tags=item.get("tags", []),
            handler=handler,
        )
    return tasks


_TASKS = _load_specs()


def get_task(name: str) -> Optional[TaskSpec]:
    return _TASKS.get(name)


def list_tasks() -> List[TaskSpec]:
    return list(_TASKS.values())

