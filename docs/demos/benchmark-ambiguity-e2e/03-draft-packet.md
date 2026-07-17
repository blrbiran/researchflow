# Draft Packet

## target_scope
Introduction opening plus benchmark-framing paragraph.

## evidence_basis
- Literature Map in `01-literature-map.md`
- Structure Brief in `02-structure-brief.md`
- Working claim that ambiguity handling is the benchmark's load-bearing evaluation axis

## draft_text_or_path
### Draft prose
Natural-language interfaces for visualization systems are often evaluated by the quality of the chart they eventually produce. Yet this perspective can hide a more basic capability question: what does the system do when the request itself is ambiguous? In realistic settings, users frequently omit grouping choices, comparison targets, or the intended chart form, and a system that answers confidently without recognizing the ambiguity can appear competent under coarse evaluation while still producing misleading outputs.

We therefore argue that ambiguity handling should be benchmarked as a first-class evaluation dimension for text-to-visualization systems. Rather than folding ambiguous cases into a single accuracy-style score, the proposed benchmark distinguishes whether a system clarifies, degrades gracefully, or commits to an unjustified interpretation. This framing shifts evaluation from “did the final chart look good?” to “did the system handle uncertainty in a way a user could trust?”.

## unresolved_gaps
- The draft still needs concrete citations to existing text-to-visualization benchmarks and ambiguity-related evaluation work.
- The introduction refers to clarification behavior abstractly; a full draft would need the benchmark taxonomy and scoring examples.
- The benchmark contribution is not yet tied to the experimental section's exact findings structure.

## real_vs_planned_status
- **Real / grounded:** the benchmark framing around ambiguity-aware evaluation.
- **Still abstracted / not yet section-complete:** the exact benchmark construction details, rubric examples, and model-comparison findings.
