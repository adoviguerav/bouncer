"""Gatekeeper acceptance: loading the real policy and deciding per call."""

from pathlib import Path

import pytest

from bouncer.gate import Call, decide, load_policy

EXPECTED_ALLOWED = {("web", "search"), ("page", "read"), ("round", "question"), ("answer", "submit"), ("clock", "wait")}


def heading_slugs(task_md: Path) -> set[str]:
    """Slug = heading in lowercase with spaces replaced by hyphens, accents kept."""
    lines = task_md.read_text(encoding="utf-8").splitlines()
    return {line.lstrip("#").strip().lower().replace(" ", "-") for line in lines if line.startswith("#")}


def source_slug(source: str) -> str:
    file, slug = source.split("#", 1)
    assert file == "task.md", source
    return slug


@pytest.fixture
def policy(scenario: Path):
    return load_policy(scenario / "policy.yaml")


def test_policy_loads_and_cites_task(scenario: Path, policy) -> None:
    slugs = heading_slugs(scenario / "task.md")

    assert policy.default == "deny"
    assert len(policy.allowed) == 5
    assert {(a["tool"], a["operation"]) for a in policy.allowed} == EXPECTED_ALLOWED
    for entry in policy.allowed:
        assert entry["scope"] == "call", entry
        assert source_slug(entry["source"]) in slugs, entry

    clock_rules = [r for r in policy.memory_rules if (r["tool"], r["operation"]) == ("clock", "wait")]
    assert len(clock_rules) == 1
    rule = clock_rules[0]
    assert rule["scope"] == "agent_history"
    assert rule["budget"] == "task_seconds"
    assert rule["against"] == "wall_seconds_elapsed"
    assert rule["ratio"] == 1
    assert rule["counts"] == "authorizations"
    assert source_slug(rule["source"]) in slugs


def test_decide_allow(policy) -> None:
    entry = next(a for a in policy.allowed if (a["tool"], a["operation"]) == ("page", "read"))
    decision = decide(Call("page", "read", {"page": "saginaw-county"}), policy)
    assert decision.outcome == "allow"
    assert decision.rule == entry["id"]


def test_decide_default_deny(policy) -> None:
    calls = (
        Call("wiki", "edit", {"page": "saginaw-county", "body": "vandalism"}),
        Call("shell", "run", {"cmd": "ls"}),
    )
    for call in calls:
        decision = decide(call, policy)
        assert (decision.outcome, decision.rule) == ("block", "default-deny"), call


def test_decide_invalid_args(policy) -> None:
    calls = (
        Call("clock", "wait", {"seconds": -1}),
        Call("page", "read", {}),
    )
    for call in calls:
        decision = decide(call, policy)
        assert decision.outcome == "block", call
        # It is in the list: the block is signed by the argument rule, not by default-deny.
        assert decision.rule != "default-deny", call
