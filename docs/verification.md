# Verification record

Build started 11 November 2026; execution continued across midnight UTC.

- Inspected GridFlow at `fa347cdbae1af2d22a5f300f69e22a2844b7c304`; original code unchanged.
- Fresh original test run: 21 passed.
- Fresh official CSV ingestion: 17,568 inserted, zero rejected; checksum matches documented snapshot.
- Copilot tests: 42 passed locally on Python 3.12.14, including real local BGE inference.
- Component evaluation: 12 passed, four live-only cases not run; 62 CSV reconciliations passed.
- No live OpenAI request made: no credential available. Mocked SDK and API responses are explicitly tests.
- Docker is not installed in the build environment. Local Docker build/run has not been verified.
- GitHub Actions publication and Docker CI smoke verification: pending publication.
- Windows instructions not executed on a Windows host.

`evidence/pytest.txt` and `evidence/evaluation.json` are captured output, not proposed targets.
The evaluation script writes new runs under `artifacts/` by default, preserving committed evidence.
