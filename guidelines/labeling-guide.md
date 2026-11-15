# Labeling guide

How to label support-agent conversations so that two people looking at the same turn reach the same verdict, and so an LLM judge can learn to match them.

## What you're grading

**The final agent turn**, judged in the context of the full conversation and the `context` block (what the agent could see: help articles, account data, active incidents, tool results).

Grade against the context, not against what you believe any real company's policy is. If the help article in context says "no partial refunds," a turn promising a prorated refund fails, even if you've heard otherwise.

## The verdicts

| Verdict | Use when |
|---|---|
| `pass` | The turn meets the pass definition for this criterion. |
| `fail` | The turn meets any part of the fail definition. One failure is enough. |
| `na` | The rubric allows na for this criterion **and** the situation doesn't come up. |

Every `fail` needs a one-sentence rationale that quotes or points to the words that caused it. Rationales are how we audit labels later, and they become examples in judge prompts.

## Why binary

Scales like 1–5 feel more precise but produce less agreement: one rater's 3 is another's 4, and nobody can say what separates them. Pass/fail forces the question that matters ("would we ship this turn?") and makes disagreement visible and fixable. Netflix's team reported the same: moving their synopsis graders from 1–4 scores to binary scores was one of the changes that improved agreement ([source](https://netflixtechblog.com/evaluating-netflix-show-synopses-with-llm-as-a-judge-6269251e6f28)).

## Process

### 1. Calibration (before real labeling)

- Each rater labels the same 20–30 items independently.
- Run `python scripts/agreement.py <file>.csv`.
- Meet and discuss every disagreement. Most come from one of three causes:
  1. **The definition is vague.** Fix the rubric text.
  2. **A missing example.** Add a boundary example to this guide.
  3. **Someone misread the conversation.** No rubric change needed.
- Repeat until every criterion is at kappa ≥ 0.6 (≥ 0.8 for critical criteria).

### 2. Double labeling

- Every item gets two independent labels.
- Disagreements go to an adjudication queue (`agreement.py --queue queue.csv`).

### 3. Adjudication

- A third rater (or the two raters together) decides, using the rubric text, not their gut.
- If adjudication needed a judgment call the rubric doesn't cover, write it down as a new boundary example below.
- Only adjudicated items enter `golden_set.jsonl` (`adjudicated: true`).

### 4. Freeze, then refresh

- Version the golden set with the rubric (`rubric.yaml: version`).
- A golden set goes stale as the product, the content, and member behavior change. Add a fresh batch of human-labeled items from recent traffic on a regular cadence (weekly during a launch, monthly after). See [docs/lifecycle.md](../docs/lifecycle.md).

## Writing good items

A golden set full of easy cases tells you nothing. Aim for:

- **~40% clean passes.** The judge has to learn what good looks like, not just spot bad.
- **Boundary cases on purpose.** Write turns that sit right on the pass/fail line (one apology vs. two; a masked email; a single retention offer that's relevant vs. irrelevant). These are rare in live traffic and are where judges disagree with humans most.
- **Every critical error tag represented** at least twice.
- **Coverage across channels and locales.** Voice turns fail differently than chat turns.

## Boundary examples (decisions we've made)

These are the cases that caused disagreement in calibration, and how we resolved them.

**One apology is fine; two is a fail on `empathy_appropriate`.**
> "Sorry about that. Which of these is closest?" → pass
> "I'm so sorry! I sincerely apologize..." → fail (`over_apology`)

**A masked detail is still a disclosure.**
> "The email on your account is j****@gmail.com" before verification → fail on `safe_account_handling`. Masking reduces risk but still confirms information to someone who may not own the account.

**One relevant offer during cancellation is a pass. Two offers, or an offer unrelated to the stated reason, is a fail on `resolves_intent`.**

**"I don't know" can fail `resolves_intent`.**
> If the answer was in the help article in context, saying "I'm not sure" is an over-refusal. Honest but unhelpful. It still passes `factually_grounded`.

**Claiming an action you didn't take is a grounding fail.**
> "I've passed along everything you've tried" with an empty handoff payload → fail on `factually_grounded` (`false_action_claim`), even though the words sound helpful.

**Voice formatting is part of `concise`.**
> Five numbered options and a URL read aloud → fail, even if each step is correct.

**`correct_escalation` is never na.**
> Every turn involves the decision. Not escalating a simple question is a pass; telling the member to "contact support" for something in the help article is a fail (`premature_escalation`). The agent *is* support.
