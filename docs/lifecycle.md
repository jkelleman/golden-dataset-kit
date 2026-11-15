# The golden set and judge lifecycle

A golden dataset isn't a one-time deliverable. It's the reference point for every prompt change, vendor model update, and LLM judge, so it needs an operating rhythm.

```
 ┌──────────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐
 │ 1. DEFINE    │ →  │ 2. LABEL     │ →  │ 3. CALIBRATE  │ →  │ 4. OPERATE   │
 │ rubric +     │    │ double-label │    │ judge per     │    │ gate releases│
 │ boundary     │    │ adjudicate   │    │ criterion vs. │    │ sample live  │
 │ examples     │    │ freeze v1    │    │ golden labels │    │ traffic,     │
 └──────────────┘    └──────────────┘    └───────────────┘    │ watch drift  │
        ↑                                                     └──────┬───────┘
        └───────────── new failure types, rubric updates ────────────┘
```

## 1. Define

- Start from real failures in conversation logs, not from a generic quality checklist. The rubric's `error_tags` are a taxonomy of what actually goes wrong.
- Write pass and fail definitions as observable behavior ("reveals email before verification"), not adjectives ("insecure").
- Assign severity. Critical criteria gate launches.

**Artifacts:** `rubric/rubric.yaml`, `guidelines/labeling-guide.md`

## 2. Label

- Calibrate raters until agreement holds (`scripts/agreement.py`).
- Double-label, adjudicate, freeze.
- Deliberately include boundary cases. Netflix's recommendation-explanation team describes generating examples near the pass/fail line and having humans rate them, because live traffic rarely surfaces the ambiguous cases on its own ([source](https://netflixtechblog.com/the-lifecycle-of-llm-as-a-judge-building-aligning-and-monitoring-at-scale-c95bd8283508)).

**Artifacts:** `data/golden_set.jsonl`, `scripts/validate_dataset.py`

## 3. Calibrate the judge

- **One judge per criterion.** A single prompt grading eight criteria blurs them. Netflix's synopsis team found dedicated judges per criterion performed better than one prompt for everything ([source](https://netflixtechblog.com/evaluating-netflix-show-synopses-with-llm-as-a-judge-6269251e6f28)).
- Render prompts with `scripts/render_judge_prompt.py`. Include labeled pass/fail examples from the golden set (`--with-examples`), never the item being graded.
- Score with `scripts/score_judge.py`. For critical criteria, the gate is **fail recall**: the share of human-labeled failures the judge catches. Missing a hallucinated refund policy is worse than flagging an extra turn for review.
- When the judge misses, read its rationale next to the human rationale. Fix the rubric text or add an example. Don't just add "be careful" to the prompt.

**Artifacts:** `scripts/render_judge_prompt.py`, `scripts/score_judge.py`

## 4. Operate

| Use | How |
|---|---|
| **Release gate** | Every prompt or model change runs the full golden set. Any new critical fail blocks the release. |
| **Live sampling** | Judge a daily sample of production conversations. Track fail rate per criterion over time. |
| **Drift check** | Humans label a fresh sample weekly. If judge–human agreement drops on any criterion, recalibrate before trusting the judge's numbers. |
| **Refresh** | Add newly labeled items to the golden set, especially new failure types. Bump the version. |

The core principle in Netflix's judge-lifecycle post applies directly: "An LLM judge must never operate alone." Humans stay in the loop at every phase ([source](https://netflixtechblog.com/the-lifecycle-of-llm-as-a-judge-building-aligning-and-monitoring-at-scale-c95bd8283508); [paper](https://arxiv.org/abs/2608.18300)).

## Roles

| Role | Owns |
|---|---|
| Conversation designer | Rubric definitions, boundary examples, adjudication decisions |
| Raters (internal or vendor) | Labels and rationales |
| ML / eval engineer | Judge pipeline, scoring, dashboards |
| Product / CS leadership | Severity levels, launch gates |
