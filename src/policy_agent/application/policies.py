"""The policy agent's ports: the clauses a caller may read, and the analyst that answers."""

from dataclasses import dataclass
from typing import Protocol

from margin_copilot_shared.contracts import AgentReply


@dataclass(frozen=True)
class Clause:
    citation: str
    title: str
    content: str


class PolicyStore(Protocol):
    async def readable(self, group_ids: frozenset[str]) -> list[Clause]: ...


class Analyst(Protocol):
    async def answer(self, question: str) -> AgentReply: ...
