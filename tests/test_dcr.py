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

    init_state = ts.initial_state()
    enabled_init = set(ts.get_enabled_actions(init_state))
    assert enabled_init == {'a'}

    succs = ts.get_successors(init_state, 'a')
    assert len(succs) == 1
    m2 = next(iter(succs))
    assert m2.executed == {'a'}

    enabled_m2 = set(ts.get_enabled_actions(m2))
    # after executing 'a', 'b' should be enabled (executed events remain included
    # in this semantics, so 'a' may still be enabled as well)
    assert 'b' in enabled_m2


def test_response_relation():
    # a -> b is a response: executing a makes b pending
    g = make_graph(['a', 'b'], responses={'a': {'b'}})
    init = make_marking(executed=set(), included={'a', 'b'}, pending=set())
    ts = DcrTransitionSystem(g, init).as_transition_system()

    init_state = ts.initial_state()
    assert set(ts.get_enabled_actions(init_state)) == {'a', 'b'} or set(ts.get_enabled_actions(init_state)) == {'a', 'b'}

    succs = ts.get_successors(init_state, 'a')
    assert len(succs) == 1
    m2 = next(iter(succs))
    assert 'b' in m2.pending


def test_exclude_relation():
    # a excludes b: executing a removes b from included
    g = make_graph(['a', 'b'], excludes={'a': {'b'}})
    init = make_marking(executed=set(), included={'a', 'b'}, pending=set())
    ts = DcrTransitionSystem(g, init).as_transition_system()

    init_state = ts.initial_state()
    assert set(ts.get_enabled_actions(init_state)) == {'a', 'b'} or set(ts.get_enabled_actions(init_state)) == {'a', 'b'}

    succs = ts.get_successors(init_state, 'a')
    assert len(succs) == 1
    m2 = next(iter(succs))
    assert 'b' not in m2.included


def test_include_relation():
    # a includes b: executing a adds b to included
    g = make_graph(['a', 'b'], includes={'a': {'b'}})
    # initially only a included
    init = make_marking(executed=set(), included={'a'}, pending=set())
    ts = DcrTransitionSystem(g, init).as_transition_system()

    init_state = ts.initial_state()
    assert set(ts.get_enabled_actions(init_state)) == {'a'}

    succs = ts.get_successors(init_state, 'a')
    assert len(succs) == 1
    m2 = next(iter(succs))
    assert 'b' in m2.included
