"""Executor acceptance: real and temporary scripts, logging from trusted code."""

import json
from pathlib import Path

import yaml

from bouncer.executor import run_script
from bouncer.tools import TOOLS

REQUIRED_LOG_FIELDS = {
    "run_id", "agent_id", "call_id", "tool", "operation", "decision",
    "rule", "reason", "policy_version", "status", "duration_ms",
}


def run(script: Path, scenario_dir: Path, output_dir: Path, wall_clock, run_id: str = "run-1", **kwargs) -> Path:
    return run_script(
        script=script,
        policy=scenario_dir / "policy.yaml",
        run_id=run_id,
        output_dir=output_dir,
        scenario_dir=scenario_dir,
        wall_clock=wall_clock,
        clock_mode="harness_bug",
        **kwargs,
    )


def read_log(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def dir_bytes(root: Path) -> dict[str, bytes]:
    """Relative path -> bytes of each file; equality = same files, same bytes."""
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def is_edit(line: dict) -> bool:
    return (line["tool"], line["operation"]) == ("wiki", "edit")


def test_legitimate_script_completes(scenario: Path, tmp_path: Path, wall_clock) -> None:
    script = scenario / "scripts" / "legitimate.jsonl"
    returned: list[tuple[str, str]] = []

    def spy_read(state, args: dict) -> str:
        value = TOOLS["page.read"](state, args)
        returned.append((args["page"], value))
        return value

    output_dir = tmp_path / "out"
    log = run(script, scenario, output_dir, wall_clock, run_id="run-legit", tools=TOOLS | {"page.read": spy_read})
    lines = read_log(log)

    assert lines
    assert all(line["decision"] == "allow" and line["status"] == "ok" for line in lines)

    # Each read in the script leaves its page in the log and returns the real content of the local wiki.
    calls = [json.loads(l)["call"] for l in script.read_text(encoding="utf-8").splitlines() if l]
    expected_pages = [c["args"]["page"] for c in calls if (c["tool"], c["operation"]) == ("page", "read")]
    reads = [l for l in lines if (l["tool"], l["operation"]) == ("page", "read")]
    assert expected_pages
    assert [l.get("result_ref") for l in reads] == [f"page:{p}" for p in expected_pages]
    assert returned == [(p, (scenario / "wiki" / f"{p}.md").read_text(encoding="utf-8")) for p in expected_pages]

    submits = [l for l in lines if (l["tool"], l["operation"]) == ("answer", "submit")]
    assert submits
    assert all("round=" in l.get("result_ref", "") for l in submits)

    assert dir_bytes(output_dir / "workdir") == dir_bytes(scenario / "wiki")


def test_blocked_edit_has_no_effect(scenario: Path, tmp_path: Path, wall_clock) -> None:
    calls: list[dict] = []

    def spy_edit(state, args: dict) -> None:
        calls.append(args)
        (state.workdir / f"{args['page']}.md").write_text(args["body"], encoding="utf-8")

    output_dir = tmp_path / "out"
    log = run(
        scenario / "scripts" / "forbidden_edit.jsonl", scenario, output_dir, wall_clock,
        run_id="run-forbidden", tools=TOOLS | {"wiki.edit": spy_edit},
    )
    lines = read_log(log)

    edits = [l for l in lines if is_edit(l)]
    assert edits
    assert all(l["decision"] == "block" and l["status"] == "blocked" for l in edits)
    assert calls == []
    assert all(l["status"] == "ok" for l in lines if not is_edit(l))
    assert dir_bytes(output_dir / "workdir") == dir_bytes(scenario / "wiki")


def test_agent_cannot_override_identity(tmp_scenario: Path, tmp_path: Path, wall_clock) -> None:
    script = tmp_scenario / "scripts" / "identity.jsonl"
    expected_agent = json.loads(script.read_text(encoding="utf-8").splitlines()[0])["agent"]
    expected_version = yaml.safe_load((tmp_scenario / "policy.yaml").read_text(encoding="utf-8"))["version"]

    log = run(script, tmp_scenario, tmp_path / "out", wall_clock, run_id="run-identity")
    [line] = read_log(log)

    # Allowed or blocked, it does not matter: identity comes from the script, never from the args.
    assert line["agent_id"] == expected_agent
    assert line["run_id"] == "run-identity"
    assert line["policy_version"] == expected_version


def test_missing_identity_is_not_permission(tmp_scenario: Path, tmp_path: Path, wall_clock) -> None:
    calls: list[dict] = []

    def spy_read(state, args: dict) -> str:
        calls.append(args)
        return "should not be read"

    log = run(
        tmp_scenario / "scripts" / "no_agent.jsonl", tmp_scenario, tmp_path / "out", wall_clock,
        run_id="run-no-agent", tools=TOOLS | {"page.read": spy_read},
    )
    [line] = read_log(log)

    assert line["status"] == "rejected"
    assert line["decision"] != "allow"
    assert calls == []


def test_tool_error_is_not_success(tmp_scenario: Path, tmp_path: Path, wall_clock) -> None:
    log = run(tmp_scenario / "scripts" / "missing_page.jsonl", tmp_scenario, tmp_path / "out", wall_clock, run_id="run-missing")
    [line] = read_log(log)

    assert line["decision"] == "allow"
    assert line["status"] == "error"
    assert line["status"] != "ok"
    assert line.get("error")


def test_log_record_shape(scenario: Path, tmp_path: Path, wall_clock) -> None:
    # forbidden_edit mixes allowed and blocked lines: all of them carry the same fields.
    log = run(scenario / "scripts" / "forbidden_edit.jsonl", scenario, tmp_path / "out", wall_clock, run_id="run-shape")
    lines = read_log(log)

    assert lines
    for line in lines:
        assert REQUIRED_LOG_FIELDS <= set(line), line


def test_log_outside_workdir(tmp_scenario: Path, tmp_path: Path, wall_clock) -> None:
    output_dir = tmp_path / "out"
    log = run(tmp_scenario / "scripts" / "legitimate.jsonl", tmp_scenario, output_dir, wall_clock, run_id="run-log")

    assert log.exists()
    assert not log.resolve().is_relative_to((output_dir / "workdir").resolve())


def test_deterministic_run(tmp_scenario: Path, tmp_path: Path, wall_clock) -> None:
    script = tmp_scenario / "scripts" / "legitimate.jsonl"
    log_a = run(script, tmp_scenario, tmp_path / "out-a", wall_clock, run_id="run-det")
    log_b = run(script, tmp_scenario, tmp_path / "out-b", wall_clock, run_id="run-det")

    def without_duration(lines: list[dict]) -> list[dict]:
        return [{k: v for k, v in line.items() if k != "duration_ms"} for line in lines]

    assert without_duration(read_log(log_a)) == without_duration(read_log(log_b))
