"""Test doubles: a policy store, an AI Search client and a scripted model."""

from collections.abc import Sequence
from typing import Any

from agent_framework import BaseChatClient, ChatResponse, FunctionInvocationLayer, Message


class FakeStore:
    def __init__(self, clauses=()) -> None:
        self.clauses, self.asked = list(clauses), []

    async def readable(self, group_ids: frozenset[str]):
        self.asked.append(group_ids)
        return self.clauses


class FakeSearchClient:
    def __init__(self, hits) -> None:
        self.hits, self.calls = hits, []

    async def search(self, **kwargs):
        self.calls.append(kwargs)
        return _Hits(self.hits)


class _Hits:
    def __init__(self, hits) -> None:
        self._hits = iter(hits)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._hits)
        except StopIteration:
            raise StopAsyncIteration from None


class ScriptedChatClient(FunctionInvocationLayer, BaseChatClient):
    """Replays scripted model turns and records what the model was sent. `_inner_get_response` is
    Agent Framework's private extension point (1.26.0); re-check it when upgrading."""

    def __init__(self, turns: Sequence[Message], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.turns, self.calls = list(turns), []

    async def _inner_get_response(self, *, messages, stream, options, **kwargs) -> ChatResponse:
        self.calls.append((list(messages), dict(options)))
        return ChatResponse(messages=[self.turns.pop(0)])
