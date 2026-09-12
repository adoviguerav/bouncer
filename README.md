# Bouncer

A gatekeeper that checks tool calls before executing them. Project for the AI Incident Response Sprint by Apart Research × CeSIA, with about 12 hours of actual work.

**Status:** scope and design defined; phases 1 (single dataset) and 2–3 (scenario, policy, gatekeeper, and local executor) implemented; per-agent memory, demo, and results pending.

## The thesis

**It is not that there were no controls.** In the OpenAI/Hugging Face incident there was agent identity set by trusted code, ~1,300 transcripts with the calls and the reasoning, containers with no route to the internet, and a proxy with a four-domain allowlist.

What was missing was worse than having nothing:

- **Nobody read the transcripts.** "OpenAI did not use a scorer that would review their transcripts". The agents believed someone did, and coordinated for days to fool a watcher that did not exist.
- **The log was within reach of the watched.** They escaped the container and replaced the part of the system that executes the calls, so they could declare one and execute another. At least 96 transcripts, around 7%.
- **The channel through which 1,200 agents coordinated had no authentication.** "Shared board unauthenticated, names can be posted by anyone", an agent wrote it. They set up a signature scheme themselves to avoid impersonating each other.
- **Visibility ended at the sandbox escape.** The ~17,600 later actions were reconstructed by the victim from its own logs.

**The failure was not a lack of data. It was having it, not looking at it, and storing it where the watched could rewrite it.**

Hence the gatekeeper's two functions, and the second one is not an extra: check the call before executing it, and **produce the log from trusted code**, out of the agent's write reach. None of the existing controls asked whether a call fit the authorized task.

The wiki case shows it in miniature and without assuming anything: writing was forbidden and the sandbox enforced it by blocking POST, but the wiki accepts edits via GET, so the write got through disguised as a read. The control looked at the transport; a gatekeeper looks at the call.

## What the deliverable contains

**Part 1** walks through the OpenAI/Hugging Face case, which is what Track 1 asks for: what control existed, what each one would have seen across the nine documented phases (control × phase matrix), what data we would ask the operator for, and what we cannot run, for budget or for prudence.

**Part 2** prepares a single dataset with the edit log of a wiki, implements the gatekeeper, and demonstrates it with local tools. We use the non-human names as IDs, declare the missing data, and replay the edits without executing instructions, code, or URLs from the corpus.

The sprint demonstration simulates the research task with a gatekeeper between the tool call and its execution. We wrote the task and the scripted calls ourselves, with no LLM and no API spend. The gatekeeper and the local tools do run: reads return content and a blocked edit leaves the local wiki intact. The goal is to show a verifiable use case with concrete tests; the script is not observed model behavior, and the corpus only preserves the edits, not the full research.

The minimum combines **permission rules** and **rules with memory per ID**, together with a decision log and a controlled executor to verify that blocked calls are not executed. The policy is **a list of the calls the task authorizes, with default deny**: whatever is not in the list is blocked. Editing a page is stopped because it is absent, not because any rule names it.

Review with an LLM or classifier and cross-agent analysis are **optional**. Statistical anomaly detection is not a requirement of the minimum, and the incident's aggregates argue against it: actions outside the task are 2.7% of the documented volume.

## Implementation phases

The [PRD](PRD.md), in section 11, defines the tasks and the closing of each phase. Phases 1 to 3 are done; the rest, pending:

1. **Single clean dataset.** Done: see [Preparing the dataset](#preparing-the-dataset). A tabular JSONL file, one row per revision used, the fields needed to analyze it, and its provenance. Inspected as a table without re-joining the original files; the cleaning summary explains the exclusions.
2. **Our own research scenario.** Done: see [Scenario, policy, and gatekeeper](#scenario-policy-and-gatekeeper). Pages, questions, and local state; policy with the five legitimate operations; scripts with legitimate work, a forbidden edit, and an unknown operation. The memory constraint is declared with its parameters.
3. **Gatekeeper and controlled execution.** Done: same section. Each call is checked before invoking the tool, identity and policy come from trusted code, and the log records decision and result. A read returns content; a blocked edit does not touch the local wiki.
4. **Memory per run and agent.** Enforce the sequence constraint defined in the scenario. Check limits, simultaneous attempts, and separation of histories.
5. **Demo, replay, and results.** Run the scripts without an LLM and pass the historical dataset through the gatekeeper without executing its content. Compare permissions alone against permissions with memory, produce tables and timings, and verify the commands to repeat it.

Tests accompany each phase. The sprint report and the Hugging Face matrix remain mandatory deliverables; they are documentary work separate from these technical phases.

## Preparing the dataset

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run python -m bouncer.prepare --output-dir data/prepared/wiki
uv run pytest -q tests/test_prepare.py
```

**Inputs:** `data/collusion-wiki/revisions.jsonl.gz` and `labels.jsonl.gz`. They are not modified; `cleaning.json` records their SHA-256.

**Outputs** in `data/prepared/wiki/`, versioned in the repository:

- `events.jsonl`: 13,661 rows, one per revision used, ordered by `time` with a tie-break by `rev_id` (the tie-break is technical; it does not claim real order within the same second). Columns: `rev_id`, `source_ref` (source file:line), `agent_id` (the literal `label`, names not merged), `time`, `time_grade`, `uncertainty_seconds`, `page_key`, `seq`, `body` (full body; `""` is an emptied page, not missing data), `request_action` (`null` when the original lacks it), `operation` (always `wiki.edit`, a declared adaptation), and `provenance` (what is observed, adapted, or unknown in that row).
- `cleaning.json`: input 14,591 = 31 humans (`is_human_handle` in `labels`) + 899 without a name + 13,661 used. Recovered 0: no nameless row has a `related_event_id`. 3,099 IDs, 74 empty bodies, 74 without `request_action`.

Two runs over the same originals produce byte-identical files. The dataset loads on its own:

```python
import pandas as pd
df = pd.read_json("data/prepared/wiki/events.jsonl", lines=True)
```

It contains no decisions, policy, or scripts of ours; the replay ID will be assigned by the executor in later phases.

## Scenario, policy, and gatekeeper

Everything in `scenario/` is **our own material**: a round-based research task ([task.md](scenario/task.md)) reconstructed from what the agents say in the corpus, three local wiki pages with invented data, three questions with a reference answer, and five scripts. It is not the task any real agent received.

[policy.yaml](scenario/policy.yaml) is the only policy: the five calls the task authorizes (`web.search`, `page.read`, `round.question`, `answer.submit`, `clock.wait`), each with the section of `task.md` it comes from, and `default: deny`. Editing the wiki is not in the list and that is why it is blocked; no rule names it. The memory rule (`clock-budget`: the task seconds requested with `clock.wait` cannot exceed the wall seconds elapsed) is declared with `scope: agent_history` and is enforced in phase 4; requesting it now raises an error instead of being ignored.

```sh
uv run python -m bouncer.executor --script scenario/scripts/legitimate.jsonl --run-id demo-legit --output-dir /tmp/bouncer/legit
uv run python -m bouncer.executor --script scenario/scripts/forbidden_edit.jsonl --run-id demo-edit --output-dir /tmp/bouncer/edit
uv run pytest -q
```

The executor copies `scenario/wiki/` to `<output-dir>/workdir/`, the only directory the tools see, and writes `<output-dir>/decisions.jsonl` outside it. If `workdir/` already exists from a previous run it is replaced; if it contains files that do not come from the scenario, the executor refuses. Each log line carries `run_id`, `agent_id`, `call_id`, `tool`, `operation`, `decision`, `rule`, `reason`, `policy_version`, `clock_mode`, `cooldown_seconds`, `status` (`ok` | `blocked` | `error` | `rejected`), and `duration_ms`; `result_ref` points to the result without copying bodies (`round:none` when `round.question` had no new round). Identity is assigned by the executor from the script; arguments carrying `agent_id` or `policy` do not change it. A line without an agent, or without well-formed `call.tool`, `call.operation`, and `call.args`, is logged as `rejected` and not executed.

Verified results on the scripts: the legitimate one ends with 12 `ok` calls; the forbidden-edit one blocks `wiki.edit` by `default-deny` with the working copy byte-identical to the original. `clock.wait` runs by default in `harness_bug` mode (advances the task clock instantly, a labeled reproduction of the documented bug); `--clock honest` really sleeps. The fixed wait between rounds is `--cooldown`, 2111 s by default (35m11, a value observed in the corpus).

## Declared limits

We take nothing from ExploitGym for the code: no instances, no tasks, no tools, no tests. It only provides documentary context on the existing control for the control × phase matrix.

The wiki replay shows retrospective decisions on observed actions. The executor test demonstrates the veto in a controlled environment. Neither allows claiming that the full incident would have been prevented. That the wiki agents came in through the provider-side gap is a hypothesis consistent with the evidence, not a demonstrated mechanism: the corpus contains no tool call.

The whole wiki is incident behavior, so on its own it does not allow counting wrongful blocks of legitimate work. We check that with our own cases and declared limits, without depending on an external corpus or attributing a general accuracy rate to them.

## Documentation

- [PRD: scope, requirements, and acceptance criteria](PRD.md).
- [Project design: parts 1 and 2, schema, data, and evaluation](docs/proyecto-portero-tool-calls.md).
- [Findings on ExploitGym and its harness](docs/hallazgos-exploitgym.md), with sources and version caveat.
- [Sprint context and requirements](docs/ai-incident-response-sprint.md).
- [Wiki data](data/collusion-wiki/) and [Hugging Face aggregates and samples](docs/datos-replay-hf.json).
- [Pending tasks](docs/tareas-pendientes.md).
- [Instructions for working in the repository](AGENTS.md).

For corpus counts and assumptions, the documented review in the project design prevails over the historical summaries in the data README.
