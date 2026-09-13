# Bouncer

**Bouncer checks what an AI agent is about to do before letting the action happen.**

Giving an agent a task does not normally stop it from using an available tool for something else. Bouncer closes that gap. It turns the task's permissions into rules that are checked between the agent's request and the tool's execution.

This repository contains a local Python prototype built for Track 1 of the AI Incident Response Sprint by Apart Research × CeSIA. Bouncer is a runtime control, not a framework for running dangerous evaluations.

## What it does

For every proposed tool call:

1. trusted harness code supplies the real agent, run, and policy context;
2. Bouncer checks whether the task allows the tool, operation, and arguments;
3. if needed, it checks the same agent's previous authorized calls;
4. it records the decision and reason; and
5. it runs the tool only if the call is allowed.

Anything missing from the policy is blocked by default. An agent cannot gain permissions by putting a different `agent_id` or policy in its arguments.

The prototype includes a gatekeeper, local executor, YAML policy, controlled scripts, same-agent history, historical replay, and tests. It does not include a web service, model reviewer, cross-agent rules, or production integration.

## What I tested

I kept two sources of evidence separate because they answer different questions.

### Historical wiki replay

The dataset comes from the [AI Agent Collaboration Network (Collusion Wiki)](https://collusion.wiki/) case, published by Nightingale Collective and supplied for this sprint by Apart Research. The [source files](data/collusion-wiki/) remain unchanged.

After documented exclusions, the prepared dataset contains 13,661 revisions from 3,099 literal identifiers. I adapted each revision to a `wiki.edit` operation and asked what the fixed policy would decide. All were blocked because editing was not authorized.

This shows that default deny covers the adapted operation. It does **not** mean that Bouncer detected 13,661 attacks or would have prevented those edits. The corpus contains past effects, not the original tasks and complete tool calls.

### Controlled execution

I also wrote controlled scripts with known permissions and effects. These calls pass through the real local executor.

The tests show that:

- authorized work completes when task time and wall time advance together;
- forbidden wiki edits and unlisted shell calls do not reach their tools;
- same-agent history can block repeated waits; and
- the current history rule can also block a legitimate wait when the clock is broken, and cannot protect shared state from several agents.

These tests support one narrow claim: **a denied call routed through Bouncer does not reach its tool.** They do not measure a general detection rate or show that Bouncer outperforms other systems.

See the [generated results](docs/results.md)

## Run it

Requirements: Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```sh
uv sync
uv run python -m bouncer.prepare --output-dir data/prepared/wiki
uv run python -m bouncer.demo --output-dir results/demo
uv run pytest -q
```

The demo runs the controlled scripts through the executor and the historical data through a decide-only replay. It regenerates the result summaries. Corpus text, code, instructions, and URLs are treated only as data; the replay cannot invoke the local tools.

The current suite has 72 passing tests. 

## Limits and possible use

Bouncer can control only calls routed through its executor. It cannot contain an already-running process or an action that bypasses that path. Production use would also need maintained policies, safe concurrent state, and protected remote logs.

The OpenAI/Hugging Face incident is a possible application, not a validated result. Testing that case would require the operators' original tasks, permissions, identities, calls, and effects. Bouncer could then be evaluated offline, followed by shadow mode before any rule was allowed to block live calls. This repository cannot establish that Bouncer would have prevented the incident.

## Repository map

- [`bouncer/`](bouncer/) — gatekeeper, history, executor, replay, and demo
- [`scenario/`](scenario/) — task, policy, local wiki, and controlled scripts
- [`data/collusion-wiki/`](data/collusion-wiki/) — frozen source dataset
- [`data/prepared/wiki/`](data/prepared/wiki/) — prepared replay data and cleaning record
- [`tests/`](tests/) — unit and acceptance tests
- [`PRD.md`](PRD.md) — scope and acceptance criteria

## Status

The five technical phases are implemented: dataset preparation; local task and policy; gatekeeper and executor; same-agent history; and demo, replay, and results. The report remains a draft for final editing and submission.

## License

See [`LICENSE`](LICENSE).
