# Structure Brief

## paper_type
Technical / system paper with evaluation-heavy evidence.

### rationale
The core contribution is not a benchmark alone and not a survey alone; it is a lifecycle-and-runtime design for scoped memory reuse in coding agents, supported by controlled evidence.

## thesis_or_goal
Coding-agent memory should be framed and implemented as **scoped experience reuse** with explicit lifecycle controls, because that framing better matches real coding workflows and enables utility gains without treating unsafe cross-scope carryover as acceptable behavior.

## logic_chain
- **background:** coding agents increasingly rely on reusable context and past experience.
- **gap:** existing “agent memory” framing is often too broad and hides scope, staleness, and leakage problems.
- **goal:** define a lifecycle and runtime boundary for safe experience reuse.
- **challenges:** deciding what to save, when to trust it, how to prevent cross-project leakage, and how to evaluate both utility and safety.
- **modules:** memory lifecycle, runtime retrieval/injection, safety controls, evaluation protocol.
- **evidence:** controlled utility runs, safety scenarios, and runtime/operational observations.
- **contributions:** conceptual reframing, system design, lifecycle policy, and empirical control surface.

## section_skeleton
- **Introduction** — motivate scoped experience reuse and the mismatch with generic “memory” language.
- **Related Work** — position against agent memory, experience reuse, and agent-eval literature.
- **System / Method** — define lifecycle stages and runtime architecture.
- **Evaluation** — utility, safety, and runtime-control evidence.
- **Discussion / Limitations** — what the framing clarifies and what remains open.
- **Conclusion** — restate the memo-not-memory thesis and its implications.

## contribution_list
- A scoped reframing of coding-agent memory as safe experience reuse.
- A lifecycle model for memory creation, promotion, revalidation, and forgetting.
- A runtime architecture that exposes scope boundaries as first-class controls.
- An evaluation protocol that separates utility from safety and non-discriminative pilot evidence.

## structural_risks
- The paper becomes vague if the safety/control story is not tied to concrete scenarios.
- The system contribution weakens if lifecycle stages are not mapped cleanly to runtime behavior.
- The evaluation section must avoid over-claiming from weakly separated pilot results.
