"""Phase 5: the historical corpus through the gatekeeper, decided but never executed.

Reads the prepared events one line at a time, asks what would have been decided about
each one, and writes a log line per event plus a summary with its denominators.

Nothing here can act. This module has no access to the local tools of the scenario: it
reaches the gatekeeper and stops there. The corpus is read as data — its bodies are not
logged, its instructions are not followed and its links are not visited.
"""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from bouncer.gate import (Call, HistoryView, Policy, check_layers, decide, load_policy,
                          history_rules_for)

EVENTS_FILE = Path("data/prepared/wiki/events.jsonl")
POLICY_FILE = Path("scenario/policy.yaml")
LOG_NAME = "events.jsonl"
SUMMARY_NAME = "summary.json"

# Fields the log needs from an event. A row missing one of them is a broken corpus, not a
# call to judge: we produced the file, so we fail loudly instead of logging a wrong line.
REQUIRED = ("rev_id", "source_ref", "agent_id", "page_key", "operation")

# Why a declared rule cannot be evaluated against this record. P0-03 asks for it in writing.
NON_EVALUABLE = {
    "wait-costs-real-time": (
        "the corpus preserves only the edits that reached the wiki: it contains no "
        "clock.wait call and no response times, so the task seconds this rule compares "
        "against elapsed time cannot be read from it"
    ),
}

# How history state moves on a hypothetical block, which PRD.md:231 requires declaring.
# It says what this walk does, not what the executor does: claiming an update-after-allow
# the walk does not perform would describe code that is not here.
BLOCKED_STATE_UPDATE = (
    "the walk updates no history state, on a block or on an allow. These events already "
    "happened, so there is no authorization to reserve against: each one is decided "
    "against an empty history for its own agent. The policy counts authorizations, so a "
    "block would reserve nothing in any case, and every event of this record is blocked"
)


def event_call(row: dict) -> Call:
    """The adapted call an observed revision stands for.

    The body travels as the argument it was, and no rule reads it: `wiki.edit` is absent
    from the policy, so default deny answers before arguments are looked at.
    """
    tool, _, operation = row["operation"].partition(".")
    return Call(tool, operation, {"page": row["page_key"], "body": row.get("body")})


def event_record(row: dict, run_id: str, policy: Policy, layers: tuple[str, ...],
                 call: Call, decision) -> dict:
    return {
        "run_id": run_id,
        "rev_id": row["rev_id"],
        "source_ref": row["source_ref"],
        "agent_id": row["agent_id"],
        "page_key": row["page_key"],
        "tool": call.tool,
        "operation": call.operation,
        "decision": decision.outcome,
        "rule": decision.rule,
        "reason": decision.reason,
        "policy_version": policy.version,
        "layers": list(layers),
    }


def read_events(path: Path):
    """Rows in file order, already chronological. Yields (line number, row)."""
    with path.open(encoding="utf-8") as source:
        for number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{number}: line is not JSON: {error}") from error
            missing = [field for field in REQUIRED if not isinstance(row.get(field), str)]
            if missing:
                raise ValueError(f"{path}:{number}: event without {missing}")
            if "." not in row["operation"]:
                # Blocking it anyway would be the safe direction, but it would log a call
                # with an empty operation as if that were what the agent did.
                raise ValueError(f"{path}:{number}: operation {row['operation']!r} is not tool.operation")
            yield number, row


def replay(events: Path, policy: Path, run_id: str, output_dir: Path,
           layers: tuple[str, ...] = ("per_call",)) -> Path:
    check_layers(layers)
    policy_obj = load_policy(policy)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / LOG_NAME
    # The log shares its name with the corpus, so writing it into the corpus directory
    # would truncate the input before a single row had been read — and report a clean walk
    # of an empty file. The executor refuses the same shape of mistake.
    if log_path.resolve() == events.resolve():
        raise ValueError(f"the log would overwrite the events file: {events}")

    decisions: Counter = Counter()
    rules: Counter = Counter()
    governed_by_rule: Counter = Counter()
    agents: set[str] = set()
    total = 0
    check_seconds = 0.0

    # newline="\n" so two walks are byte-identical on any machine, not only on this one.
    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        for _number, row in read_events(events):
            call = event_call(row)
            agents.add(row["agent_id"])
            # Nothing is ever authorized on this record, so nothing is ever reserved and
            # no wall time is consumed. Reading a real clock here would make the same
            # corpus decide differently on a slower machine, which P0-07 forbids.
            history = HistoryView(row["agent_id"], 0, 0) if "per_history" in layers else None
            matched = history_rules_for(policy_obj, call)

            started = time.perf_counter()
            decision = decide(call, policy_obj, layers, history)
            check_seconds += time.perf_counter() - started

            # A rule governs an event only if the check actually got as far as asking it.
            # The per_call layer runs first, so a call blocked by default deny or by its arguments
            # never reaches the history layer, however well its name matches a rule.
            if history is not None and (decision.outcome == "allow"
                                       or decision.rule in {rule["id"] for rule in matched}):
                governed_by_rule.update(rule["id"] for rule in matched)

            total += 1
            decisions[decision.outcome] += 1
            rules[decision.rule] += 1
            record = event_record(row, run_id, policy_obj, layers, call, decision)
            log.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Per rule, not per run: one rule that did get evaluated must not silence the
    # declaration for another that did not. A layer nobody asked for was not evaluated,
    # which is a different statement, so only requested layers are declared at all.
    declared = [{"rule": rule["id"], "reason": NON_EVALUABLE[rule["id"]]}
                for rule in policy_obj.history_rules
                if "per_history" in layers and rule["id"] in NON_EVALUABLE
                and not governed_by_rule[rule["id"]]]
    summary = {
        "run_id": run_id,
        "layers": list(layers),
        "policy_version": policy_obj.version,
        "events": total,
        "decisions": dict(decisions),
        "rules": dict(rules),
        "agent_ids": len(agents),
        "history_governed_events": sum(governed_by_rule.values()),
        "history_governed_by_rule": dict(governed_by_rule),
        "non_evaluable_rules": declared,
        "blocked_state_update": BLOCKED_STATE_UPDATE,
        "check_seconds_total": round(check_seconds, 6),
        "check_us_per_call": round(check_seconds / total * 1e6, 3) if total else 0.0,
    }
    (output_dir / SUMMARY_NAME).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return log_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--events", type=Path, default=EVENTS_FILE)
    parser.add_argument("--policy", type=Path, default=POLICY_FILE)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--layers", default="per_call", help="comma-separated: per_call[,per_history]")
    args = parser.parse_args(argv)
    log_path = replay(args.events, args.policy, args.run_id, args.output_dir,
                      tuple(args.layers.split(",")))
    summary = json.loads((args.output_dir / SUMMARY_NAME).read_text(encoding="utf-8"))
    print(json.dumps({k: summary[k] for k in
                      ("run_id", "layers", "events", "decisions", "rules", "agent_ids",
                       "history_governed_events", "check_us_per_call")} | {"log": str(log_path)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
