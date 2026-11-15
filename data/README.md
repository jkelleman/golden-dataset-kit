# Data

| File | What it is | Real or simulated |
|---|---|---|
| `golden_set.jsonl` | 24 hand-written support conversations, each labeled on all 8 rubric criteria with rationales and error tags | Hand-written examples for a fictional streaming service. Prices, error codes, and policies are illustrative. |
| `annotations_round1.csv` | Two raters' labels for every item and criterion, used to demo `scripts/agreement.py` | **Simulated** to show a realistic pattern: subjective criteria (concise, brand voice, empathy) disagree more than objective ones. |
| `sample_judge_predictions.jsonl` | An LLM judge's verdicts, used to demo `scripts/score_judge.py` | **Simulated** to show how a judge can look good on agreement but miss critical failures. |

## Item schema

```json
{
  "id": "gs-002",
  "intent": "refund_request",
  "channel": "chat | voice",
  "locale": "en-US",
  "difficulty": "easy | medium | hard",
  "context": { "help_article": "...", "account": { } },
  "conversation": [
    {"role": "member", "text": "..."},
    {"role": "agent", "text": "... (the turn being graded)"}
  ],
  "labels": { "factually_grounded": "fail", "...": "pass | fail | na" },
  "rationale": { "factually_grounded": "Why it failed, pointing to the words." },
  "error_tags": ["hallucinated_policy"],
  "adjudicated": true
}
```
