# CV evidence — use only after you can explain the code

## Three concise bullet candidates

- Built a Python/FastAPI energy-data copilot with structured LLM tool calling, validated
  read-only SQLite analyses and traceable answers over 17,568 NESO demand observations.
- Implemented local 384-dimensional BGE embeddings and cosine retrieval with source-linked
  excerpts; verified 6/6 documentation retrieval cases and 62 independent data reconciliations.
- Added 42 passing automated tests covering SQL safety, API failures, retrieval and mocked LLM
  integration, with Docker packaging and a no-paid-API GitHub Actions workflow.

Use “implemented” for the OpenAI integration, not “validated end-to-end with a live model”.
Check `docs/verification.md` for actual remote CI and Docker status before describing them as verified.
This code was built with AI assistance. The learning exercises are intended to make your own
understanding and ability to modify it demonstrable; do not imply independent authorship if asked.

## Technologies actually used

Python 3.12; FastAPI; Pydantic; SQLite; existing GridFlow/SQLAlchemy ingestion;
OpenAI Python SDK and Responses API request schemas; FastEmbed/BGE-small; ONNX Runtime;
NumPy; pytest/pytest-cov; Ruff; HTML/JavaScript; Dockerfile; GitHub Actions YAML.

## Verified measurements and skills

Full-year data was ingested with unchanged GridFlow and its known SHA-256 verified.
42 copilot tests passed locally, including real local embedding inference. Original GridFlow's
21 tests also passed. Numeric component checks: 6/6. Expected-document hit@3: 6/6.
CSV reconciliations: 62/62. These show data correctness and retrieval on a small regression set,
not general model accuracy. See raw reports and methodology for the exact boundaries.

Demonstrated: API design, untrusted-input validation, bounded tool capabilities, SQL aggregation,
provenance, retrieval engineering, dependency management, failure handling and test design.
Unverified: live OpenAI routing/grounding/refusals, Windows execution, public deployment,
production performance and robustness at scale. The corpus is eight reviewed notes, not a large knowledge base.

## Five realistic interview questions

1. How do the metric allowlist, bound values and SQLite read-only connection each prevent different failures?
2. Why did you choose exact cosine search and extractive rendering, and when would you change them?
3. How can every returned number be correct yet the answer still be wrong for the user's question?
4. How did you independently reconcile aggregates, and what does your hit@3 result actually mean?
5. How would you safely add live LLM verification and update evidence without overstating the result?
