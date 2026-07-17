# ResearchFlow Unified Router Design Spec

Date: 2026-07-17  
Status: Draft for review  
Topic: Thin unified routing layer for research and paper workflows

## 1. Purpose

This spec defines the first version of a unified entrypoint and routing layer for `reference/researchflow`.

The goal is not to merge every reference library into a shared skill marketplace. The goal is to make one public ResearchFlow entrypoint route a user's one-sentence research or paper request to the right workflow phase more reliably, while borrowing proven ideas from:

- `reference/ECC/`
- `reference/academic-research-skills/`
- `reference/Supervisor-Skills/`
- `reference/gstack/`
- `reference/superpowers/`

The first version should solve one problem well:

> Given a research- or paper-related request, decide which main workflow phase the user should enter first.

This spec is a repo-local design for the ResearchFlow plugin. It does not replace the canonical handoff definitions in `docs/workflow-contracts.md`. Instead, it defines how `using-researchflow` should route requests onto that existing contract chain more consistently.

Unless explicitly superseded later, `docs/workflow-contracts.md` remains the source of truth for:

- the five handoff artifacts,
- the meaning of phase boundaries,
- and the default "earliest missing or unstable artifact" routing invariant.

This spec only tightens the router behavior, clarifying when to route directly, when to route backward, when to ask one clarification question, and which repo-local surfaces the implementation must update.

## 2. Scope and settled decisions

### 2.1 Primary host

Version 1 should land on `reference/researchflow` as an evolution of the existing `using-researchflow` entrypoint rather than as a new cross-repo meta-plugin.

### 2.2 Workflow domain

Version 1 is limited to research and academic-paper workflows.

It does not try to unify general engineering, QA, deployment, debugging, product, or design work.

### 2.3 Main routing surface

The only public entrypoint should remain:

- `using-researchflow`

The only first-class routing targets should remain the five existing ResearchFlow phases:

- `literature-discovery`
- `paper-structuring`
- `paper-drafting`
- `paper-review`
- `artifact-packaging`

### 2.4 Default routing policy

The router should default to direct routing.

It should ask a clarifying question only when:

- two adjacent phases are both plausible,
- the current files and stated intent do not resolve the ambiguity,
- and routing to the wrong phase would waste substantial work.

That clarification should be exactly one question.

## 3. Chosen design and rejected alternatives

### 3.1 Chosen design: thin router

The chosen design is a thin router built on top of the existing ResearchFlow phase model.

It keeps ResearchFlow as the only visible workflow skeleton and uses other libraries only as internal enhancement sources.

### 3.2 Rejected alternative: dual-layer router

A two-step design with both phase routing and explicit strategy routing was considered but rejected for V1.

It would be extensible, but it introduces extra concepts before the base routing behavior is proven stable.

### 3.3 Rejected alternative: skill-market router

A marketplace-style router that treats ResearchFlow, academic-research-skills, Supervisor-Skills, superpowers, ECC, and gstack as peer destinations was also rejected.

That design conflicts with the requirement that V1 remain a research-only router with a single user-facing entrypoint and a single workflow skeleton.

## 4. Design principles

The router should follow these principles.

1. **Single public entrypoint.** Users should not need to choose among overlapping frameworks before the system can help.
2. **Single workflow skeleton.** The ResearchFlow five-phase model remains the only primary routing surface.
3. **Artifact-first routing.** Route based on the earliest missing or unstable handoff artifact, not merely the most downstream action named by the user.
4. **Default directness.** Route immediately in the common case.
5. **Single-question clarification.** When ambiguity is real and expensive, ask one question and no more.
6. **Hidden internal complexity.** Borrowed logic from other libraries should improve judgment without surfacing as a competing UI.
7. **Subordinate support only.** External reference libraries may strengthen a phase decision or stage policy, but they may not add a new top-level phase.

## 5. Router architecture

The unified router should remain user-visible as one entrypoint but operate internally through four layers.

### 5.1 Intent Normalizer

The first layer normalizes the user's request into research-domain intents such as:

- find papers or related work,
- identify the gap,
- shape the outline or contribution framing,
- write or rewrite prose,
- critique a draft,
- prepare submission-facing artifacts.

This layer should only normalize language. It should not yet choose external support skills or leak internal routing jargon.

### 5.2 Phase Router

The second layer maps the normalized request onto one of the five ResearchFlow phases.

Its primary rule remains:

> Route to the earliest missing or unstable artifact in the ResearchFlow contract chain.

The contract chain remains:

```text
Literature Map -> Structure Brief -> Draft Packet -> Review Packet -> Submission Packet
```

This means the router should not blindly follow the most downstream action word in the user's request. It should combine the request surface with the stability of the existing workflow state.

### 5.3 Clarification Gate

The third layer decides whether a clarifying question is necessary.

By default, it should not ask one.

It should ask exactly one question only when:

- two adjacent phases remain genuinely plausible after reading the available materials,
- both interpretations would lead to materially different work,
- and a wrong route would likely create avoidable drafting, review, or packaging churn.

The clarification question should ask only for the minimum information needed to choose the phase.

### 5.4 Subordinate Enhancer Layer

The fourth layer applies internal enhancements after the main phase is chosen.

This layer may borrow judgment rules, interaction discipline, or support-escalation ideas from other libraries, but it must not override the main phase skeleton or introduce new top-level destinations.

## 6. Main routing rules

### 6.1 Surface-intent mapping

The router should treat the following expressions as default signals for the corresponding phase.

- Requests about related work, literature review, closest work, novelty check, or gap extraction default to `literature-discovery`.
- Requests about paper type, outline, contribution framing, section skeleton, or logic chain default to `paper-structuring`.
- Requests about drafting a section, rewriting prose, turning notes into paper text, or expanding a validated structure default to `paper-drafting`.
- Requests about reviewing, critiquing, checking claim-evidence alignment, or preparing a revision order default to `paper-review`.
- Requests about PDF export, supplement packaging, artifact README work, appendix assembly, or submission-facing checklists default to `artifact-packaging`.

### 6.2 Artifact-stability correction

After a surface-intent match, the router should test whether the upstream artifact chain is stable enough to support that phase.

Examples:

- A request to write an Introduction should route backward if the paper still lacks a stable literature-backed gap or contribution framing.
- A request to draft the whole paper should route to `paper-structuring` if the logic chain or section roles are still unstable.
- A request to export or prepare for submission should route to `paper-review` if the manuscript has not yet passed a credible review and revision-order pass.

The governing rule is:

> Surface intent proposes a phase; artifact stability confirms it or routes to an earlier phase.

### 6.3 Adjacent-phase ambiguity

The clarification gate should be optimized for adjacent-phase confusion such as:

- `literature-discovery` vs `paper-structuring`
- `paper-structuring` vs `paper-drafting`
- `paper-review` vs `artifact-packaging`

It should not ask broad menu-style questions or expose the whole internal phase list unless the user explicitly asks for expert mode or implementation details.

## 7. External-library contribution model

The unified router should absorb ideas from the reference libraries through four contribution types only.

### 7.1 Route hints

These help determine which ResearchFlow phase best matches the user's request.

- `academic-research-skills` contributes stage-detection and mid-entry thinking.
- `Supervisor-Skills` contributes distinctions between idea evaluation, structure shaping, evidence-grounded drafting, and submission-minded review.
- `superpowers` contributes disciplined early skill detection and minimal necessary clarification.

### 7.2 Phase policies

These constrain how a chosen phase should behave.

- `Supervisor-Skills` contributes evidence discipline, citation caution, and the boundary that academic judgment stays with the user.
- ResearchFlow's own workflow contracts remain the canonical phase-boundary definition.

### 7.3 Support escalations

These are subordinate suggestions that may be made only after the main phase is fixed.

Examples:

- `literature-discovery` may escalate to `arxiv`.
- `paper-drafting` may adopt the evidence and drafting discipline exemplified by `paper-writer` or the section-specific behavior exemplified by an Introduction-focused writer.
- `paper-review` may escalate to a stronger submission-minded review behavior when the user explicitly wants a final gate.
- `artifact-packaging` may recommend PDF, figure, or artifact-surface helpers as subordinate tooling.

### 7.4 Execution heuristics

These improve implementation details without changing the chosen phase.

- `ECC` and `gstack` contribute router-engineering ideas such as metadata surfaces, model-route hints, and harness-awareness.
- `superpowers` contributes process-first interaction discipline and checkpoint-minded execution style.

## 8. Hard boundary for external references

The router must enforce one explicit architectural boundary:

> External libraries may not introduce new top-level phases in V1.

They may:

- help identify one of the five ResearchFlow phases,
- strengthen the rules inside that phase,
- or provide subordinate support after the phase is selected.

They may not:

- compete with `using-researchflow` as a peer public router,
- turn the system into a multi-framework skill directory,
- or cause the visible workflow skeleton to drift away from the five ResearchFlow phases.

## 9. User-visible behavior

### 9.1 Default response shape

The router should usually respond in one or two sentences that:

- name the chosen phase,
- and explain briefly why that phase is the right start point.

It should not default to long routing menus or framework comparisons.

### 9.2 Support-skill visibility

Subordinate support behavior should stay hidden by default.

The router should explicitly name a support skill or external influence only when:

- the user explicitly asks for expert mode or names a specific support skill,
- or a subordinate support surface materially changes what happens next.

### 9.3 Silent internal borrowing

The router should remain silent about:

- internal route-hint logic,
- evidence-discipline borrowing,
- model-route or harness heuristics,
- or any other internal enhancement that does not change the public workflow step.

The user should perceive a better unified research assistant, not a federation of competing frameworks.

### 9.4 Clarification style

When clarification is necessary, the question should:

- be singular,
- ask only for the minimum missing distinction,
- use the user's language rather than internal artifact names,
- and avoid exposing the whole routing graph.

Examples of acceptable clarification behavior include:

- asking whether the user wants help stabilizing structure or is ready for prose only,
- asking whether the user wants a general critique or a final pre-submission gate.

## 10. Repo-local implementation surfaces

This spec is intended to guide changes inside the `reference/researchflow` repository rather than remain an abstract cross-repo note.

A conforming implementation should review and update the following repo-local surfaces where needed.

### 10.1 Required implementation surface

- `skills/using-researchflow/SKILL.md` — primary routing behavior, clarification discipline, and subordinate support policy
- `docs/workflow-contracts.md` — treated as the canonical contract reference; update only if the contract itself changes, not merely because routing behavior becomes clearer

### 10.2 Likely documentation sync surface

- `README.md` — user-facing description of the unified entrypoint and routing behavior
- `CLAUDE.md` — contributor rules for keeping the router phase-first and non-marketplace-like
- `docs/README.claude.md` — Claude-facing verification expectations for bootstrap behavior
- `docs/handover/researchwork-plugin-handover.md` — update if the router behavior, acceptance criteria, or next recommended work changes materially

### 10.3 Verification surface

A repo-local implementation should be considered incomplete if it changes router behavior but leaves the verification story implicit.

At minimum, the implementation should confirm that:

- the bootstrap still behaves as if `using-researchflow` is loaded,
- a fresh related-work request still routes to `literature-discovery`,
- drafting-style requests route backward when the upstream artifacts are unstable,
- packaging-style requests route backward to review when review stability is missing,
- and any clarified router behavior remains consistent with `docs/workflow-contracts.md`.

The exact test location can evolve, but the acceptance behavior must remain repo-local and verifiable from inside `reference/researchflow`.

## 11. Non-goals

Version 1 does not aim to:

- become a universal router for engineering and non-research work,
- reproduce the full multi-stage orchestration behavior of `academic-pipeline`,
- expose expert-mode strategy routing by default,
- make all external libraries peer public destinations,
- or perfectly classify every ambiguous request without fallback.

The objective is narrower: stable high-frequency routing for research and paper work.

## 11. Failure boundaries

The design should explicitly guard against four failure modes.

### 11.1 Routing drift

The router should not behave as though another framework has taken ownership of the workflow skeleton.

### 11.2 Over-clarification

The router should not turn routine interactions into a questionnaire when a confident direct route is available.

### 11.3 Surface-only routing

The router should not follow downstream verbs such as "write" or "submit" when the upstream artifacts are still unstable.

### 11.4 Internal complexity leakage

The router should not force users to understand which reference library influenced the decision in order to follow the workflow.

## 12. Validation

The V1 router design should be considered sound only if it can satisfy all of the following checks.

### 12.1 Canonical route tests

Given representative research requests, the router should map them to the five ResearchFlow phases in a stable and unsurprising way.

Minimum examples:

- "Help me find related work" -> `literature-discovery`
- "Help me frame the contributions and outline" -> `paper-structuring`
- "Rewrite this Methods section" -> `paper-drafting`
- "Review this manuscript" -> `paper-review`
- "Help me package the PDF, supplement, and artifact README" -> `artifact-packaging`

### 12.2 Backward-routing tests

For downstream-sounding requests, the router should route backward when upstream artifacts are missing or unstable.

Examples:

- A request to write an Introduction should not remain in `paper-drafting` if the literature-backed gap is not yet stable.
- A request to prepare for submission should not remain in `artifact-packaging` if review stability is missing.

### 12.3 Clarification-discipline tests

The router should ask no question in the common case and at most one question in the high-cost ambiguity case.

### 12.4 User-experience tests

The user-facing behavior should satisfy these conditions:

- most requests route directly,
- explanations remain brief,
- support layers remain mostly invisible,
- and the system still feels like one ResearchFlow assistant rather than a routing console.

## 13. Success criteria

Version 1 is complete when all of the following are true.

- `using-researchflow` remains the only public unified entrypoint.
- The only primary routing targets remain the five ResearchFlow phases.
- Surface-intent mapping is corrected by artifact stability rather than replacing it.
- The router defaults to direct routing.
- Clarification is limited to one question in high-cost adjacent-phase ambiguity.
- External libraries strengthen judgment, policy, or execution heuristics without becoming peer top-level routes.
- The resulting behavior is visibly simpler for users, not more complex.

## 14. Concise design summary

The V1 unified router should be understood as follows:

> It does not unify every skill surface into one marketplace. It unifies the phase-routing judgment for research and paper work under a single ResearchFlow entrypoint, while treating other libraries as internal sources of routing hints, stage policies, and subordinate support behavior.
