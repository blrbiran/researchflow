# Draft Packet

## target_scope
Introduction opening plus contribution-framing paragraph.

## evidence_basis
- Literature Map in `01-literature-map.md`
- Structure Brief in `02-structure-brief.md`
- Project claim that scoped reuse and safety boundaries are the paper's load-bearing axis

## draft_text_or_path
### Draft prose
Coding agents increasingly benefit from carrying forward useful context across tasks, yet the language used to describe this capability often obscures the real engineering problem. In practice, the question is not whether an agent can accumulate an open-ended notion of memory, but whether it can reuse past experience in ways that remain relevant, bounded, and safe for the current working context. This distinction matters especially in coding environments, where stale conventions, cross-project leakage, and mis-scoped retrieval can turn a seemingly helpful memory mechanism into a source of silent error.

In this work, we argue that coding-agent memory is better understood as scoped experience reuse rather than unconstrained long-term memory. Building on that framing, we present a lifecycle-oriented design that separates what should be saved, how it should be promoted or revalidated, and when it must be excluded from the agent's active context. We then evaluate this design through utility and safety-oriented control scenarios, showing how the framing clarifies both the system surface and the evidence required to justify it.

## unresolved_gaps
- The draft still needs real citations attached at the sentence level.
- The prose names utility and safety evidence generically; a full draft would need the concrete evaluation setup.
- The contribution paragraph is not yet tied to section numbers or figure references.

## real_vs_planned_status
- **Real / grounded:** the paper's framing around scope, lifecycle, and safety controls.
- **Still abstracted / not yet section-complete:** the exact cited prior-work comparison and full evaluation narrative.
