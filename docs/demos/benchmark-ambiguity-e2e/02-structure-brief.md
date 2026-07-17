# Structure Brief

## paper_type
Benchmark / evaluation paper.

### rationale
The central contribution is a new evaluation dimension and benchmark design around ambiguity handling, not a novel visualization-generation algorithm.

## thesis_or_goal
Text-to-visualization systems should be evaluated on how they handle ambiguous requests, because overall chart-quality scores can hide whether a model recognized the ambiguity, guessed, or asked for clarification.

## logic_chain
- **background:** text-to-visualization systems are increasingly judged by final output quality.
- **gap:** current evaluation often collapses ambiguity handling into a single end metric.
- **goal:** define a benchmark that exposes ambiguity as a first-class capability boundary.
- **challenges:** constructing realistic ambiguous prompts, labeling ambiguity types, and scoring clarification versus brittle guessing.
- **modules:** benchmark construction pipeline, ambiguity taxonomy, rubric-based evaluation framework, empirical findings section.
- **evidence:** benchmark examples, scoring rubric, model comparisons, and qualitative failure cases.
- **contributions:** benchmark framing, construction method, evaluation framework, and capability-boundary findings.

## section_skeleton
- **Introduction** — motivate ambiguity as a missing evaluation dimension.
- **Related Work** — position against text-to-vis benchmark and judge-model literature.
- **Benchmark Design** — define ambiguity categories and construction pipeline.
- **Evaluation Framework** — metrics, rubric, and comparison setup.
- **Experiments / Findings** — model behavior under ambiguity, clarification, and failure modes.
- **Discussion / Limitations** — what the benchmark reveals and what it still misses.
- **Conclusion** — restate why ambiguity-aware evaluation changes the picture.

## contribution_list
- A benchmark framing that treats ambiguity handling as a first-class evaluation target.
- A construction pipeline for ambiguity-focused text-to-visualization examples.
- An evaluation framework that distinguishes clarification, graceful degradation, and brittle guessing.
- Empirical findings about capability boundaries that overall chart-quality scores can obscure.

## structural_risks
- The paper weakens if ambiguity categories are vague or not tied to realistic user requests.
- The benchmark claim weakens if related-work positioning does not clearly distinguish prior evaluation surfaces.
- Findings must be phrased as capability-boundary observations, not overclaimed product recommendations.
