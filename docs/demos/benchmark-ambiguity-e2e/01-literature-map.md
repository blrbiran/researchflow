# Literature Map

## frozen_question
How should ambiguity in natural-language requests to text-to-visualization systems be benchmarked so that evaluation reveals clarification, robustness, and failure boundaries rather than only final-chart accuracy?

## retrieval_axes
- text-to-visualization benchmarks
- ambiguity and underspecification in natural-language interfaces
- evaluation taxonomies for visualization systems
- human versus model behavior under ambiguous requests

## closest_works
- **Existing text-to-visualization benchmarks** — establish the current evaluation baseline but often underweight ambiguity as a first-class dimension.
- **Visualization quality and chart-judging work** — relevant for thinking about fine-grained evaluation rubrics beyond a single overall score.
- **Dialogue and clarification literature** — relevant because humans often resolve ambiguity by asking follow-up questions rather than guessing.
- **Robustness / prompt-variation studies** — relevant for measuring how small wording changes affect output quality.

## taxonomy_or_clusters
1. **Benchmark scope** — what existing datasets and tasks cover.
2. **Ambiguity types** — missing fields, vague comparison targets, unclear grouping, implicit chart intent.
3. **Evaluation design** — exact-match, rubric-based judging, clarification-aware scoring, human comparison.
4. **Capability boundaries** — when systems clarify, guess, or fail silently.

## likely_gap
Existing text-to-visualization evaluation appears to under-specify **ambiguity handling as an explicit benchmark dimension**. The gap is not merely more examples, but a benchmark that measures whether systems recognize ambiguity, seek clarification, or degrade gracefully instead of confidently producing misleading charts.

## confidence_and_uncertainty
- **High confidence:** ambiguity should be treated as an evaluation dimension rather than a nuisance variable.
- **Medium confidence:** a benchmark framing is stronger than a pure method-paper framing for this topic.
- **Main uncertainty:** a production run would need a fuller nearest-neighbor corpus to ensure the benchmark claim is not duplicating an existing evaluation dataset.
