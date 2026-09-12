"""Gatekeeper: loads the policy and decides on a call before it is executed.

`permissions` layer: the call is in the list of authorized calls and its arguments
meet the declared constraint; everything else is blocked by default deny.
`memory` layer: the same agent's history, as a budget. It looks; it does not record —
the executor owns the reservations and passes what it has in a `MemoryView`.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_DENY = "default-deny"
LAYERS = ("permissions", "memory")
ARG_TYPES = {"str": str, "int": int}
ALLOWED_KEYS = {"id", "scope", "tool", "operation", "args", "source", "name_source"}
MEMORY_KEYS = {"id", "scope", "tool", "operation", "budget", "against", "ratio", "counts", "source"}
# Which argument of the call spends each kind of budget. A budget we cannot read is not enforced.
BUDGET_ARG = {"task_seconds": "seconds"}


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
class MemoryView:
    """What the gatekeeper is allowed to know about this agent's past. Owned by the executor."""
    agent_id: str
    reserved_task_seconds: int
    wall_seconds_elapsed: int


@dataclass(frozen=True)
class Policy:
    version: str
    task: str
    default: str
    allowed: tuple[dict, ...]
    memory_rules: tuple[dict, ...]


def check_memory_rule(path: Path, rule: dict, allowed: list[dict]) -> None:
    """A memory rule the code cannot enforce as written is rejected at the door, not mid-run.

    Every field is checked against what `decide` actually does, so the rule text and the
    behaviour it is logged as cannot disagree.
    """
    missing = MEMORY_KEYS - set(rule)
    if missing:
        raise ValueError(f"{path}: memory rule missing {sorted(missing)}: {rule}")
    unsupported = {"scope": "agent_history", "against": "wall_seconds_elapsed", "counts": "authorizations"}
    for field, only in unsupported.items():
        if rule[field] != only:
            raise ValueError(f"{path}: {rule['id']} declares {field}: {rule[field]}, and only {only} is enforced")
    if rule["budget"] not in BUDGET_ARG:
        raise ValueError(f"{path}: {rule['id']} counts an unknown budget {rule['budget']!r}")
    if not isinstance(rule["ratio"], (int, float)) or isinstance(rule["ratio"], bool) or rule["ratio"] <= 0:
        raise ValueError(f"{path}: {rule['id']} needs a positive ratio, not {rule['ratio']!r}")
    target = next((a for a in allowed if (a["tool"], a["operation"]) == (rule["tool"], rule["operation"])), None)
    if target is None:
        raise ValueError(f"{path}: {rule['id']} governs {rule['tool']}.{rule['operation']}, which the task does not authorize")
    if BUDGET_ARG[rule["budget"]] not in target["args"]:
        raise ValueError(f"{path}: {rule['id']} spends {BUDGET_ARG[rule['budget']]!r}, absent from {target['id']}")


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
    for rule in raw.get("memory_rules", []):
        check_memory_rule(path, rule, raw.get("allowed", []))
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
    if "permissions" not in layers:
        # Permissions are always enforced. Refusing the tuple keeps the `layers` stamped on every
        # log line from claiming a run that did less checking than it did.
        raise ValueError("permissions is not optional: every run enforces it and the log says so")


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


def memory_rules_for(policy: Policy, call: Call) -> tuple[dict, ...]:
    """The memory rules that govern this call. Empty means the memory layer has nothing to say."""
    return tuple(r for r in policy.memory_rules if (r["tool"], r["operation"]) == (call.tool, call.operation))


def over_budget(rule: dict, memory: MemoryView) -> str | None:
    """Reason if this agent's history already spends more than it has earned; None if not."""
    earned = memory.wall_seconds_elapsed * rule["ratio"]
    if memory.reserved_task_seconds > earned:
        return (f"{memory.agent_id} has {memory.reserved_task_seconds} task seconds reserved "
                f"against {memory.wall_seconds_elapsed} wall seconds elapsed")
    return None


def decide(call: Call, policy: Policy, layers: tuple[str, ...] = ("permissions",),
           memory: MemoryView | None = None) -> Decision:
    check_layers(layers)
    if "memory" in layers and memory is None:
        # No silent pass: an unknown history is not permission.
        raise ValueError("the memory layer needs a MemoryView; it is not evaluated without one")

    name = f"{call.tool}.{call.operation}"
    entry = next((a for a in policy.allowed if (a["tool"], a["operation"]) == (call.tool, call.operation)), None)
    if entry is None:
        return Decision("block", DEFAULT_DENY, f"{name} is not in the list of calls the task authorizes")
    reason = invalid_args(call.args, entry["args"])
    if reason:
        return Decision("block", f"{entry['id']}:args", reason)

    if "memory" in layers:
        for rule in memory_rules_for(policy, call):
            reason = over_budget(rule, memory)
            if reason:
                return Decision("block", rule["id"], reason)
    return Decision("allow", entry["id"], f"{name} authorized by {entry['source']}")
