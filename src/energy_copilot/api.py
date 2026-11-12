"""FastAPI entry point. Bind to localhost unless adding authentication and rate limits."""

import logging
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .config import Settings
from .database import Database
from .llm import InvalidModelOutput, OpenAIRouter, ServiceUnavailable
from .schemas import AnalysisArgs, Answer, Question, SearchArgs
from .service import Copilot

log = logging.getLogger(__name__)


def create_app(service=None):
    settings = Settings.from_env()
    service = service or Copilot(Database(settings.database), OpenAIRouter(settings.api_key, settings.model))
    app = FastAPI(title="Energy AI Copilot", version="0.1.0")

    def safely(operation):
        try:
            return operation()
        except ServiceUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc
        except InvalidModelOutput as exc:
            raise HTTPException(502, "AI returned an invalid tool call") from exc
        except sqlite3.Error as exc:
            raise HTTPException(503, "Database unavailable or incompatible; run setup first") from exc
        except Exception as exc:
            log.error("request_failed type=%s", type(exc).__name__)
            raise HTTPException(503, "Evidence service unavailable; inspect local setup") from exc

    @app.get("/health")
    def health():
        return {"status": "ok", "note": "Liveness only; does not verify AI credentials, data or embeddings"}

    @app.get("/")
    def home():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @app.post("/ask", response_model=Answer)
    def ask(question: Question):
        return safely(lambda: service.answer(question.question))

    @app.post("/tools/analyse", response_model=Answer)
    def analyse(args: AnalysisArgs):
        def run():
            evidence, sources = service.execute("analyse_demand", args.model_dump())
            return service.render([evidence], sources, "direct_tool")

        return safely(run)

    @app.post("/tools/search", response_model=Answer)
    def search(args: SearchArgs):
        def run():
            evidence, sources = service.execute("search_documents", args.model_dump())
            return service.render([evidence], sources, "direct_tool")

        return safely(run)

    return app


app = create_app()
