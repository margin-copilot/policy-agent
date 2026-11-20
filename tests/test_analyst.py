"""FoundryPolicyAnalyst with a scripted model: what it reads, what it may cite, how it refuses."""

import json

from agent_framework import Message
from margin_copilot_shared.contracts import AgentReply
from margin_copilot_shared.security.context import RequestContext, request_scope
from margin_copilot_shared.security.tokens import Caller

from policy_agent.adapters.outbound.analyst import FakePolicyAnalyst, FoundryPolicyAnalyst
from policy_agent.application.policies import Clause
from tests.fakes import FakeStore, ScriptedChatClient

G1 = "11111111-1111-1111-1111-111111111111"
CLAUSES = [
    Clause("PP-02 §2", "Price Tiers and KVI List", "Tier B (core range). UHT milk, plain yogurt."),
    Clause("PP-04 §3.2", "Price Change Rules", "Limits per increase. Tier B: up to 4%."),
]


def caller(groups=frozenset({G1}), overage=False):
    who = Caller("north-mgr", "tid", "orchestrator", frozenset(), groups, overage)
    return request_scope(RequestContext(who, token="t"))


def answers(answer, citations=(), found=True):
    body = {"answer": answer, "citations": list(citations), "found_policy": found}
    return Message("assistant", [json.dumps(body)])


async def ask(model, store, **who):
    with caller(**who):
        return await FoundryPolicyAnalyst(model, store).answer("Can I raise UHT milk by 3.6%?")


async def test_the_model_sees_only_the_readable_clauses():
    model, store = ScriptedChatClient([answers("Yes.", ["PP-04 §3.2"])]), FakeStore(CLAUSES)
    await ask(model, store)
    _, options = model.calls[0]
    assert (
        "[PP-04 §3.2] Price Change Rules: Limits per increase. Tier B: up to 4%."
        in (options["instructions"])
    )
    assert "PP-06" not in options["instructions"]
    assert store.asked == [frozenset({G1})]


async def test_citations_outside_the_readable_clauses_are_dropped():
    model = ScriptedChatClient([answers("Yes, within 4%.", ["PP-06 §1", "PP-04 §3.2"])])
    reply = await ask(model, FakeStore(CLAUSES))
    assert reply == AgentReply(answer="Yes, within 4%.", citations=["PP-04 §3.2"])


async def test_no_policy_found_is_no_data():
    model = ScriptedChatClient([answers("No policy you can open covers that.", found=False)])
    reply = await ask(model, FakeStore(CLAUSES))
    assert reply.refusal == "no_data"


async def test_no_readable_clauses_means_no_data_without_a_model_call():
    model = ScriptedChatClient([])
    reply = await ask(model, FakeStore([]))
    assert reply.refusal == "no_data"
    assert model.calls == []


async def test_group_overage_is_no_access_without_a_model_call():
    model, store = ScriptedChatClient([]), FakeStore(CLAUSES)
    reply = await ask(model, store, groups=frozenset(), overage=True)
    assert reply.refusal == "no_access"
    assert model.calls == [] and store.asked == []


async def test_reasoning_effort_is_medium():
    model = ScriptedChatClient([answers("Yes.", ["PP-04 §3.2"])])
    await ask(model, FakeStore(CLAUSES))
    assert model.calls[0][1]["reasoning"] == {"effort": "medium"}


async def test_the_fake_analyst_answers_as_the_caller():
    with caller():
        reply = await FakePolicyAnalyst().answer("anything")
    assert reply == AgentReply(answer="fake policy-agent answers as user north-mgr")


async def test_citations_are_asked_for_without_brackets():
    model = ScriptedChatClient([answers("Yes.", ["PP-04 §3.2"])])
    await ask(model, FakeStore(CLAUSES))
    instructions = " ".join(model.calls[0][1]["instructions"].split())
    assert "without the brackets, for example PP-04 §3.2" in instructions


async def test_the_model_is_asked_to_cover_every_answering_clause():
    model = ScriptedChatClient([answers("Yes.", ["PP-04 §3.2"])])
    await ask(model, FakeStore(CLAUSES))
    instructions = " ".join(model.calls[0][1]["instructions"].split())
    assert "Cover every clause that answers the question" in instructions


async def test_yes_no_rule_questions_get_a_plain_verdict():
    model = ScriptedChatClient([answers("Yes.", ["PP-04 §3.2"])])
    await ask(model, FakeStore(CLAUSES))
    instructions = " ".join(model.calls[0][1]["instructions"].split())
    assert 'say "allowed" or "not allowed" in the first sentence' in instructions
