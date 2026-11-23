import httpx
from agent_framework.observability import enable_instrumentation
from margin_copilot_shared.testing.telemetry import recorded_spans, texts_in
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

from policy_agent.adapters.outbound.azure_search import AzureSearchStore
from policy_agent.main import create_app
from tests.fakes import FakeSearchClient, FakeStore, ScriptedChatClient
from tests.test_analyst import CLAUSES, G1, answers, ask
from tests.test_azure_search import HITS

ANSWER = "Yes, raising UHT milk 1 L by 3.6% is allowed: Tier B allows up to 4% (PP-04 §3.2)."


async def test_no_question_text_reaches_a_span():
    enable_instrumentation(enable_sensitive_data=False)
    model = ScriptedChatClient([answers(ANSWER, ["PP-04 §3.2"])])
    with recorded_spans() as spans:
        reply = await ask(model, FakeStore(CLAUSES))
    assert reply.answer == ANSWER
    texts = texts_in(spans)
    for content in ("Can I raise UHT milk by 3.6%?", ANSWER, "Limits per increase"):
        assert content not in texts


async def test_clauses_are_counted():
    with recorded_spans() as spans:
        await AzureSearchStore(FakeSearchClient(HITS)).readable(frozenset({G1}))
    (read,) = [s for s in spans if s.name == "policy_agent.clauses"]
    assert read.attributes["margin.clauses"] == 2


async def test_the_app_is_wrapped_and_untraced_without_a_connection_string(monkeypatch):
    monkeypatch.setenv("ADAPTERS", "fake")
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)
    app = create_app()
    assert isinstance(app, OpenTelemetryMiddleware)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://p") as c:
        assert (await c.post("/", json={})).status_code == 401
