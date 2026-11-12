# Practical learning checkpoints

Do these yourself. Keep a short learning log with the command, observed output and your explanation.
Do not tick a checkpoint merely because you read the supplied code.

## 1. Run and explain the application

Run setup and the server. Use the direct monthly button. Find the winning month, its mean,
observation count and source checksum in the response. Explain why the unit is MW.
Expected outcome: January, approximately 31,808.84 MW, 1,488 observations for that month.
Explain the distinction between monthly count and annual coverage. State which part did not use an LLM.

## 2. Python basics with this project

Open a Python prompt using `.venv`. Import `AnalysisArgs`, create a peak request for month 1,
print its `.model_dump()` and access the `analysis` dictionary key. Change the month to 13 and
observe the exception. Write your own five-line function that accepts a result dictionary and
returns the number of returned rows. Explain imports, arguments, `return`, lists, dictionaries,
`None`, classes and `self` using actual lines in this repository.
Expected outcome: valid arguments produce a dictionary; invalid month fails before SQL executes.
Do not remove validation to make it run.

## 3. Trace a tool call

Run `tests/test_llm.py` and read the mocked call-contract test. Draw the question → tool schema →
model-selected arguments → validation → local function → evidence path. If existing API access
is available, run one real `/ask` question and compare its evidence with `/tools/analyse`.
Expected outcome: identify exactly which part was mocked and which, if any, reached OpenAI.
Explain why a successful mocked test says nothing about the model's choice of tool.

## 4. Modify an analytical tool

On your own branch, add minimum demand as a separate analysis that returns all tied settlement
keys. Update the allowed schema, SQL dispatch and tool description. Keep the query read-only
and month-filtered. Do not permit arbitrary column names or SQL strings.
Expected outcome: new tool result matches a hand-checked small fixture and handles tied minima.
Explain why an `ORDER BY ... LIMIT 1` solution can conceal ties.

## 5. Write a failing test, then make it pass

Before implementing checkpoint 4, write a test with two tied minima and a different month.
Run only that test and observe the failure. Implement the minimum tool, rerun, then run the suite.
Expected outcome: the test detects a missing tie or incorrect month filter, not just a function name.
Record the initial failure and final result. Do not copy a test that simply repeats the SQL.

## 6. Understand retrieval

Search for “wind output estimates” and “total renewable generation”. Record the top three IDs
and similarity scores. Check the source text. Explain why related text might not answer a question.
Temporarily raise the threshold and observe what disappears; restore it afterwards.
Add a reviewed source note with an authoritative URL and a test question, then rerun evaluation.
Expected outcome: you can explain 384-dimensional embeddings, normalization, cosine ranking,
chunk overlap, source hashes and why hit@3 is not answer accuracy.

## 7. Exercise failures

Unset the API key and call `/ask`. Send month 13 to the analysis endpoint. Point `COPILOT_DB`
at a missing path, restart, and request analysis. Restore settings afterwards.
Expected outcome: 503, 422, and 503 respectively; no invented response and no empty DB created.
Explain why liveness can be healthy while a dependency is unavailable.

## 8. Review scope and settlement semantics

Find the 31 March and 27 October rows using an independent read-only query. Count their periods.
Explain why settlement period 49 cannot be interpreted as a normal fixed clock time for every day.
Explain why embedded generation is not total GB renewable output and why MW cannot be summed
and labelled MWh without a duration calculation and correct scope.
Expected outcome: 46 and 50 periods, with no invented timestamps.

## 9. Reproduce the evidence

Run all tests, the component evaluation and Docker locally when available. Compare your output
with committed evidence. If you have existing API access, run `--live` and inspect every case;
report failures honestly. Check Actions on your exact commit, not an earlier successful run.
Expected outcome: distinguish component checks, real embeddings, mocked LLM calls, live LLM calls,
Docker packaging and actual hosting. None can stand in for all the others.

## 10. Interview rehearsal — answer aloud without reading

1. Walk from an HTTP question to SQL and back. Where could the result be wrong?
2. Why is validated tool calling safer than model-generated SQL? What risks remain?
3. How does this extractive RAG design differ from free-form generation over retrieved text?
4. What does the retrieval evaluation measure, and what does it fail to measure?
5. How would you support a larger corpus, a new year or concurrent database refresh safely?
6. Why are DST and embedded-generation definitions important to your engineering design?
7. Which parts did you build with assistance, and which have you personally modified and tested?

Expected outcome: explain the actual repository, admit unverified areas, and propose a measured
next step. Do not claim production use, deployed infrastructure or model accuracy that you did not measure.
