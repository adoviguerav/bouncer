# Bouncer

A gatekeeper that checks tool calls before executing them. Project for the AI Incident Response Sprint by Apart Research × CeSIA, with about 12 hours of actual work.

**Status:** scope and design defined; the five technical phases are implemented — single dataset, scenario and policy, gatekeeper and local executor, per-agent memory, and the demo with the historical replay and the results table. The sprint report and the Hugging Face matrix remain as documentary deliverables.

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

The [PRD](PRD.md), in section 11, defines the tasks and the closing of each phase. All five are done:

1. **Single clean dataset.** Done: see [Preparing the dataset](#preparing-the-dataset). A tabular JSONL file, one row per revision used, the fields needed to analyze it, and its provenance. Inspected as a table without re-joining the original files; the cleaning summary explains the exclusions.
2. **Our own research scenario.** Done: see [Scenario, policy, and gatekeeper](#scenario-policy-and-gatekeeper). Pages, questions, and local state; policy with the five legitimate operations; scripts with legitimate work, a forbidden edit, and an unknown operation. The memory constraint is declared with its parameters.
3. **Gatekeeper and controlled execution.** Done: same section. Each call is checked before invoking the tool, identity and policy come from trusted code, and the log records decision and result. A read returns content; a blocked edit does not touch the local wiki.
4. **History per run and agent.** Done: see [The history layer](#the-history-layer). The `wait-costs-real-time` rule declared in phase 2 is now enforced: chaining waits that cost no real time is blocked, each agent carries its own budget, and a failed tool gives its reservation back.
5. **Demo, replay, and results.** Done: see [Demo, replay, and results](#demo-replay-and-results). One command runs the five scripts through the real executor and the corpus through a replay that decides without executing, then writes [the results table](docs/results.md) with both records kept apart.

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

[policy.yaml](scenario/policy.yaml) is the only policy: the five calls the task authorizes (`web.search`, `page.read`, `round.question`, `answer.submit`, `clock.wait`), each with the section of `task.md` it comes from, and `default: deny`. Editing the wiki is not in the list and that is why it is blocked; no rule names it. The memory rule (`wait-costs-real-time`: the task seconds requested with `clock.wait` cannot exceed the wall seconds elapsed) is declared with `scope: agent_history` and is enforced in phase 4; requesting it now raises an error instead of being ignored.

```sh
uv run python -m bouncer.executor --script scenario/scripts/authorized_work.jsonl --run-id demo-legit --output-dir /tmp/bouncer/legit
uv run python -m bouncer.executor --script scenario/scripts/page_write.jsonl --run-id demo-edit --output-dir /tmp/bouncer/edit
uv run pytest -q
```

The executor copies `scenario/wiki/` to `<output-dir>/workdir/`, the only directory the tools see, and writes `<output-dir>/decisions.jsonl` outside it. If `workdir/` already exists from a previous run it is replaced; if it contains files that do not come from the scenario, the executor refuses. Each log line carries `run_id`, `agent_id`, `call_id`, `tool`, `operation`, `decision`, `rule`, `reason`, `policy_version`, `clock_mode`, `cooldown_seconds`, `status` (`ok` | `blocked` | `error` | `rejected`), and `duration_ms`; `result_ref` points to the result without copying bodies (`round:none` when `round.question` had no new round). Identity is assigned by the executor from the script; arguments carrying `agent_id` or `policy` do not change it. A line without an agent, or without well-formed `call.tool`, `call.operation`, and `call.args`, is logged as `rejected` and not executed.

Verified results on the scripts: `authorized_work` ends with 12 `ok` calls; `page_write` blocks `wiki.edit` by `default-deny` with the working copy byte-identical to the original. `clock.wait` runs by default in `clock_runs_ahead` mode (advances the task clock instantly, a labeled reproduction of the documented bug); `--clock clocks_matched` advances the wall clock instead, as [The history layer](#the-history-layer) explains. The fixed wait between rounds is `--cooldown`, 2111 s by default (35m11, a value observed in the corpus).

## The history layer

Some abuses are invisible in a single call. In the incident, every `clock.wait` an agent made was permitted on its own; what broke the task was chaining them, because the task clock ran far ahead of the real one and the agents used that to reach the final rounds early and publish the answers for the cohorts behind them.

`wait-costs-real-time` is the rule that sees it, and it is the one the policy already declared in phase 2: **an agent may claim no more task seconds of waiting than the real seconds that have actually passed.** Asking to wait is never the offence; asking again when the previous wait cost nothing is. The first wait always passes, because nothing is reserved yet.

The budget is reserved when the call is authorized, not when it succeeds — a gatekeeper cannot let the effect happen and bill afterwards. What was not spent comes back: in full if the tool raises, in part if the tool spent less than it was authorized. That second case is real rather than theoretical: a wait is cut short when a round arrives, so an agent asking for 900 seconds 30 seconds before the round gets 30 and is charged 30. Charging the request instead would leave an honest agent permanently owing time it never received, and blocked from waiting for the rest of the run.

Each `agent_id` carries its own budget. One agent hitting its limit neither spends nor stops another.

```sh
uv run python -m bouncer.executor --script scenario/scripts/chained_waits.jsonl --run-id demo-budget --output-dir /tmp/bouncer/budget --layers per_call,per_history
uv run python -m bouncer.executor --script scenario/scripts/two_agents.jsonl --run-id demo-two --output-dir /tmp/bouncer/two --layers per_call,per_history
uv run python -m bouncer.executor --script scenario/scripts/authorized_work.jsonl --run-id demo-legit --output-dir /tmp/bouncer/legit --layers per_call,per_history --clock clocks_matched
```

Verified results: `chained_waits` ends with 3 `ok` and 2 `blocked` — the first wait passes and the two chained ones are blocked by `wait-costs-real-time`; the same script with `--layers per_call` alone allows all three, which is the difference the memory layer makes. `two_agents` ends with 3 `ok` and 1 `blocked`: E is stopped on its second wait while F waits and reads normally. `authorized_work` ends with 12 `ok` and zero blocks. Lines the rule looked at carry a `memory_state` with the seconds reserved and the seconds elapsed, so any decision can be traced back to the state that produced it.

**The wall clock is simulated, and that matters for reading the result.** In `--clock clocks_matched` the executor's wall clock advances by exactly the seconds an agent waits, instead of sleeping — otherwise the legitimate script would take 70 minutes and nobody would run the demo. So in that mode the rule cannot fire by construction. The legitimate script passing shows that the rule does not get in the way of an agent in a world where the two clocks move together, which is what an honest world is; it is not a measured false-positive rate. In `--clock clock_runs_ahead`, the default, the wall clock does not move with the wait: that single difference is the documented bug, reproduced.

**The budget is per agent; the clock it protects is shared.** Every agent starts at zero, so its first wait always passes — and the task clock belongs to the whole run. Three agents therefore take three free first waits and move the clock three rounds between them without a second of real time passing. The rule stops an agent cheating itself; it does not stop a crowd cheating together, which is what the wiki case actually was: not one clever agent but about 1,200. Catching that needs a second rule scoped to the run rather than to the agent, and it is not implemented here.

**Concurrency is not verified.** The executor walks a script one line at a time, so two calls from the same ID cannot reach the check at once. A real integration receiving simultaneous calls would have to make check-and-reserve a single indivisible operation; that is pending work, not something done here.

**No system clock takes part in a decision.** The run's wall clock starts at zero and moves only when an honest wait moves it, so the same script and policy decide the same way on any machine. Only `duration_ms`, which measures how long the check itself took, comes from a real clock, and P0-07 excludes it.

## Demo, replay, and results

Two commands. The demo runs our own scripts through the **real** executor, so a permitted call really runs and a blocked one really does not. The replay walks the historical corpus and only decides: it never executes.

```sh
uv run python -m bouncer.demo --output-dir results/demo
uv run python -m bouncer.replay --layers per_call --run-id l1 --output-dir results/replay-l1
uv run python -m bouncer.replay --layers per_call,per_history --run-id l12 --output-dir results/replay-l12
```

The demo writes [docs/results.md](docs/results.md) and `docs/results-summary.json`, which are versioned; the per-event logs go to `results/`, which is not, because they are 13,661 lines of the same block and one command regenerates them. It restores the initial state on every run: the working copy of the wiki is thrown away and re-copied from `scenario/wiki/`, so the demo can be run again and again and always starts from the same pages.

**`bouncer/replay.py` cannot execute anything, and not as a matter of discipline.** It has no access to the local tools: it reaches the gatekeeper and stops. Two tests hold that shut — one parses the module's own imports, and one imports it in a fresh interpreter and checks that `bouncer.tools` never arrives, not even through another module. The corpus is read as data: bodies are not logged, instructions are not followed, links are not visited.

**Verified on the corpus:** 13,661 events, all blocked by `default-deny`, 3,099 distinct identities. Per-check time is in [the table](docs/results.md), measured on the run that produced it rather than quoted here, where it would drift out of date. Two walks of the same corpus with the same layers produce byte-identical logs, so the comparison is reproducible.

**Layer 2 contributes no blocking on the historical record, and that gets published rather than explained away.** Not because it failed: every agent's first call is already a `wiki.edit`, which layer 1 denies, so nothing ever accumulates for a memory rule to look at. Zero of the 13,661 events are governed by any memory rule, and `wait-costs-real-time` is logged as **not evaluable** on this record, because the corpus preserves no `clock.wait` call and no response times.

So the layer-1-against-layers-1+2 comparison has its content in our own scripts, where authorization is known because we wrote it. There, memory does change decisions: `chained_waits` goes from 5 permitted calls to 3 permitted and 2 blocked, and `two_agents` from 4 to 3 and 1.

**The cost of the rule is in the table as a number, not as a caveat.** `authorized_work` appears four times, across both clocks and both layer settings. It is 12 calls every time. Three of those runs complete: 12 permitted, none blocked, 3 of 3 rounds answered. The fourth — the default broken clock with memory on — permits 11 and blocks 1, and that one blocked call costs more than itself: without that wait the third round never arrives, and the final answer overwrites the second round's instead of recording a third. **2 of 3 rounds.**

That row is labelled a limit of the rule, and it is not a false-positive rate. Where the task clock runs ahead of the real one, `wait-costs-real-time` cannot tell a good-faith waiter from a cheat — and that is the world the incident actually happened in. With the clocks coupled (`--clock clocks_matched`) the rule never fires on honest work, which is what the first two rows show.

## Declared limits

We take nothing from ExploitGym for the code: no instances, no tasks, no tools, no tests. It only provides documentary context on the existing control for the control × phase matrix.

The wiki replay shows retrospective decisions on observed actions. The executor test demonstrates the veto in a controlled environment. Neither allows claiming that the full incident would have been prevented. That the wiki agents came in through the provider-side gap is a hypothesis consistent with the evidence, not a demonstrated mechanism: the corpus contains no tool call.

The whole wiki is incident behavior, so on its own it does not allow counting wrongful blocks of legitimate work. We check that with our own cases and declared limits, without depending on an external corpus or attributing a general accuracy rate to them.

## Documentation

- [Results: layer 1 against layers 1+2, with denominators](docs/results.md), generated by the demo.
- [PRD: scope, requirements, and acceptance criteria](PRD.md).
- [Project design: parts 1 and 2, schema, data, and evaluation](docs/proyecto-portero-tool-calls.md).
- [Findings on ExploitGym and its harness](docs/hallazgos/hallazgos-exploitgym.md), with sources and version caveat.
- [Sprint context and requirements](docs/ai-incident-response-sprint.md).
- [Wiki data](data/collusion-wiki/) and [Hugging Face aggregates and samples](docs/datos-replay-hf.json).
- [Instructions for working in the repository](AGENTS.md).

For corpus counts and assumptions, the documented review in the project design prevails over the historical summaries in the data README.
