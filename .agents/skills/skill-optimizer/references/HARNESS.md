# Skill Optimization Harness

A model-agnostic harness for improving Markdown-based agent skills through
measured rollouts, bounded edits, held-out validation, and recorded rejection
history.

The harness treats a `SKILL.md` file as the trainable artifact. It does not
modify model weights and it does not rely on fine-tuning.

## 1. Purpose

Use this harness to improve a Markdown skill through a controlled loop:

1. execute representative tasks with the current skill,
2. record complete trajectories,
3. identify reusable success and failure patterns,
4. propose bounded edits,
5. evaluate candidates on held-out tasks,
6. accept only validated improvements,
7. remember rejected changes,
8. export the best-performing skill.

The final artifact is a portable Markdown skill that works with the unchanged
target model.

## 2. Core Principle

Treat the skill document as the trainable state of the agent.

| Optimization Concept | Skill Equivalent |
| --- | --- |
| Model weights | `SKILL.md` |
| Forward pass | Task rollout |
| Training example | Task case |
| Loss or reward | Evaluator score |
| Gradient | Reflection on trajectories |
| Gradient aggregation | Consolidated edit proposals |
| Learning rate | Maximum edits per iteration |
| Optimizer step | Apply bounded Markdown edits |
| Validation set | Held-out task set |
| Early stopping | Stop after no validated improvement |
| Checkpoint | Versioned skill snapshot |
| Momentum | Cross-iteration guidance |
| Optimizer memory | Rejection and learning buffer |

## 3. Roles

The harness separates responsibilities between independent roles.

### 3.1 Target Agent

The target agent performs tasks using the current skill.

It must:

- load the current skill without changing it,
- execute the assigned task,
- use available tools normally,
- record relevant actions,
- produce a final answer or artifact,
- avoid evaluating its own performance unless explicitly asked.

It must not:

- edit the skill,
- see hidden validation labels,
- see optimizer conclusions,
- adapt its behavior outside the supplied skill and task context,
- receive rejected-edit history.

### 3.2 Evaluator

The evaluator scores each rollout.

It must:

- use deterministic criteria where possible,
- compare outputs against explicit rubrics,
- record both numeric and qualitative feedback,
- separate task failure from harness failure,
- avoid rewarding style changes that do not improve performance.

### 3.3 Optimizer

The optimizer analyzes rollout evidence and proposes skill edits.

It must:

- compare successful and failed trajectories,
- identify recurring patterns,
- preserve rules that already work,
- propose reusable instructions instead of task-specific answers,
- obey the edit budget,
- consider rejected-edit history,
- provide evidence for every proposed edit.

It must not:

- directly answer benchmark tasks,
- rewrite the whole skill unless full rewrite mode is explicitly enabled,
- optimize against the held-out test set,
- accept its own candidate,
- remove working constraints without evidence.

### 3.4 Gatekeeper

The gatekeeper decides whether a candidate skill is accepted.

It must:

- compare the candidate against the current skill,
- use only held-out validation results,
- apply the configured acceptance rule,
- reject regressions,
- record the decision and evidence,
- update `best_skill.md` only when the candidate beats the best validated score.

### 3.5 Harness Controller

The controller coordinates the complete loop.

It must:

- create reproducible runs,
- maintain dataset splits,
- control random seeds,
- prevent information leakage,
- manage checkpoints,
- enforce budgets,
- detect failed or incomplete runs,
- produce an auditable history.

## 4. Repository Layout

This repository is the skill-library checkout, not a full optimization
workspace. It contains the optimizer skill and its reference docs, but it does
not ship task splits or run artifacts by default.

```text
repo-root/
├── AGENTS.md
├── README.md
├── agents.json
└── .agents/
    └── skills/
        ├── academix/
        ├── apocalypse/
        ├── crawler-readiness-audit/
        ├── fact-checker/
        ├── pre-launch-security-gate/
        ├── prompt-preflight/
        ├── quick-recap/
        ├── rigorous-response/
        ├── shepherd/
        ├── skill-optimizer/
        ├── ux-logic-loop/
        ├── visual-flow-storyboard/
        └── visual-pr-review/
```

When you run this harness in a target skill repository, create the experiment
workspace there:

```text
repo-root/
├── evals/
│   ├── train/
│   ├── validation/
│   └── test/
└── runs/
```

The exact implementation language is optional. The data contracts and process
rules are not optional.

## 5. Dataset Splits

Use 3 isolated task splits.

### 5.1 Training Split

Used to produce rollout evidence and generate edit proposals.

The optimizer may inspect:

- tasks,
- target trajectories,
- evaluator scores,
- evaluator feedback.

### 5.2 Validation Split

Used only to accept or reject candidate skills.

The optimizer may receive aggregate validation results after a decision, but
must not use validation tasks as direct edit examples.

Do not repeatedly expose full validation answers to the optimizer.

### 5.3 Test Split

Used only for final evaluation.

Never use test results to propose, select, or revise edits.

After test evaluation, freeze the result.

Any further optimization requires a new test split or a clearly documented new
experiment.

### 5.4 Split Requirements

Splits must:

- represent the intended production workload,
- cover normal cases and important edge cases,
- avoid duplicate or near-duplicate tasks across splits,
- avoid leaking expected answers through metadata,
- remain stable throughout a run,
- be versioned.

## 6. Task Schema

Store each task in a machine-readable format.

```json
{
  "id": "task-001",
  "category": "architecture-review",
  "difficulty": "medium",
  "prompt": "Review the proposed module architecture.",
  "context_files": [
    "fixtures/task-001/architecture.md"
  ],
  "allowed_tools": [
    "filesystem",
    "shell"
  ],
  "expected_artifact": "markdown",
  "rubric": "rubrics/architecture-review.md",
  "metadata": {
    "source": "curated",
    "version": "1.0.0"
  }
}
```

Do not include hidden expected answers in fields visible to the target agent.

## 7. Rollout Contract

A rollout is the complete execution record for 1 task with 1 skill version.

```json
{
  "run_id": "run-20260710-001",
  "iteration": 2,
  "task_id": "task-001",
  "split": "train",
  "target_model": "model-name",
  "skill_version": "skill-v0003",
  "started_at": "2026-07-10T12:00:00Z",
  "completed_at": "2026-07-10T12:01:43Z",
  "status": "completed",
  "messages": [],
  "tool_calls": [],
  "tool_results": [],
  "final_output": "...",
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "tool_calls": 0,
    "estimated_cost": 0
  },
  "errors": []
}
```

Capture enough information to explain why the task succeeded or failed. Do not
store secrets, credentials, or unnecessary personal data. Redact sensitive tool
output before persistence.

## 8. Evaluation Contract

Each rollout receives structured evaluation.

```json
{
  "task_id": "task-001",
  "skill_version": "skill-v0003",
  "hard_score": 1,
  "soft_score": 0.84,
  "dimensions": {
    "correctness": 0.9,
    "completeness": 0.8,
    "constraint_compliance": 1.0,
    "efficiency": 0.7
  },
  "verdict": "pass",
  "strengths": [
    "Identified cyclic dependency."
  ],
  "failures": [
    "Did not provide migration sequence."
  ],
  "evidence": [
    {
      "criterion": "migration-plan",
      "observation": "No ordered migration steps included."
    }
  ],
  "evaluator_version": "rubric-v2"
}
```

### 8.1 Hard Score

Use binary or exact outcomes. Examples:

- tests pass,
- expected file exists,
- exact answer is correct,
- required constraint is satisfied.

### 8.2 Soft Score

Use graded outcomes. Examples:

- completeness,
- clarity,
- solution quality,
- efficiency,
- robustness.

### 8.3 Composite Score

When needed:

```text
composite =
  hard_weight * hard_score
  + soft_weight * soft_score
```

Weights must be defined before optimization starts. Do not change weights
during the run to favor a candidate.

## 9. Baseline

Before editing the skill:

1. freeze `initial_skill.md`,
2. execute the full training split,
3. execute the full validation split,
4. calculate baseline metrics,
5. store trajectories,
6. copy baseline `current_skill.md`,
7. copy baseline `best_skill.md`.

The baseline establishes whether later edits improve performance.

Never compare a candidate only against an assumed baseline.

## 10. Optimization Loop

Run these stages every iteration:

```text
1. Sample training tasks
2. Execute rollouts
3. Evaluate rollouts
4. Reflect on successes and failures
5. Generate edit proposals
6. Aggregate duplicate proposals
7. Rank proposals
8. Apply edit budget
9. Create candidate skill
10. Validate candidate skill
11. Accept or reject candidate
12. Update memory checkpoints
13. Check stopping conditions
```

## 11. Sampling

Select a balanced batch from the training split. The batch should include:

- recurring failures,
- stable successes,
- relevant edge cases,
- multiple task categories,
- tasks affected by recent edits.

Avoid repeatedly sampling only the worst task. That can overfit the skill to a
single case.

Record the sampling seed and selected task IDs.

## 12. Rollouts

Run each selected task with the same:

- target model,
- model settings,
- tool permissions,
- environment version,
- task context,
- execution limits.

Use the current skill as immutable input.

Retries are allowed only for infrastructure failures. Do not retry genuine task
failures until they succeed.

Mark the difference between:

- `task_failure`,
- `tool_failure`,
- `timeout`,
- `harness_failure`,
- `invalid_output`.

## 13. Evaluation

Evaluate every rollout using its assigned rubric.

For stochastic target models, use one or more of:

- multiple runs per task,
- fixed seeds where supported,
- aggregate confidence intervals,
- minimum improvement margin.

Do not treat a 1-run fluctuation as proof of improvement.

## 14. Reflection

Analyze successes and failures separately before combining them.

### 14.1 Failure Reflection

For every meaningful failure, determine:

1. What was the expected behavior?
2. What did the agent do instead?
3. Which part of the skill influenced the failure?
4. Was a required rule missing?
5. Was an existing rule ambiguous?
6. Did two rules conflict?
7. Was the failure caused by the model, tools, task, or harness?
8. Is the pattern reusable across tasks?
9. What evidence supports the proposed correction?

### 14.2 Success Reflection

For successful trajectories, determine:

1. Which behaviors contributed to success?
2. Which current rules supported those behaviors?
3. Which rules must be protected?
4. Did the agent discover a reusable strategy not yet documented?
5. Could the proposed failure fix damage a success pattern?

### 14.3 Reflection Output

```json
{
  "iteration": 2,
  "patterns": [
    {
      "id": "pattern-014",
      "type": "recurring-failure",
      "summary": "Agent proposes architecture changes before inspecting existing ADRs.",
      "affected_tasks": [
        "task-001",
        "task-009"
      ],
      "evidence": [
        "task-001 omitted ADR review",
        "task-009 contradicted ADR-004"
      ],
      "candidate_rule": "Inspect relevant ADRs before proposing architecture changes.",
      "confidence": "high"
    }
  ],
  "protected_behaviors": [
    {
      "summary": "Agent states assumptions when repository evidence is missing.",
      "supporting_tasks": [
        "task-002",
        "task-006"
      ]
    }
  ]
}
```

## 15. Edit Proposal

Allowed edit operations:

- `ADD`
- `DELETE`
- `REPLACE`

Every proposal must contain:

```json
{
  "proposal_id": "edit-0021",
  "operation": "ADD",
  "target_section": "Workflow > Repository Inspection",
  "old_text": null,
  "new_text": "Inspect relevant ADRs before proposing architecture changes.",
  "reason": "2 training failures contradicted existing architecture decisions.",
  "evidence_task_ids": [
    "task-001",
    "task-009"
  ],
  "expected_effect": "Reduce unsupported architecture recommendations.",
  "risk": "May add unnecessary repository inspection to simple requests.",
  "confidence": "high"
}
```

### 15.1 Edit Quality Rules

Proposed edits must be:

- generalizable,
- concise,
- actionable,
- testable,
- non-duplicative,
- compatible with existing constraints,
- supported by rollout evidence.

Reject proposals that:

- encode benchmark answers,
- mention specific training tasks,
- add vague advice,
- duplicate an existing rule,
- merely restate evaluator feedback,
- introduce unverifiable claims,
- increase skill size without expected value,
- weaken safety or correctness boundaries without strong evidence.

## 16. Edit Budget

The edit budget acts as the textual learning rate.

Recommended default:

```text
2-6 edits per iteration
```

Use smaller budgets when:

- the skill already performs well,
- the validation set is small,
- proposed edits affect core rules,
- the target model is highly stochastic.

Use larger budgets only when:

- the initial skill is minimal,
- failure patterns are independent,
- validation coverage is strong.

Do not permit unlimited rewrites in normal optimization mode.

## 17. Aggregation

Before selecting edits:

1. merge semantically duplicate proposals,
2. remove contradictions,
3. identify dependencies,
4. rank by evidence strength,
5. estimate regression risk,
6. preserve protected behaviors.

## 18. Candidate Construction

Create candidate skills from selected edits.

Requirements:

- preserve valid YAML frontmatter,
- preserve heading hierarchy,
- preserve protected regions,
- produce valid Markdown,
- avoid duplicated rules,
- keep the skill internally consistent,
- record the complete diff,
- assign a unique version.

## 19. Protected Regions

Use protected regions for longitudinal guidance or non-editable policy.

```markdown
<!-- PROTECTED_POLICY_START -->
This region may not be changed by iteration-level edits.
<!-- PROTECTED_POLICY_END -->

<!-- SLOW_UPDATE_START -->
Cross-iteration guidance here.
<!-- SLOW_UPDATE_END -->
```

Iteration-level edits must not modify protected content. Safety, compliance,
licensing, and repository-specific policy are normally protected.

## 20. Validation Gate

Evaluate the current candidate and the current skill on the same held-out
validation tasks.

Use identical:

- target model,
- settings,
- task order,
- tool permissions,
- evaluator version,
- execution limits.

### 20.1 Accept as New Best

```text
candidate_score > current_score
candidate_score > best_score
and no critical dimension regresses beyond tolerance
```

Actions:

- set candidate as `current_skill.md`,
- set candidate as `best_skill.md`,
- record `accept_new_best`.

### 20.2 Accept as Current

```text
candidate_score > current_score
and candidate_score <= best_score
and exploration_mode = true
```

Actions:

- set candidate as `current_skill.md`,
- preserve existing `best_skill.md`,
- record `accept_current`.

### 20.3 Reject

```text
candidate_score <= current_score
or critical regression detected
```

Actions:

- preserve current and best skills,
- store candidate and rejection reason,
- record proposals in the rejection buffer.

### 20.4 Strict Improvement Default

```text
candidate_score > current_score + minimum_delta
```

For noisy evaluations, require statistical confidence or repeated runs.

## 21. Rejection Buffer

Rejected edits must not disappear.

Store:

```json
{
  "proposal_id": "edit-0021",
  "candidate_version": "skill-v0004",
  "iteration": 2,
  "decision": "rejected",
  "validation_delta": -0.03,
  "regressions": [
    {
      "category": "simple-review",
      "summary": "Agent performed unnecessary repository inspection."
    }
  ],
  "reason": "The rule improved architecture tasks but reduced efficiency across simple review tasks.",
  "retry_conditions": [
    "Scope rule only architecture decisions.",
    "Add a relevance condition."
  ],
  "fingerprint": "inspect-adrs-before-all-architecture-advice"
}
```

When proposing a new edit, search the rejection buffer for:

- exact duplicates,
- semantic duplicates,
- previously observed regressions,
- retry conditions.

A rejected edit may be retried only if it is materially changed and supported by
new evidence.

## 22. Slow Update

At the end of each epoch, compare previous and current skills on the same
sampled tasks.

Classify tasks as:

- improved,
- regressed,
- persistent failure,
- stable success.

Generate compact longitudinal guidance.

```markdown
<!-- SLOW_UPDATE_START -->
## Longitudinal Guidance
- Preserve explicit assumption labeling; it remains stable across successful tasks.
- Scope repository-inspection rules to decisions that depend on existing architecture.
- Avoid adding broad process requirements based on a single failure.
- Prefer conditional rules over unconditional workflow expansion.
<!-- SLOW_UPDATE_END -->
```

Keep the slow update compact, evidence-based, and free of benchmark answers.

## 23. Meta Memory

Maintain optimizer-only memory in `meta-memory.md`. This file is not provided
to the target agent.

Store:

- edit patterns that worked,
- edit patterns that caused regressions,
- effective scopes and conditions,
- common sources of overfitting,
- evaluator weaknesses,
- task categories with insufficient coverage.

## 24. Reproducibility

Every run must record:

- repository commit,
- skill hash,
- task-set version,
- rubric version,
- target model identifier,
- optimizer model identifier,
- model parameters,
- tool versions,
- environment details,
- seeds,
- timestamps,
- budgets,
- acceptance rules,
- all candidate diffs.

A result is not reproducible if the exact evaluated skill cannot be
reconstructed.

## 25. Safety and Integrity

The harness must not optimize away:

- safety constraints,
- authorization boundaries,
- privacy requirements,
- legal requirements,
- mandatory human approval,
- source-verification rules,
- destructive-action confirmation,
- audit requirements.

If task scores reward unsafe behavior, fix the evaluator or dataset. Do not let
optimization exploit a broken metric.

## 26. Final Evaluation

After optimization:

1. freeze `best_skill.md`,
2. run the untouched test split,
3. compare it against the initial baseline,
4. report aggregate category-level scores,
5. report uncertainty,
6. report cost and iteration count,
7. report skill size,
8. report accepted and rejected edit counts,
9. report known limitations.

## 27. Final Run Report

Create `summary.md` with:

```markdown
# Skill Optimization Report

## Run
- Run ID:
- Skill:
- Target model:
- Optimizer model:
- Started:
- Completed:

## Baseline
- Validation score:
- Test score:
- Skill size:

## Final Result
- Validation score:
- Test score:
- Absolute improvement:
- Relative improvement:
- Final skill size:

## Optimization Activity
- Iterations:
- Epochs:
- Accepted candidates:
- Rejected candidates:
- Total proposed edits:
- Total accepted edits:
- Estimated cost:

## Category Results
| Category | Baseline | Final | Delta |
| --- | ---: | ---: | ---: |

## Accepted Changes
1.
2.

## Rejected Directions
1.
2.

## Remaining Failure Modes
- 
- 

## Transfer Notes
- Tested target environments:
- Known portability limits:

## Artifacts
- Initial skill:
- Best skill:
- History:
- Test results:
```

## 28. Completion Criteria

The optimization run is complete only when:

- the initial baseline exists,
- all accepted edits passed validation,
- rejected edits were recorded,
- the best skill is reproducible,
- the test split stayed untouched during optimization,
- category regressions are documented,
- the final report exists,
- `best_skill.md` was exported,
- no protected policy was modified,
- all artifacts were committed or archived.

## 29. Minimal Loop

A lightweight implementation can still be valid if it preserves the rules:

1. Run a batch of training tasks.
2. Score each result.
3. Reflect on recurring failures and stable successes.
4. Propose a small set of edits.
5. Build one candidate skill.
6. Evaluate the candidate on held-out validation tasks.
7. Accept only if it improves by the configured margin.
8. Store rejected edits.
9. Repeat until convergence or patience is exhausted.
10. Evaluate the best skill on the untouched test set.

## 30. Final Rule

Never accept an edit because it sounds better. Accept only when:

- the edit is grounded in rollout evidence,
- it fits within the edit budget,
- it preserves known working behavior,
- it improves held-out validation performance,
- it introduces no unacceptable regression,
- the result is reproducible.
