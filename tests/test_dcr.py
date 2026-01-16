import os
from Semantics.dcr import load_dcr_as_ts
from Semantics.dcr import DcrGraph, DcrMarking, DcrTransitionSystem

def test_load_dcr_ts():
    path = os.path.join(os.path.dirname(__file__), 'data', 'dcr_test.xml')
    path = os.path.normpath(path)
    ts = load_dcr_as_ts(path)
    # initial state should be part of states
    assert ts.initial_state() in ts.states()
    nstates, ntrans = ts.size()
    assert nstates >= 1
    # there's at least one enabled transition in the initial marking for this model
    enabled = ts.get_enabled_actions(ts.initial_state())
    assert len(enabled) >= 1

def make_graph(events, conditions=None, responses=None, excludes=None, includes=None, milestones=None, labels=None):
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
    _add(g.milestones, milestones)
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


def test_milestone_relation():
    # a -> b is a milestone: b enabled only if a is included and NOT pending
    g = make_graph(['a', 'b'], milestones={'a': {'b'}})
    # case 1: a included and not pending => both a and b enabled
    init1 = make_marking(executed=set(), included={'a', 'b'}, pending=set())
    ts1 = DcrTransitionSystem(g, init1).as_transition_system()
    print("milestone TS1 size:", ts1.size())

    m0 = init1
    m1 = DcrMarking({'a'}, {'a', 'b'}, set())
    m3 = DcrMarking({'b'}, {'a', 'b'}, set())
    m2 = DcrMarking({'a', 'b'}, {'a', 'b'}, set())

    assert {m0, m1, m2, m3}.issubset(ts1.states())

    expected_transitions_1 = {
        m0: {'a': {m1}, 'b': {m3}},
        m1: {'a': {m1}, 'b': {m2}},
        m3: {'a': {m2}, 'b': {m3}},
        m2: {'a': {m2}, 'b': {m2}}
    }
    for src, act_map in expected_transitions_1.items():
        for act, targets in act_map.items():
            assert ts1.transitions.get(src, {}).get(act) == targets

    # case 2: a included but pending => b disabled until a executed
    init2 = make_marking(executed=set(), included={'a', 'b'}, pending={'a'})
    ts2 = DcrTransitionSystem(g, init2).as_transition_system()
    print("milestone TS2 size:", ts2.size())

    m0p = init2
    m1 = DcrMarking({'a'}, {'a', 'b'}, set())
    m2 = DcrMarking({'a', 'b'}, {'a', 'b'}, set())

    assert {m0p, m1, m2}.issubset(ts2.states())

    expected_transitions_2 = {
        m0p: {'a': {m1}},
        m1: {'a': {m1}, 'b': {m2}},
        m2: {'a': {m2}, 'b': {m2}}
    }
    for src, act_map in expected_transitions_2.items():
        for act, targets in act_map.items():
            assert ts2.transitions.get(src, {}).get(act) == targets
