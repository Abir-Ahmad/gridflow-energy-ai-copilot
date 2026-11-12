import json
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pytest

from energy_copilot.llm import InvalidModelOutput, OpenAIRouter, ServiceUnavailable


def router(name="analyse_demand", arguments=None, status="completed", n=1):
    client = Mock()
    args = (
        {"metric": "national_demand_mw", "analysis": "peak", "month": None}
        if arguments is None
        else arguments
    )
    client.responses.create.return_value = NS(
        status=status,
        output=[NS(type="function_call", name=name, arguments=json.dumps(args), call_id="c1")] * n,
    )
    return OpenAIRouter(None, "test-model", client), client


def test_mocked_sdk_call_contract():
    r, c = router()
    calls = r.route("highest demand?")
    assert calls[0][1]["analysis"] == "peak"
    sent = c.responses.create.call_args.kwargs
    assert sent["store"] is False and sent["tool_choice"] == "required"
    assert len(sent["tools"]) == 3
    assert all(t["strict"] for t in sent["tools"])
    assert sent["tools"][0]["parameters"]["additionalProperties"] is False


@pytest.mark.parametrize(
    "kwargs",
    [{"name": "run_sql"}, {"arguments": {"metric": "bad"}}, {"status": "incomplete"}, {"n": 0}, {"n": 4}],
)
def test_invalid_model_outputs(kwargs):
    r, _ = router(**kwargs)
    with pytest.raises(InvalidModelOutput):
        r.route("question")


def test_invalid_json():
    r, c = router()
    c.responses.create.return_value.output[0].arguments = "not json"
    with pytest.raises(InvalidModelOutput):
        r.route("question")


def test_unavailable_and_sanitised_errors():
    with pytest.raises(ServiceUnavailable):
        OpenAIRouter(None, "test").route("question")
    r, c = router()
    c.responses.create.side_effect = RuntimeError("secret credential")
    with pytest.raises(ServiceUnavailable) as exc:
        r.route("question")
    assert "secret" not in str(exc.value)


def test_grounding_selection_is_evidence_bound():
    from energy_copilot.schemas import Source

    r, c = router()
    sources = [Source(id="doc1", title="Wind", url="https://example.org", text="Estimate", score=0.8)]
    c.responses.create.return_value = NS(status="completed", output_text='{"source_ids":["doc1"]}')
    assert r.select_sources("wind meaning", sources) == ["doc1"]
    assert "retrieved_sources" in c.responses.create.call_args.kwargs["input"]
    c.responses.create.return_value.output_text = '{"source_ids":["invented"]}'
    with pytest.raises(InvalidModelOutput):
        r.select_sources("wind meaning", sources)
    assert r.select_sources("wind meaning", []) == []


def test_real_sdk_serialisation_with_mock_http_transport():
    """Exercises installed SDK parsing, not the OpenAI network or a real model."""
    import httpx
    from openai import OpenAI

    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "resp_test",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "test-model",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_test",
                        "call_id": "call_test",
                        "name": "analyse_demand",
                        "arguments": json.dumps(
                            {"metric": "national_demand_mw", "analysis": "peak", "month": None}
                        ),
                        "status": "completed",
                    }
                ],
            },
        )

    client = OpenAI(
        api_key="test-placeholder",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    )
    try:
        result = OpenAIRouter(None, "test-model", client).route("Highest demand?")
        assert result[0][0] == "analyse_demand"
        assert requests[0]["tools"][0]["parameters"]["required"] == ["metric", "analysis", "month"]
    finally:
        client.close()
