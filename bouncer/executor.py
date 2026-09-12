"""Controlled executor: assigns identity, asks the gatekeeper, executes only if allowed, and logs.

Walks a JSONL script. Identity and policy come from here, not from the call's
arguments. The log is written outside the working directory the tools receive.
"""

import argparse
import json
import shutil
import time
from collections.abc import Callable
from pathlib import Path

from bouncer.gate import (BUDGET_ARG, Call, HistoryView, Policy, check_layers, decide, load_policy,
                          history_rules_for)
from bouncer.tools import NO_NEW_ROUND, TOOLS, RunState

LOG_NAME = "decisions.jsonl"
# Fixed wait between rounds of the scenario: 2111 s = 35m11, a value observed in one
# corpus cohort ("35m11 cooldown" in records.jsonl.gz). The question does not announce it.
COOLDOWN_SECONDS = 2111


def result_ref(name: str, args: dict, state: RunState, value: object) -> str:
    """Reference to the result without copying bodies into the log."""
    if name == "page.read":
        return f"page:{args['page']}"
    if name == "round.question":
        return "round:none" if value == NO_NEW_ROUND else f"round:{state.round}"
    if name == "web.search":
        return f"search:{len(value)}"
    if name == "clock.wait":
        return f"wait:{value}s"
    return str(value)


def wall_elapsed(state: RunState) -> int:
    """Whole wall seconds since the run began. The agent never supplies this."""
    return int(state.wall_clock() - state.wall_start) + state.wall_offset


def execute_line(index: int, line: dict, run_id: str, policy: Policy, layers: tuple[str, ...],
                 state: RunState, tools: dict[str, Callable], reserved: dict[str, int]) -> dict:
    raw = line.get("call") if isinstance(line.get("call"), dict) else {}
    tool, operation, args = raw.get("tool"), raw.get("operation"), raw.get("args", {})
    record = {
        "run_id": run_id,
        "agent_id": line.get("agent"),
        "call_id": f"{run_id}:{index}",
        "tool": tool,
        "operation": operation,
        "decision": None,
        "rule": None,
        "reason": None,
        "policy_version": policy.version,
        "layers": list(layers),
        "clock_mode": state.clock_mode,
        "cooldown_seconds": state.cooldown_seconds,
        "status": None,
        "duration_ms": 0,
    }
    if not isinstance(record["agent_id"], str) or not record["agent_id"].strip():
        # A non-string identity is no identity: it would key a budget of its own, and `True`
        # would share one with `1`.
        return record | {"reason": "no agent_id assigned by the executor", "status": "rejected"}
    if not (isinstance(tool, str) and isinstance(operation, str) and isinstance(args, dict)):
        return record | {"reason": "malformed script line: call.tool, call.operation and call.args", "status": "rejected"}

    call = Call(tool, operation, dict(args))
    agent_id = record["agent_id"]
    history = rules = None
    if "per_history" in layers:
        history = HistoryView(agent_id, reserved.get(agent_id, 0), wall_elapsed(state))
        rules = history_rules_for(policy, call)

    started = time.perf_counter()
    decision = decide(call, policy, layers, history)
    record |= {
        "decision": decision.outcome,
        "rule": decision.rule,
        "reason": decision.reason,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
    }
    if rules:  # the state that justifies the decision, only where a rule actually looked
        record["history_state"] = {
            "reserved_task_seconds": history.reserved_task_seconds,
            "wall_seconds_elapsed": history.wall_seconds_elapsed,
        }
    if decision.outcome != "allow":
        return record | {"status": "blocked"}

    # `counts: authorizations`: the budget is spent on the permission, not on the result.
    spending = sum(call.args[BUDGET_ARG[rule["budget"]]] for rule in rules or ())
    if spending:
        reserved[agent_id] = reserved.get(agent_id, 0) + spending

    name = f"{call.tool}.{call.operation}"
    try:
        value = tools[name](state, call.args)
    except Exception as error:  # the tool failed after being allowed: logged, not a success
        if spending:
            reserved[agent_id] -= spending  # released: a call that did not happen spends nothing
        message = str(error).replace(str(state.workdir), "<workdir>")  # no host paths in the log
        return record | {"status": "error", "error": f"{type(error).__name__}: {message}"}
    if spending:
        # A budgeted tool returns what it actually spent: `clock.wait` gives back the seconds
        # really waited, which are fewer when a round cuts the wait short. Charging the full
        # request would leave an honest agent owing time it never received. A tool that cannot
        # say what it spent is billed the full authorization; it never gets a refund it did not
        # earn, and the budget can neither go negative nor exceed what was authorized.
        reported = value if isinstance(value, int) and not isinstance(value, bool) else -1
        spent = reported if 0 <= reported <= spending else spending
        reserved[agent_id] -= spending - spent
    return record | {"status": "ok", "result_ref": result_ref(name, call.args, state, value)}


def run_script(script: Path, policy: Path, run_id: str, output_dir: Path, scenario_dir: Path,
               layers: tuple[str, ...] = ("per_call",), wall_clock: Callable[[], float] | None = None,
               clock_mode: str = "clock_runs_ahead", tools: dict[str, Callable] | None = None,
               cooldown_seconds: int = COOLDOWN_SECONDS) -> Path:
    check_layers(layers)
    if cooldown_seconds < 1:
        raise ValueError(f"cooldown_seconds must be a positive integer, not {cooldown_seconds}")
    if scenario_dir.resolve() in (output_dir.resolve(), *output_dir.resolve().parents):
        raise ValueError("output_dir must not be inside the scenario: the originals are never touched")
    policy_obj = load_policy(policy)
    questions = [json.loads(l) for l in (scenario_dir / "questions.jsonl").read_text(encoding="utf-8").splitlines() if l]

    workdir = output_dir / "workdir"
    if workdir.exists():
        # Only what a previous run left behind is replaced; nothing that does not come from the scenario.
        foreign = {p.name for p in workdir.iterdir()} - {p.name for p in (scenario_dir / "wiki").iterdir()}
        if foreign:
            raise ValueError(f"workdir already exists with files foreign to the scenario: {sorted(foreign)}")
        shutil.rmtree(workdir)
    shutil.copytree(scenario_dir / "wiki", workdir)
    # No system clock by default: the only thing that costs time here is waiting, and the
    # waits are counted in `wall_offset`. Reading `time.monotonic` would make the same input
    # decide differently on a slower machine, which P0-07 forbids.
    clock = wall_clock or (lambda: 0.0)
    state = RunState(
        workdir=workdir,
        task_clock_seconds=0,
        wall_clock=clock,
        clock_mode=clock_mode,
        cooldown_seconds=cooldown_seconds,
        round=0,
        answers={},
        questions=questions,
        wall_start=clock(),
    )
    reserved: dict[str, int] = {}  # task seconds authorized per agent; never shared between agents

    log_path = output_dir / LOG_NAME
    lines = [json.loads(l) for l in script.read_text(encoding="utf-8").splitlines() if l]
    with log_path.open("w", encoding="utf-8") as fh:
        for index, line in enumerate(lines, start=1):
            record = execute_line(index, line, run_id, policy_obj, layers, state, tools or TOOLS, reserved)
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=Path("scenario/policy.yaml"))
    parser.add_argument("--scenario", type=Path, default=Path("scenario"))
    parser.add_argument("--clock", choices=("clocks_matched", "clock_runs_ahead"), default="clock_runs_ahead")
    parser.add_argument("--cooldown", type=int, default=COOLDOWN_SECONDS, help="task seconds between rounds")
    parser.add_argument("--layers", default="per_call", help="comma-separated: per_call[,per_history]")
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_script(args.script, args.policy, args.run_id, args.output_dir, args.scenario,
                          layers=tuple(args.layers.split(",")), clock_mode=args.clock,
                          cooldown_seconds=args.cooldown)
    records = [json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines()]
    counts = {status: sum(r["status"] == status for r in records) for status in ("ok", "blocked", "error", "rejected")}
    print(json.dumps({"run_id": args.run_id, "calls": len(records), **counts, "log": str(log_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
