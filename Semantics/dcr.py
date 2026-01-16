from __future__ import annotations
import xml.etree.ElementTree as ET
from collections import deque
from typing import Set, Dict

from Semantics.transition_system import TransitionSystem


class DcrGraph:
    def __init__(self):
        self.events: Set[str] = set()
        self.event_label: Dict[str, str] = {}
        # relations stored as mapping from source -> set[target]
        self.conditions: Dict[str, Set[str]] = {}
        self.responses: Dict[str, Set[str]] = {}
        self.excludes: Dict[str, Set[str]] = {}
        self.includes: Dict[str, Set[str]] = {}

    @classmethod
    def from_xml(cls, path: str) -> 'DcrGraph':
        tree = ET.parse(path)
        root = tree.getroot()
        g = cls()

        # events
        for ev in root.findall('.//specification/resources/events/event'):
            eid = ev.get('id')
            if eid:
                g.events.add(eid)

        # labels and mappings
        # labels: <label id="Register"/>
        labels = {lab.get('id'): lab.get('id') for lab in root.findall('.//specification/resources/labels/label')}
        for lm in root.findall('.//specification/resources/labelMappings/labelMapping'):
            eventId = lm.get('eventId')
            labelId = lm.get('labelId')
            if eventId and labelId:
                # store readable label (labels in this xml use id as the name)
                g.event_label[eventId] = labels.get(labelId, labelId)

        def add_rel(rel_dict, source, target):
            if source is None or target is None:
                return
            rel_dict.setdefault(source, set()).add(target)

        # parse constraints: conditions, responses, excludes, includes
        for cond in root.findall('.//specification/constraints/conditions/condition'):
            add_rel(g.conditions, cond.get('sourceId'), cond.get('targetId'))

        for resp in root.findall('.//specification/constraints/responses/response'):
            add_rel(g.responses, resp.get('sourceId'), resp.get('targetId'))

        for exc in root.findall('.//specification/constraints/excludes/exclude'):
            add_rel(g.excludes, exc.get('sourceId'), exc.get('targetId'))

        for inc in root.findall('.//specification/constraints/includes/include'):
            add_rel(g.includes, inc.get('sourceId'), inc.get('targetId'))

        return g


class DcrMarking:
    def __init__(self, executed: Set[str], included: Set[str], pending: Set[str], labels: Dict[str, str] | None = None):
        self.executed = set(executed)
        self.included = set(included)
        self.pending = set(pending)
        # optional mapping from event id -> readable label
        self.labels = dict(labels) if labels else None

    def __eq__(self, other):
        return isinstance(other, DcrMarking) and self.executed == other.executed and self.included == other.included and self.pending == other.pending

    def __hash__(self):
        return hash((frozenset(self.executed), frozenset(self.included), frozenset(self.pending)))

    def __repr__(self):
        def _map(eset):
            if not self.labels:
                return sorted(eset)
            return sorted([str(self.labels.get(e, e)) for e in eset])

        return f"(exe={_map(self.executed)}, inc={_map(self.included)}, pen={_map(self.pending)})"


class DcrTransitionSystem:
    """Builds a labelled transition system from a DCR graph."""
    def __init__(self, graph: DcrGraph, initial_marking: DcrMarking):
        self.graph = graph
        self.initial = initial_marking

    def enabled(self, marking: DcrMarking, event: str) -> bool:
        # enabled iff event is included and all condition predecessors that are included have been executed
        if event not in marking.included:
            return False
        # find predecessors that have condition -> event
        preds = {s for s, targets in self.graph.conditions.items() if event in targets}
        for p in preds:
            if p in marking.included and p not in marking.executed:
                return False
        return True

    def _apply_event(self, marking: DcrMarking, event: str) -> DcrMarking:
        exe = set(marking.executed)
        inc = set(marking.included)
        pen = set(marking.pending)

        # (i) executed
        exe.add(event)

        # (ii) pending responses: remove event itself, add responses targets
        pen.discard(event)
        for t in self.graph.responses.get(event, set()):
            if t in inc:
                pen.add(t)
            else:
                # if target not included currently, it still becomes pending per many DCR semantics
                pen.add(t)

        # (iii) update inclusion: remove excludes, add includes
        for t in self.graph.excludes.get(event, set()):
            if t in inc:
                inc.discard(t)

        for t in self.graph.includes.get(event, set()):
            inc.add(t)

        return DcrMarking(exe, inc, pen, labels=self.graph.event_label)

    def as_transition_system(self) -> TransitionSystem[DcrMarking]:
        # BFS explore reachable markings
        initial = self.initial
        visited = set()
        transitions: Dict[DcrMarking, Dict[str, Set[DcrMarking]]] = {}
        q = deque([initial])

        while q:
            m = q.popleft()
            if m in visited:
                continue
            visited.add(m)
            transitions[m] = {}

            for e in sorted(self.graph.events):
                if self.enabled(m, e):
                    # label for action
                    label = self.graph.event_label.get(e, e)
                    m2 = self._apply_event(m, e)
                    transitions[m].setdefault(label, set()).add(m2)
                    if m2 not in visited:
                        q.append(m2)

        return TransitionSystem(visited, transitions, initial)


def parse_runtime_marking(root, labels: Dict[str, str] | None = None) -> DcrMarking:
    # root is xml root
    executed = {ev.get('id') for ev in root.findall('.//runtime/marking/executed/event')}
    included = {ev.get('id') for ev in root.findall('.//runtime/marking/included/event')}
    pending = {ev.get('id') for ev in root.findall('.//runtime/marking/pendingResponses/event')}
    return DcrMarking(executed, included, pending, labels=labels)


def load_dcr_as_ts(path: str) -> TransitionSystem[DcrMarking]:
    tree = ET.parse(path)
    root = tree.getroot()
    graph = DcrGraph.from_xml(path)
    initial = parse_runtime_marking(root, labels=graph.event_label)
    dcr_ts = DcrTransitionSystem(graph, initial)
    return dcr_ts.as_transition_system()
