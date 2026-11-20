import pytest

from policy_agent.domain.access import group_filter, keep_known

G1 = "11111111-1111-1111-1111-111111111111"
G2 = "22222222-2222-2222-2222-222222222222"


def test_the_filter_lists_the_callers_groups():
    assert group_filter(frozenset({G2, G1})) == (
        f"group_ids/any(g: search.in(g, '{G1},{G2}', ',')) and is_fixture eq false"
    )


@pytest.mark.parametrize("bad", ["x') or true or ('", "not-a-guid", ""])
def test_non_guid_group_ids_are_rejected(bad):
    with pytest.raises(ValueError):
        group_filter(frozenset({G1, bad}))


def test_unknown_or_repeated_citations_are_dropped():
    cited = ["PP-04 §3.2", "PP-06 §1", "PP-04 §3.2", "PP-02 §2"]
    assert keep_known(cited, {"PP-04 §3.2", "PP-02 §2"}) == ["PP-04 §3.2", "PP-02 §2"]
