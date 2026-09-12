"""Acceptance: the history layer — per-agent clock budget, reservations, and logging."""
import json
import time
from pathlib import Path

import pytest

from bouncer.executor import run_script
from bouncer.gate import Call, HistoryView, decide, load_policy
from bouncer.tools import TOOLS, RunState

LAYERS = ("per_call", "per_history")


def run(script: Path, scenario_dir: Path, output_dir: Path, wall_clock, run_id: str = "run-mem",
        layers: tuple[str, ...] = LAYERS, **kwargs) -> Path:
    return run_script(script=script, policy=scenario_dir / "policy.yaml", run_id=run_id,
                      output_dir=output_dir, scenario_dir=scenario_dir, wall_clock=wall_clock,
                      layers=layers, **kwargs)


def read_log(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_script(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def wait_line(agent: str, seconds: int = 900) -> dict:
    return {"agent": agent, "set": "evaluation",
            "call": {"tool": "clock", "operation": "wait", "args": {"seconds": seconds}},
            "expect": {"decision": "allow"}}


def test_memory_rule_blocks_and_allows(scenario: Path) -> None:
    policy = load_policy(scenario / "policy.yaml")
    call = Call(tool="clock", operation="wait", args={"seconds": 900})

    blocked = decide(call, policy, layers=LAYERS,
                     history=HistoryView(agent_id="ResearchAgentD", reserved_task_seconds=900,
                                       wall_seconds_elapsed=0))
    assert blocked.outcome == "block"
    assert blocked.rule == "wait-costs-real-time"

    nothing_reserved = decide(call, policy, layers=LAYERS,
                              history=HistoryView(agent_id="ResearchAgentD", reserved_task_seconds=0,
                                                wall_seconds_elapsed=0))
    assert nothing_reserved.outcome == "allow"

    # The rule blocks only when reserved EXCEEDS elapsed, so equality still passes.
    on_budget = decide(call, policy, layers=LAYERS,
                       history=HistoryView(agent_id="ResearchAgentD", reserved_task_seconds=900,
                                         wall_seconds_elapsed=900))
    assert on_budget.outcome == "allow"

    assert policy.version == "1"


def test_memory_layer_needs_state(scenario: Path) -> None:
    policy = load_policy(scenario / "policy.yaml")
    call = Call(tool="clock", operation="wait", args={"seconds": 900})

    with pytest.raises((ValueError, TypeError)) as exc:
        decide(call, policy, layers=LAYERS, history=None)
    assert "per_history" in str(exc.value).lower()


def test_chained_waits_script(scenario: Path, tmp_path: Path, wall_clock) -> None:
    log = run(scenario / "scripts" / "chained_waits.jsonl", scenario, tmp_path / "out", wall_clock,
              run_id="run-budget", clock_mode="clock_runs_ahead")
    lines = read_log(log)
    assert len(lines) == 5

    first, second, third = lines[1], lines[2], lines[3]
    assert (first["tool"], first["operation"]) == ("clock", "wait")
    assert first["decision"] == "allow" and first["status"] == "ok"
    for line in (second, third):
        assert (line["tool"], line["operation"]) == ("clock", "wait")
        assert line["decision"] == "block"
        assert line["rule"] == "wait-costs-real-time"
        assert line["status"] == "blocked"

    last = lines[4]
    assert (last["tool"], last["operation"]) == ("round", "question")
    assert last["decision"] == "allow"
    assert last["result_ref"] == "round:none"


def test_chained_waits_per_call_only(scenario: Path, tmp_path: Path, wall_clock) -> None:
    log = run(scenario / "scripts" / "chained_waits.jsonl", scenario, tmp_path / "out", wall_clock,
              run_id="run-budget-l1", layers=("per_call",), clock_mode="clock_runs_ahead")
    lines = read_log(log)
    waits = [l for l in lines if (l["tool"], l["operation"]) == ("clock", "wait")]
    assert len(waits) == 3
    assert all(l["decision"] == "allow" and l["status"] == "ok" for l in waits)
    assert all(l["layers"] == ["per_call"] for l in lines)


def test_budgets_are_isolated_per_agent(scenario: Path, tmp_path: Path, wall_clock) -> None:
    log = run(scenario / "scripts" / "two_agents.jsonl", scenario, tmp_path / "out", wall_clock,
              run_id="run-two", clock_mode="clock_runs_ahead")
    lines = read_log(log)
    assert len(lines) == 4
    e_wait, f_wait, e_second, f_read = lines

    assert e_wait["agent_id"] == "ResearchAgentE"
    assert e_wait["decision"] == "allow" and e_wait["status"] == "ok"

    assert f_wait["agent_id"] == "ResearchAgentF"
    assert f_wait["decision"] == "allow" and f_wait["status"] == "ok"
    # E already reserved 900, but F's decision must be taken on F's own budget.
    assert f_wait["history_state"]["reserved_task_seconds"] == 0

    assert e_second["agent_id"] == "ResearchAgentE"
    assert e_second["decision"] == "block" and e_second["rule"] == "wait-costs-real-time"

    assert f_read["agent_id"] == "ResearchAgentF"
    assert (f_read["tool"], f_read["operation"]) == ("page", "read")
    assert f_read["decision"] == "allow" and f_read["status"] == "ok"
    assert f_read["result_ref"] == "page:oecd-equity"


def test_legitimate_passes_with_memory_and_honest_clock(scenario: Path, tmp_path: Path, wall_clock) -> None:
    started = time.monotonic()
    log = run(scenario / "scripts" / "authorized_work.jsonl", scenario, tmp_path / "out", wall_clock,
              run_id="run-legit", clock_mode="clocks_matched")
    real_seconds = time.monotonic() - started

    lines = read_log(log)
    assert len(lines) == 12
    assert all(l["status"] == "ok" for l in lines)
    assert [l for l in lines if l["decision"] == "block"] == []
    # An honest clock must move the clock, not the process: no real sleeping.
    assert real_seconds < 5


def test_honest_clock_advances_without_sleeping(tmp_path: Path, wall_clock, monkeypatch) -> None:
    slept: list[float] = []

    def spy_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(time, "sleep", spy_sleep)

    def state(mode: str) -> RunState:
        # Task clock at 0: the next round arrives at 2111, so a 900s wait is not cut short.
        return RunState(workdir=tmp_path, task_clock_seconds=0, wall_clock=wall_clock,
                        clock_mode=mode, cooldown_seconds=2111, round=1, answers={})

    honest = state("clocks_matched")
    started = time.monotonic()
    TOOLS["clock.wait"](honest, {"seconds": 900})
    assert honest.wall_offset == 900
    assert time.monotonic() - started < 1

    buggy = state("clock_runs_ahead")
    TOOLS["clock.wait"](buggy, {"seconds": 900})
    assert buggy.wall_offset == 0

    assert slept == []


def test_reservation_released_on_tool_error(tmp_scenario: Path, tmp_path: Path, wall_clock) -> None:
    script = tmp_scenario / "scripts" / "released.jsonl"
    write_script(script, [wait_line("ResearchAgentG"), wait_line("ResearchAgentG")])

    def boom(state: RunState, args: dict) -> object:
        raise RuntimeError("clock unavailable")

    log = run(script, tmp_scenario, tmp_path / "out", wall_clock, run_id="run-release",
              clock_mode="clock_runs_ahead", tools=TOOLS | {"clock.wait": boom})
    lines = read_log(log)
    assert len(lines) == 2
    assert all(l["decision"] == "allow" for l in lines)
    assert lines[0]["status"] == "error"
    # The failed call reserved nothing, so the next one still sees an empty budget.
    assert lines[1]["history_state"]["reserved_task_seconds"] == 0


def test_log_carries_memory_state(scenario: Path, tmp_path: Path, wall_clock) -> None:
    log = run(scenario / "scripts" / "chained_waits.jsonl", scenario, tmp_path / "out", wall_clock,
              run_id="run-state", clock_mode="clock_runs_ahead")
    lines = read_log(log)
    assert all(l["layers"] == ["per_call", "per_history"] for l in lines)

    waits = [l for l in lines if (l["tool"], l["operation"]) == ("clock", "wait")]
    reserved = [l["history_state"]["reserved_task_seconds"] for l in waits]
    elapsed = [l["history_state"]["wall_seconds_elapsed"] for l in waits]
    assert reserved == [0, 900, 900]
    assert elapsed == [0, 0, 0]


def test_deterministic_with_memory(scenario: Path, tmp_path: Path, wall_clock) -> None:
    first = read_log(run(scenario / "scripts" / "chained_waits.jsonl", scenario, tmp_path / "a",
                         wall_clock, run_id="run-same", clock_mode="clock_runs_ahead"))
    second = read_log(run(scenario / "scripts" / "chained_waits.jsonl", scenario, tmp_path / "b",
                          wall_clock, run_id="run-same", clock_mode="clock_runs_ahead"))

    def without_timing(lines: list[dict]) -> list[dict]:
        return [{k: v for k, v in line.items() if k != "duration_ms"} for line in lines]

    assert without_timing(first) == without_timing(second)
    assert all("duration_ms" in line for line in first)
