"""Acceptance: the replay of the historical corpus and the demo results table."""
import ast
import inspect
import json
from pathlib import Path

import pytest

import bouncer.replay
from bouncer.demo import demo
from bouncer.replay import replay


LOG_KEYS = {
    "run_id",
    "rev_id",
    "source_ref",
    "agent_id",
    "page_key",
    "tool",
    "operation",
    "decision",
    "rule",
    "reason",
    "policy_version",
    "layers",
}

PER_CALL = ("per_call",)
PER_CALL_HISTORY = ("per_call", "per_history")

# A string that exists only inside a fixture body. It must never reach the log.
SENTINEL = "ZZ-SENTINEL-BODY-MUST-NOT-BE-LOGGED-ZZ"


def make_event(index: int, body: str = "External links: some prose.",
               request_action: str | None = "form_edit") -> dict:
    """Build one corpus row with the same shape as data/prepared/wiki/events.jsonl."""
    return {
        "rev_id": f"dse~FixturePage{index}@1",
        "source_ref": f"revisions.jsonl.gz:{6000 + index}",
        "agent_id": f"FixtureAgent{index % 3}",
        "time": "2026-05-24T06:02:19Z",
        "time_grade": "reqlog",
        "uncertainty_seconds": 1,
        "page_key": f"dse~FixturePage{index}",
        "seq": 1,
        "body": body,
        "request_action": request_action,
        "operation": "wiki.edit",
        "provenance": {"agent_id": "label", "operation": "adapted",
                       "request_action": "observed"},
    }


def write_events(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def fixture_corpus(tmp_path: Path, count: int = 3) -> tuple[Path, list[dict]]:
    """A small corpus including an empty body, a null request_action and the sentinel."""
    rows = [make_event(index) for index in range(count)]
    rows[0] = make_event(0, body="")
    rows[1] = make_event(1, request_action=None)
    rows[-1] = make_event(count - 1, body=f"Body carrying {SENTINEL} inside it.")
    return write_events(tmp_path / "events.jsonl", rows), rows


def read_log(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_summary(output_dir: Path) -> dict:
    return json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))


def table_rows(markdown: str) -> list[str]:
    return [line for line in markdown.splitlines() if line.strip().startswith("|")]


def walk_dicts(node: object) -> list[dict]:
    """Every dict reachable inside a nested JSON-shaped structure, including the root."""
    found: list[dict] = []
    if isinstance(node, dict):
        found.append(node)
        for value in node.values():
            found.extend(walk_dicts(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(walk_dicts(value))
    return found


def imported_names(source: str) -> list[str]:
    """Every module name a module actually imports, absolute and relative.

    Prose that merely mentions a module is not an import and does not appear here.
    """
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            # `from . import tools` carries the name in node.names, not in node.module.
            if node.module:
                names.append(node.module)
            names.extend(f"{node.module}.{alias.name}" if node.module else alias.name
                         for alias in node.names)
    return names


def test_replay_logs_every_event(tmp_path: Path, scenario: Path) -> None:
    """One log line per input event, same order, exactly the twelve documented keys."""
    events, rows = fixture_corpus(tmp_path, count=4)
    output_dir = tmp_path / "run"

    log_path = replay(events=events, policy=scenario / "policy.yaml", run_id="fixture-run",
                      output_dir=output_dir, layers=PER_CALL)

    assert log_path == output_dir / "events.jsonl"
    log = read_log(log_path)
    assert len(log) == len(rows)
    assert [line["rev_id"] for line in log] == [row["rev_id"] for row in rows]
    for line, row in zip(log, rows):
        assert set(line) == LOG_KEYS
        assert line["run_id"] == "fixture-run"
        assert line["source_ref"] == row["source_ref"]
        assert line["agent_id"] == row["agent_id"]
        assert line["page_key"] == row["page_key"]
        # "wiki.edit" is split into tool and operation.
        assert line["tool"] == "wiki"
        assert line["operation"] == "edit"
        assert line["layers"] == ["per_call"]


def test_replay_blocks_every_edit(tmp_path: Path, scenario: Path) -> None:
    """Every historical edit is blocked by default-deny, and the summary shows the denominator."""
    events, rows = fixture_corpus(tmp_path, count=5)
    output_dir = tmp_path / "run"

    log_path = replay(events=events, policy=scenario / "policy.yaml", run_id="blocks",
                      output_dir=output_dir, layers=PER_CALL)

    log = read_log(log_path)
    assert [line["decision"] for line in log] == ["block"] * len(rows)
    assert [line["rule"] for line in log] == ["default-deny"] * len(rows)

    summary = read_summary(output_dir)
    assert summary["events"] == len(rows)
    assert summary["decisions"]["block"] == len(rows)
    assert summary["rules"]["default-deny"] == len(rows)
    assert summary["decisions"].get("allow", 0) == 0


def test_memory_changes_nothing_on_the_corpus(tmp_path: Path, scenario: Path) -> None:
    """The history layer alters no decision on the corpus; only the declared layers differ."""
    events, rows = fixture_corpus(tmp_path, count=4)
    policy = scenario / "policy.yaml"
    permissions_dir = tmp_path / "per_call"
    memory_dir = tmp_path / "per_history"

    permissions_log = read_log(replay(events=events, policy=policy, run_id="perm",
                                      output_dir=permissions_dir, layers=PER_CALL))
    memory_log = read_log(replay(events=events, policy=policy, run_id="mem",
                                 output_dir=memory_dir, layers=PER_CALL_HISTORY))

    def triples(log: list[dict]) -> list[tuple[str, str, str]]:
        return [(line["rev_id"], line["decision"], line["rule"]) for line in log]

    assert triples(permissions_log) == triples(memory_log)
    assert len(memory_log) == len(rows)

    # The layers field must record what was actually run, so it differs between the runs.
    assert all(line["layers"] == ["per_call"] for line in permissions_log)
    assert all(line["layers"] == ["per_call", "per_history"] for line in memory_log)

    assert read_summary(memory_dir)["history_governed_events"] == 0


def test_summary_declares_non_evaluable_rule(tmp_path: Path, scenario: Path) -> None:
    """The history run declares wait-costs-real-time as non-evaluable and names the blocked state update."""
    events, _rows = fixture_corpus(tmp_path, count=3)
    policy = scenario / "policy.yaml"
    permissions_dir = tmp_path / "per_call"
    memory_dir = tmp_path / "per_history"

    replay(events=events, policy=policy, run_id="perm", output_dir=permissions_dir,
           layers=PER_CALL)
    replay(events=events, policy=policy, run_id="mem", output_dir=memory_dir,
           layers=PER_CALL_HISTORY)

    memory_summary = read_summary(memory_dir)
    declared = {entry["rule"]: entry["reason"] for entry in memory_summary["non_evaluable_rules"]}
    assert "wait-costs-real-time" in declared
    assert isinstance(declared["wait-costs-real-time"], str)
    assert declared["wait-costs-real-time"].strip() != ""
    assert isinstance(memory_summary["blocked_state_update"], str)
    assert memory_summary["blocked_state_update"].strip() != ""

    # The per_call-only run must not claim the history rule was evaluated.
    permissions_summary = read_summary(permissions_dir)
    assert permissions_summary["layers"] == ["per_call"]
    assert "wait-costs-real-time" not in permissions_summary["rules"]
    assert permissions_summary["history_governed_events"] == 0


def test_replay_is_deterministic(tmp_path: Path, scenario: Path) -> None:
    """The same corpus and layers produce byte-identical logs in two output directories."""
    events, _rows = fixture_corpus(tmp_path, count=5)
    policy = scenario / "policy.yaml"

    first = replay(events=events, policy=policy, run_id="same-run",
                   output_dir=tmp_path / "first", layers=PER_CALL)
    second = replay(events=events, policy=policy, run_id="same-run",
                    output_dir=tmp_path / "second", layers=PER_CALL)

    assert first != second
    assert first.read_bytes() == second.read_bytes()


def test_replay_never_executes(tmp_path: Path, scenario: Path) -> None:
    """No corpus body reaches the log, and the replay module imports no tool."""
    events, _rows = fixture_corpus(tmp_path, count=3)

    log_path = replay(events=events, policy=scenario / "policy.yaml", run_id="no-exec",
                      output_dir=tmp_path / "run", layers=PER_CALL)

    # (a) the body never leaves the corpus.
    raw = log_path.read_text(encoding="utf-8")
    assert SENTINEL not in raw
    assert all("body" not in line for line in read_log(log_path))

    # (b) the module has no access to the tools at all. Mentioning them in prose is fine;
    # importing them, under any alias or relative form, is not.
    assert "tools" not in bouncer.replay.__dict__
    for name in imported_names(inspect.getsource(bouncer.replay)):
        assert name != "tools"
        assert not name.endswith(".tools")


def test_demo_shows_effect_and_absence_of_effect(
    tmp_path: Path, scenario: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The demo reports agent, call, decision and rule; the blocked edit leaves the wiki untouched."""
    events, _rows = fixture_corpus(tmp_path, count=3)
    output_dir = tmp_path / "runs"
    docs_dir = tmp_path / "docs"

    summary = demo(output_dir=output_dir, scenario_dir=scenario, events=events, docs_dir=docs_dir)

    reported = capsys.readouterr().out + json.dumps(summary)
    for token in ("ResearchAgentB", "wiki.edit", "block", "default-deny"):
        assert token in reported

    # The blocked edit never reached the page: the working copy still matches the original.
    original = (scenario / "wiki" / "saginaw-county.md").read_bytes()
    working_copies = list(output_dir.rglob("saginaw-county.md"))
    assert working_copies
    for copy in working_copies:
        assert copy.read_bytes() == original


def test_results_table_has_both_blocks(tmp_path: Path, scenario: Path) -> None:
    """results.md separates the historical record from our own scripts and shows the four rows."""
    events, rows = fixture_corpus(tmp_path, count=13)
    docs_dir = tmp_path / "docs"

    demo(output_dir=tmp_path / "runs", scenario_dir=scenario, events=events, docs_dir=docs_dir)

    markdown = (docs_dir / "results.md").read_text(encoding="utf-8")
    headings = [line for line in markdown.splitlines() if line.startswith("#")]
    historical = [head for head in headings if "historical" in head.lower()]
    ours = [head for head in headings
            if "script" in head.lower() or "scenario" in head.lower()]
    assert historical
    assert ours
    assert set(historical).isdisjoint(ours)

    # The historical denominator is stated, not just the blocked count.
    assert str(len(rows)) in markdown

    # Each authorized_work row names the script, the clock mode and the layers.
    authorized = [row for row in table_rows(markdown) if "authorized_work" in row]
    assert len(authorized) == 4

    def pick(clock: str, with_memory: bool) -> str:
        matches = [row for row in authorized
                   if clock in row and ("per_history" in row) == with_memory]
        assert len(matches) == 1
        return matches[0]

    for clock, with_memory in (("clocks_matched", False), ("clocks_matched", True), ("clock_runs_ahead", False)):
        row = pick(clock, with_memory)
        assert "12" in row
        assert "limit" not in row.lower()

    blocked_row = pick("clock_runs_ahead", True)
    assert "11" in blocked_row
    assert "1" in blocked_row
    # The single block is labelled a limit of the rule, not a false-positive rate.
    assert "limit" in blocked_row.lower()
    assert "false positive" not in blocked_row.lower()
    assert "false-positive" not in blocked_row.lower()


def test_table_counts_rounds_not_only_calls(tmp_path: Path, scenario: Path) -> None:
    """Both outputs report rounds answered out of rounds available, 2 of 3 for clock_runs_ahead+history."""
    events, _rows = fixture_corpus(tmp_path, count=13)
    docs_dir = tmp_path / "docs"

    summary = demo(output_dir=tmp_path / "runs", scenario_dir=scenario, events=events,
                   docs_dir=docs_dir)

    markdown = (docs_dir / "results.md").read_text(encoding="utf-8")
    assert "3 of 3" in markdown
    assert "2 of 3" in markdown
    blocked_row = [row for row in table_rows(markdown)
                   if "authorized_work" in row and "clock_runs_ahead" in row and "per_history" in row]
    assert len(blocked_row) == 1
    assert "2 of 3" in blocked_row[0]

    written = json.loads((docs_dir / "results-summary.json").read_text(encoding="utf-8"))
    assert written == summary

    entries = [node for node in walk_dicts(written)
               if "rounds_answered" in node and "rounds_available" in node]
    assert len(entries) >= 4

    # authorized_work identifies its entries with a "script" key.
    authorized = [entry for entry in entries if entry.get("script") == "authorized_work"]
    assert len(authorized) == 4
    assert all(entry["rounds_available"] == 3 for entry in authorized)

    blocked = [entry for entry in authorized
               if entry.get("clock") == "clock_runs_ahead" and "per_history" in str(entry.get("layers"))]
    assert len(blocked) == 1
    assert blocked[0]["rounds_answered"] == 2
