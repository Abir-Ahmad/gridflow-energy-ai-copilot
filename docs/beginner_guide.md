# Beginner guide: understand Energy AI Copilot

You already know electrical quantities. Start with that: each row describes one GB settlement
half-hour. National demand is a power value in MW. The software's job is to find the right rows,
calculate exactly, and show which evidence supports an answer. The LLM does not calculate demand.

## 1. Follow one numerical question

Suppose you ask: “Which month had the highest average national demand?”

1. Your browser sends `{"question": "Which month ...?"}` to `/ask` using HTTP POST.
2. FastAPI receives it. Pydantic checks that it is text, has useful characters, is no more than
   1,000 characters, and has no unexpected fields.
3. `OpenAIRouter.route()` sends the question plus three tool definitions to OpenAI. The model
   can choose `analyse_demand`, `search_documents`, or `decline`. It has no SQL execution access.
4. For this question the intended call is:

```python
{"metric": "national_demand_mw", "analysis": "monthly", "month": None}
```

5. Python validates these arguments again. The database module chooses its prewritten SQL
   template. `None` means no month filter, so the query considers all 2024 observations.
6. SQLite groups rows by month, computes the mean of each group and sorts the means descending.
7. Python attaches the SQL, bound parameters, source checksum and coverage. The renderer
   displays the actual rows. January's measured mean is 31,808.836... MW.
8. FastAPI returns JSON. The browser uses `textContent` to display it without treating it as HTML.

There is one LLM call on this path. The answer's numbers never come from model-written prose.
The free monthly button skips steps 3–4 and supplies the tool arguments explicitly. That is
useful for learning and debugging, but it does not demonstrate natural-language model routing.

## 2. Follow a documentation question

Ask: “What does embedded wind generation mean?”

1. The same API validates the question. The model should choose `search_documents`.
2. The retriever converts the query into a numerical vector using the local BGE embedding model.
3. It compares that vector to vectors for reviewed documentation chunks and returns up to three
   with cosine scores at least 0.60. Each result includes text, ID, URL and title.
4. A second OpenAI call receives those excerpts and the question. It generates a constrained
   list of source IDs. It cannot supply new text as an answer.
5. Python checks that each ID really appeared in the retrieved evidence, then quotes the selected
   excerpts. If no sources survive, it says it cannot ground the answer.

This is **extractive retrieval-augmented generation**: retrieval supplies external evidence;
the model generates a selection of evidence, and a deterministic renderer supplies the wording.
It sacrifices fluent synthesis to make claims traceable. It does not guarantee that a selected
excerpt answers the user's question correctly. Always check relevance.

## 3. What the important files do

| File | Responsibility |
| --- | --- |
| `src/energy_copilot/config.py` | Reads database path, model name and optional key from environment variables |
| `schemas.py` | Defines valid questions, arguments, evidence and API responses |
| `database.py` | Opens SQLite read-only and runs allowlisted analytical SQL |
| `retrieval.py` | Chunks notes, creates dense embeddings and ranks cosine similarity |
| `llm.py` | Defines tools, calls OpenAI, validates calls and source selections |
| `service.py` | Connects the modules and renders actual evidence |
| `api.py` | Exposes HTTP routes and converts failures to useful status codes |
| `static/index.html` | Small browser interface with live and direct-tool buttons |
| `corpus/sources.json` | Reviewed source notes and traceable links |
| `scripts/setup_data.py` | Downloads/checks the source and invokes the existing GridFlow loader |
| `scripts/warm_embeddings.py` | Downloads/loads embeddings before serving questions |
| `scripts/evaluate.py` | Runs numeric/document cases and independent CSV reconciliation |
| `evals/cases.json` | Questions, expected operations and expected results |
| `tests/` | Tests using small controlled data and one real embedding test |
| `.github/workflows/ci.yml` | Runs checks on GitHub without an LLM key |
| `Dockerfile` | Describes the runtime container, not a hosted service |

GridFlow owns validation and loading; this repository owns read-only answering. Ingestion is
performed before the server starts. `requirements.lock` records dependency versions; it is
not Python code. Tests use synthetic rows unless explicitly described as real data.

## 4. Python ideas you will see

### Functions

A function is a named operation with inputs and a return value:

```python
def average(values):
    return sum(values) / len(values)
```

Calling `average([10, 20])` returns `15.0`. In our actual program, SQLite performs aggregation;
this small function explains the same idea. `return` sends a value to the caller. It does not
print to the screen. `print()` displays output and usually returns `None`.

### Dictionaries and lists

```python
arguments = {"metric": "national_demand_mw", "analysis": "peak", "month": None}
print(arguments["analysis"])  # peak
```

A dictionary maps names to values. A list such as `[row1, row2]` stores ordered items.
JSON looks similar but is a text interchange format: JSON has `null`, Python has `None`.
`json.loads()` turns JSON text into Python objects; `json.dumps()` does the reverse.

### Imports and classes

```python
from pathlib import Path
from energy_copilot.database import Database

database = Database(Path("data/energy.db"))
```

An import makes another module's definitions available. A class groups state and operations.
`Database(...)` creates an object holding a path; `.analyse(...)` is a method on that object.
`self` means “this instance”. The object is not the database itself: SQLite opens the actual file.
A Pydantic model is also a class, but it additionally checks types and allowed values.

## 5. Key functions in plain English

`Settings.from_env()` reads terminal settings. Missing keys disable the LLM; they do not cause
the app to invent responses. Settings are loaded when the app is created, so restart after changes.

`AnalysisArgs(...)` rejects unknown fields and values. `Literal[...]` means the input must be
one of the listed strings. `month` must be a real integer between 1 and 12 or `None`; text and
booleans are rejected. Type hints help readers; Pydantic supplies the runtime checks.

```python
from energy_copilot.schemas import AnalysisArgs
args = AnalysisArgs(metric="national_demand_mw", analysis="peak", month=1)
result = database.analyse(args)
print(result["rows"])
```

`connect_readonly()` is a context manager: `with` opens a connection, yields it to the query,
and closes it even if an exception occurs. SQLite `mode=ro` prevents writes at the connection
level. `query_only` is an additional guard. There is no tool accepting a SQL string.

`Database.analyse()` selects one fixed template. A month becomes a `?` bound parameter, rather
than text pasted into SQL. SQL identifiers cannot be bound this way, so the metric is checked
against a fixed allowlist before it is inserted into a template.

`chunk_documents()` divides source text into word windows. Adjacent windows overlap so useful
context near a boundary is not wholly lost. Our current notes are short and form eight chunks.
Their IDs include a content hash, making an altered quotation distinguishable from an old one.

`Retriever.search()` embeds the query, normalizes vectors, computes their dot products and
sorts descending. For unit-length vectors, the dot product is cosine similarity.

`OpenAIRouter.route()` calls the external model. `Copilot.execute()` invokes the validated
local function. These are different actions: receiving a function-call JSON is not execution.
`select_sources()` sends retrieved evidence back to the model for a constrained citation choice.
`Copilot.render()` creates the visible answer from results, never from unchecked model prose.

## 6. What embeddings and vector search do

An embedding model maps text to a fixed-length list of numbers. Here each list has 384 numbers.
It has learned patterns that often place related text in nearby directions. A question about
“wind output estimates” may therefore match “embedded wind generation” without identical words.
The numbers are not a dictionary of facts and cannot calculate monthly demand.

Cosine similarity measures the angle between vectors. Larger similarity often means related
text, but does not prove correctness or answerability. The cutoff is a search setting, not “60%
confidence”. This corpus is tiny, so comparing every vector with NumPy is simpler than operating
a separate vector database. No retrieval score is presented as an accuracy percentage.

## 7. Run, inspect and debug

Follow README's PowerShell commands from the repository root. Start with the free monthly
button. Then search for wind definitions. Configure an API key privately only if you already
have access and want to test the model path. Never share that key in chat or Git.

Run `python -m pytest -q -m "not integration"` using your virtual-environment Python. This runs
controlled tests without downloading model weights. Run the full suite after warming embeddings.
Use `python -m pytest tests/test_database.py -q` to focus on SQL behaviour.

| Symptom | What to inspect |
| --- | --- |
| `ModuleNotFoundError` | Did you use `.venv`'s Python and install the project? |
| HTTP 422 | Compare your JSON with `/docs`; check field names, strings, null and month range |
| HTTP 503 on analysis | Check `COPILOT_DB`, file existence and GridFlow schema |
| HTTP 503 on `/ask` | Check private key configuration, model access and provider availability |
| HTTP 502 | Model response did not match the allowed tool/source contract |
| Slow first search | Public embedding model may still be downloading |
| No documents found | Corpus may lack evidence, or similarity fell below the heuristic cutoff |
| Unexpected mean | Inspect metric, month, `observations`, SQL and source checksum in evidence |
| Setup checksum failure | NESO may have revised the file; review before changing the pinned checksum |

Do not fix a failing test by blindly changing the expected value. Reproduce the input, calculate
what should happen independently, then decide whether the code or expectation is wrong.

## 8. Why these choices

- FastAPI gives typed HTTP routes, validation and interactive docs with little boilerplate.
- SQLite reuses GridFlow and needs no server, cloud billing or database credentials.
- Pydantic treats model output as untrusted input rather than assuming valid JSON is safe.
- Prewritten SQL gives bounded capabilities and auditable calculations.
- OpenAI structured tools provide a practical API integration; the model can be changed through
  configuration, but compatibility and behaviour must be retested for a different model.
- Local FastEmbed avoids per-query embedding charges; its first download is still a dependency.
- Exact NumPy search is appropriate for eight chunks. A vector server would add maintenance here.
- Evidence-only rendering trades fluent paragraphs for verifiable numbers and quotations.
- Docker packages runtime dependencies; GitHub Actions checks changes. Neither proves deployment
  to a public service or real LLM accuracy.

You should be able to explain these trade-offs in your own words before putting this on your CV.
