# Evaluation methodology and limits

The report in `evidence/evaluation.json` was actually executed against the official full-year
SQLite database and the real local BGE-small embedding model. It contains per-case results,
execution time, corpus/data checksums and mode.

| Check | Measured result | What it establishes |
| --- | --- | --- |
| Numeric component cases | 6/6 | Selected SQL tools match fixed expected values |
| Documentation expected-source hit@3 | 6/6 | A relevant source appeared among the first three retrieved chunks |
| Independent CSV reconciliation | 62/62 | All monthly ND means/counts/peaks and all period ND means/counts match Python CSV calculations |
| Local tests | 42 passed | Validation, safety, SQL, retrieval mechanics, API behaviour and mocked model integration |
| Live LLM evaluations | 0 executed | Nothing yet about actual model routing or source selection |
| Refusal evaluation cases | 4 not run | Require a live LLM; mocked refusal plumbing is separately tested |

Fixed numeric cases come from GridFlow's previously captured monthly evidence and peak/count
claims. Independent reconciliations recompute from raw CSV with Python rather than reusing SQL.
The component evaluator calls each expected tool directly: passing it is NOT question-answering
accuracy. Retrieval hit@3 is not precision, citation entailment, hallucination rate or generalization.
There are eight reviewed notes; this small authored set is too small for benchmark claims.
The 0.60 cosine threshold is a heuristic; out-of-domain inputs can still retrieve plausible-looking
but irrelevant text. No held-out threshold calibration or adversarial robustness score is claimed.

## Live follow-up

Set a key privately using README instructions, with existing account access only. Run:
`python scripts/evaluate.py --live --csv data/demanddata_2024.csv --output artifacts/live-evaluation.json`.
This executes model-selected tools, source selection and four refusal cases. Inspect failures and
citation relevance manually as well as the automatic checks. Record the exact model, execution
time and output; never replace a failed result with a success claim. Do not commit credentials.
Each numeric/refusal case uses one API call; documentation may use two. No retries are automatic.

## Known failure modes

- The LLM may select an allowed but wrong metric, month or analysis. Schema validation cannot
  establish user-intent correctness. Every response exposes arguments and SQL for review.
- Retrieval may miss paraphrases or return related but insufficient evidence. The model may choose
  an irrelevant retrieved ID. The renderer prevents fabricated quotation text, not wrong relevance.
- The corpus is curated and small. Questions about unsupported columns may have insufficient context.
- A mixed unsupported/supported question may be declined entirely; a decline vetoes other tool calls.
- Results depend on the database supplied. Coverage and source checksums are shown, but the serving
  app does not certify an arbitrary existing database against the pinned official CSV.
- API timeouts, missing credentials, rate limits and unavailable model downloads produce explicit
  errors. No fake answer or silent model fallback is substituted.
- No multi-turn memory, stream responses, public-user auth, load testing or cloud deployment.
- Linux/Python 3.12 was tested. PowerShell instructions were authored but not executed on Windows.
