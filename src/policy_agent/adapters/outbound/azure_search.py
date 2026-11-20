"""PolicyStore on AI Search. The service's own identity reads the index, filtered by the
caller's validated groups (CLAUDE.md: per-user search runs on the user's groups claim)."""

from typing import Any

from policy_agent.application.policies import Clause
from policy_agent.domain.access import group_filter

FIELDS = ["citation", "title", "content"]
MAX_CLAUSES = 200  # the whole corpus is 46 clauses (D-036)


class AzureSearchStore:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def readable(self, group_ids: frozenset[str]) -> list[Clause]:
        if not group_ids:
            return []
        hits = await self._client.search(
            search_text="*", filter=group_filter(group_ids), select=FIELDS, top=MAX_CLAUSES
        )
        clauses = [Clause(hit["citation"], hit["title"], hit["content"]) async for hit in hits]
        return sorted(clauses, key=lambda clause: clause.citation)
