"""Who may read which clause: the AI Search filter on the caller's groups, and the check that the
model cites only clauses it was given."""

import uuid


def group_filter(group_ids: frozenset[str]) -> str:
    """OData filter for the caller's groups. IDs must be GUIDs, so nothing else reaches OData."""
    ids = ",".join(sorted(str(uuid.UUID(group_id)) for group_id in group_ids))
    return f"group_ids/any(g: search.in(g, '{ids}', ',')) and is_fixture eq false"


def keep_known(citations: list[str], known: set[str]) -> list[str]:
    return list(dict.fromkeys(citation for citation in citations if citation in known))
