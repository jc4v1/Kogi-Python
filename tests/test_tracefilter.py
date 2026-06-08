from collections import Counter

import pytest
from unittest.mock import patch

from Semantics.goccva.filter import TraceFilter
from Semantics.enums import ComplianceStatus, LinkType
from Semantics.goal_model import GoalModel
from Semantics.parsers.istar_processor import read_istar_model


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def goal_model():
    gm = GoalModel()
    gm.add_task("Task")
    gm.add_quality("q")
    gm.add_link("q", "Task", LinkType.MAKE)
    gm.reset()
    return gm


@pytest.fixture
def goal_model_from_file():
    return read_istar_model("tests/data/simple_gm.txt")


@pytest.fixture
def traces():
    return [
        ["A", "B", "C"],
        ["D", "E"],
        ["A", "F"],
        ["A", "B", "C"],
    ]


@pytest.fixture
def activity_mapping():
    return {"A": {"Task"}, "B": {"Task"}, "C": {"Task"},
            "D": {"Task"}, "E": {"Task"}, "F": {"Task"}}


@pytest.fixture
def tf(goal_model, traces, activity_mapping):
    return TraceFilter(goal_model, traces, activity_mapping)


MOCK_SUMMARY = [
    {"trace_id": 1, "trace": "A | B | C", "goal_class": ComplianceStatus.STRONGLY_COMPLIANT.value},
    {"trace_id": 2, "trace": "D | E",       "goal_class": ComplianceStatus.NON_COMPLIANT.value},
    {"trace_id": 3, "trace": "A | F",       "goal_class": ComplianceStatus.WEAKLY_COMPLIANT.value},
    {"trace_id": 4, "trace": "A | B | C",   "goal_class": ComplianceStatus.STRONGLY_COMPLIANT.value},
]


# ---------------------------------------------------------------------------
# _normalize_trace
# ---------------------------------------------------------------------------

class TestNormalizeTrace:
    def test_pipe_separated_string(self, tf):
        assert tf._normalize_trace("A | B | C") == ["A", "B", "C"]

    def test_list(self, tf):
        assert tf._normalize_trace(["X", "Y"]) == ["X", "Y"]

    def test_empty_string(self, tf):
        assert tf._normalize_trace("") == []

    def test_whitespace_around_pipes(self, tf):
        assert tf._normalize_trace("  A  |  B  ") == ["A", "B"]

    def test_single_element(self, tf):
        assert tf._normalize_trace("only") == ["only"]

    def test_tuple(self, tf):
        assert tf._normalize_trace(("X", "Y")) == ["X", "Y"]


# ---------------------------------------------------------------------------
# _trace_key
# ---------------------------------------------------------------------------

class TestTraceKey:
    def test_string_trace(self, tf):
        assert tf._trace_key("A | B") == ("A", "B")

    def test_list_trace(self, tf):
        assert tf._trace_key(["A", "B"]) == ("A", "B")

    def test_equal_for_same_content(self, tf):
        assert tf._trace_key("A | B | C") == tf._trace_key(["A", "B", "C"])


# ---------------------------------------------------------------------------
# analyse_target / caching
# ---------------------------------------------------------------------------

class TestAnalyseTarget:
    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_caches_result(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        first = tf.analyse_target("q")
        second = tf.analyse_target("q")
        assert first is second
        assert mock_analyse.call_count == 1

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_different_targets_separate_cache(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        tf.analyse_target("q")
        tf.analyse_target("other")
        assert mock_analyse.call_count == 2


# ---------------------------------------------------------------------------
# traces_by_status
# ---------------------------------------------------------------------------

class TestTracesByStatus:
    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_strongly_compliant(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = tf.traces_by_status("q", ComplianceStatus.STRONGLY_COMPLIANT)
        assert result == [["A", "B", "C"], ["A", "B", "C"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_weakly_compliant(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = tf.traces_by_status("q", ComplianceStatus.WEAKLY_COMPLIANT)
        assert result == [["A", "F"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_compliant_includes_strong_and_weak(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = tf.traces_by_status("q", ComplianceStatus.COMPLIANT)
        assert result == [["A", "B", "C"], ["A", "F"], ["A", "B", "C"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_non_compliant(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = tf.traces_by_status("q", ComplianceStatus.NON_COMPLIANT)
        assert result == [["D", "E"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_no_matching_traces_returns_empty(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = tf.traces_by_status("q", "NonexistentStatus")
        assert result == []


# ---------------------------------------------------------------------------
# Query DSL
# ---------------------------------------------------------------------------

class TestQuery:
    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_where_single_status(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = tf.query().where("q", ComplianceStatus.STRONGLY_COMPLIANT).traces()
        assert result == [["A", "B", "C"], ["A", "B", "C"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_and_where_intersects(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", ComplianceStatus.COMPLIANT)
                  .and_where("q", ComplianceStatus.WEAKLY_COMPLIANT)
                  .traces())
        assert result == [["A", "F"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_and_where_empty_intersection(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", ComplianceStatus.STRONGLY_COMPLIANT)
                  .and_where("q", ComplianceStatus.WEAKLY_COMPLIANT)
                  .traces())
        assert result == []

    def test_filter_with_predicate(self, tf):
        result = (tf.query()
                  .filter(lambda t: len(t) > 2)
                  .traces())
        assert result == [["A", "B", "C"], ["A", "B", "C"]]

    def test_contains_matching(self, tf):
        result = tf.query().contains("F").traces()
        assert result == [["A", "F"]]

    def test_contains_no_match(self, tf):
        result = tf.query().contains("Z").traces()
        assert result == []

    def test_not_contains_excludes(self, tf):
        result = tf.query().not_contains("D").traces()
        assert all("D" not in act for trace in result for act in trace)

    def test_unique_deduplicates(self, tf):
        result = tf.query().unique().traces()
        assert len(result) == 3
        assert result == [["A", "B", "C"], ["D", "E"], ["A", "F"]]

    def test_unique_preserves_order(self, tf):
        result = tf.query().unique().traces()
        assert result[0] == ["A", "B", "C"]

    def test_sort_by_length(self, tf):
        result = tf.query().sort_by_length().traces()
        assert result == [["D", "E"], ["A", "F"], ["A", "B", "C"], ["A", "B", "C"]]

    def test_chained_contains_and_unique(self, tf):
        result = (tf.query()
                  .contains("A")
                  .unique()
                  .traces())
        assert result == [["A", "B", "C"], ["A", "F"]]

    def test_query_no_filters_returns_all_traces(self, tf):
        result = tf.query().traces()
        assert result == [["A", "B", "C"], ["D", "E"], ["A", "F"], ["A", "B", "C"]]

    def test_and_where_is_alias_for_where(self, tf):
        q1 = tf.query().where("q", ComplianceStatus.STRONGLY_COMPLIANT)
        q2 = tf.query().where("q", ComplianceStatus.STRONGLY_COMPLIANT)
        assert q1.traces() == q2.traces()


# ---------------------------------------------------------------------------
# Query composition: status + content filters
# ---------------------------------------------------------------------------

class TestQueryComposition:
    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_where_then_contains(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", ComplianceStatus.COMPLIANT)
                  .contains("F")
                  .traces())
        assert result == [["A", "F"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_where_then_unique(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", ComplianceStatus.STRONGLY_COMPLIANT)
                  .unique()
                  .traces())
        assert result == [["A", "B", "C"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_where_no_results_then_filter(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", "NonexistentStatus")
                  .filter(lambda t: True)
                  .traces())
        assert result == []


# ---------------------------------------------------------------------------
# or_where
# ---------------------------------------------------------------------------

class TestOrWhere:
    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_or_where_non_compliant(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = tf.query().or_where("q", ComplianceStatus.NON_COMPLIANT).traces()
        assert result == [["A", "B", "C"], ["D", "E"], ["A", "F"], ["A", "B", "C"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_or_where_adds_weakly_to_strongly(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", ComplianceStatus.STRONGLY_COMPLIANT)
                  .or_where("q", ComplianceStatus.WEAKLY_COMPLIANT)
                  .traces())
        assert result == [["A", "B", "C"], ["A", "B", "C"], ["A", "F"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_or_where_union_of_disjoint_sets(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", ComplianceStatus.NON_COMPLIANT)
                  .or_where("q", ComplianceStatus.STRONGLY_COMPLIANT)
                  .traces())
        assert result == [["D", "E"], ["A", "B", "C"], ["A", "B", "C"]]


# ---------------------------------------------------------------------------
# .not
# ---------------------------------------------------------------------------

class TestNotIn:
    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_not_with_no_prior_filter(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = tf.query().not_in().traces()
        assert result == []

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_not_inverts_strongly_compliant(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", ComplianceStatus.STRONGLY_COMPLIANT)
                  .not_in()
                  .traces())
        assert result == [["D", "E"], ["A", "F"]]

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_not_inverts_non_compliant(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", ComplianceStatus.NON_COMPLIANT)
                  .not_in()
                  .traces())
        assert result == [["A", "B", "C"], ["A", "F"], ["A", "B", "C"]]


# ---------------------------------------------------------------------------
# frequency
# ---------------------------------------------------------------------------

class TestFrequency:
    def test_frequency_all_traces(self, tf):
        result = tf.query().frequency()
        expected = Counter(tuple(t) for t in tf.traces)
        assert result == expected

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_frequency_after_where(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        result = (tf.query()
                  .where("q", ComplianceStatus.STRONGLY_COMPLIANT)
                  .frequency())
        traces = tf.traces_by_status("q", ComplianceStatus.STRONGLY_COMPLIANT)
        expected = Counter(tuple(t) for t in traces)
        assert result == expected

    def test_frequency_empty(self, tf):
        result = (tf.query()
                  .filter(lambda t: False)
                  .frequency())
        assert result == Counter()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_traces(self, goal_model, activity_mapping):
        tf = TraceFilter(goal_model, [], activity_mapping)
        assert tf.query().traces() == []

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_empty_summary(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = ([], None, None)
        assert tf.traces_by_status("q", ComplianceStatus.STRONGLY_COMPLIANT) == []

    def test_traces_with_no_activities(self, goal_model, activity_mapping):
        tf = TraceFilter(goal_model, [[]], activity_mapping)
        result = tf.query().contains("X").traces()
        assert result == []

    def test_normalize_mixed_types_in_pipe(self, tf):
        assert tf._normalize_trace("") == []
        assert tf._normalize_trace("   ") == []

    @patch("Semantics.goccva.filter.analyse_no_pm")
    @patch("Semantics.goccva.filter.sequences_to_event_log")
    def test_cache_hit_returns_same_object(self, mock_seq, mock_analyse, tf):
        mock_analyse.return_value = (MOCK_SUMMARY, None, None)
        r1 = tf.analyse_target("q")
        r2 = tf.analyse_target("q")
        assert r1 is r2
