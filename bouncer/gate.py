"""Gatekeeper: loads the policy and decides on a call before it is executed.

`permissions` layer: the call is in the list of authorized calls and its arguments
meet the declared constraint; everything else is blocked by default deny.
The `memory` layer is declared in the policy and implemented in phase 4.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_DENY = "default-deny"
LAYERS = ("permissions", "memory")
ARG_TYPES = {"str": str, "int": int}
ALLOWED_KEYS = {"id", "scope", "tool", "operation", "args", "source", "name_source"}


@dataclass(frozen=True)
class Call:
    tool: str
    operation: str
    args: dict


@dataclass(frozen=True)
class Decision:
    outcome: str  # "allow" | "block"
    rule: str
    reason: str


@dataclass(frozen=True)
class Policy:
    version: str
    task: str
    default: str
    allowed: tuple[dict, ...]
    memory_rules: tuple[dict, ...]


def load_policy(path: Path) -> Policy:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw.get("default") != "deny":
        raise ValueError(f"{path}: the policy must declare default: deny")
    for entry in raw.get("allowed", []):
        missing = ALLOWED_KEYS - set(entry)
        if missing or entry["scope"] != "call":
            raise ValueError(f"{path}: allowed entry incomplete or with scope other than call: {entry}")
        unknown_types = set(entry["args"].values()) - set(ARG_TYPES)
        if unknown_types:
            raise ValueError(f"{path}: unsupported argument types {unknown_types} in {entry['id']}")
    return Policy(
        version=str(raw["version"]),
        task=raw["task"],
        default=raw["default"],
        allowed=tuple(raw.get("allowed", [])),
        memory_rules=tuple(raw.get("memory_rules", [])),
    )


def check_layers(layers: tuple[str, ...]) -> None:
    unknown = set(layers) - set(LAYERS)
    if unknown:
        raise ValueError(f"unknown layers: {sorted(unknown)}")
    if "memory" in layers:
        raise NotImplementedError("the memory layer is implemented in phase 4; it is not evaluated silently")


def invalid_args(args: dict, schema: dict) -> str | None:
    """Reason if the arguments do not meet the constraint; None if they do."""
    extra = set(args) - set(schema)
    if extra:
        return f"unexpected arguments: {sorted(extra)}"
    for name, type_name in schema.items():
        if name not in args:
            return f"missing argument {name}"
        value = args[name]
        if not isinstance(value, ARG_TYPES[type_name]) or isinstance(value, bool):
            return f"{name} must be {type_name}"
        if type_name == "str" and not value.strip():
            return f"{name} must not be empty"
        if type_name == "int" and value < 1:
            return f"{name} must be a positive integer"
    return None


def decide(call: Call, policy: Policy, layers: tuple[str, ...] = ("permissions",)) -> Decision:
    check_layers(layers)
    name = f"{call.tool}.{call.operation}"
    entry = next((a for a in policy.allowed if (a["tool"], a["operation"]) == (call.tool, call.operation)), None)
    if entry is None:
        return Decision("block", DEFAULT_DENY, f"{name} is not in the list of calls the task authorizes")
    reason = invalid_args(call.args, entry["args"])
    if reason:
        return Decision("block", f"{entry['id']}:args", reason)
    return Decision("allow", entry["id"], f"{name} authorized by {entry['source']}")
