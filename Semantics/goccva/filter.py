from collections import Counter
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

from Semantics.enums import ComplianceStatus
from Semantics.goccva.helpers import sequences_to_event_log

from Semantics.goccva.pipeline import analyse_no_pm

class TraceFilter:
    """Fluent DSL to query traces by target compliance status and trace content.

    Args:
        goal_model: A goal model with targets (goals).
        traces: List of traces, each trace is a list of activity labels (strings).
        activity_mapping: Mapping from goal model labels to process model activities.

    Usage::

        # Basic setup
        trace_filter = TraceFilter(
            goal_model=goal_model,
            traces=[
                ["Activity A", "Activity B", "Activity C"],
                ["Activity A", "Activity X", "Activity C"],
                ["Activity A", "Activity B"],
            ],
            activity_mapping={"Goal1": "Activity A", "Goal2": "Activity B"},
        )

        # Filter traces by a single compliance status
        strong_traces = trace_filter.query().where("MyTarget", ComplianceStatus.STRONGLY_COMPLIANT).traces()

        # Filter by multiple status types using COMPLIANT
        all_compliant = trace_filter.query().where("MyTarget", ComplianceStatus.COMPLIANT).traces()

        # Chain multiple status filters (intersection)
        result = (
            trace_filter.query()
            .where("Target1", ComplianceStatus.STRONGLY_COMPLIANT)
            .and_where("Target2", ComplianceStatus.WEAKLY_COMPLIANT)
            .traces()
        )

        # Add a custom predicate filter
        long_traces = (
            trace_filter.query()
            .where("MyTarget", ComplianceStatus.COMPLIANT)
            .filter(lambda trace: len(trace) > 2)
            .traces()
        )

        # Filter by activity name substring
        traces_with_a = (
            trace_filter.query()
            .where("MyTarget", ComplianceStatus.COMPLIANT)
            .contains("Activity")
            .traces()
        )

        # Exclude traces containing a substring
        traces_without_x = (
            trace_filter.query()
            .where("MyTarget", ComplianceStatus.COMPLIANT)
            .not_contains("X")
            .traces()
        )

        # Deduplicate traces
        unique = (
            trace_filter.query()
            .where("MyTarget", ComplianceStatus.COMPLIANT)
            .unique()
            .traces()
        )

        # Union of two compliance statuses
        union = (
            trace_filter.query()
            .where("Target1", ComplianceStatus.STRONGLY_COMPLIANT)
            .or_where("Target1", ComplianceStatus.WEAKLY_COMPLIANT)
            .traces()
        )

        # Complement of a status filter
        not_strong = (
            trace_filter.query()
            .where("Target1", ComplianceStatus.STRONGLY_COMPLIANT)
            .not_in()
            .traces()
        )

        # Frequency count of traces in the filtered set
        counts = trace_filter.query().frequency()
        for trace_key, count in counts.most_common():
            print(trace_key, count)

        # Get all traces for a target at once
        summary = trace_filter.analyse_target("MyTarget")
        for item in summary:
            print(item["trace"], item["goal_class"])

    Available compliance statuses:
        - ComplianceStatus.STRONGLY_COMPLIANT
        - ComplianceStatus.WEAKLY_COMPLIANT
        - ComplianceStatus.COMPLIANT (matches STRONGLY or WEAKLY)
        - ComplianceStatus.NON_COMPLIANT

    Note:
        Traces can be provided as List[List[str]] or as pipe-separated strings
        (e.g., "Activity A | Activity B | Activity C"). Both formats are accepted.
    """

    def __init__(
        self,
        goal_model,
        traces: List[List[str]],
        activity_mapping,
    ) -> None:
        self.goal_model = goal_model
        self.traces: List[List[str]] = traces
        self.activity_mapping = activity_mapping
        self._summary_cache: Dict[str, List[dict]] = {}

    def query(self) -> "_TraceQuery":
        return _TraceQuery(self)

    def analyse_target(self, target: str) -> List[dict]:
        if target not in self._summary_cache:
            summary, _, _ = analyse_no_pm(
                self.goal_model,
                sequences_to_event_log(self.traces),
                [target],
                self.activity_mapping,
            )
            self._summary_cache[target] = summary
        return self._summary_cache[target]

    def _normalize_trace(self, trace: Union[str, Iterable[str]]) -> List[str]:
        """Normalize trace values to a list of activity labels."""
        if isinstance(trace, str):
            return [part.strip() for part in trace.split(" | ") if part.strip()]
        return list(trace)

    def _trace_key(self, trace: Union[str, Iterable[str]]) -> Tuple[str, ...]:
        return tuple(self._normalize_trace(trace))

    def _trace_from_summary_item(self, item: dict) -> List[str]:
        return self._normalize_trace(item["trace"])

    def traces_by_status(self, target: str, status: str) -> List[List[str]]:
        summary = self.analyse_target(target)
        if status == ComplianceStatus.COMPLIANT:
            allowed: Set[str] = {
                ComplianceStatus.STRONGLY_COMPLIANT,
                ComplianceStatus.WEAKLY_COMPLIANT,
            }
            return [
                self._trace_from_summary_item(s)
                for s in summary
                if s["goal_class"] in allowed
            ]
        return [
            self._trace_from_summary_item(s)
            for s in summary
            if s["goal_class"] == status
        ]


class _TraceQuery:
    def __init__(self, dsl: TraceFilter) -> None:
        self.dsl = dsl
        self._selected_traces: Optional[List[List[str]]] = None

    def where(self, target: str, status: str) -> "_TraceQuery":
        traces = self.dsl.traces_by_status(target, status)
        if self._selected_traces is None:
            self._selected_traces = list(traces)
        else:
            allowed = {self.dsl._trace_key(trace) for trace in traces}
            self._selected_traces = [
                trace
                for trace in self._selected_traces
                if self.dsl._trace_key(trace) in allowed
            ]
        return self

    def and_where(self, target: str, status: str) -> "_TraceQuery":
        return self.where(target, status)

    def or_where(self, target: str, status: str) -> "_TraceQuery":
        """Union of current selection with traces matching the given status."""
        traces = self.dsl.traces_by_status(target, status)
        if self._selected_traces is None:
            self._selected_traces = list(self._effective_traces())
        else:
            existing_keys = {self.dsl._trace_key(t) for t in self._selected_traces}
            for trace in traces:
                if self.dsl._trace_key(trace) not in existing_keys:
                    self._selected_traces.append(trace)
        return self

    def not_in(self) -> "_TraceQuery":
        """Complement of the current selection within all traces."""
        all_traces = [self.dsl._normalize_trace(t) for t in self.dsl.traces]
        if self._selected_traces is None:
            self._selected_traces = []
        else:
            excluded = {self.dsl._trace_key(t) for t in self._selected_traces}
            self._selected_traces = [
                t for t in all_traces if self.dsl._trace_key(t) not in excluded
            ]
        return self

    def filter(self, predicate: Callable[[List[str]], bool]) -> "_TraceQuery":
        """Apply a predicate to each trace (trace is a list of activity labels)."""
        self._selected_traces = [
            trace for trace in self._effective_traces() if predicate(trace)
        ]
        return self

    def contains(self, substring: str) -> "_TraceQuery":
        return self.filter(lambda trace: any(substring in activity for activity in trace))

    def not_contains(self, substring: str) -> "_TraceQuery":
        return self.filter(lambda trace: all(substring not in activity for activity in trace))

    def unique(self) -> "_TraceQuery":
        """Deduplicate traces while preserving order of first appearance."""
        seen: Set[Tuple[str, ...]] = set()
        unique_traces: List[List[str]] = []
        for trace in self._effective_traces():
            trace_key = self.dsl._trace_key(trace)
            if trace_key not in seen:
                seen.add(trace_key)
                unique_traces.append(trace)
        self._selected_traces = unique_traces
        return self

    def sort_by_length(self) -> "_TraceQuery":
        """Sort traces by length, from shortest to longest."""
        self._selected_traces = sorted(self._effective_traces(), key=len)
        return self

    def traces(self) -> List[List[str]]:
        return list(self._effective_traces())

    def frequency(self) -> Counter:
        """Count occurrences of each unique trace in the filtered set."""
        return Counter(tuple(t) for t in self._effective_traces())

    def _effective_traces(self) -> List[List[str]]:
        if self._selected_traces is None:
            return [self.dsl._normalize_trace(trace) for trace in self.dsl.traces]
        return self._selected_traces
