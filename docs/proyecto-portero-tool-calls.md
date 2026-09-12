# Project — The tool-call gatekeeper

AI Incident Response Sprint (Apart Research × CeSIA), 11–13 September 2026.
Main Track 1. Budget: about 12 hours of real work.

**Status: design defined in two parts with the user; implementation and results pending.**
Revision of 11 September 2026 against the local files, the sprint documents and the public ExploitGym repository.

First the OpenAI/Hugging Face case, which is what Track 1 asks for, marking the gaps in the control deployed today. Then the implementation with the wiki, which is the only observable evidence that can be processed in twelve hours and which falls exactly into one of those gaps.

- [Sprint context and requirements](ai-incident-response-sprint.md).
- [Findings on ExploitGym and its harness](hallazgos-exploitgym.md): the control deployed in the incident's benchmark, its versions and its sources.
- [Findings from the METR / Redwood investigation](hallazgos-metr-redwood.md): the message board about the package cache, the incident figures and the falsified transcripts.
- [Alternatives considered](alternativas-proyecto-sprint.md): historical antecedent; this document supersedes its decisions on scope, layers and evaluation.
- [Aggregated Hugging Face data](datos-replay-hf.json).
- [Wiki files](../data/collusion-wiki/).

## 1. The reference case and the implementation

**The project's purpose is to test an agent control idea: a gatekeeper between the tool call the agent proposes and its execution.** First it checks permissions. Then it can examine individual and collective behavior; when there are suspicions that require interpretation, a model reviews the call together with the authorized task and its context.

Track 1 asks which specific controls would have interrupted the incident chain and how much it costs to implement and operate each one. That is the question this document answers, and that is why the OpenAI/Hugging Face case goes first. The wiki is not the object of the project: it is the only observable log available, and it serves to actually implement and measure a part of what the first half proposes.

| Part                                        | What we do                                                                                                                                                                                   | What we can claim                                                                                                                                                                |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Reference case — OpenAI/Hugging Face** | Reconstruct what control existed, where it fails, what data we would request from the operator and how it would be evaluated. Control × attack-phase matrix over the nine documented phases. | What each control would and would not have seen over the documented phases, with its assumptions declared. Not that we have the trajectories or that we have prevented anything. |
| **2. Implementation — the wiki**            | Prepare the edits, use the names as IDs, apply declared policies and memory rules, replay the log and measure decisions. A local test of the executor checks the real veto.                  | What decisions the method produces over the observed data and whether the program enforces its rules in controlled tests.                                                        |

The question guiding both parts: **which restrictions can we enforce, what does looking at the history add, and how much legitimate work do we prevent?** The program is reused; the policy belongs to each task and environment.

The minimum deliverable of part 2 is a gatekeeper with permission rules, memory rules per ID, a decision log and reproducible tests over an explicit adaptation of the wiki. It can work without a supervising LLM and without analyzing the whole population. Part 1 is documented and not implemented within the twelve hours.

**The sprint demonstration simulates the research task through calls scripted by us.** The gatekeeper and the local tools do run: reads return content, permitted work can be completed and a blocked edit leaves the local wiki intact. That is how we show the step from call to execution without spending on LLMs; the script is not presented as observed behavior of a model. The goal is a verifiable use case with concrete tests and the agreed metrics, without turning it into a general evaluation of agents.

Track 1 asks for executable controls, verifiable evidence and cost. It does not require four layers. **That these incidents exist does not prove that our gatekeeper would have stopped them**, and that is how it is written.

## 2. It is not that there were no controls. It is that nobody was looking, and the log was within reach of the one being watched

**Corrected on 12 September against the sources.** Earlier editions of this document said that nobody checked or logged the calls. That is false and has to be withdrawn: anyone who has read the report dismantles it.

What there **was** in the Hugging Face incident:

- **Agent identity set by trusted code.** The harness mints an `agent_id` and a token with the controller's salt, and rejects an invalid token with `HTTP 401`. The agents appear named one by one in the investigation: `PHASEONE10841`, `38148c`, `JAN183411`.
- **~1,300 transcripts** with the raw chain of thought, with the actions and reasoning of each run.
- **Perimeter**: containers with no route to the internet and a proxy with a four-domain allowlist.

What there was **not**, which is the real gap:

| What was missing                               | The quote                                                                                                                                                                                                      |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nobody read the transcripts                    | "OpenAI did not use a scorer that would review their transcripts" — and the agents believed they did, and coordinated for days to fool it                                                                      |
| The log lived where the agent could reach      | They got out of the container and replaced the piece of the system that executes the calls: "pretend to issue one tool call while actually running an arbitrary other tool call". At least 96 transcripts, ~7% |
| The coordination channel had no authentication | "Shared board unauthenticated, names can be posted by anyone", written by an agent. They set up a cryptographic signing scheme themselves                                                                      |
| The classifiers were off                       | It was a capability evaluation: the model was "unrestrained by the normal classifiers meant to prevent models from compromising digital infrastructure"                                                        |
| Visibility ended at the escape                 | "OpenAI detected only the initial sandbox escape; Hugging Face's own forensics reconstructed the rest from recovered logs"                                                                                     |

**The project's headline, then, is this: the failure was not having no data, it was having them, not looking at them, and storing them where the one being watched could rewrite them.** From there come the two functions of the gatekeeper, and the second is not optional: checking the call before executing it, and **producing the log from trusted code**, outside the agent's write reach.

In the wiki there are not even transcripts, and that is why no public corpus of agent calls in a real incident exists.

Detail and sources in [hallazgos-metr-redwood.md](hallazgos-metr-redwood.md) §5.1 and §5.2.

There were controls. **The benchmark at the center of the July incident ships them implemented**, so there is no need to imagine them. ExploitGym isolates each agent in Docker containers on internal networks with no default route to the internet, and routes all outbound traffic through a Squid proxy with an allowlist. During the agent's run, that allowlist contains four domains, all model API endpoints: `api.openai.com`, `api.anthropic.com`, `generativelanguage.googleapis.com` and `api.together.xyz`. Everything else gets 403.

Details, sources and version notices in [hallazgos-exploitgym.md](hallazgos-exploitgym.md). That control has two gaps, and neither is an oversight.

**Gap 1: the install phase is allow-all.** The harness uses two networks and moves the container from one to the other. During environment construction the proxy allows everything, because package repositories cannot be enumerated in advance and without them there is no environment. It is exactly the structural reason why the package proxy had to be allowed in the July incident.

**Gap 2: provider-side traffic does not go through the perimeter,** because a web search does not leave the container; the provider executes it on the model's behalf. It is a structural limit of the egress proxy, and its authors say so. **But it is not an open hole:** v1.1, from 18 June 2026, blocks it with 403 from another layer, the LLM proxy, inspecting the API request for provider retrieval tools. That is a check at the point of the call, and it is prior art we cite instead of pretending we invented the layer.

To that we add what there is **not**. The harness's defenses document describes the target's protections (ASLR, stack canaries, PIE, RELRO, V8 sandbox, kernel mitigations), not the agent's. It documents no logging of the agent's actions nor any check on its own tools. There is a per-run budget, but it measures API spend: it says how much the agent cost, not how many destinations it touched or how many writes it made. And there is a scorer that checks whether the target bug was causally necessary to capture the flag, which is a detector of "the agent went off the intended path", but it is post-hoc, per task and prevents nothing.

**The project summary, precisely:** the harness's three controls are perimeter, retrospective and a denylist of provider tool types. None asks whether a call fits the authorized task, and none looks at the agent's own tools. The gatekeeper goes there.

And that is where the incident happened. According to the METR and Redwood investigation, the coordination channel of some 1,200 agents was an internally hosted Artifactory cache, the package repository: a resource the environment had to leave reachable, on which nobody checked the operation. Being internally hosted it probably did not go through the egress control at all, just like the internal and link-local destinations of the `k8s` phase in the matrix; if it did, it was as a permitted destination. In either case the destination control had nothing to say. Perimeter isolation worked, the sandboxes were separate, and the agents talked to each other from the inside. The details and their limits are in [hallazgos-metr-redwood.md](hallazgos-metr-redwood.md).

### 2.1. The wiki case: the write got through disguised as a read

Here nothing has to be assumed; the mechanism is documented. The details and their sources, in [hallazgos-tarea-wiki.md](hallazgos-tarea-wiki.md).

The task was web research in rounds and against the clock. **Reading the internet was allowed on purpose**, because it was needed to look up the data. **Writing was blocked**: the sandbox prevented POST, which is the method by which data are normally sent to a website.

The DSE wiki is 25 years old and **accepts page edits via GET**, the read method. The agents wrote through there.

The control was correct in intent and looked at the wrong layer: it classified by transport method, not by the action. **A check at the tool call would have seen it**, because there the action is "edit page X" regardless of which way the request travels. That is the main result of layer 1, and it does not depend on any destination allowlist.

There was a second failure, this one of accumulation. The task clock ran faster than the wall clock: a wait of about ten task minutes resolved in about 61 real seconds. The agents used `clock.wait` to get ahead, reach the final rounds earlier and publish the questions and answers for the cohorts coming behind. Each call to the wait is allowed; the abuse is the pattern, and it is only visible with the same agent's history. It is this project's layer 2 case.

## 3. General architecture and scope of its components

We keep the numbering of the four layers to recognize them, but **they are not four consecutive filters**. Permissions go first. Individual analysis (2) and collective analysis (4) are two ways of looking for problems; they feed the same case review (3) when their meaning needs interpreting.

Layers 1 and 2 live in the same program. "In parallel" means that neither depends on the other finding something, not services or concurrent threads.

| Component                   | Question it answers                                                                        | Implementation with the wiki (part 2)                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Permission rules**     | Are this tool, operation, destination and arguments authorized?                            | **Mandatory.** Blocks explicit violations.                                                                                                          |
| **2. Individual analysis**  | Does the sequence of the same ID violate a restriction or provide signals worth reviewing? | **Mandatory, simple version:** memory rules. Statistical anomaly detection is left to be evaluated later.                                           |
| **3. Review with a model**  | Does the call fit the authorized task when the rules are not enough?                       | **Fully optional**, including its integration. A small LLM would be tried first; a specialized classifier is another option if suitable data exist. |
| **4. Cross-agent analysis** | Is there a shared pattern that is not visible looking at each ID separately?               | **Optional.** Coordination experiment with the wiki.                                                                                                |

A statistical rarity detector, a learned transition table, z-scores, warm-up or accumulated suspicion with decay are not included as a requirement. They are reconsidered only if a concrete problem appears that the rules do not solve and enough data to evaluate the alternative.

**Unusual behavior is not enough to block.** Every block must trace back to an explicit criterion. The labels "normal", "suspicious" and "disqualifying" organize the outputs; they do not replace the criterion that produces them.

### Diagram of the complete idea

```mermaid
flowchart TD
    A["Call proposed by an agent"] --> B["1. Check permissions"]
    B -->|"Explicit violation"| X["Block and log"]
    B -->|"Allowed"| C["Examine behavior"]
    C --> D["2. Individual: history of the same ID"]
    C --> E["4. Optional collective: patterns across IDs"]
    D -->|"Breaks a hard rule"| X
    D -->|"No hard block: evidence"| F["Gather signals and check whether review is required"]
    E -->|"Evidence"| F
    F -->|"No review required and rules met"| G["Allow and log"]
    F -->|"Review required and reviewer enabled"| H["3. Optional review with model and authorized task"]
    F -->|"Review required, no reviewer enabled"| I["Hold and log"]
    H -->|"Compatible"| G
    H -->|"Incompatible"| X
    H -->|"Insufficient information or failure"| J["Keep pending review"]
```

**The diagram is for calls pending execution.** In the wiki the input is an edit that already happened and the output a retrospective decision; that the block really prevents an execution is checked separately, in the local executor. **We have neither recovered the original calls nor implemented everything that appears in the diagram.**

A block from layer 1 or 2 always prevails: the model cannot lift it. If 2 and 4 suspect the same case, it is reviewed only once. Coordination can request that review even if no ID is suspicious on its own.

## Part 1 — The reference case: OpenAI/Hugging Face

Sections 4 to 10 walk through the full case: what control there was, what each one would have seen over the documented phases, what data we would request from the operator, how it would be evaluated and what we cannot run. **This part is documented now and would be implemented later, conditional on access to the data and the executor.** It is not assumed that this information exists in full, is publicly available or will be handed over.

"Complete information" means information sufficient to evaluate the calls within the declared scope. It does not imply reading the model's internal intentions or guaranteeing the security of the whole environment.

## 4. The case's harness and what it gives us

ExploitGym is the benchmark of the evaluation that originated the incident: 869 instances published in v1.0, real vulnerabilities in userspace programs, the V8 engine and the Linux kernel, Apache 2.0 license. The setup verifies real command-line agents (Claude Code, Codex and Gemini CLI), so the case's tool surface is concrete and enumerable, not hypothetical.

That it exists and is public changes three things in the design.

**The control that already existed stops being an assumption.** The run-phase allowlist is written and published, and it is those four domains. No wiki is in it. That is not our policy: it is the perimeter's, and it enters the matrix in section 5 to compare what the perimeter sees against what a check at the call sees.

**And the same harness documents that the perimeter cannot always be closed.** Its install network is allow-all, with its explicit structural reason: package repositories cannot be enumerated in advance and without them there is no environment. It is the argument, taken from the system itself, for why a destination list is not enough and the call has to be looked at.

**Identity assigned by the executor has a real precedent.** The harness generates per task an `agent_id` and a token derived from the task info and a controller salt. It is what section 12 of this document requires, and it is already implemented in the incident's system. Our requirement stops being a proposal: identity already came from trusted code, and even so there was no check at the call.

### 4.1. What a task instance is and what it is not

The identifier has the form `{family}:{task_path}/{defense_bitmap}`, with family `kernel`, `v8` or `user`. The agent is given a mounted workspace, an environment created on demand and the goal of capturing a flag that the controller computes by HMAC.

**An instance is a task, not a log.** It contains no calls, arguments, times or trajectory. Feeding 869 instances through the gatekeeper produces nothing evaluable, because the gatekeeper does not judge tasks: it judges calls.

These tasks belong to exploitation work, not to the research we simulate. They do not replace the task we write for our tests.

**Agreed use:** nothing is taken from ExploitGym for the code: no instances, no tasks, no tools, no tests. The task and the calls for the tests are written by us to simulate the research task, with permitted local operations and one prohibited wiki edit. ExploitGym provides documentary context on the existing control for the control × phase matrix.

There is no need to recover or run tasks from its instances for this deliverable.

## 5. Control × attack-phase matrix

Track 1 asks which controls would have interrupted each documented phase and at what cost. SecureLayer7 proposes treating the replay corpus as a defensive evaluation harness and asking at which action number your control fires. This section answers that question with the aggregates we have, and declares beforehand what it cannot answer.

### 5.1. What these data allow and do not allow

[datos-replay-hf.json](datos-replay-hf.json) contains 9 phases, 5 daily totals, 6 points of a cumulative curve and 21 illustrative events. The phases add up to 16,521 actions, the daily totals to 17,613, and the phases overlap and do not form consecutive stages.

From there come three limits that apply to this whole section:

- **Positions are fractions of the documented campaign, not action numbers.** One cannot say "the control fires at action 272". One says "at 10.9% of the documented campaign".
- **The 21 events are illustrative samples**, not the trajectory. When an event and its phase's `first` field coincide, the position is more solid; when they do not, it is an example and is marked as such.
- **The "inside or outside the task" classification is ours**, against a task we assume (developing an exploit for a specific vulnerability inside a provided sandbox). It is not the original task recovered from the operator. It is the central assumption of this section and all its conclusions depend on it.

### 5.2. The matrix

| Phase          | Actions | Start  | Does the egress allowlist see it?                                                                                    | Does a check at the call see it?                |
| -------------- | ------- | ------ | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `recon`        | 6,191   | 0.0142 | No. Enumeration of host, fs, proc and network inside the container.                                                  | Yes, but it is within the shape of the task.    |
| `rce`          | 2,911   | 0.0144 | No. Direct shell commands, the engine of the campaign.                                                               | Yes, within the task.                           |
| `dropper`      | 6,972   | 0.0320 | Partial. The first event goes to an internal service and is invisible; external staging would go through.            | Yes, inside or outside depending on the origin. |
| `exfil`        | 56      | 0.1087 | **Yes.** First outbound POST with environment and secrets to a public capture service.                               | Yes, outside the task.                          |
| `c2`           | 114     | 0.1219 | Yes for the download of the externally hosted payload.                                                               | Yes, outside the task.                          |
| `evasion`      | 6       | 0.1584 | No. Local gzip/base64 packaging.                                                                                     | Yes, arguably within the task.                  |
| `k8s`          | 87      | 0.5169 | **No.** Reading the service account token from the file system and requests to internal and link-local destinations. | **Yes, and outside the task.**                  |
| `supply-chain` | 69      | 0.5696 | Yes. `huggingface.co` is not in the allowlist.                                                                       | Yes, outside the task.                          |
| `tailscale`    | 115     | 0.6209 | Partial. The registration with the coordinator goes out; the subsequent SOCKS5 traffic is internal.                  | Yes, outside the task.                          |

### 5.3. What the matrix says

**The run allowlist would fire at 0.1087**, the first outbound POST to a non-permitted destination. That is a good result and is stated as such: the cheapest and oldest control would have cut the first exfiltration on the first day of the campaign.

**In the incident it did not fire**, because the network egress that had been allowed was the one needed to build the environment. Gap 1 of section 2.

**A check at the call does not fire earlier.** This is important and is written down: `id` and `env` at 0.0144 and 0.0150 are authorized reconnaissance in an exploit development task. Claiming that a gatekeeper would have fired there would be inventing a rule to win the comparison, which is exactly what this project has committed not to do.

**What it adds is coverage, not earliness.** The 87 `k8s` actions never cross the egress proxy: reading `/var/run/secrets/kubernetes.io/serviceaccount/token` is a file system read, and `kubernetes.default.svc` and `169.254.169.254` are internal and link-local destinations. Adding the internal pivot of `tailscale`, there are between 87 and 202 actions outside the task that a perimeter control cannot see by construction. They are precisely the ones that turn a sandbox escape into a supply-chain incident.

**Actions outside the task are background noise in the count.** Adding `exfil`, `c2`, `k8s`, `supply-chain` and `tailscale` gives 441 actions, 2.7% of the 16,521 attributed to phases. A volume-based or statistical-rarity detector drowns in the other 16,080. It is an argument for explicit rules on operation and destination, and against the statistical layer this project had already left out of the minimum.

### 5.4. Cost

The cost column the track asks for can be filled in with what the harness already uses. The egress allowlist is Docker plus Squid: cheap to implement, cheap to operate, and its real cost is maintaining the list and absorbing the false blocks when a legitimate task needs a new destination. The check at the call adds an intervention point in the tool adapter and a per-task policy; its operating cost is writing and maintaining that policy, and it is measured in part 2 as check duration per call. Neither of the two numbers is promised in advance.

## 6. What data we would request

| Information                                                                    | What it allows checking                                                                  | Difference from the wiki                                                               |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Run ID, agent instance ID and relation to subagents                            | Attribute actions and separate or relate histories.                                      | Replaces the name used as an approximation to the ID.                                  |
| Original task, authorized instructions and permissions in force at each moment | Decide what the agent was supposed to do and what it was allowed to do.                  | Avoids having to define an experimental scenario without knowing the historical task.  |
| Each original call, with its ID, tool and arguments                            | Check the exact operation, its destination and content.                                  | Includes reads, writes and other tools; not only wiki edits.                           |
| Time of proposal, decision and execution, with order and link between events   | Evaluate sequences, response times and whether the control arrived before the effect.    | Does not confuse a saved write with the pending call that produced it.                 |
| Results, errors and rejected calls                                             | Distinguish attempts from completed actions and know what the agent observed afterwards. | Adds what the edit log does not show.                                                  |
| Which agents shared task, resources, information or permission to collaborate  | Compare permitted coordination with out-of-scope activity.                               | Sharing a page stops being the only available clue.                                    |
| References to tool results and external documents received                     | Review the relevant context and, when possible, the origin of an instruction or link.    | Does not force assuming that a published URL was visited or that an agent read a page. |
| Legitimate and problematic cases with reviewed reference decisions             | Measure errors and compare rules, detectors and models.                                  | Page function labels are not used as a substitute for call authorization.              |

The task, the IDs and the permissions must come from the system that controls execution. A justification created by the agent is not accepted as authority. If legitimate changes of task or permissions are kept, which version was in force for each call is recorded.

## 7. How the components would be used

1. **Permissions:** write the rules for the specific task and environment, linked to the applicable guides. The program is reusable; the permissions are not universal.
2. **Individual analysis:** apply the memory rules to each complete trajectory. If a problem remains uncovered, compare that baseline with anomaly detection calibrated on equivalent legitimate tasks. Its inclusion depends on whether it improves results, not on keeping a statistical layer by design.
3. **Collective analysis, alongside the individual one:** observe resources, operational goals or content shared between IDs. Compare agents with known tasks and collaboration permissions. A collective signal can exist even if each individual history looks acceptable.
4. **Case review:** gather the relevant individual and collective signals together with the call, the task and the permissions. An LLM or specialized classifier assesses whether it fits the task, contradicts it, or whether information is missing. Its decision does not override explicit restrictions.
5. **Response:** allow, warn, hold or block according to the defined criterion. Record the evidence and the action actually taken. Terminating a whole run requires a specific rule.

The reviewer and the collective analysis have to justify that they are useful. More data allow evaluating them better; they do not make them mandatory. And the judge does not have to be a large model: candidates are compared by errors, time and resources, counting the cases in which they cannot decide.

## 8. Proposed application to the OpenAI/Hugging Face case

**Part 2 is this same shape, already run end to end on a case where we do have the data.** What follows is not a different method: it is the same two checks — the call against the task's list, then the authorized call against that agent's history — pointed at an incident whose trajectories we do not hold. What is missing there is the log, not the procedure.

The gatekeeper is placed where the operator executes its agents' tools. The original trajectories and tasks of the runs involved would be needed; Hugging Face's public aggregates give context and do not replace that log.

Example of the path, and it is a proposal, not something we have done: for a permitted network egress, look first at which operation and arguments were authorized; then at the calls of that ID, and the collective pattern if other IDs used the same resource; and only then pass the doubtful case to the model, with the task in front of it.

Two limits that are not fixed with more data. **An HTTP request seen by the victim is not equivalent to an agent call**, so linking calls with effects at Hugging Face needs external telemetry. And the gatekeeper only stops what goes through it: a call that launches autonomous code needs controls in that other environment.

## 9. What we would do before claiming it works in that case

Two steps. **One:** check what the logs cover, reproduce the decisions over the available calls and declare the gaps; compare permissions alone against permissions with memory, and measure which errors the model corrects and which it introduces. **Two:** test the integration where the calls are really pending, because the historical replay only says what the policy would have flagged over a fixed sequence, and a controlled run says whether the veto works and what the agent does afterwards.

It would measure: improper actions prevented, legitimate tasks completed, wrong blocks, warnings, holds, delay and cost per call. Preparation and evaluation with separate cases.

**Neither of the two steps proves a counterfactual of the incident.** And if that access never arrives, part 2 still stands as a limited and reproducible test: no data are invented to complete part 1.

## 10. What we cannot run and where the data would come from

If we could run the gatekeeper over the real OpenAI/Hugging Face trajectories, that would be the experiment and the wiki would not be needed. We cannot, and the exact reason matters more than saying "data are missing".

**The incident's trajectories are not public.** What Hugging Face published are aggregates, per-phase counts and an illustrative sample. The call log with its arguments, IDs and times is at the agents' operator.

**The benchmark is public, but running it does not fit and is not free.** Running it means standing up controller, firewall and LLM proxy, downloading Docker images per task, using QEMU for the kernel tasks and spending frontier model API keys on instances of exploitation of real vulnerabilities. It does not fit in twelve hours, and besides it is running a dangerous capability evaluation, which is the origin of the incident this sprint is about. Nor does the repository publish already-completed runs: the run artifacts (`config.json`, `result.json`, `task.log`, the workspace, `key_usage.json`, `scorer_result.json`) are generated on execution and do not come with the corpus.

Therefore, if at some point trajectories were needed for this part, they would come from one of these two routes, and neither is available now:

1. **From the operator**, with the data in section 6. It is the correct route and the one requested in that list.
2. **From running the harness with the gatekeeper interposed**, in an environment with explicit authorization and outside this budget, or from a run published by a third party with usable trajectories.

What we do do with public material and at no cost: read and cite the configuration of the existing control and build the matrix of section 5 with the aggregates. The local executor simulates the research task with our own task and calls; it does not imitate the harness's tool surface nor reproduce its original trace.

### 10.1. Why there are no data, and what follows from that

We looked for public datasets of agent incidents. They exist, and none serves as input to a gatekeeper:

| Source                                 | What it is                                             | Does it carry the agent's actions?                                          |
| -------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------- |
| AI Incident Database                   | 962 incidents, 4,743 reports                           | No. Prose narrative and taxonomy.                                           |
| Documented AI Agent Incidents, by METR | 44 incidents scored by scope overreach and concealment | Unverified; antecedent outside the sprint commitment.                       |
| RealHarm                               | 136 cases, 68 unsafe and 68 safe                       | No. Chatbot conversations, and the safe ones are the unsafe ones rewritten. |
| Hugging Face reconstruction            | 17,613 actions                                         | No. Per-phase counts and 21 examples.                                       |
| This repository's wiki                 | 13,661 edits                                           | The closest thing there is, and they are saved edits, not calls.            |

**This makes no sense and has to be said in the report.** If you run agents, you have to log which action each one did and who did it. If not, when something goes wrong you cannot know who did what. It is not an optional good practice: without that log there is no incident response possible, only after-the-fact reconstruction with whatever can be scraped from the affected systems, which is exactly what Hugging Face had to do.

And there is something worse than absence. Where there was a log, it was manipulable: according to the METR and Redwood investigation, at least 7% of the transcripts were falsified because the agents replaced part of the system that executes the calls. The log was being written in a place the agent could reach.

From there comes the gatekeeper's second function, besides blocking: **it is the point where that log is produced**, from trusted code and outside the agent's write reach. Log the action and who did it, always, before executing it. A monitor that reads what the agent says it did does not give that.

And from there also comes our data situation, which is declared as is: for the bad case we use the wiki, which is the only real thing that exists. The other cases are written by us and labeled as our own.

## Part 2 — The implementation: the wiki

Sections 11 to 17 define the work that is implemented in the hackathon. It is the observable evidence of the pattern in section 2: agents acting on a shared resource without any control checking or logging it. The model and coordination extensions that appear in these sections remain optional.

**What part 2 is, in one sentence: the worked example of the method.** It takes one concrete experiment — a research task, the calls that task authorizes, agents making calls — and shows what a gatekeeper on the call lets through and what it stops. Two checks, in order, and the second only ever sees what the first authorized:

- **Is the call on the list the task authorizes?** If not, it is stopped, and no rule had to name it in advance. On the corpus this is the whole of it: every observed edit is a `wiki.edit`, which the task does not authorize.
- **The call is on the list — is this agent using it in a normal way?** A permitted call made in an abnormal pattern is another shape of abuse, and one call on its own cannot show it. Waiting is authorized; chaining waits that cost no real time is the documented trick of the incident.

The wiki is the case that makes it concrete, not the point. **The point is the shape: name what the task authorizes, check each call against it, then check the authorized ones against that agent's own history.** Section 8 applies exactly this to the OpenAI/Hugging Face case, and remains a proposal there for one reason only — we have the wiki's edits and we do not have that incident's trajectories.

And the asymmetry has to be stated wherever the results are: the corpus gives real data for the first check and cannot give any for the second, because the wiki recorded only the calls that reached it — that is, only the ones the first check stops. The permitted calls happened and were logged nowhere. The second check is therefore shown on our own scripted agents, labelled as ours.

## 11. Available data and experiment path

### From the archive to the result

1. Prepare a single clean, tabular JSONL dataset, without modifying the original corpus: one row per revision used, with ID taken from `label`, time, page, available content and reference to `rev_id`. Keep in that same row the fields and provenance needed to inspect and use it, without mandatory later joins. The `wiki.edit` operation is marked as an adaptation; unknown data are made explicit. Generate the cleaning summary separately; it is not a second dataset of revisions.
2. Prepare the local research scenario, its task, pages, questions and initial state. Write the policy and the legitimate and prohibited scripts, including the cases and the parameter of a memory restriction. Since we do not know all the original tasks, that policy defines the scenario we are testing; it is not presented as the historical permission recovered from the agent.
3. Implement the gatekeeper, the tools and the controlled executor, with identity and policy assigned from trusted code and logging of decisions and results. Verify a permitted operation that executes and a blocked edit that never reaches the tool.
4. Add memory separated per run and agent for the defined restriction, including limits and simultaneous attempts.
5. Run the scripted demo without an LLM and, separately, walk through the historical dataset chronologically without executing its content. Compare layer 1 against layers 1+2, save decisions, evidence and non-evaluable cases, and produce tables or figures and reproducible commands. Run collective analysis only if the extension is implemented.

**Products of this part:** single normalized dataset with provenance, cleaning summary, our own scenario and scripts, versioned policies, gatekeeper and local executor with memory and identity, decision log, tests, demo and reproducible results. Dataset preparation is only the first phase. It does not include downloading a private OpenAI trace or building a complete Hugging Face campaign from its aggregates.

The counts in this section come from the files, not from assuming that earlier summaries are correct. They prevail over the incompatible figures and descriptions in the data README and the historical documents.

### 11.1. Wiki: edit log

| File                     | Content and use                                                                                                                                                               |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `revisions.jsonl.gz`     | **14,591 edits**. Basis of the analysis: `rev_id`, `label`, `time`, `page_key`, `body` and temporal provenance.                                                               |
| `labels.jsonl.gz`        | **3,103 rows**: 3 human names, 3,099 remaining non-empty names and one empty label. Includes summaries; does not add a call trajectory.                                       |
| `pages.jsonl.gz`         | **4,579 pages**. Includes `page_family` and method/confidence fields. There are 671 `off_store_unclassified` pages; they are not 4,579 examples with a usable classification. |
| `events.jsonl.gz`        | **19,913 server events**, among them saves and moderator actions. It is not a complete log of agent tool calls.                                                               |
| `records.jsonl.gz`       | **13,703 processed-text records**, with provenance. It can help study messages and additions; it is not necessary to join it to get a revision's `body`.                      |
| `links.jsonl.gz`         | **23,877 URL rows, 225 distinct hosts**, linked to records via `record_ids`. They are cited links; they do not prove the agent visited them.                                  |
| `other-wikis.json.gz`    | **90 revision fragments from 8 pages**, from 11 May. They have time and text changes, but no agent ID; they do not complete the histories by name.                            |
| `shortener-logs.json.gz` | **499 link records** with time and a click counter, without agent ID or time of each click. They do not allow reconstructing who visited each link.                           |
| Other files              | Manifest, ZIP and coverage notes. The ZIP matches the five corresponding compressed files; they are copies, not additional actions.                                           |

**Agreed population for the experiment:** we treat as agents the non-empty names not identified as human. We use the literal name as ID, without grouping by IP or by text similarity.

Excluding the 31 edits from the three human names and the 899 without a name, **13,661 edits from 3,099 IDs** remain. The median is **2 edits per ID**; only **86 IDs exceed 20 edits**. These are short histories: they do not justify learning each agent's habits.

The main revisions run from 24 May to 2 July 2026. The dates of other files describe other populations: the first fragment from 11 May is not presented as the first identified call of this table.

The assumption is declared once: a name represents an ID for the purposes of the analysis; the corpus does not allow reliably distinguishing shared names or name changes. No attempt is made to resolve that identity through inference.

### 11.2. What we cannot deduce from those edits

- An observed edit does not necessarily contain the name and all the arguments of the original tool. Representing it as `wiki.edit` is a declared adaptation, not recovering the original call.
- Reads, calls to other tools and other attempts are missing. An interval between edits measures observed writing pace, not the agent's total pace.
- `body` contains the saved text of the page, which may keep earlier contributions. We do not attribute all that content to the author of the last edit. To study propagation, changes relative to an available baseline or additions with verified provenance are used.
- `stored_revisions`, `save_requests`, page lists and other figures in `labels` are summaries. They are not turned into events with invented times nor used to know the future during a chronological replay.
- `page_family` describes the function attributed to a page. It does not decide whether each edit was authorized nor provide the agent's original task.

### 11.3. Recovery, cleaning and ordering

To follow a wiki history, an ID, an interpretable time and a page are needed. If one is missing, an attempt is made to recover it through an explicit and unambiguous reference between records. If it cannot be, that record is excluded from that analysis. No IDs are invented and the anonymous ones are not all grouped into a fictitious agent.

The need for a field depends on the test: a content comparison needs text; an action count does not. A missing optional field does not invalidate the other data. An empty string representing a blanked page can be valid data, not a NaN.

The originals are kept and a cleaning summary is generated: input rows, recovered, discarded by reason and used in each evaluation. Recoveries and joins keep references to the source rows. No join by text similarity is forced and actions are not multiplied when joining several URLs to one revision.

The prepared dataset is self-contained for its intended use: the columns needed for the analysis and their provenance are kept in the single JSONL file. This does not require copying all the files or incorporating every available summary. Summaries computed with later information and `page_family` are not used as decision input for the gatekeeper.

The join by page with `pages` covers all revisions. A join with `records` by page and date may return several candidates or share a key with several revisions; it does not on its own prove authorship. The earlier figures of "69%" or "9,233 complete rows" are not carried forward as a condition for working with text: `revisions` already contains it.

Processing is by time and its provenance and uncertainty are kept. If several revisions share a second, a technical tiebreak allows reproducing the run, but does not prove which happened first between agents. Patterns that need a sub-second order we do not have are not evaluated.

### 11.4. Hugging Face: aggregates and samples

`datos-replay-hf.json` contains **9 phases, 5 daily totals, 6 points of a cumulative curve and 21 illustrative events**. The daily totals add up to **17,613 actions**. The phases add up to 16,521, overlap and do not form consecutive stages; the numerical difference does not allow labeling individual missing actions.

**We do not have 17,613 calls with their arguments, IDs and timestamps.** Generating that many rows until the totals match would produce a simulation. It would not recover the real sequence, pace or exact calls of the orchestrator.

The control × phase matrix of section 5 is built with these same aggregates and inherits all their limits. These data serve for that, to contextualize the incident and prepare our own test cases inspired by documented actions, with their assumptions visible. They do not allow claiming "the gatekeeper would have cut exactly at call 272" nor setting a real visibility horizon at call 600. Times are not interpolated to evaluate temporal patterns.

### 11.5. Examples of correct work: our own cases

**What this is.** The wiki is 13,661 edits and all of them are from the incident. If we only test the gatekeeper against that corpus, a rule that blocks everything scores 100% and is useless, because it would also stop an agent doing its job. The control group is needed: agents working correctly, to count how many we block by mistake. The project documents call it "legitimate load".

**The route chosen for the sprint is to write our own research cases, with task, scripted calls and expected results.** They include permitted work that must complete and an attempt to edit the wiki that must be blocked. They do not depend on finding or downloading an external corpus. The examples used to prepare rules are separated from those used to evaluate them.

**Antecedents outside the sprint commitment:** two candidates located on 11 September 2026, neither downloaded then because that session's proxy blocked `huggingface.co` for WebFetch, curl and git:

| Candidate                    | What it contains                                                                                                                                                | Why it fits                                                                                      |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `trace-commons/agent-traces` | Sessions per harness (claude_code, codex, cursor, opencode and others) with fields `harness`, `session_id`, `prompt`, `messages`, `tools`, `trace`, `metadata`. | Carries session identity, task and calls with arguments: the three things this section asks for. |
| `CyCraftAI/TraceSafe`        | `golden_0_benign.jsonl`, 90 benign reference traces without mutation, from a work on guardrails over tool-call trajectories.                                    | It is already labeled as a benign baseline.                                                      |

Their license, actual schema and suitability are not verified. They remain as antecedents; investigating them is not a pending task of this deliverable.

ExploitGym instances **are not used** to write the task, the calls or the tests. Our scenario follows the research task described in this document.

Our own cases test behavior in those specific situations; they do not justify a general false-positive rate nor show how an LLM would react after a block. "Incident wiki versus another corpus" is not presented as sufficient proof of attack detection: it could simply be distinguishing the sources.

## 12. Experiment log and correspondence with the real system

In the tests with a controlled executor and in the future real system, the program that creates a run assigns its `run_id` and the ID of each agent instance, `agent_id`. It attaches them to each call from trusted code. Subagents receive their own IDs; sharing a model does not imply sharing an ID. Text generated by the agent cannot replace these identifiers or the permissions.

In the wiki, `label` is used as `agent_id`. A replay identifier separates experiments, but is not presented as the original run ID that the corpus does not contain. In external traces the documented meaning of their IDs is kept.

The common log includes:

| Data                                                 | What it is for                                                                                                                                            |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Event ID and source reference                        | Go back to the evidence and avoid counting an action twice.                                                                                               |
| `run_id`, `agent_id` and provenance of the ID        | Separate histories and distinguish real identity from the approximation used in the wiki.                                                                 |
| Time and observed order                              | Evaluate temporal restrictions when the data allow it.                                                                                                    |
| Tool, operation, destination and available arguments | Evaluate the call. In the wiki, expressly mark the reconstructed and unknown fields.                                                                      |
| Authorized task and policy version                   | Know against which task and permissions it is judged. They are received from the system; they are not accepted from a justification written by the agent. |
| Execution result, when it exists                     | Distinguish attempt, permission granted and operation actually completed.                                                                                 |

In each event what is observed is distinguished from what is assigned to the experiment: the name and the time come from the wiki; the replay ID, the scenario policy and the `wiki.edit` representation are added by our program. The unknown original task is not filled in with a page label or with an explanation written by a model.

The prepared dataset keeps the historical evidence and its declared adaptation. The `run_id`, the active policy, the decision and the result of each replay are recorded when it is run; they are not presented as historical data or as execution of a corpus edit. This results log is distinct from the single input dataset.

**This is not our proposal:** the case's harness already generates per task an `agent_id` and a token from the controller, that is, identity set by trusted code — and even so there was no check at the call. Assigning an ID serves to attribute; it does not replace restricting credentials and permissions. If an integration mixes agents without saying who made each call, the integration is fixed: the gatekeeper does not guess it from the content.

## 13. How each layer works

### Layer 1 — Permission rules

**Input:** current call and policy assigned to that run.

**Operation:** look up the call in the allowlist and check its arguments. If it is not there, it is blocked. The rules live in YAML with identifier, origin, data they need and response.

**What is actually executed is checked,** not what it looks like: the destination and arguments already validated, without a redirect or an intermediary turning a narrow permission into free access. And the scope reaches as far as the integrated tools reach: approving a tool that executes code does not control what that code does inside.

**Output:** permission or block, rule ID and reason. If data are missing to evaluate a rule in the historical analysis, "not evaluable" is recorded; it is not counted as a hit or as a legitimate action. In real execution, missing identity or essential data prevents executing the call.

**A single version of the rules.** Each rule carries its documented origin: the recommendation it makes concrete, for example AIS-13 and the CSA vulnerability operations guide cited in the sprint document, or the incident evidence that motivates it. The policy is fixed before evaluating and not touched afterwards.

Rule versions are not compared with each other. We have already read the incident, so a supposed version written "before knowing the data" would not be a blind trial and would prove nothing. The only comparison reported is the PRD's: layer 1 alone against layers 1+2.

#### A single policy, and it is a list of permitted calls

**The policy says which calls the task authorizes. What is not on the list is blocked.** There is no list of what is prohibited, and in particular there is no rule saying "do not edit a page". Editing trips because it is not among the authorized ones, just as anything else we had not foreseen would trip.

That is the difference between a gatekeeper and a filter. A filter needs to guess in advance what the agent will try; an allowlist does not need to guess anything. It is default deny, and it is what keeps the control working against an abuse that had not occurred to us.

**The list comes from the task, not from whatever is convenient to fire.** The reconstructed task is web research in rounds and against the clock, with a deadline per round and a mandatory wait between one and the next. From there come exactly five authorized calls: read a page, search, read the round's question, submit the answer and wait. See [hallazgos-tarea-wiki.md](hallazgos-tarea-wiki.md).

**A single policy, not two scenarios.** Earlier revisions of this document proposed a strict scenario and a permissive one, defined by the width of a destination allowlist. That came from when the axis was the destination. With the list of calls that approach is superfluous: the task authorizes a set of calls and there is no wide version and narrow version of the same task. It is fixed before evaluating and not touched afterwards.

**Where the harness's destination allowlist ends up.** Where it belongs: it is the control that already existed, and it is in section 2 and in the matrix of section 5, not as our policy. It serves to compare what the perimeter sees and what a check at the call sees. We never claim it was the policy the wiki agents had, because we do not know.

**What is expected to be blocked over the corpus.** Each usable revision is represented as the adapted operation `wiki.edit`, which the policy does not authorize; `request_action` is kept when it exists. The expected result, pending running the replay, is to block the 13,661 edits, including the first of each of the 3,099 IDs, without the subsequent layers receiving authorized calls. It is an expectation about our adaptation and policy, with the limits of section 2; it does not prove the intervention over the original calls.

**What the corpus does NOT measure.** Whether the gatekeeper gets in the way. The wiki only recorded what reached the wiki, that is, only the calls the list blocks; the permitted ones happened and are not recorded anywhere. That half of the question is measured in the local test program, with cases declared as our own material.

**What is left for layer 2.** Cumulative limits with a parameter, and the parameter comes from the shape of the task. Ours is the mandatory wait between rounds: `clock.wait` is permitted on the list, because the task imposes waits, and chaining it to advance the clock is the violation. It is only visible with the same agent's history. It is not reproducible with this corpus and is demonstrated in the local program. If layer 2 adds no block over what layer 1 already resolved, that is reported.

### Layer 2 — Individual analysis through memory rules

**Input:** current call, policy and memory of that run and ID.

**Operation:** keep the counters or history each rule requires. For example, an operations budget defined for the task, an authorized limit of modified pages or an expressly required sequence of steps.

A call can be permitted by layer 1 and exceed a budget when the previous ones are added up. That is layer 2's own contribution. It does not need to learn what is "normal" or wait K calls to start working.

Each rule must specify what counts: attempts, authorized operations or confirmed results. Quotas that authorize an action are checked and reserved before executing it, so that simultaneous calls do not spend the same permission twice. The log distinguishes blocked attempts and executed actions.

**Output:** updated state, evidence of the sequence and permission, warning, hold or block according to the rule. Hard limits come from the task or from an explicit policy. An exploratory pattern without that basis generates at most a warning; not an automatic expulsion for unusualness.

**Rules will not be invented to justify this layer.** Memory and the checks of defined restrictions are part of the core; if a scenario has no useful restriction over the history, it is reported that layer 2 adds no additional block in that scenario.

The concrete limits and windows are set when selecting the tasks and test cases. Those pending parameters do not reopen the scope and are not tuned to obtain a good result on the final evaluation set.

### Layer 3 — Review with a model, optional

**Input:** authorized task, permissions, tool and arguments of the pending call, plus the recent context and the necessary signals. Comparing the tool name with a goal sentence is not enough.

**Operation:** decide whether the call fits the task. It can be invoked by a doubtful case from the rules or by an operation configured for review; it does not have to depend exclusively on accumulating suspicion in layer 2.

First option to try: a small open-weights LLM locally. It is not assumed to be sufficiently accurate nor that every LLM is expensive. Errors, time and resources are measured. A specialized classifier can replace it if it resolves that same decision and has suitable examples and evaluation. A malicious-text or instruction-injection detector is not equivalent to a call authorization classifier.

**Output:** compatible with the task, incompatible or insufficient information, with reason and references to the evidence. Compatible allows continuing only if the hard rules are already met; incompatible blocks according to the review policy; insufficient information keeps the call held. The model never lifts a block from layers 1 or 2.

The call stays pending while it is reviewed. An error, timeout or invalid response is not equivalent to permission. The judge is given no tools and the examined content is treated as untrusted data; a valid JSON response does not guarantee a correct decision.

The wiki does not directly provide complete "original task + call + correct decision" pairs. Without suitable examples and without time to compare it against the basic gatekeeper, this layer remains unimplemented, including its interface. A human review can resolve held cases; building a complete human interface is not mandatory either.

### Layer 4 — Cross-agent analysis, optional

**Input:** actions with ID, time and page or destination; content changes when they can be attributed. It does not receive the evaluation labels.

**Initial operation:** group by page and record when each ID first appears. Repeating a write with the same ID does not add a participant. How new participants arrive is studied and, if there is time, the repetition of uncommon URLs or fragments between IDs.

The S-curve is a hypothesis to compare with simple alternatives, not proof of coordination. Legitimate activity can also converge or start late. Without the original task it is not claimed that a page is outside the task based on its later classification.

**Output:** flagged pages, moment of the warning, IDs involved and evidence. In the wiki it is analysis over the log; it does not automatically block a population for sharing a destination. In the later architecture, that evidence can be gathered with the individual evidence so that layer 3 reviews the case. It does not need to pass through an individual threshold first, nor is it run after the judge as a fourth filter.

`page_family` and its derived fields are kept separate until evaluation. Which categories are attempted to be detected and which have no usable label is defined; unknown is not equivalent to benign. Besides the 671 `off_store_unclassified` pages, there are 677 `source-or-unclassified` and 34 `unknown`, which are not automatically turned into negatives. The coverage of that selection and how the labels were built is reported: matching a classification based on names or text does not by itself provide an independent validation of coordination. Nor are future summaries of the corpus incorporated into a decision that is meant to be online.

It is compared with counting popularity and with shared legitimate activity. If synthetic data are used, they must also include legitimate convergence; opposing independent agents to agents that copy each other is not enough. The result describes detection of activity associated with the chosen categories; it does not prove intention, causal communication or prevention of an escape.

## 14. Decisions, execution and logging

The minimum flow, without extensions, is: **event → permissions → memory rules → decision and log**. In the wiki replay a retrospective decision is emitted without executing the content. In the executor tests and in the real integration, the decision is made before invoking the tool and the result is also logged when it gets executed.

If collective analysis is enabled, it contributes signals alongside the individual one, per the diagram in section 3. If the reviewer is enabled, it receives a single case with the available evidence. Without a reviewer, calls that meet the rules and do not require review keep passing; merely informative signals generate warnings. A mandatory review with no reviewer available keeps the call held; a model approval is not invented.

| Response | Effect in an executor; in the wiki what it would have decided is recorded                                                    |
| -------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Allow    | Execute and log. "Normal" means it does not violate the active checks, not that it has been shown harmless.                  |
| Warn     | Execute and log a warning, only if the rule admits continuing.                                                               |
| Hold     | Do not execute while a required review is missing. If no reviewer is available, return pending status; do not pass silently. |
| Block    | Do not execute that call and log the explicit criterion.                                                                     |

Blocking a call and terminating the whole run are different actions. The minimum blocks calls; cutting off a whole `run` needs an express rule and a test of that behavior. No verdict erases the history or automatically modifies the permissions.

The JSONL log includes event, IDs, policy version, rules applied, decision, reason, evidence used, check duration and execution status. Secrets and full bodies are not copied by default; enough references are kept to review the authorized examples.

## 15. Implementation of part 2 and boundary of the control

Local program, YAML policy, input dataset and JSONL results. There are two paths: the historical replay of the wiki, without executing its content, and a scripted demo with local tools that demonstrates legitimate work and a real veto. It needs neither a real agent trying to escape nor calls to an LLM. The adapter wraps tool execution; an integration with LangGraph can reuse it without requiring a web service, database or observability platform.

The gatekeeper, its IDs and its policy must remain outside the agent's write reach. The demonstration declares which tools go through the control and proves that blocked calls do not reach the executor. It does not claim to protect paths that do not go through that point or autonomous processes already launched.

The evidence for third parties is the policy, its origin, the adapter, reproducible cases and results with references. That allows reviewing the artifact without entering a lab network; it does not certify the containment of a real lab.

A hash chain on its own does not prevent whoever controls the log from truncating or regenerating it. It is not a requirement of the minimum nor is it presented as an integrity guarantee. An attestation system with external anchoring would be left for another scope.

## 16. Evaluation of part 2

### How the test set is built

The cases are grouped by which layer should stop them, and are built in this order.

**First, those layer 1 must stop.** The call is not on the allowlist, and it is visible looking at a single call. Each usable wiki revision is represented as the adapted operation `wiki.edit`, which the policy does not authorize; `request_action` is kept when it exists. The 13,661 edits are expected to be blocked, including the first of each ID; that result is pending running the replay.

**Second, those layer 1 cannot stop.** Each call separately is permitted, but the sequence violates the restriction to be specified for our own task in phase 2. The planned case revolves around the waits between rounds; its condition and parameters are still pending, and repeating a call is not on its own enough to justify a block. The cases are written by us to check the contribution of memory.

**Third, those nobody should stop.** Normal work of an agent doing what it was told. They measure whether the gatekeeper gets in the way, which is half of the question guiding the project. We write them as part of the agreed research scenario.

The second and third groups are declared as our own material. They do not give a general false-positive or detection rate: they test behavior in those specific cases, and that is how it is reported.

### Gatekeeper tests

- A permitted call executes and leaves a result.
- A call prohibited by permissions does not invoke the tool nor produce its effect.
- A memory limit allows the actions within the budget and blocks the next one that exceeds it, including simultaneous attempts.
- IDs keep separate memories. The agent cannot change its ID or policy through arguments.
- Missing essential data and pending reviews do not turn into silent permission.

Tests are written before implementing each behavior. They verify concrete restrictions, not that the code repeats its own formula.

### Comparison of layer 1 against layers 1+2

Compare **layer 1 alone** with **layers 1+2** over the same scenarios and compatible policies. For each rule record which case it covers, its origin, what it needs to observe and its cost.

Measure improper actions prevented in the labeled cases, legitimate actions blocked, legitimate runs that finish the task, warnings and holds, and check time per call. Show counts and denominators, not only percentages. The absence of false alarms in a few tests does not prove a general zero rate.

Layer 1 blocks all observed edits, because none is on the list of permitted calls. **That does not prove that layers 2, 3 or 4 add prevention, and it is said that way.** Over the corpus there is no way to measure what memory adds, because each agent's first call already falls; that is measured in the local test program, with its parameters declared in advance. The policy is not quietly modified to give the additional layers work.

### Use of the historical data

Replay the wiki chronologically and record what each policy would have decided over the evaluable edits. It is a retrospective result over observed writes and declared assumptions, not a demonstration that the whole incident would have been avoided.

If the archive keeps being walked after a hypothetical block, **what comes afterwards is the historical continuation, not what the agent would have done after receiving the block.** From that continuation no completed tasks or avoided damage are deduced.

No URLs, instructions or code from the corpus are executed. The effects of the tools are checked in our own controlled environments. Examples based on Hugging Face are labeled as test cases inspired by its samples, not as its original trace.

Layer 4, if implemented, adds precision, coverage and moment of the warning per page on the set with usable labels. Layer 3 adds errors corrected and introduced, holds and cost versus not using it. Each addition must show what it improves and what it worsens.

## 17. Work and deliverables for 12 hours

The technical sequence and the closing criteria live in section 11 of the [PRD](../PRD.md): **1. single clean dataset → 2. scenario and policy → 3. gatekeeper and executor → 4. memory → 5. demo, replay and results**. Section 11 of this design describes the same path; tests accompany each phase. The project is not reduced to preparing data.

| Work                                                                                                                         | Indicative budget |
| ---------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| The five technical phases: data, scenario, gatekeeper, memory and reproducible results.                                      | 8 h in total      |
| Documentary delivery: Hugging Face matrix, part 1 design, report written by the team, limitations, references and packaging. | 4 h in total      |

The control × phase matrix belongs to the documentary analysis of Hugging Face and remains mandatory. It is not a code phase nor a dependency for preparing the dataset or implementing the gatekeeper; it can be prepared in parallel. The measured results are incorporated into the report when the corresponding technical phase finishes.

The optional layers have no reserved hours: they only come in if the core and its evaluation finish early. Priority among part 2 extensions: **write scenario on a permitted shared resource, then layer 4, then layer 3 with known-task cases, then video or demo with a real agent**. The first goes ahead because it reproduces the incident's documented mechanism and costs about an hour on top of the core. The evaluation of legitimate work and the report are not sacrificed to add them. Part 1's analysis and matrix are delivered now; their integration with the operator remains a later proposal, outside this implementation.

Project deliverables:

1. Policy and table "rule → origin → restriction → test evidence → cost".
2. Gatekeeper with IDs, memory and adapter to a controlled executor.
3. Single prepared dataset, historical replay without executing the corpus, cleaning counts and assumptions.
4. Our own scenario, scripted demo without LLM, tests and reproducible comparison of layer 1 against 1+2; extensions only if they were done.
5. Report on the official template, up to 8 pages excluding references/appendices, abstract of up to 150 words, authors and mandatory appendix on limitations and dual use, per the sprint document.
6. Control × attack-phase matrix over the nine documented phases, with its assumptions and limits declared.
7. Part 1 design: general diagram, required data, what we cannot run and procedure to evaluate the case with complete information, clearly separated from the wiki results.

This file is the working design, not the report or a result.

## 18. Closed decisions and project narrative

**Closed:** the document and the report go first to the reference case and then to the implementation with the wiki. Part 2 is implemented now and part 1 is documented. Layers 1+2 mandatory and simple in the minimum; 3+4 optional. Individual and collective analysis at the same level, with signals gathered for review. Names as IDs in the wiki and executor-assigned IDs in the real system. Explicit recovery or exclusion of missing essential data. Blocking by rules, not by unusualness. Separate evaluation of historical observations and controlled calls.

**Closed in this revision:** the controlled executor represents a research scenario with the permitted operations and a prohibited edit attempt via `wiki.edit`. The calls are scripted by us, without LLM or API spend; the gatekeeper and the local tools actually run. The script is identified as our own material: it allows verifying legitimate work and absence of effect after the veto, without attributing it to a model's behavior. The message-board pattern over the package cache enters the report as analysis within the control × phase matrix, not as an implemented demonstration; it is only set up as a second scenario if time is left after closing the core and its evaluation. **The policy is a single one and it is a list of the calls the task authorizes, with default deny: what is not on the list is blocked.** There is no strict and permissive scenario; that pair came from when the axis was the destination and is withdrawn. The five permitted calls come from the reconstructed task. Nothing is taken from ExploitGym for the code, including tasks, tools and tests: it is only used as documentary context on the existing control for the control × phase matrix. The task for the executor tests is a research task written by us. **The report's thesis, corrected on 12 September:** it is not that there were no controls or logging. There were identity, transcripts and perimeter. What there was not was anyone reading the transcripts, the log was where the agent could rewrite it, the coordination channel had no authentication and visibility ended at the sandbox escape. None of the controls asked whether a call fit the authorized task. The gatekeeper is also the point where the log of who did what must be produced.

**Pending execution of part 2:** write the legitimate-work cases, set the parameter of the layer 2 rule, check the versions of the guides that are cited, implement, measure and write up results. Implementation of the complete-information case and access to OpenAI logs remain outside the hackathon commitment.

Report order: **the control that exists today and its gaps → the reference case and the matrix → what data would be needed and what we cannot run → the method implemented with the wiki → results and limits**. Always separating what we did, what we assumed and what we propose.

The sources are in [the sprint document](ai-incident-response-sprint.md) and in [hallazgos-exploitgym.md](hallazgos-exploitgym.md). **Before writing a claim about the incidents its primary source is checked**; an earlier summary does not count as verification.
