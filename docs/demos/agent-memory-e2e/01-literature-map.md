# Literature Map

## frozen_question
How should coding-agent memory systems be scoped and evaluated if the goal is safe experience reuse rather than unconstrained long-term personalization?

## retrieval_axes
- agent memory systems and coding agents
- retrieval and scoped context reuse
- safety / scope isolation / cross-project leakage
- evaluation methodology for agentic memory systems

## closest_works
- **Contextual Agentic Memory is a Memo, Not True Memory** — argues for scoped, task-facing memory surfaces rather than anthropomorphic “memory” claims; directly relevant to framing.
- **Self-Improving Agents in the Era of Experience** — situates experience reuse and self-improving agents in a broader taxonomy; relevant to related-work positioning.
- **Coding-agent memory plugin and retrieval-system implementations** — practical evidence that scoped retrieval, trust, and project boundaries matter for real coding-agent workflows.
- **Agent evaluation and benchmark methodology work** — relevant because the paper's claims depend on clean control conditions, not only mechanism descriptions.

## taxonomy_or_clusters
1. **Memory representation** — notes, traces, embeddings, structured memories.
2. **Retrieval and reuse policy** — lexical/semantic retrieval, trust, ranking, scope filters.
3. **Lifecycle and governance** — save, promote, revalidate, forget, contradiction handling.
4. **Evaluation and controls** — utility uplift, safety leakage, runtime overhead, judge protocol.

## likely_gap
Existing work discusses agent memory broadly, but there is a narrower under-articulated gap around **safe experience reuse for coding agents**: how to define a lifecycle and runtime boundary that improves reuse without enabling cross-project scope leakage or stale-memory overreach.

## confidence_and_uncertainty
- **High confidence:** the framing should emphasize scope and safety, not generic “long-term memory”.
- **Medium confidence:** the lifecycle framing is a useful organizing contribution if it stays tightly tied to coding-agent behavior.
- **Main uncertainty:** the literature map is intentionally minimal and not a real survey-grade corpus; a production run would need a fuller verified paper set and closer nearest-neighbor comparison.
