# Structure Brief

## paper_type
Survey / synthesis paper.

### rationale
The proposed contribution is a cross-study taxonomy and evidence synthesis. It does not introduce a new judge model, benchmark, or evaluation algorithm.

## thesis_or_goal
LLM-as-a-judge evidence should be interpreted through separate reliability, validity, bias, calibration, and governance lenses; no single agreement statistic is sufficient to establish evaluator trustworthiness.

## logic_chain
- **background:** model-based judges are increasingly used because human evaluation is expensive and slow.
- **gap:** studies report agreement and failure evidence under heterogeneous assumptions, making conclusions difficult to compare.
- **goal:** organize the evidence into a common taxonomy and derive conditional guidance about when judge outputs are credible.
- **challenges:** incompatible tasks and metrics, inconsistent human baselines, hidden prompt sensitivity, and publication emphasis on positive agreement results.
- **synthesis modules:** construct validity, reliability, systematic bias, calibration, and governance.
- **evidence plan:** verified study matrix, within-branch comparison, contradiction analysis, and explicit confidence grading.
- **contributions:** taxonomy, comparative evidence map, conditional interpretation rules, and open research questions.

## section_skeleton
- **Introduction** — frame the difference between scalable judging and trustworthy judging.
- **Review Method** — define search, screening, inclusion, extraction, and verification procedures.
- **Taxonomy** — define the five synthesis branches and their boundaries.
- **Evidence Synthesis** — compare findings within and across branches, including contradictions.
- **Practical Guidance** — derive conditional safeguards without overstating consensus.
- **Open Problems** — identify missing replications, benchmarks, and validity evidence.
- **Conclusion** — answer the frozen question and state the limits of the synthesis.

## contribution_list
- A taxonomy separating reliability, construct validity, bias, calibration, and governance.
- A cross-study synthesis that distinguishes convergent evidence from setting-specific results.
- Conditional guidance for combining LLM judges with human and deterministic evaluation.
- A research agenda centered on replication, calibration, and external validity.

## structural_risks
- The survey becomes a list of papers if it does not compare evidence within each taxonomy branch.
- The taxonomy can become arbitrary unless branch boundaries and assignment rules are explicit.
- Practical guidance must remain conditional because the demo corpus cannot establish universal recommendations.
