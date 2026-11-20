from policy_agent.adapters.outbound.azure_search import AzureSearchStore
from policy_agent.domain.access import group_filter
from tests.fakes import FakeSearchClient

G1 = "11111111-1111-1111-1111-111111111111"
HITS = [
    {"citation": "PP-04 §3.2", "title": "Price Change Rules", "content": "Limits per increase."},
    {"citation": "PP-01 §5", "title": "Pricing Governance", "content": "Reason codes."},
]


async def test_the_query_filters_on_the_callers_groups_and_skips_fixtures():
    client = FakeSearchClient(HITS)
    clauses = await AzureSearchStore(client).readable(frozenset({G1}))
    assert client.calls == [
        {
            "search_text": "*",
            "filter": group_filter(frozenset({G1})),
            "select": ["citation", "title", "content"],
            "top": 200,
        }
    ]
    assert [clause.citation for clause in clauses] == ["PP-01 §5", "PP-04 §3.2"]


async def test_a_caller_without_groups_reads_no_clauses():
    client = FakeSearchClient(HITS)
    assert await AzureSearchStore(client).readable(frozenset()) == []
    assert client.calls == []
