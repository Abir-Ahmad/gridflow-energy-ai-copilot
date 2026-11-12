"""Execute validated calls, then render only actual evidence (no invented model prose)."""

import json
import logging
from threading import Lock

from .database import Database
from .llm import TOOL_MODELS
from .retrieval import Retriever
from .schemas import Answer, Evidence, Source

log = logging.getLogger(__name__)
LIMITATIONS = [
    "2024 historical observations only; this is not a forecast or causal analysis.",
    "LLM chooses tools; answers use deterministic SQL rendering and verbatim retrieved excerpts.",
    "Retrieval similarity is not proof of relevance. Check the cited source and coverage.",
    "Embedded wind/solar estimates are not total GB renewable generation.",
]


class Copilot:
    def __init__(self, database: Database, router=None, retriever=None):
        self.database = database
        self.router = router
        self._retriever = retriever
        self._lock = Lock()

    @property
    def retriever(self):
        with self._lock:
            if self._retriever is None:
                self._retriever = Retriever()
        return self._retriever

    def execute(self, name: str, arguments: dict, index=1):
        args = TOOL_MODELS[name].model_validate(arguments)
        sources: list[Source] = []
        if name == "analyse_demand":
            result = self.database.analyse(args)
            kind = "sql"
        elif name == "search_documents":
            sources = self.retriever.search(args.query)
            result = {"matches": [source.model_dump() for source in sources]}
            kind = "documentation"
        else:
            result = {
                "reason": args.reason,
                "message": "This request cannot be answered with the supported 2024 evidence. Please clarify or choose a supported question.",
            }
            kind = "refusal"
        log.info("tool_complete tool=%s evidence=E%s", name, index)
        return Evidence(
            id=f"E{index}", kind=kind, tool=name, arguments=args.model_dump(), result=result
        ), sources

    def answer(self, question: str):
        calls = self.router.route(question)
        # A decline vetoes other calls: never silently answer a substitute question.
        if any(name == "decline" for name, _ in calls):
            calls = [next(call for call in calls if call[0] == "decline")]
        evidence, sources = [], []
        for i, (name, args) in enumerate(calls, 1):
            item, refs = self.execute(name, args, i)
            evidence.append(item)
            sources.extend(refs)
        if sources:
            selected = self.router.select_sources(question, sources)
            sources = [s for s in sources if s.id in selected]
            for item in evidence:
                if item.kind == "documentation":
                    item.result["matches"] = [s for s in item.result["matches"] if s["id"] in selected]
        return self.render(evidence, sources, "live_llm", self.router.model)

    @staticmethod
    def render(evidence, sources, mode, model=None):
        blocks = []
        for item in evidence:
            result = item.result
            if item.kind == "sql":
                prefix = f"[{item.id}] {result['metric']} — {result['analysis']} (MW)."
                rows = result["rows"]
                if not rows or (result["analysis"] == "summary" and not rows[0]["observations"]):
                    blocks.append(prefix + " No matching observations.")
                else:
                    if result["analysis"] == "monthly":
                        prefix += " Ranked highest mean first; all months shown."
                    # Values are formatted from SQL, never copied from model text.
                    blocks.append(prefix + "\n" + json.dumps(rows, indent=2) + "\n" + result["note"])
                blocks.append("Annual database coverage: " + json.dumps(result["annual_coverage"]))
            elif item.kind == "documentation":
                matches = result["matches"]
                blocks.append(
                    "Retrieved excerpts (check relevance):\n"
                    + "\n\n".join(f"[{s['id']}] {s['text']}\nSource: {s['url']}" for s in matches)
                    if matches
                    else "No sufficiently similar documentation found; I cannot ground this answer."
                )
            else:
                blocks.append(result["message"])
        return Answer(
            answer="\n\n".join(blocks),
            evidence=evidence,
            sources=sources,
            mode=mode,
            model=model,
            limitations=LIMITATIONS,
        )
