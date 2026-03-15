"""Lightweight tool registry — replaces FastMCP's @mcp.tool() decorator.

Usage in tool modules:
    from mcp_server.tool_registry import register_tool

    @register_tool
    async def my_tool(param1: str, param2: int = 0, session_id: str = "default") -> dict:
        '''Tool description here.'''
        ...

The registry auto-generates JSON Schema from function signatures and hides
the ``session_id`` parameter (internal, not exposed to MCP clients).
"""

from __future__ import annotations

import inspect
import json
from typing import Any, Callable, get_type_hints

from mcp.types import Tool, TextContent

# Global registries
_TOOLS: dict[str, Tool] = {}
_HANDLERS: dict[str, Callable] = {}

# Type mapping for JSON Schema
_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    dict: "object",
    list: "array",
}


def _is_union(annotation: Any) -> bool:
    """Check if annotation is a Union type (typing.Union or Python 3.10+ X | Y)."""
    import typing
    import types
    origin = getattr(annotation, "__origin__", None)
    return origin is typing.Union or isinstance(annotation, types.UnionType)


def _get_union_args(annotation: Any) -> tuple:
    """Get args from Union or X | Y syntax."""
    return getattr(annotation, "__args__", ())


def _python_type_to_json_schema(annotation: Any) -> dict:
    """Convert a Python type annotation to a JSON Schema snippet."""
    origin = getattr(annotation, "__origin__", None)

    # Handle Optional (Union[X, None]) — both typing.Union and X | Y
    if _is_union(annotation):
        args = [a for a in _get_union_args(annotation) if a is not type(None)]
        if len(args) == 1:
            inner = _python_type_to_json_schema(args[0])
            # When inner is "number", also accept "integer" for MCP clients
            # that strictly distinguish integer vs number
            if inner.get("type") == "number":
                return {"anyOf": [inner, {"type": "integer"}, {"type": "null"}]}
            return {"anyOf": [inner, {"type": "null"}]}
        return {}

    # list[X]
    if origin is list:
        inner_args = getattr(annotation, "__args__", None)
        schema: dict = {"type": "array"}
        if inner_args:
            schema["items"] = _python_type_to_json_schema(inner_args[0])
        return schema

    # dict[K, V]
    if origin is dict:
        return {"type": "object"}

    # Plain types
    if annotation in _TYPE_MAP:
        return {"type": _TYPE_MAP[annotation]}

    return {}


def _build_input_schema(func: Callable) -> dict:
    """Build a JSON Schema ``inputSchema`` from function signature."""
    sig = inspect.signature(func)
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        # Skip session_id — internal parameter, not exposed to MCP clients
        if name == "session_id":
            continue
        # Skip **kwargs / *args
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        annotation = hints.get(name, param.annotation)
        prop: dict[str, Any] = {}

        if annotation is not inspect.Parameter.empty:
            prop = _python_type_to_json_schema(annotation)

        # Check if Optional (has None in union args)
        is_optional = False
        if _is_union(annotation):
            args = _get_union_args(annotation)
            if type(None) in args:
                is_optional = True

        properties[name] = prop

        # Required if no default value and not Optional
        if param.default is inspect.Parameter.empty and not is_optional:
            required.append(name)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def register_tool(func: Callable) -> Callable:
    """Decorator that registers an async function as an MCP tool."""
    name = func.__name__
    description = (func.__doc__ or "").strip()
    input_schema = _build_input_schema(func)

    _TOOLS[name] = Tool(
        name=name,
        description=description,
        inputSchema=input_schema,
    )
    _HANDLERS[name] = func
    return func


def get_all_tools() -> list[Tool]:
    """Return all registered Tool objects."""
    return list(_TOOLS.values())


async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Look up and call a registered tool, returning MCP TextContent."""
    handler = _HANDLERS.get(name)
    if not handler:
        return [TextContent(type="text", text=f"未知工具: {name}")]

    try:
        # Coerce int → float where the handler expects float / float | None
        hints = get_type_hints(handler)
        for arg_name, value in arguments.items():
            if isinstance(value, int) and not isinstance(value, bool):
                expected = hints.get(arg_name)
                if expected is float:
                    arguments[arg_name] = float(value)
                elif _is_union(expected):
                    non_none = [a for a in _get_union_args(expected) if a is not type(None)]
                    if float in non_none:
                        arguments[arg_name] = float(value)

        result = await handler(**arguments)
        if isinstance(result, str):
            text = result
        elif isinstance(result, dict) or isinstance(result, list):
            text = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            text = str(result)
        return [TextContent(type="text", text=text)]
    except PermissionError as e:
        return [TextContent(type="text", text=f"权限错误: {e}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]
