import os
from Semantics.dcr import load_dcr_as_ts
from Semantics.dcr import DcrGraph, DcrMarking, DcrTransitionSystem

def test_load_dcr_ts():
    path = os.path.join(os.path.dirname(__file__), '..', 'Data', 'example2', 'dcr.xml')
    path = os.path.normpath(path)
    ts = load_dcr_as_ts(path)
    # initial state should be part of states
    assert ts.initial_state() in ts.states()
    nstates, ntrans = ts.size()
    assert nstates >= 1
    # there's at least one enabled transition in the initial marking for this model
    enabled = ts.get_enabled_actions(ts.initial_state())
    assert len(enabled) >= 1

def make_graph(events, conditions=None, responses=None, excludes=None, includes=None, labels=None):
    g = DcrGraph()
    for e in events:
        g.events.add(e)
    if labels:
        g.event_label.update(labels)
    def _add(rel_dict, mapping):
        if not mapping:
            return
        for s, targets in mapping.items():
            rel_dict.setdefault(s, set()).update(set(targets))

    _add(g.conditions, conditions)
    _add(g.responses, responses)
    _add(g.excludes, excludes)
    _add(g.includes, includes)
    return g

def make_marking(executed=None, included=None, pending=None, labels=None):
    return DcrMarking(executed or set(), included or set(), pending or set(), labels=labels)

def test_condition_relation():
    # a -> b is a condition: b disabled until a executed
    g = make_graph(['a', 'b'], conditions={'a': {'b'}})
    init = make_marking(executed=set(), included={'a', 'b'}, pending=set())
    ts = DcrTransitionSystem(g, init).as_transition_system()
    print(ts.size())

    # expected reachable markings
    m0 = init
    m1 = DcrMarking({'a'}, {'a', 'b'}, set())
    m2 = DcrMarking({'a', 'b'}, {'a', 'b'}, set())

    assert {m0, m1, m2}.issubset(ts.states())

    expected_transitions = {
        m0: {'a': {m1}},
        m1: {'a': {m1}, 'b': {m2}},
        m2: {'a': {m2}, 'b': {m2}}
    }
    for src, act_map in expected_transitions.items():
        for act, targets in act_map.items():
            assert ts.transitions.get(src, {}).get(act) == targets

def test_response_relation():
    # a -> b is a response: executing a makes b pending
    g = make_graph(['a', 'b'], responses={'a': {'b'}})
    init = make_marking(executed=set(), included={'a', 'b'}, pending=set())
    ts = DcrTransitionSystem(g, init).as_transition_system()
    print(ts.size())

    # observed reachable markings (order-independent)
    m0 = init
    m1 = DcrMarking({'a'}, {'a', 'b'}, {'b'})
    m2 = DcrMarking({'a', 'b'}, {'a', 'b'}, set())
    m3 = DcrMarking({'a', 'b'}, {'a', 'b'}, {'b'})
    m4 = DcrMarking({'b'}, {'a', 'b'}, set())

    assert {m0, m1, m2, m3, m4}.issubset(ts.states())

    expected_transitions = {
        m0: {'a': {m1}, 'b': {m4}},
        m1: {'a': {m1}, 'b': {m2}},
        m4: {'a': {m3}, 'b': {m4}},
        m2: {'a': {m3}, 'b': {m2}},
        m3: {'a': {m3}, 'b': {m2}}
    }
    for src, act_map in expected_transitions.items():
        for act, targets in act_map.items():
            assert ts.transitions.get(src, {}).get(act) == targets

def test_exclude_relation():
    # a excludes b: executing a removes b from included
    g = make_graph(['a', 'b'], excludes={'a': {'b'}})
    init = make_marking(executed=set(), included={'a', 'b'}, pending=set())
    ts = DcrTransitionSystem(g, init).as_transition_system()
    print(ts.size())

    m0 = init
    m1 = DcrMarking({'a'}, {'a'}, set())
    m2 = DcrMarking({'b'}, {'a', 'b'}, set())
    m3 = DcrMarking({'a', 'b'}, {'a'}, set())

    assert {m0, m1, m2, m3}.issubset(ts.states())

    expected_transitions = {
        m0: {'a': {m1}, 'b': {m2}},
        m1: {'a': {m1}},
        m2: {'a': {m3}, 'b': {m2}},
        m3: {'a': {m3}}
    }
    for src, act_map in expected_transitions.items():
        for act, targets in act_map.items():
            assert ts.transitions.get(src, {}).get(act) == targets


def test_include_relation():
    # a includes b: executing a adds b to included
    g = make_graph(['a', 'b'], includes={'a': {'b'}})
    # initially only a included
    init = make_marking(executed=set(), included={'a'}, pending=set())
    ts = DcrTransitionSystem(g, init).as_transition_system()
    print(ts.size())

    m0 = init
    m1 = DcrMarking({'a'}, {'a', 'b'}, set())
    m2 = DcrMarking({'a', 'b'}, {'a', 'b'}, set())

    assert {m0, m1, m2}.issubset(ts.states())

    expected_transitions = {
        m0: {'a': {m1}},
        m1: {'a': {m1}, 'b': {m2}},
        m2: {'a': {m2}, 'b': {m2}}
    }
    for src, act_map in expected_transitions.items():
        for act, targets in act_map.items():
            assert ts.transitions.get(src, {}).get(act) == targets
