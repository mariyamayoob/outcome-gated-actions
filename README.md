# outcome-gated-actions

This repo contains one narrow experiment for a DSC article:

Can a rubric-gated retry loop reduce wrong final actions when a support decision agent must choose from a closed set?

The experiment uses OpenAI Responses API structured outputs for the support decision agent. A separate rubric judge checks the selected action against objective policy constraints. If the judge fails the first answer, the agent receives the failed criteria and gets one retry.

This repo intentionally requires a real LLM provider at runtime. There is no fake provider because the experiment is about actual model behavior in two loops:

- baseline decision
- rubric-gated decision with one retry

## What It Tests

The agent must choose one final action:

- `APPROVE`
- `DENY`
- `ASK_CLARIFYING_QUESTION`
- `ESCALATE`
- `NO_ACTION`

The 30 synthetic cases cover authentication constraints, existing workflow constraints, policy exceptions, conflicting evidence, and safe approvals.

The baseline path is:

```text
case -> OpenAI agent -> final action
```

The gated path is:

```text
case -> OpenAI agent -> rubric judge -> one retry if failed -> final action
```

## Scope

This repo is a narrow action-selection experiment. It is a support repo for an article, not a benchmark. It leaves out brand voice, empathy, long-form answer quality, user satisfaction, general support performance, model-provider comparison, and prompt-strategy comparison.

The experiment focuses on outcomes that are objective, structured, and checkable.

## Why The Outcome Must Be Checkable

The judge can only enforce constraints that are explicit in the case rubric. That works for closed-set decisions like "do not approve a refund while a chargeback workflow is active." It is weaker for subjective checks like "write a better answer" because the judge has less objective ground truth.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Set the OpenAI environment variables:

```bash
set OUTCOME_GATED_PROVIDER=openai
set OPENAI_API_KEY=your-api-key
set OUTCOME_GATED_MODEL=your-model
```

On macOS or Linux, use `export` instead of `set`.

## Run

```bash
python scripts/run_baseline.py
python scripts/run_gated.py
python scripts/make_report.py
```

`make_report.py` expects fresh OpenAI outputs from the two run scripts. It will reject stale outputs that do not include OpenAI run metadata.

The scripts write:

- `outputs/baseline.jsonl`
- `outputs/gated.jsonl`
- `outputs/summary.csv`
- `outputs/failure_examples.md`

## Output Table

The table below shows the report shape. Values depend on the model, prompt, and run.

| metric | value |
| --- | ---: |
| metadata_baseline_provider | openai |
| metadata_baseline_model | your-model |
| metadata_gated_provider | openai |
| metadata_gated_model | your-model |
| baseline_wrong_actions | varies |
| baseline_wrong_action_rate | varies |
| gated_wrong_actions | varies |
| gated_wrong_action_rate | varies |
| fixed_after_retry | varies |
| false_rejections | varies |
| retry_rate | varies |
| average_calls_per_case | varies |

## Interpret Results

Interpret the result by separating error reduction from retry cost and false rejections:

- The gated run should reduce wrong final actions on objective policy constraints.
- Retry rate shows how often the gate intervened.
- Fixed after retry shows whether the retry actually corrected failed actions.
- False rejection rate shows whether the gate blocked initially correct actions.
- Average calls per case shows the cost of adding the gate.

If wrong actions fall but false rejections and extra calls rise sharply, the gate may be too strict for the workflow.

## Limitations

The cases are synthetic and small. The judge checks the final action, not the full customer-facing response. The rubric is handcrafted, so it represents known policy constraints rather than discovered edge cases. Live model results can vary across models, prompts, and repeated runs.

Rubric-gated retries can help when the agent outcome is a closed, objective decision. They are less reliable when the desired improvement is subjective quality.

## Example run

Model: gpt-4.1-mini
Cases: 30
Baseline wrong actions: 6 / 30
Gated wrong actions: 2 / 30
Wrong-action rate reduced from 20.00% to 6.67%
Retry rate: 20.00%
False rejections: 0 in this run