# Literature Map

## frozen_question
Under what conditions can LLM-as-a-judge evaluations be treated as reliable and valid evidence, and which failure modes require human or multi-method safeguards?

## retrieval_axes
- agreement between LLM judges and human evaluators
- position, verbosity, self-preference, and demographic or cultural biases
- rubric design, reference-based versus reference-free judging, and calibration
- robustness across tasks, models, prompts, and repeated trials
- mitigation through panels, human adjudication, and deterministic checks

## closest_works
- **Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena** (Zheng et al., 2023) — an influential empirical basis for using strong language models as evaluators and studying judge biases.
- **G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment** (Liu et al., 2023) — relevant to rubric- and reasoning-guided model evaluation of generated text.
- **Prometheus: Inducing Fine-grained Evaluation Capability in Language Models** (Kim et al., 2024) — relevant to specialized evaluator models and fine-grained feedback.
- **Large Language Models are not Fair Evaluators** (Wang et al., 2023) — relevant to systematic preference and ordering effects in model-based evaluation.

These are illustrative seed works. Metadata and coverage must be independently verified before use in a real survey.

## taxonomy_or_clusters
1. **Construct validity** — whether the judge score represents the quality dimension the evaluation claims to measure.
2. **Reliability** — repeatability across runs, prompts, judge models, and sampling settings.
3. **Systematic bias** — position, verbosity, style, self-preference, identity, and domain effects.
4. **Calibration and grounding** — rubric quality, references, examples, and score interpretation.
5. **Governance and safeguards** — human review, judge panels, disagreement handling, and deterministic checks.

## likely_gap
The literature contains many isolated demonstrations of agreement or bias, but the field still needs an integrated synthesis that separates **reliability**, **construct validity**, and **governance** instead of treating correlation with human ratings as sufficient proof that an LLM judge is trustworthy.

## confidence_and_uncertainty
- **High confidence:** reliability and validity are distinct and should not be collapsed into one judge-quality score.
- **Medium confidence:** the five-branch taxonomy is a useful synthesis frame for comparing methods and failure evidence.
- **Main uncertainty:** this demo corpus is intentionally incomplete and cannot support claims about field-wide coverage, prevalence, or effect magnitude.
