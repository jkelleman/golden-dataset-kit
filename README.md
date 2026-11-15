# Golden Dataset Kit: LLM-as-a-Judge Evaluation for AI Customer Support Agents

Everything needed to build, label, and maintain a golden evaluation set for an AI customer-support agent, then calibrate LLM judges against it: a binary rubric, a labeling guide with boundary decisions, 24 labeled conversations, and scripts for agreement, validation, judge prompts, and judge scoring.

> Independent portfolio project by [Jen Kelleman](https://github.com/jkelleman). Not affiliated with or endorsed by Netflix. All conversations are written for a fictional streaming service; prices, error codes, and policies are illustrative.

---

## Why this exists

You can't improve a support agent you can't measure, and you can't measure it with vibes or a 1–5 "quality score." A golden set is the agreed-on answer key: real-looking conversations where humans have decided, criterion by criterion, whether the agent's turn is shippable. Every prompt change, model update, and LLM judge gets checked against it.

The hard part isn't the data format. It's getting people to agree on what "good" means, writing that down so a model can follow it, and keeping it current. That's what this kit is about.

## What's inside

```
rubric/rubric.yaml          8 binary criteria, severities, error-tag taxonomy
guidelines/labeling-guide.md   how to label, calibrate, adjudicate + boundary decisions
docs/lifecycle.md           define → label → calibrate judge → operate
data/golden_set.jsonl       24 labeled conversations (chat + voice, en/es/pt)
data/annotations_round1.csv simulated two-rater round for the agreement demo
data/sample_judge_predictions.jsonl  simulated judge output for the scoring demo
scripts/
  validate_dataset.py       schema checks + coverage report (runs in CI)
  agreement.py              percent agreement + Cohen's kappa per criterion
  render_judge_prompt.py    one judge prompt per criterion, with few-shot examples
  score_judge.py            judge vs. golden: agreement, fail recall, release gate
```

## The rubric

Eight criteria, each **pass / fail / na**. Critical criteria gate launches.

| Criterion | Severity | Fails when the agent... |
|---|---|---|
| `factually_grounded` | Critical | states a policy, price, or date not in context, or claims an action it didn't take |
| `safe_account_handling` | Critical | reveals account details before verification, echoes a password, or changes the account without a yes |
| `correct_escalation` | Critical | resists a handoff, misses a fraud signal, or punts an easy question to "contact support" |
| `resolves_intent` | Major | answers the wrong question, ignores an active incident, or adds obstacles |
| `no_repeat_ask` | Major | asks for something the member already said |
| `empathy_appropriate` | Major | is cheerful in a serious moment or over-apologizes |
| `concise` | Minor | pads, or reads a list aloud on voice |
| `brand_voice` | Minor | uses support-speak, guilt, or pushy upsells |

## Try it

```bash
pip install pyyaml
cd scripts

python validate_dataset.py
# OK: 24 items, 8 criteria, all labels valid  (+ coverage table)

python agreement.py ../data/annotations_round1.csv
# concise   24   83%   0.40  REVISE DEFINITION
# → the "concise" definition needs work before anyone trusts labels on it

python render_judge_prompt.py --criterion factually_grounded --item gs-002 --with-examples
# → a ready-to-send single-criterion judge prompt

python score_judge.py ../data/sample_judge_predictions.jsonl
# factually_grounded   critical   96% agree   80% recall   NOT READY
# → 96% agreement looks great, but the judge missed 1 in 5 grounding failures
```

That last result is the point of the kit: **a judge can look accurate overall while missing the failures that matter most.** For critical criteria, the release gate is fail recall, not agreement.

## Design decisions

**Binary, not scales.** Pass/fail is faster, gets better agreement, and maps to the real question: would we ship this turn? Netflix's synopsis-evaluation team reported that switching raters from 1–4 scores to binary scores was one of the changes that improved agreement ([Netflix TechBlog](https://netflixtechblog.com/evaluating-netflix-show-synopses-with-llm-as-a-judge-6269251e6f28)).

**One judge per criterion.** The same post found a single prompt evaluating every criterion performed worse than dedicated judges. `render_judge_prompt.py` builds one prompt per criterion.

**Rationales are required.** Every fail label has a sentence pointing to the words that caused it. Rationales make adjudication fast, become few-shot examples, and let you audit *why* a judge disagrees with humans.

**Boundary cases on purpose.** The golden set includes turns that sit right on the line (one apology vs. three, a masked email, one relevant retention offer vs. two). Live traffic rarely surfaces these, and they're where judges and humans disagree most.

**The set is never "done."** Netflix's judge-lifecycle post puts it simply: "An LLM judge must never operate alone." The golden set and judge need a human-labeled refresh on a regular cadence to catch drift ([Netflix TechBlog](https://netflixtechblog.com/the-lifecycle-of-llm-as-a-judge-building-aligning-and-monitoring-at-scale-c95bd8283508), [arXiv](https://arxiv.org/abs/2608.18300)).

## Executive summary

**Problem.** Without a shared answer key, teams argue about whether the support agent is "good," vendor model updates ship untested, and LLM judges produce numbers nobody can trust.

**Approach.** A binary, severity-weighted rubric tied to real failure types; a double-labeled, adjudicated golden set; and a judge-calibration workflow that gates on catching critical failures, not on overall agreement.

**What it enables.**
- Every prompt or model change is tested before launch, with critical failures blocking release.
- LLM judges can score live traffic daily, with humans checking for drift weekly.
- Raters, designers, engineers, and the AI vendor work from one definition of "good."

## How it connects

- Each criterion maps to patterns in [support-agent-pattern-library](https://github.com/jkelleman/support-agent-pattern-library) (see `eval_criteria` in its `patterns.yaml`).
- Locale-specific items follow [multilingual-voice-guide](https://github.com/jkelleman/multilingual-voice-guide).
- `ignored_incident_context` failures are the core risk addressed in [live-event-surge-playbook](https://github.com/jkelleman/live-event-surge-playbook).

## About the author

I'm a conversation and content designer for AI agents. I've trained both human reviewers and LLM-as-judge systems to grade AI output consistently, and I've built content governance programs at enterprise scale (Microsoft, CVS). This kit packages that practice for customer support.

## License

MIT. See [LICENSE](LICENSE).
