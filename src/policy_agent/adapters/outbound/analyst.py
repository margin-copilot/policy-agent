"""Analyst port adapters: a Foundry model that answers from the clauses the caller may read,
and a fake. Code, not the model, decides what may be cited and the refusal label."""

from typing import Any

from agent_framework import Agent
from margin_copilot_shared.contracts import AgentReply
from margin_copilot_shared.security.context import current_request
from pydantic import BaseModel, ValidationError

from policy_agent.adapters.outbound.instructions import instructions
from policy_agent.application.policies import PolicyStore
from policy_agent.domain.access import keep_known

OVERAGE = "Your account is in too many groups to check policy access; ask an administrator."
NO_POLICY = "No policy you can open covers that."


class PolicyAnswer(BaseModel):
    answer: str
    citations: list[str]
    found_policy: bool


class AnalystFailed(Exception):
    pass


class FoundryPolicyAnalyst:
    def __init__(self, client: Any, store: PolicyStore) -> None:
        self._client = client
        self._store = store

    async def answer(self, question: str) -> AgentReply:
        caller = current_request().caller
        if caller.groups_overage:
            return AgentReply(answer=OVERAGE, refusal="no_access")
        clauses = await self._store.readable(caller.groups)
        if not clauses:
            return AgentReply(answer=NO_POLICY, refusal="no_data")
        agent = Agent(
            client=self._client,
            instructions=instructions(clauses),
            default_options={"response_format": PolicyAnswer, "reasoning": {"effort": "medium"}},
        )
        response = await agent.run(question)
        try:
            result = response.value
        except ValidationError:
            result = None
        if result is None:
            raise AnalystFailed("the model gave no structured answer")
        return AgentReply(
            answer=result.answer,
            refusal=None if result.found_policy else "no_data",
            citations=keep_known(result.citations, {clause.citation for clause in clauses}),
        )


class FakePolicyAnalyst:
    async def answer(self, question: str) -> AgentReply:
        oid = current_request().caller.oid
        return AgentReply(answer=f"fake policy-agent answers as user {oid}")
