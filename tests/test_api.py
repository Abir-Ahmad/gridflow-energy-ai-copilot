from unittest.mock import Mock

from fastapi.testclient import TestClient

from energy_copilot.api import create_app
from energy_copilot.llm import InvalidModelOutput, OpenAIRouter
from energy_copilot.schemas import Source
from energy_copilot.service import Copilot

ARGS = {"metric": "national_demand_mw", "analysis": "peak", "month": None}


def client(db, router=None, retriever=None):
    return TestClient(create_app(Copilot(db, router or OpenAIRouter(None, "test"), retriever)))


def test_health_and_interface(db):
    c = client(db)
    assert c.get("/health").json()["status"] == "ok"
    assert "Energy AI Copilot" in c.get("/").text
    assert c.get("/openapi.json").status_code == 200


def test_direct_sql_and_no_secret(db):
    response = client(db).post("/tools/analyse", json=ARGS)
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "direct_tool" and body["model"] is None
    assert "300" in body["answer"] and len(body["evidence"]) == 1


def test_invalid_requests(db):
    c = client(db)
    for q in ["", "  ", "x" * 1001, 123]:
        assert c.post("/ask", json={"question": q}).status_code == 422
    assert c.post("/tools/analyse", json={**ARGS, "sql": "DROP TABLE x"}).status_code == 422


def test_no_key_503(db):
    assert client(db).post("/ask", json={"question": "highest demand?"}).status_code == 503


def test_mocked_llm_end_to_end(db):
    router = Mock(model="mock-model")
    router.route.return_value = [("analyse_demand", ARGS)]
    body = client(db, router).post("/ask", json={"question": "highest demand?"}).json()
    assert body["evidence"][0]["result"]["rows"][0]["value_mw"] == 300
    assert body["model"] == "mock-model"


def test_mocked_docs_grounding(db):
    retriever = Mock()
    retriever.search.return_value = [
        Source(id="doc:1", title="Wind", url="https://example.org", text="Estimated output.", score=0.8)
    ]
    body = client(db, retriever=retriever).post("/tools/search", json={"query": "wind meaning"}).json()
    assert "Estimated output." in body["answer"]
    assert body["sources"][0]["id"] == "doc:1"


def test_empty_retrieval(db):
    retriever = Mock()
    retriever.search.return_value = []
    body = client(db, retriever=retriever).post("/tools/search", json={"query": "unknown"}).json()
    assert "cannot ground" in body["answer"]


def test_model_error_502(db):
    router = Mock()
    router.route.side_effect = InvalidModelOutput()
    assert client(db, router).post("/ask", json={"question": "highest demand?"}).status_code == 502


def test_database_error_503(db):
    db.path = db.path.with_name("missing.db")
    assert client(db).post("/tools/analyse", json=ARGS).status_code == 503


def test_retrieval_error_503(db):
    retriever = Mock()
    retriever.search.side_effect = RuntimeError("private detail")
    response = client(db, retriever=retriever).post("/tools/search", json={"query": "wind meaning"})
    assert response.status_code == 503 and "private detail" not in response.text


def test_decline_vetoes_analysis(db):
    router = Mock(model="mock")
    router.route.return_value = [("analyse_demand", ARGS), ("decline", {"reason": "outside_scope"})]
    body = client(db, router).post("/ask", json={"question": "2025 peak?"}).json()
    assert len(body["evidence"]) == 1 and body["evidence"][0]["kind"] == "refusal"


def test_mocked_grounding_selection_removes_unselected_sources(db):
    router = Mock(model="mock-model")
    router.route.return_value = [("search_documents", {"query": "wind meaning"})]
    router.select_sources.return_value = ["wind"]
    retriever = Mock()
    retriever.search.return_value = [
        Source(id="wind", title="Wind", url="https://example.org/wind", text="Wind estimate.", score=0.8),
        Source(id="solar", title="Solar", url="https://example.org/solar", text="Solar estimate.", score=0.7),
    ]
    body = client(db, router, retriever).post("/ask", json={"question": "wind meaning"}).json()
    assert [s["id"] for s in body["sources"]] == ["wind"]
    assert "Wind estimate." in body["answer"] and "Solar estimate." not in body["answer"]
    router.select_sources.assert_called_once()
