"""Scaffolding: the executor CLI and loud validations the acceptance tests do not touch."""

import json
from pathlib import Path

import pytest

from bouncer import executor, tools
from bouncer.gate import Call, Policy, check_layers, decide, load_policy
from bouncer.tools import TOOLS, RunState

REPO = Path(__file__).resolve().parents[2]
SCENARIO = REPO / "scenario"


def test_cli_runs_script_and_prints_counts(tmp_path: Path, capsys) -> None:
    out = tmp_path / "out"
    executor.main([
        "--script", str(SCENARIO / "scripts" / "unknown_operation.jsonl"),
        "--run-id", "cli", "--output-dir", str(out),
        "--policy", str(SCENARIO / "policy.yaml"), "--scenario", str(SCENARIO), "--cooldown", "10",
    ])
    summary = json.loads(capsys.readouterr().out)
    assert summary == {"run_id": "cli", "calls": 3, "ok": 2, "blocked": 1, "error": 0, "rejected": 0,
                       "log": str(out / "decisions.jsonl")}


def test_policy_validation_is_loud(tmp_path: Path) -> None:
    bad = tmp_path / "policy.yaml"
    bad.write_text("version: '1'\ntask: task.md\ndefault: allow\nallowed: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="default: deny"):
        load_policy(bad)
    bad.write_text("version: '1'\ntask: task.md\ndefault: deny\nallowed:\n  - {id: x, scope: run, tool: a, operation: b, args: {}, source: s, name_source: ours}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="scope"):
        load_policy(bad)
    bad.write_text("version: '1'\ntask: task.md\ndefault: deny\nallowed:\n  - {id: x, scope: call, tool: a, operation: b, args: {n: float}, source: s, name_source: ours}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="types"):
        load_policy(bad)


def test_unknown_layer_and_arg_types() -> None:
    with pytest.raises(ValueError, match="unknown layers"):
        check_layers(("permissions", "telepathy"))
    policy = Policy("1", "task.md", "deny", ({"id": "w", "tool": "clock", "operation": "wait", "args": {"seconds": "int"}, "source": "s"},), ())
    assert decide(Call("clock", "wait", {"seconds": True}), policy).rule == "w:args"
    assert decide(Call("clock", "wait", {"seconds": "9"}), policy).rule == "w:args"
    policy = Policy("1", "task.md", "deny", ({"id": "r", "tool": "page", "operation": "read", "args": {"page": "str"}, "source": "s"},), ())
    assert decide(Call("page", "read", {"page": "   "}), policy).reason == "page must not be empty"


def test_tool_guards(tmp_path: Path, monkeypatch) -> None:
    state = RunState(tmp_path, 0, lambda: 0.0, "harness_bug", 100, 0, {}, [])
    with pytest.raises(ValueError, match="invalid page name"):
        TOOLS["page.read"](state, {"page": "../etc/passwd"})
    with pytest.raises(ValueError, match="no round in progress"):
        TOOLS["answer.submit"](state, {"value": "1"})
    state.clock_mode = "sundial"
    with pytest.raises(ValueError, match="unknown clock mode"):
        TOOLS["clock.wait"](state, {"seconds": 5})

    slept: list[int] = []
    monkeypatch.setattr(tools.time, "sleep", slept.append)
    state.clock_mode = "honest"
    assert TOOLS["clock.wait"](state, {"seconds": 5}) == 5
    assert slept == [5] and state.task_clock_seconds == 5


@pytest.mark.parametrize("name", ["legitimate", "forbidden_edit", "unknown_operation"])
def test_real_scripts_match_their_expectations(name: str, tmp_path: Path) -> None:
    script = SCENARIO / "scripts" / f"{name}.jsonl"
    log = executor.run_script(script, SCENARIO / "policy.yaml", "expect", tmp_path / "out", SCENARIO, wall_clock=lambda: 0.0)
    expected = [json.loads(l)["expect"]["decision"] for l in script.read_text(encoding="utf-8").splitlines() if l]
    assert [json.loads(l)["decision"] for l in log.read_text(encoding="utf-8").splitlines()] == expected


def test_run_guards(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cooldown"):
        executor.run_script(SCENARIO / "scripts" / "legitimate.jsonl", SCENARIO / "policy.yaml", "g", tmp_path, SCENARIO, cooldown_seconds=0)
    with pytest.raises(ValueError, match="scenario"):
        executor.run_script(SCENARIO / "scripts" / "legitimate.jsonl", SCENARIO / "policy.yaml", "g", SCENARIO / "wiki", SCENARIO)


def test_wait_is_cut_at_next_arrival_even_if_unread(tmp_path: Path) -> None:
    state = RunState(tmp_path, 0, lambda: 0.0, "harness_bug", 100, 0, {}, [])
    assert TOOLS["clock.wait"](state, {"seconds": 5000}) == 100
    assert state.task_clock_seconds == 100


def test_tool_error_has_no_host_path(tmp_path: Path) -> None:
    scene = tmp_path / "scene"
    (scene / "wiki").mkdir(parents=True)
    (scene / "questions.jsonl").write_text("", encoding="utf-8")
    script = scene / "s.jsonl"
    script.write_text(json.dumps({"agent": "A", "call": {"tool": "page", "operation": "read", "args": {"page": "nope"}}}) + "\n", encoding="utf-8")
    log = executor.run_script(script, SCENARIO / "policy.yaml", "err", tmp_path / "out", scene)
    [record] = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    assert record["status"] == "error" and str(tmp_path) not in record["error"] and "<workdir>" in record["error"]


def test_result_ref_falls_back_to_value(tmp_path: Path) -> None:
    state = RunState(tmp_path, 0, lambda: 0.0, "harness_bug", 100, 1, {}, [])
    assert executor.result_ref("answer.submit", {"value": "1"}, state, "answer:round=1") == "answer:round=1"


def test_result_ref_marks_no_new_round(tmp_path: Path) -> None:
    state = RunState(tmp_path, 0, lambda: 0.0, "harness_bug", 100, 1, {}, [])
    assert executor.result_ref("round.question", {}, state, tools.NO_NEW_ROUND) == "round:none"


def test_workdir_with_foreign_files_is_not_deleted(tmp_path: Path) -> None:
    out = tmp_path / "out"
    notes = out / "workdir" / "my-notes.md"
    notes.parent.mkdir(parents=True)
    notes.write_text("mine", encoding="utf-8")
    with pytest.raises(ValueError, match="foreign"):
        executor.run_script(SCENARIO / "scripts" / "legitimate.jsonl", SCENARIO / "policy.yaml", "w", out, SCENARIO)
    assert notes.read_text(encoding="utf-8") == "mine"
    # A workdir left by a previous run is replaced.
    notes.unlink()
    executor.run_script(SCENARIO / "scripts" / "legitimate.jsonl", SCENARIO / "policy.yaml", "w", out, SCENARIO)
    executor.run_script(SCENARIO / "scripts" / "legitimate.jsonl", SCENARIO / "policy.yaml", "w", out, SCENARIO)


def test_malformed_script_line_is_rejected_and_run_continues(tmp_path: Path) -> None:
    script = tmp_path / "s.jsonl"
    script.write_text("\n".join([
        json.dumps({"agent": "A", "call": {"tool": "round", "operation": "question", "args": {}}}),
        json.dumps({"agent": "A", "nope": 1}),
        json.dumps({"agent": "A", "call": {"tool": "page", "operation": "read", "args": "hello"}}),
        json.dumps({"agent": "A", "call": {"tool": "page", "operation": "read", "args": {"page": "saginaw-county"}}}),
    ]) + "\n", encoding="utf-8")
    log = executor.run_script(script, SCENARIO / "policy.yaml", "bad", tmp_path / "out", SCENARIO)
    records = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    assert [r["status"] for r in records] == ["ok", "rejected", "rejected", "ok"]
    assert all(r["decision"] is None and "malformed" in r["reason"] for r in records[1:3])


def test_log_records_run_parameters(tmp_path: Path) -> None:
    log = executor.run_script(SCENARIO / "scripts" / "unknown_operation.jsonl", SCENARIO / "policy.yaml", "p",
                              tmp_path / "out", SCENARIO, clock_mode="harness_bug", cooldown_seconds=10)
    for record in (json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()):
        assert (record["clock_mode"], record["cooldown_seconds"]) == ("harness_bug", 10)
