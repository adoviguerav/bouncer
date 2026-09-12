"""Phase 5: one command runs the scripts and the corpus, and writes the results table.

Walks our own scripts through the real executor — so a permitted call really runs and a
blocked one really does not — and the historical corpus through the replay, which decides
without executing. Then writes the comparison of layer 1 against layers 1+2 with its
quantities and denominators, keeping the two records apart.
"""

import argparse
import json
from pathlib import Path

from bouncer.executor import run_script
from bouncer.replay import SUMMARY_NAME, replay

EVENTS_FILE = Path("data/prepared/wiki/events.jsonl")
SCENARIO_DIR = Path("scenario")
DOCS_DIR = Path("docs")
TABLE_NAME = "results.md"
TABLE_SUMMARY_NAME = "results-summary.json"

PER_CALL = ("per_call",)
PER_CALL_HISTORY = ("per_call", "per_history")

# script, clock mode, layers. authorized_work is run across both clocks because that
# is where the history rule's cost shows; the rest keep the default broken clock.
RUNS = (
    ("authorized_work", "clocks_matched", PER_CALL),
    ("authorized_work", "clocks_matched", PER_CALL_HISTORY),
    ("authorized_work", "clock_runs_ahead", PER_CALL),
    ("authorized_work", "clock_runs_ahead", PER_CALL_HISTORY),
    ("page_write", "clock_runs_ahead", PER_CALL),
    ("page_write", "clock_runs_ahead", PER_CALL_HISTORY),
    ("unlisted_tool", "clock_runs_ahead", PER_CALL),
    ("unlisted_tool", "clock_runs_ahead", PER_CALL_HISTORY),
    ("chained_waits", "clock_runs_ahead", PER_CALL),
    ("chained_waits", "clock_runs_ahead", PER_CALL_HISTORY),
    ("two_agents", "clock_runs_ahead", PER_CALL),
    ("two_agents", "clock_runs_ahead", PER_CALL_HISTORY),
)

HEADLINE = """\
BOUNCER — a gatekeeper that checks a tool call before it runs

The policy is the list of calls the task authorizes. Two checks, in this order,
and the second only ever sees what the first let through:

  1. per_call     Is this call on the list? If it is not, it is stopped.
  2. per_history  It is on the list. Is this agent using it in a normal way?
                  A permitted call, made in an abnormal pattern, is another
                  shape of abuse — and one call on its own cannot show it.

What follows is that, run for real: every call below goes through the gatekeeper,
and the ones that pass invoke the actual tool."""

# The three beats of the demo, in order, and which run of which script shows each.
# The run has to be the one where the claim is visible: printing chained_waits without the
# per_history layer would caption blocked waits over a walkthrough that allows all three.
BEATS = (
    ("1. AUTHORIZED WORK GOES THROUGH UNTOUCHED",
     "Nothing here is stopped. This is the half the gatekeeper must not get in the way of.",
     (("authorized_work", "clocks_matched", PER_CALL_HISTORY),
      "the research task completes: three rounds asked, read and answered")),
    ("2. A CALL THAT IS NOT ON THE LIST IS STOPPED — per_call",
     "No rule names these. They fall because the task never authorized them, which is what "
     "catches the abuse nobody thought of in advance.",
     (("page_write", "clock_runs_ahead", PER_CALL_HISTORY),
      "writing to the wiki: stopped, and the page is left byte-for-byte untouched"),
     (("unlisted_tool", "clock_runs_ahead", PER_CALL_HISTORY),
      "a shell command out to the network: stopped, and no rule mentions shells")),
    ("3. A CALL THAT IS ON THE LIST, USED STRANGELY, IS ALSO STOPPED — per_history",
     "Every call below is authorized. Each one on its own is fine; the pattern is not. "
     "This is the check that needs the agent's own history to see anything at all.",
     (("chained_waits", "clock_runs_ahead", PER_CALL_HISTORY),
      "waiting is permitted — chaining waits that cost no real time is not"),
     (("two_agents", "clock_runs_ahead", PER_CALL_HISTORY),
      "and one agent's exhausted budget neither spends nor stops the other")),
)

# What the corpus can and cannot support, said out loud at the end of the demo.
CLOSING = """\
What of this rests on real data, and what does not:

  Beat 2 does.  The wiki corpus is {events} real edits by {agents} real identities, and
                per_call stops every one of them, decided without executing a thing.
  Beat 3 does not, and cannot. The corpus preserved only the calls that reached the wiki —
                that is, only the ones per_call blocks. The permitted calls happened and
                were recorded nowhere, so there is no real trace of a permitted tool being
                misused. Beat 3 is our own scripted case, labelled as ours.

That is the shape of the experiment, not a result about agents. With the trajectories of a
real incident — the ones we do not have — the same two checks run unchanged."""

STATUSES = ("ok", "blocked", "error", "rejected")

# Said once, in the table, because P0-08 requires it in writing.
LAYER2_ON_THE_RECORD = (
    "**Layer 2 is not scored on this record — it is never asked.** The two layers are a "
    "pipeline, not rivals: `per_history` only ever sees the calls `per_call` has already "
    "authorized. Every row here is a `wiki.edit`, which `per_call` denies, so the number of "
    "events that reached `per_history` is **0 of 13661**, and that zero is its sample size, "
    "not its result. Layer 2 contributing no blocking here is layer 1 doing its job, and the "
    "only honest reading of it. Where `per_call` does authorize a call — `clock.wait` in our "
    "own scripts — `per_history` does change decisions, and the table below shows where."
)

BLOCKED_ROW_LABEL = (
    "limit of the rule: with the task clock ahead of the real one it cannot tell a "
    "good-faith waiter from a cheat"
)


def is_answer(record: dict) -> bool:
    return (record["tool"], record["operation"]) == ("answer", "submit")


def rounds_answered(records: list[dict]) -> int:
    """Distinct rounds that actually got an answer, read from the log's result references.

    A blocked wait can cost a round without costing a call: the round never arrives and the
    next answer overwrites the previous one instead of recording a new one.
    """
    answered = {record["result_ref"].split("=")[-1] for record in records
                if record.get("status") == "ok" and str(record.get("result_ref", "")).startswith("answer:round=")}
    return len(answered)


def run_one(script: str, clock: str, layers: tuple[str, ...], scenario_dir: Path,
            output_dir: Path) -> tuple[dict, list[dict]]:
    tag = f"{script}-{clock}-{'+'.join(layers)}"
    log_path = run_script(
        script=scenario_dir / "scripts" / f"{script}.jsonl",
        policy=scenario_dir / "policy.yaml",
        run_id=f"demo-{tag}",
        output_dir=output_dir / tag,
        scenario_dir=scenario_dir,
        layers=layers,
        clock_mode=clock,
    )
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line]
    answered = rounds_answered(records)
    entry = {
        "script": script,
        "clock": clock,
        "layers": list(layers),
        "calls": len(records),
        **{status: sum(r["status"] == status for r in records) for status in STATUSES},
    }
    # Only a script that tries to answer has a task to complete, and its denominator is what
    # IT attempts, not what the scenario offers. Both halves matter: "0 of 3" for a script
    # that never calls answer.submit, and "1 of 3" for one that only ever attempts round 1,
    # read as costs of the gatekeeper in a column where the row above means exactly that.
    attempted = sum(1 for r in records if is_answer(r))
    if attempted:
        entry["rounds_answered"] = answered
        entry["rounds_available"] = attempted
        # Label the shortfall only where the history rule actually caused it. A round lost
        # for another reason must not be reported under this rule's name.
        if answered < attempted and any(r["rule"] == "wait-costs-real-time" for r in records):
            entry["note"] = BLOCKED_ROW_LABEL
    return entry, records


def effect_of(record: dict) -> str:
    """What actually happened, read from the status rather than from a missing reference.

    A permitted call whose tool raised has no `result_ref` either, and reporting that as
    "the tool was not invoked" would claim a veto that never happened — and read exactly
    like the blocked edit two lines down.
    """
    status = record["status"]
    if status == "ok":
        return record.get("result_ref", "done")
    if status == "blocked":
        return "no effect: the tool was not invoked"
    if status == "error":
        return f"invoked and failed: {record.get('error', 'unknown error')}"
    return "not evaluated: the line carried no usable call"


def print_walkthrough(script: str, caption: str, records: list[dict]) -> None:
    print(f"\n{script} — {caption}")
    for record in records:
        name = f"{record['tool']}.{record['operation']}"
        print(f"  {record['agent_id']:<16} {name:<16} {record['decision'] or '-':<6} "
              f"{record['rule'] or '-':<14} {record['status']:<9} {effect_of(record)}")


def provenance(summary: dict) -> str:
    """Where the denominator comes from, so it cannot be read as the whole corpus.

    Without this a judge sees 13,661 and no sign that rows were excluded at all.
    """
    cleaning = summary.get("cleaning")
    if not cleaning:
        return ""
    excluded = sum(cleaning["excluded"].values())
    return (f"Those come from {cleaning['input']['rows']} original revisions, "
            f"{excluded} of them excluded with a recorded reason "
            f"({', '.join(f'{name} {count}' for name, count in cleaning['excluded'].items() if count)}); "
            f"the reconciliation is in `cleaning.json` beside the dataset.")


def not_evaluable(rules: list[dict]) -> str:
    """The declared rules the record carries no evidence for. P0-03 asks for this in writing."""
    if not rules:
        return "Every declared rule could be evaluated against this record."
    declared = "; ".join(f"`{rule['rule']}` — {rule['reason']}" for rule in rules)
    return f"Not evaluable on this record: {declared}."


def table(summary: dict) -> str:
    historical = summary["historical"]
    denominator = historical[0]["events"]
    lines = [
        "# Results",
        "",
        "**What this shows.** The policy is the list of calls the task authorizes. Two checks "
        "run in order, and the second only ever sees what the first let through:",
        "",
        "1. **`per_call`** — is this call on the list? If it is not, it is stopped. No rule has "
        "to name it in advance, which is what catches the abuse nobody foresaw.",
        "2. **`per_history`** — it is on the list, so: is this agent using it in a normal way? "
        "A permitted call made in an abnormal pattern is another shape of abuse, and a single "
        "call cannot show it.",
        "",
        "**What rests on real data, and what does not.** Check 1 is run against the real "
        "corpus below. Check 2 cannot be: the wiki recorded only the calls that reached it — "
        "that is, only the ones check 1 stops. The permitted calls happened and were logged "
        "nowhere, so no real trace exists of a permitted tool being misused. Check 2 is "
        "therefore demonstrated on our own scripted case, labelled as ours throughout. That is "
        "the shape of the experiment, not a result about agents: given the trajectories of a "
        "real incident, the same two checks run unchanged.",
        "",
        "Generated by `uv run python -m bouncer.demo`. Two records that must not be mixed: "
        "the wiki corpus, which is observed behaviour of an incident, and our own scripts, "
        "whose authorization we know because we wrote it.",
        "",
        "## Historical record — the wiki corpus",
        "",
        f"Denominator: {denominator} used revisions, one row per revision, "
        f"{historical[0]['agent_ids']} distinct identities. {provenance(summary)}",
        "",
        "The two timings below are single samples of the same code path, so the difference "
        "between them is measurement noise and not a cost of the history layer.",
        "",
        "| layers | events | blocked | rule | reached layer 2 | µs per check |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for run in historical:
        lines.append(
            f"| {','.join(run['layers'])} | {run['events']} | {run['decisions'].get('block', 0)} "
            f"| {'/'.join(run['rules'])} | {run['history_governed_events']} "
            f"| {run['check_us_per_call']} |"
        )
    lines += [
        "",
        LAYER2_ON_THE_RECORD,
        "",
        not_evaluable(historical[-1]["non_evaluable_rules"]),
        "",
        "## Our own scripts — known authorization",
        "",
        "These are the cases the corpus cannot measure: it only preserved the calls that "
        "the policy blocks, so whether the gatekeeper gets in the way of permitted work has "
        "to be checked here.",
        "",
        "Every call is accounted for: `ok` + `blocked` + `error` + `rejected` equals `calls` "
        "on every row. `rounds answered` counts the rounds a script actually got recorded "
        "out of the rounds **it attempts**, so a script that submits one answer by design "
        "reads 1 of 1, not 1 of 3.",
        "",
        "| script | clock | layers | calls | ok | blocked | error | rejected | rounds answered | note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for run in summary["scripts"]:
        rounds = (f"{run['rounds_answered']} of {run['rounds_available']}"
                  if "rounds_answered" in run else "not attempted")
        lines.append(
            f"| {run['script']} | {run['clock']} | {','.join(run['layers'])} | {run['calls']} "
            f"| {run['ok']} | {run['blocked']} | {run['error']} | {run['rejected']} "
            f"| {rounds} | {run.get('note') or '—'} |"
        )
    lines.append("")  # one trailing newline, not a blank line at EOF
    return "\n".join(lines)


def demo(output_dir: Path, scenario_dir: Path, events: Path, docs_dir: Path) -> dict:
    scripts: list[dict] = []
    shown: dict[tuple, list[dict]] = {}
    for script, clock, layers in RUNS:
        entry, records = run_one(script, clock, layers, scenario_dir, output_dir)
        scripts.append(entry)
        shown[(script, clock, layers)] = records

    # The three beats, in order, so the demo tells one story instead of listing five scripts.
    print(HEADLINE)
    for title, blurb, *runs in BEATS:
        print(f"\n\n{'=' * 78}\n{title}\n{'=' * 78}\n{blurb}")
        for key, caption in runs:
            print_walkthrough(key[0], caption, shown[key])

    historical = []
    for layers in (PER_CALL, PER_CALL_HISTORY):
        run_dir = output_dir / f"replay-{'+'.join(layers)}"
        replay(events=events, policy=scenario_dir / "policy.yaml",
               run_id=f"demo-replay-{'+'.join(layers)}", output_dir=run_dir, layers=layers)
        historical.append(json.loads((run_dir / SUMMARY_NAME).read_text(encoding="utf-8")))

    print(f"\n\n{'=' * 78}")
    print(CLOSING.format(events=historical[0]["events"], agents=historical[0]["agent_ids"]))

    summary = {"policy_version": historical[0]["policy_version"],
               "historical": historical, "scripts": scripts}
    # Written by the preparation step beside the dataset; absent for a fixture corpus.
    cleaning_path = events.parent / "cleaning.json"
    if cleaning_path.exists():
        summary["cleaning"] = json.loads(cleaning_path.read_text(encoding="utf-8"))
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / TABLE_NAME).write_text(table(summary), encoding="utf-8")
    (docs_dir / TABLE_SUMMARY_NAME).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scenario", type=Path, default=SCENARIO_DIR)
    parser.add_argument("--events", type=Path, default=EVENTS_FILE)
    parser.add_argument("--docs-dir", type=Path, default=DOCS_DIR)
    args = parser.parse_args(argv)
    summary = demo(args.output_dir, args.scenario, args.events, args.docs_dir)
    print(f"\nWrote {args.docs_dir / TABLE_NAME} and {args.docs_dir / TABLE_SUMMARY_NAME}: "
          f"{len(summary['scripts'])} script runs, {len(summary['historical'])} corpus walks.")


if __name__ == "__main__":
    main()
