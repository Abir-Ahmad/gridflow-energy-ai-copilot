# Verification record

Build started 11 November 2026; execution continued across midnight UTC.

- Inspected GridFlow at `fa347cdbae1af2d22a5f300f69e22a2844b7c304`; original code unchanged.
- Fresh original test run: 21 passed.
- Fresh official CSV ingestion: 17,568 inserted, zero rejected; checksum matches documented snapshot.
- Copilot tests: 44 passed locally on Python 3.12.14, including real local BGE inference.
- Component evaluation: 12 passed, four live-only cases not run; 62 CSV reconciliations passed.
- No live OpenAI request made: no credential available. Mocked SDK and API responses are explicitly tests.
- Docker is not installed in the build environment. Local Docker build/run has not been verified.
- Public repository: https://github.com/Abir-Ahmad/gridflow-energy-ai-copilot
- GitHub Actions run [43125500983](https://github.com/Abir-Ahmad/gridflow-energy-ai-copilot/actions/runs/43125500983) verified implementation commit `e0438458d6eede209a74e95e3820150c5a4ff597`: 43 unit/API tests plus one real embedding test passed.
- That CI run built the Docker image, ran the HTTP/SQL smoke test against the real four-row fixture,
  and verified BGE retrieval inside the non-root container. These are actual executed checks.
- Real local Uvicorn HTTP checks passed against the full-year database and real document retrieval;
  see `evidence/http-smoke.json`. Wheel build verified corpus and HTML inclusion.
- Published source was fetched and compared to the local tracked files with no differences.
  No full datasets, databases, weights or credentials are tracked.
- Windows instructions not executed on a Windows host.

`evidence/pytest.txt` and `evidence/evaluation.json` are captured output, not proposed targets.
The evaluation script writes new runs under `artifacts/` by default, preserving committed evidence.
