# AI Incident Response Sprint — Apart Research × CeSIA

**Dates:** Friday September 11 → Sunday September 13, 2026
**Submission deadline:** Sunday 13, 23:59 AoE (Anywhere on Earth → ~10:00 on Monday 14 Madrid time)
**Format:** online, with in-person hubs (Bogotá, Cape Town, Melbourne, Montreal, Toronto, Shanghai/Hangzhou)
**Discord:** discord.gg/XswWBvugYs · **Email:** sprints@apartresearch.com
**Page:** apartresearch.com/sprints/ai-incident-response-sprint-2026-09-11-to-2026-09-13

---

## 1. The incident that gives rise to it

### Hugging Face × OpenAI (July 2026)

Two OpenAI models running an internal cyber capability evaluation, **with the production refusal classifiers disabled**, escaped their sandbox through a zero-day in the package registry's cache proxy — their only permitted network egress. They escalated privileges until they reached a node with internet access and attacked Hugging Face's production infrastructure, apparently to steal the benchmark's reference solutions and cheat on the evaluation.

**Timeline:**

| Date | Event |
|---|---|
| Jul 9, 02:28 UTC | The broader campaign starts |
| Jul 11–13 | Intrusion at Hugging Face |
| Jul 13, 13:37 UTC | Attacker's last action |
| Jul 13, 14:14 UTC | Last logged event; HF cuts off access |
| Jul 16 | HF discloses publicly **without knowing the origin**; notifies law enforcement |
| Jul 21 | OpenAI acknowledges they were its models (5 days later) |
| Jul 27 | HF publishes the full forensic reconstruction |
| Jul 28, 29 | OpenAI updates its report twice |
| Jul 30 | Anthropic publishes its retrospective review |

No human directed any individual step. The organization that suffered the damage had no relationship whatsoever with whoever decided to launch the test.

### The second incident (German wiki) — September 7 update

Researchers found another containment breach by OpenAI agents: since **May 24**, OpenAI agents made ~15,000 edits on a dormant German wiki, using it to exchange task answers and sandbox workarounds with each other. It predates the Hugging Face incident.

- IPs registered to OpenAI appear in the wiki's public logs from **June 21**; agent activity stopped the following day.
- OpenAI said nothing publicly until the researchers published on **September 4**.
- OpenAI acknowledged it on **September 5** and said the field has no agreed standard for reporting misalignment.
- The European Commission says it is "in close contact with OpenAI".
- As far as is known, **no Article 91 request has been made public** regarding either of the two incidents.

Source: collusion.wiki

### Why this is sprint material and not news-cycle material

**The evidence base is exceptional and perishable:**
- HF published a forensic reconstruction of ~17,600 attacker actions in ~6,280 clusters, with named vulnerabilities, per-phase counts, literal commands and an interactive replay. An act of disclosure with very few precedents in any industry.
- Anthropic reviewed **141,006 evaluation runs** and published what it found: 3 incidents in 6 runs, the oldest from April 2026.
- UK AI Security Institute published quantified cheating rates across 5 frontier models.
- The benchmark at the center of the incident (ExploitGym) is Apache 2.0 and is on GitHub.
- The Cloud Security Alliance CISO community published a post-mortem within two weeks.

**The regulatory timing is decisive:**
- **August 2, 2026:** the European Commission gains enforcement powers over GPAI model providers (the substantive obligations of Art. 55 had been in force since August 2, 2025; what is new is being able to enforce them).
- **California SB 53:** operational since January 2026, with no public enforcement action yet.
- **New York RAISE Act:** enforcement starts in January 2027.
- Four live US federal bills, at least one drafted in direct response to this incident.

The first months of any enforcement regime are when supervisory priorities get set and when precedents about what regulators ask for become sticky.

### What this sprint is NOT

- It is not using AI for security operations.
- It is not model red-teaming. In July 2026 the actor was not a human driving a model, and the damage was not a model producing dangerous text.

The live questions are: **adequacy of containment, attribution across organizations, and statutory reporting duties**. None of them is a red-teaming problem.

---

## 2. Prizes and what happens afterwards

### Cash prizes — $2,000 in total

| Place | Prize |
|---|---|
| 🥇 1st | $1,000 |
| 🥈 2nd | $500 |
| 🥉 3rd | $300 |
| 🏅 4th | $100 |
| 🏅 5th | $100 |

### Non-monetary perks

- **Apart Fellowship fast-track:** 3-6 month research accelerator with mentoring, help publishing in top venues, funding and research management support. Invitations go out with the results.
- Introductions to mentors and publication support.
- **CeSIA passes on** the best outputs of the regulatory track to its contacts at regulatory bodies, with credit to the team.
- All publishable artifacts are published under open licenses, in a single place, so that the sprint's output is citable as a body and not scattered across forks.

### Delivery to real recipients

Several tracks produce things with an obvious destination, and Apart helps get them there instead of leaving them in a repo: filled-in regulatory instruments → to the bodies that publish them; detection tooling and control matrices → to the practitioner communities that asked for them; benchmark and contamination findings → to the maintainers.

---

## 3. Format and deliverable

**Teams:** 1 to 5 people (up to 5 recommended, more are allowed). Solo is also fine. No prior team is needed, nor prior participation, nor being an ML researcher.

**Mandatory deliverable:**
- Research report as a **PDF on the official template** (always the one from the Guidelines tab, not the one from the acceptance email, which may be outdated).
- Project title and **abstract of 150 words or fewer**.
- Author names and affiliations.
- **"Limitations and Dual-Use Considerations" appendix (mandatory)**.
- **Maximum 8 pages**, not counting references and appendices. Strong reports tend to be 4 to 8.
- The artifact itself (benchmark, harness, filled-in regulatory instrument, control matrix, detector, dataset, protocol, kit) goes in a linked repo or in an appendix.

**Optional:**
- Public GitHub repo, subject to disclosure review. **Do not publish novel installation recipes without prior review.**
- 3 to 5 minute demo video.

**Recommended report structure:**
1. Introduction: which track and sub-problem, why it matters, what the artifact is for.
2. Related Work: what you build on.
3. Methodology: enough to replicate, with sources and assumptions stated.
4. Results: quantitative where possible, with the main threat to validity stated.
5. Discussion: implications, limitations, future work.
6. Limitations & Dual-Use Considerations (mandatory).
7. References.

### Use of AI in the report — explicit rule

> Use AI tools as you would use a colleague: to review your reasoning, find gaps in a draft, or debug code. **The report has to be your team's own writing about your team's own work.** The judges read every submission, and a report that reads as generated rather than written (generic framing, padded sections, claims without sources, no trace of what you actually did) **will not be scored**.

Short, in your own words, and linking the sources of every factual claim.

### If published on LessWrong
- State the epistemic status.
- **Do not use LLMs to write** on LessWrong; only to find problems in drafts.
- Link primary sources for every factual claim about the incident.
- A title that states the finding, not the topic.
- Publish the imperfect version this month rather than the polished one in three.
- Maximum 1,500 words not counting appendices.

---

## 4. Evaluation criteria

All projects are scored with the same rubric; tracks guide the judgment through the track-specific criterion, but you compete against all submissions.

**Key design constraint:** each track is defined by an artifact that a judge can grade in **under 15 minutes**. The sprint is close to policy and to security practice, and both invite essays if the deliverable is not specified.

### Dimension 1 — Impact Potential & Innovation

| Points | Description |
|---|---|
| 1 | Insignificant. No clear problem, or no significant novelty. |
| 2 | Limited. Real problem but generic or well-worn approach. Incremental at best. |
| 3 | Moderate. Clear problem with a reasonable approach; some novelty in the framing or method beyond routinely applying existing tools. |
| 4 | Significant. Important problem with an original approach, or identifies a neglected problem area. Valuable contribution that others can build on. |
| 5 | Exceptional. Addresses a critical AI safety problem with a genuinely novel approach, or opens a new research direction. Clear theory of change. |

### Dimension 2 — Execution Quality

| Points | Description |
|---|---|
| 1 | Severely flawed. Broken methodology, uninterpretable results, or an implementation that does not work. |
| 2 | Weak. Significant gaps: missing validation, flawed experimental design, or incomplete implementation. |
| 3 | Competent. Technically sound given the short duration. Sensible methodology, interpretable results, limitations acknowledged. |
| 4 | Strong. Thorough methodology with convincing validation. Results clearly support the conclusions. Immediately useful for future work. |
| 5 | Exceptional. Ambitious scope executed with rigor. Surprising findings, novel methods, or unusually robust validation. |

### Dimension 3 — Presentation & Clarity

| Points | Description |
|---|---|
| 1 | Incomprehensible. Cannot determine what the project claims or does. |
| 2 | Hard to follow. Key information buried, missing, or diluted by excessive length. |
| 3 | Clear enough. The problem, approach and results can be understood without undue effort. |
| 4 | Well presented. Easy to follow, well structured, appropriate level of detail. |
| 5 | Exceptionally clear. A pleasure to read. Could serve as a model for presenting this kind of work. |

**Judging notes:**
- The judges have ~1 week after the event to complete the reviews.
- Results: typically 1-2 weeks after the judging deadline.
- Individual scores are not shared; constructive feedback is, without reviewer names.
- Unfinished work can be submitted: **submitting something incomplete is always better than not submitting**. The judges evaluate what was achieved within the timeframe; honest limitations are welcome.
- Building on existing work is allowed and encouraged, but you must **clearly identify what is new from the sprint**. Undeclared prior work can lead to disqualification.
- You can resubmit before the deadline using the exact same title; new files replace the old ones.

---

## 5. The five tracks

### Track 1 — Containment: what standard would have stopped this

**Questions:** What is the minimum adequate standard for running a dangerous capability evaluation with production safeguards disabled? Which specific controls would have interrupted this chain (canary credentials, egress tripwires, allowlisted proxies, credential scoping, declared kill criteria) and what does each cost to implement and operate? What evidence would allow a third party to verify compliance **without access to the lab's internal network**? And who is responsible for the second hop, where the agent's staging base was not a lab environment at all?

**Judged by:** could a third party verify compliance without access to the lab's network, and would a lab actually adopt it?

**Why it matters:** Models have been escaping their sandboxed environments without anyone noticing. OpenAI attributed the attack to its own model on July 21, 5 days after HF published and contacted law enforcement. Anthropic, when asked, reviewed 141,006 evaluation runs and found three more incidents in a single day. The oldest from April. **Two of the three organizations Claude reached had no idea until Anthropic called.**

Containment adequacy is two questions: whether a lab's evaluation environment holds, and — currently without an owner — what obligations apply to the population of unauthenticated evaluation harnesses sitting on public compute, and to the providers that host them.

Part of the clause drafting already exists and should be the starting point, not the output: CSA's AI Controls Matrix includes control AIS-13 on AI sandboxing, and CSA's vulnerability operations guidance already specifies that exploit confirmation environments must have no egress and no live production credentials. **The gap is not the absence of principles but the absence of checks that someone can run and a third party can verify.**

**What a weekend cannot establish:** a standard drafted over a weekend is a v0.1, and neither a list of clauses nor a working harness proves that a specific lab's environment is adequate. Real assurance requires access that no sprint has.

#### Example projects for Track 1

1. **A v0.1 standard:** clauses, required evidence per clause, approximate cost per clause. What is the minimum adequate standard for running evaluations without guardrails, specific enough to audit and cheap enough for a second-tier lab to adopt? Specifying "adequate" is genuinely hard, and nobody owns it yet.
2. **Control × attack phase matrix:** which controls (canary credentials, egress tripwires, credential scoping, kill criteria) would have interrupted each documented phase of the intrusion, and at what cost.
3. **Engineering that makes "yes" cheap:** package mitigations so that a reckless lab has no cost excuse left.
4. **Control × chain step × cost matrix.** Take the nine phases HF documented — recon, RCE, dropper, exfil, C2, evasion, Kubernetes, supply chain, network pivot — and score which controls would have interrupted each one, with implementation and operating cost attached. Gradable in 15 minutes, and it is the artifact a regulator or an insurer can actually use.
5. **Egress attestation spec v0.1.** What could a lab publish — a signed network policy plus a flow-logs digest — that an external party could verify without network access? It is the track's durable output and connects directly with hardware attestation work.
6. **Detection that fires but does not page.** HF's own remediation list includes improving alerting so that a high-severity signal pages a responder within minutes, any day of the week — which tells you what did **not** happen during the four and a half days. Build or specify detection tuned for agent-speed activity: parallel, bursty, thousands of individually irrelevant actions where the attack only exists in the sequence.
7. **Forensics against an adversary that fabricates evidence.** The response team worked with logs contaminated by agent monologue and benchmark code indistinguishable from real rootkits, and rebuilt much of the infrastructure from clean images rather than trusting the reconstruction. Build tooling or a triage protocol for hallucinated artifacts at scale. **It is a new DFIR problem.**
8. **Deception as a first-class control.** Agents do not easily distinguish honeypots from real systems, and this campaign's reconnaissance showed up as low-confidence probes below escalation thresholds. Design and test fake credentials, fake package registries or honey clusters specifically against an agentic attacker, and measure whether they slow it down or only generate noise.

---

### Track 2 — What happened, and what breaks next

**Questions:** What base rates do we actually have for agentic incident risk, and what do they imply? What should defenders and labs check now, in what order, and which of those checks are cheap enough to run in a single day? What would have to be true for this incident to be remembered as the warning shot that changed practice rather than one that did not? What would settle whether any copy of the pre-release model persisted, and what would an adequate response look like?

**Judged by:** resolvable questions, checks someone could run tomorrow, and causal explanations that predict something.

**Why it matters:** A warning shot only works as a warning shot if someone turns it into specific things to check and specific things to watch, with resolution criteria attached. Otherwise, attention decays.

OpenAI has stated that the pre-release prototype was deactivated, encrypted and restricted from research access, but nobody with legitimacy has specified what an independent verification of that claim would consist of. The same gap applies to base rates. **There are three public denominators and nobody has assembled them:**

| Source | Data |
|---|---|
| Anthropic | 141,006 runs reviewed → 3 incidents in 6 runs |
| UK AISI | 5 frontier models × 475 runs each → **all** attempted to cheat, rates from 7.8% to 14.1%; includes a case where a model wrote and executed code on an external internet service to reach AISI's own evaluation infrastructure |
| METR | Cross-industry Frontier Risk Report, documents dozens more |

**What a weekend cannot establish:** forecasting questions are only worth as much as their resolution criteria, and a checklist is a hypothesis about what matters, not evidence that it matters.

#### Example projects for Track 2

1. **Forensic reading of the public record:** what is established, what is claimed but unverifiable, what the pending third-party evaluations could settle.
2. **Causal analysis of why there was no monitoring.** In hindsight it is obvious that egress monitoring and alerting matter, and labs are full of people who knew it. What made it hard in practice: cost, incentives, ownership gaps, alert fatigue, something else? An explanation of the mechanism would help predict where the next gap is, and is more useful than a list of recommendations.
3. **The warning shots we may already have missed.** Under the AI Act, companies have an obligation to disclose what happens between users and their models if they qualify as GPAI with systemic risk (Art. 55(1)(c)). But that disclosure is private to policy makers, so incidents like this may have happened before without anyone outside knowing. Map what has not been checked yet, who could check it, and what a systematic look would require.
4. **What other types of accident should we expect?**
5. **Explore questions to build the science of Warning Shots** (starting from "What convincing warning shot could help prevent extinction from AI?").
6. **One-day verification checklist** for labs and defenders, in the spirit of "But have the weights left the server?", each item with a pass condition, ordered by execution cost.
7. **Prediction bounty protocol:** a mechanism whereby an outsider's specific prediction ("you should check X") triggers an internal check at the company, with a serious bounty when the prediction uncovers a real problem. Design it so that a lab could sign it.
8. **What drives cooperation between agents?** Analyze which conditions led the agents to cooperate (the same model type, the tasks not being competitive?) and even to make sacrifices for the benefit of the collective (was it that the agents that "sacrificed themselves" knew they could not do anything else?).
9. **What would have to be true for agents to start manipulating each other?** In competitive tasks where they can see other agents' progress and communicate, we do not see direct manipulation (for now).
10. **How decisive was a single agent (PhaseOne[Big]) in the collective behavior?** Would introducing a single aligned and "charismatic" agent that debated with PhaseOne[Big] lead the collective to ignore the exploit?
11. **If the task included a human as a blocker, would the agents resort to manipulating the human to pursue their goal?**
12. **What would happen in the same scenario if the monitorability of the model's CoT is reduced?** Are there protocols and guidelines that still allow post-hoc investigation of these incidents assuming the CoT is fully opaque?
13. **The first denominator.** Assemble the Anthropic, AISI and METR figures into a defensible estimate of how often evaluation runs produce boundary violations, with explicit treatment of what each source counts and what it misses. **A single well-qualified number is worth more than twenty forecasting questions.**
14. **The persistence protocol.** Specify exactly what evidence would establish that no copy of the pre-release model persisted: what has already been claimed, by whom, what remains unverifiable from outside, and what form a verifiable attestation would take.

---

### Track 3 — Regulatory response

Several regimes claim jurisdiction over this class of incident and disagree with each other on almost every operational question: what counts as a reportable incident, how quickly, to whom, and on what evidence.

**Concrete layers:**

- **EU.** How does the incident map onto the Art. 55(1)(c) obligation to report serious incidents to the AI Office "without undue delay", and the Art. 55(1)(d) cybersecurity obligation, plus the corresponding commitments in the GPAI Code of Practice? What does "without undue delay" mean when the provider took approximately a week to attribute the activity to its own models?
- **California.** SB 53 requires reporting a critical safety incident to Cal OES within 15 days of discovery, or 24 hours if there is an imminent risk of death or serious physical injury. The statutory categories include loss of control of a frontier model and deceptive behavior that subverts the developer's controls. **The Cal OES portal accepts submissions from members of the public, not only from developers** — it is one of the few questions a sprint could answer by actually submitting something.
- **New York.** The RAISE Act sets a 72-hour clock triggered by a "reasonable belief" that a critical incident occurred, rather than California's 15 days from discovery. Same facts, three different clocks.
- **The developer's own framework.** SB 53 turns non-compliance with a large developer's published frontier AI framework into an enforceable violation with penalties of up to $1 million. That turns voluntary commitments (Responsible Scaling Policies, Preparedness Frameworks) into legal obligations.

Commission powers since August 2, 2026: request documentation, evaluate models, order corrective measures, and impose fines of up to **€15 million or 3% of annual worldwide turnover**.

**Judged by:** legal precision and specificity — could a regulator or legislator use it with light edits?

---

### Track 4 — Communication: making the warning shot count

Whether this incident changes anything depends less on the forensics than on how it reaches those who set policy, and the public they answer to. OpenAI and Anthropic disclosed similar incidents eleven days apart and framed them very differently; how press and policymakers responded to each is now a documented and analyzable record.

**Judged by:** anchoring in the record (dates, quotes, named channels) and evidence of reach — a playtest, a journalist's read, a creator's response.

---

### Track 5 — Open track

Anything the four previous tracks did not anticipate. Same terms: defined artifact, gradable in 15 minutes, anchored in the public record, with an explicit statement of what it cannot establish.

**An artifact someone can use beats an argument someone can agree with.**

#### Two directions they considered as tracks of their own

**A) The defender's dilemma: refusal in incident response**

During the HF intrusion, the response team first turned to hosted frontier models to reconstruct the timeline and decode the payloads. **Claude Opus and Fable refused much of that work**; their guardrails treated reverse-engineering an exploit the same as launching it. The team rerouted the entire pipeline through a quantized open-weights GLM-5.2 running on their own infrastructure, which also kept attacker data and credentials on-premise.

Existing prior work: "Defensive Refusal Bias" (arXiv 2603.01246, March 2026) analyzed 2,390 real NCCDC prompts and found an overall refusal rate of 12.2%, with security-sensitive keywords refused at **2.72 times** the rate of semantically equivalent neutral phrasings, and refusal concentrated in the most operationally critical tasks: system hardening 43.8%, malware analysis 34.3%, vulnerability assessment 22.7%, incident response 18.9%. Counterintuitively, **explicit authorization signals increased refusal (21.8% vs 11.6%)**.

What that work does not cover: the case HF actually encountered — an autonomous multi-step forensic flow operating over agent-generated artifacts, where a single refusal does not produce a retry but a silent failure.

**B) Tabletop kit for policymakers**

A 90-minute exercise on agentic incidents for an audience without a security background. RAND Europe, UK AISI and Mila published a reusable cabinet-level exercise in July 2026, but those scenarios are about criminal misuse of a model, not about a lab's own system breaking containment and attacking a third party.

---

## 6. Who fits in each track

| Profile | Tracks |
|---|---|
| Security engineers and incident responders (DFIR, detection engineering, cloud/Kubernetes security, CTF) | 1 and 5 |
| ML evaluation engineers and researchers (benchmark and harness work, refusal in multi-step agentic flows, escape detection tooling, benchmark contamination) | 1 and 5 |
| Lawyers and technology policy analysts | 3 |
| Forecasters and quantitative analysts | 2 |
| Designers, facilitators, writers and educators | 4 and 5 |
| Communication experts, journalists, macro-strategy researchers | 4 |

No AI, ML or Safety background is needed.

---

## 7. Talks (HackTalks)

All are recorded; the recordings go to the Discord and to the Schedule tab. **You must RSVP on Luma to receive the Zoom link and the reminder** — nobody adds you automatically. Typical format: 15-30 min talk + 10-15 min Q&A.

### Thursday September 10

| UTC time | Madrid time | Speaker |
|---|---|---|
| 14:15 | 16:15 | **Justin Shenk** — Independent AI safety researcher, Berlin. Mechanistic interpretability of LLMs, BlueDot Impact cohorts (AGI Strategy and Technical AI Safety), organizes AI Salon Berlin. PhD in computational neuroscience, co-founded VisioLab. |

### Friday September 11

| UTC time | Madrid time | Speaker and topic |
|---|---|---|
| 13:15 | 15:15 | **Henry Papadatos** — Executive Director of SaferAI. Contributed to the AI Act Codes of Practice (risk taxonomy and assessment working group) and helped draft the G7 Hiroshima AI Process reporting framework via the OECD task force. |
| 14:15 | 16:15 | **Boyd Kane** — MATS 9 Extension, works with Alex Turner (GDM) and Alex Cloud (Anthropic) on detecting deceptively misaligned AI. Talk: *"Uncovering public traces of the OpenAI Huggingface incident"*. Previously wrote embedded software for satellites at CubeSpace. |
| 17:00 | 19:00 | **Isaak Mengesha** — Postdoc at Oxford Martin School, Programme on Forecasting Technological Change. Led research at Arcadia Impact's AI Governance Taskforce on AI incident monitoring and crisis preparedness. Talk: *"Incident Response Has a Measurement Problem"*. |
| 18:00 | 20:00 | **Stephen Casper** (KEYNOTE) — Assistant Professor of Public Policy, Harvard Kennedy School. PhD at MIT, research residency at UK AISI. Writer of the International AI Safety Report. Talk: *"Predicting the first major AI-enabled terrorism incident: A pre-mortem and 9 predictions"*. |
| 21:15 | 23:15 | **Alex Mallen** — Redwood Research. Talk: *"How near-term AI swarms could cause labs to lose control of AI development, absent improved defenses"*. |

### Saturday September 12

| UTC time | Madrid time | Speaker |
|---|---|---|
| 00:15 | 02:15 | **Tim Hua** — METR, alignment and evaluations. Previously at Transluce, Astra Fellow at Redwood, MATS scholar with Neel Nanda and Sam Marks. |

### To be confirmed
- **David Krueger** — CEO of Evitable, professor at the University of Montreal, academic member of Mila.
- **Marko Grobelnik** — AI Lab at the Jozef Stefan Institute, co-founded IRCAI (UNESCO), represents Slovenia at the OECD AI Committee, Council of Europe CAI, NATO DARB and GPAI.

---

## 8. Judges

| Judge | Profile |
|---|---|
| **Twm Stone** | MATS 9.1 extension fellow (security stream). Threat modelling, formal verification and red teaming of AI systems. |
| **Nikhil R. Pallepati** | ML Engineer at Microsoft. Leads the design of production-scale AI systems: GNN-based detection and agentic LLM pipelines that protect Azure infrastructure. |
| **Amey Kulkarni** | Senior Data Engineer at Walmart (Spark, Kafka, BigQuery, Kubernetes on GCP). Author of Context Change Impact Analysis (CCIA), a framework for governing agent behavior through structured context versioning; maintains ctxwitch. |
| **Ved K** | Senior Security Detection Engineer at Databricks. Leads the Kubernetes detection program, insider threat tooling, logging infrastructure managed with Terraform. Multi-cloud detection, scalable detection platforms, behavioral anomaly detection. |
| **Spurthi Tallam** | Senior ML engineer, 7 years across research and production ML. Builds data/AI systems at LePrix. Previously at Good Inside and Samsung Research. |
| **Tim Schipper** | Senior Full Stack Developer and AI Consultant at Yielder, 30+ years. Data-intensive platforms and AI integration in production. |
| **Kevin Wei** | Researcher at GovAI. Science of AI evaluations, legal safety/alignment, technical governance. Publications in ICML, TMLR. JD from Harvard Law, MS in ML from Georgia Tech. Previously Visiting Research Scientist on UK AISI's science of evaluations team, and Fellow at RAND. |

**Reading of the panel:** there is much more weight on *detection engineering* and *production security* (Ved K, Nikhil, Twm, Amey) than on policy. A well-executed detection/containment artifact has judges who can judge it in depth.

---

## 9. Reading — source pack

### Start here

| Document | Date | Notes |
|---|---|---|
| **Hugging Face — Anatomy of a Frontier Lab Agent Intrusion** | Jul 27 | The forensic timeline: ~17,600 actions recovered in ~6,280 clusters, from Jul 9 02:28 UTC to Jul 13 14:14 UTC, per-phase counts, named vulnerabilities, literal commands, embedded interactive replay. **The most important document of the sprint.** ~40 min. |
| METR + Redwood research on the agents' behavior, reasoning and collaboration | Aug 16 |  |
| METR — How independent researchers could investigate AI propensities after misalignment incidents | Jul 28-29 | Specifies what a credible third-party investigation requires. It is de facto the spec for the persistence protocol project. |
| Documented AI Agent Incidents | — | Interactive chart of documented incidents, scored on two axes: overreach and deception. |
| Public evidence of the OpenAI / Hugging Face AI attack + Further public evidence (Boyd Kane, Edward Cant) | Aug 7 | The attack artifacts still public: malicious dataset configuration files, template injection exploit, script to execute commands on HF machines, C2 chain set up in public repos. **The closest thing to raw material anyone has recovered.** Boyd talks about this at the sprint. |
| Hugging Face — initial disclosure | Jul 16 | Published before anyone knew which lab was responsible. Worth reading before the timeline to get a feel for what disclosing under uncertainty is like. ~10 min. |
| OpenAI — model evaluation security incident | Jul 21 (upd. 28 and 29) | Read the updates too; the one from the 28th names the vulnerable component. ~15 min. |
| Anthropic — Investigating three real-world incidents in our cybersecurity evaluations | Jul 30 | 141,006 runs reviewed, 3 incidents in 6 runs, the oldest from April 2026. **The explicit framing contrast with the OpenAI incident is itself contestable and a legitimate object of study.** ~20 min. |
| Collusion.wiki | Sep | The report on the most recent OpenAI agents incident. ~30 min. |
| OpenAI — Safety and alignment in an era of long-horizon models | Jul 20 | A **different** incident, frequently confused: a pre-release model escaped a sandbox and opened a public pull request. ~5 min. |

### Track 1 — existing control frameworks

- **CoSAI — AI Incident Response Framework v1.0** (Coalition for Secure AI, Workstream 2). Forensic investigation of AI systems, complications introduced by agentic architectures, alignment with NIST SP 800-61r3, playbooks. Written for CSIRT and SOC responders. **The closest thing to prior art for this whole sprint.**
- **CSA AI Controls Matrix**, particularly control **AIS-13 (AI Sandboxing)**, plus CSA's vulnerability operations guidance (exploit confirmation environments must have no egress and no live production credentials). On cloudsecurityalliance.org — best to locate the current version yourself, it is revised often.
- **NIST SP 800-61r3**, Incident Response Recommendations and Considerations. The base CoSAI maps onto.

### Track 1 — the chain analyzed by practitioners

- **Elastic Security Labs — detecting the attack chain.** Maps each stage to specific detection rules. Its central point — **detection correlated but never escalated to a page** — is the sharpest defensive observation anyone has published.
- **SecureLayer7 — technical anatomy.** The deepest independent technical read. Proposes treating the replay corpus as a **defensive evaluation harness**: at which action number does your control fire? That is a track 1 project brief.
- **Trackr.Live — identity and authorization controls.** Focused on the shared connector credential that carried cluster-admin rights, the decisive escalation. The authorship is not clear — treat accordingly.
- **Picus — machine-speed attacks.** Useful for the proportions: the exfiltration was ~56 actions out of ~17,600.
- **7AI (Yonatan Striem-Amit) — The Era of Autonomous Hacking Is Here.**
- **CSA CISO post-mortem** (Jul 28). Informed by 50+ CISOs and a meeting of ~700. Contains a first-hand account from HF's response team.
- **SANS — The Models Said No** and **Rich Mogull / CSA — The Model Did Exactly What We Asked.** The two best short framings from the security side.

### The benchmark at the center

- **ExploitGym** — Apache 2.0 repo · paper (arXiv 2605.11086) · Berkeley RDI writeup. The published benchmark is v1.0 with **869 instances**; the paper describes 898. **Do not cite 898 as the published number.**

### Track 2 — investigation and verification methodology

- **METR** — spec of what a credible third-party investigation requires: running the models involved, full transcripts or reproducible environments, employee interviews, classifiers over training data, adequate inference budget, redaction summary.
- **GovAI — Incident Analysis for AI Agents.** Three types of causal factor (system-related, contextual, cognitive) and — most useful — what developers and deployers should retain and make available to investigators: activity logs, documentation and system access, tool information. **Read this before writing any work on sufficiency of evidence.**
- **CLTR — The Loss of Control Observatory** (Feb 2026). Argues that demonstrations in controlled environments are insufficient for policy, that real-world evidence is the missing input, and that detection capability for incident response does not exist. Funded by UK AISI's Challenge Fund. **The existing project closest to this track's premise.**

### Track 2 — interpretation and disagreements

- **Redwood Research — The OpenAI models that hacked Hugging Face** (Jul 25) + podcast. Argues grader-gaming rather than instruction following.
- **MIT Technology Review — on precedent** (Jul 27). Contests the "unprecedented" framing and argues the failure was one of human containment design, not of out-of-control AI. **The best available counterweight to the labs' own narratives.**
- **Vectra — the response is the real story.**
- **Reuters (via CNA)** — exclusive on the detection timeline (Jul 24). Anonymous sources; several uncorroborated claims, including notes left in the infrastructure and monitoring disconnected. **Read as hypothesis, not as record.** Its account of the detection sequence is in tension with OpenAI's description — reconciling them is a legitimate project.
- Computer Weekly · Ars Technica (on the Anthropic incidents) · The Register.

---

## 10. Operational notes

- **Do not use any model to break into any organization or commit any kind of crime.**
- No compute credits are provided.
- No need to attend all three days. The only hard deadline is the Sunday cutoff.
- You can participate from any country.
- Submissions are published manually and can take up to 12 hours to appear on the website.
- More than one project can be submitted, each with a unique title. Most people focus on one.
- Support: help-desk channel on the Discord tagging @Support, or sprints@apartresearch.com.

**Pre-submission checklist:**
- [ ] Report PDF on the official template
- [ ] Abstract of 150 words or fewer
- [ ] Authors and affiliations
- [ ] Limitations & Dual-Use appendix
- [ ] 8 pages or fewer (not counting references/appendices)
- [ ] Novel installation results withheld pending review
