import pytest
from Semantics.algorithms import check_stable_system, forward_bfs, backward_bfs, check_weak_compliance
from Semantics.transition_system import State, TransitionSystem

@pytest.fixture
def simple_lts():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q'})
    s2 = State('s2', qualities={'p', 'q'})
    transitions = {
        s0: {'a': {s1}},
        s1: {'b': {s2}},
        s2: {'c': {s0}}
    }
    return TransitionSystem(states={s0, s1, s2}, transitions=transitions, initial_state=s0)

@pytest.fixture
def stable_lts():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'p'})
    s2 = State('s2', qualities={'p'})
    s3 = State('s3', qualities={'q'})
    transitions = {
        s0: {'a': {s1}},
        s1: {'b': {s2}},
        s3: {'c': {s3}}
    }
    return TransitionSystem(states={s0, s1, s2, s3}, transitions=transitions, initial_state=s0)

@pytest.fixture
def non_stable_lts():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q'})
    transitions = {
        s0: {'a': {s1}},
        s1: {'b': {s1}}
    }
    return TransitionSystem(states={s0, s1}, transitions=transitions, initial_state=s0)

def test_weakly_complient_lts_get_successors(simple_lts):
    s0, s1, s2 = sorted(list(simple_lts.states()), key=lambda x: x.name)
    assert simple_lts.get_successors(s0, 'a') == {s1}
    assert simple_lts.get_successors(s2, 'c') == {s0}
    assert simple_lts.get_successors(State('s_nonexistent')) == set()

def test_weakly_complient_lts_get_predecessors(simple_lts):
    s0, s1, s2 = sorted(list(simple_lts.states()), key=lambda x: x.name)
    assert simple_lts.get_predecessors(s0) == {s2}
    assert simple_lts.get_predecessors(s1) == {s0}
    assert simple_lts.get_predecessors(State('s_nonexistent')) == set()

def test_forward_bfs(simple_lts):
    s0, s1, s2 = sorted(list(simple_lts.states()), key=lambda x: x.name)
    assert forward_bfs(simple_lts, s0) == {s0, s1, s2}
    assert forward_bfs(simple_lts, s2) == {s0, s1, s2}

def test_backward_bfs(simple_lts):
    s0, s1, s2 = sorted(list(simple_lts.states()), key=lambda x: x.name)
    assert backward_bfs(simple_lts, {s1}) == {s0, s1, s2}
    assert backward_bfs(simple_lts, {s0}) == {s0, s1, s2}

def test_check_stable_system_holds(stable_lts):
    qualities_to_check = {'p'}
    assert check_stable_system(stable_lts, qualities_to_check)[0]

def test_check_stable_system_fails(non_stable_lts):
    qualities_to_check = {'p'}
    assert not check_stable_system(non_stable_lts, qualities_to_check)[0]

def test_check_stable_system_multiple_qualities(simple_lts):
    s0, s1, s2 = sorted(list(simple_lts.states()), key=lambda x: x.name)
    result_p = check_stable_system(simple_lts, {'p'})
    assert result_p[0] is False
    # assert result_p[1] == {s0,s2}
    assert result_p[1] == [('a',), ('a', 'b', 'c', 'a')]
    result_q = check_stable_system(simple_lts, {'q'})
    assert result_q[0] is False
    assert result_q[1] == [('a', 'b', 'c')]
    result_pq = check_stable_system(simple_lts, {'p', 'q'})
def test_check_stable_system_counterexamples(non_stable_lts):
    # non_stable_lts has s0 with 'p' and s1 without 'p', s0 -a-> s1
    res = check_stable_system(non_stable_lts, {'p'})
    assert res[0] is False
    counterexamples = res[1]
    # counterexamples should be a sorted list of traces, shortest-first
    assert isinstance(counterexamples, list)
    assert counterexamples[0] == ('a',)

def test_check_stable_system_deadlock_case():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'p', 'q'})
    s2 = State('s2', qualities={'q'})
    transitions = {
        s0: {'a': {s1}},
        s1: {},  # s1 is a deadlock state
    }
    lts = TransitionSystem(states={s0, s1, s2}, transitions=transitions, initial_state=s0)
    assert check_stable_system(lts, {'q'})[0]
    assert check_stable_system(lts, {'p'})[0]

def test_weak_compliance_holds_with_cycle():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q'})
    s2 = State('s2', qualities={'r'})
    transitions = {
        s0: {'a': {s1}},
        s1: {'b': {s2}},
        s2: {'c': {s1}}
    }
    lts = TransitionSystem(states={s0, s1, s2}, transitions=transitions, initial_state=s0)
    assert check_weak_compliance(lts, {'q'})[0]

def test_weak_compliance_holds_with_deadlock():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q'})
    transitions = {
        s0: {'a': {s1}},
        s1: {}
    }
    lts = TransitionSystem(states={s0, s1}, transitions=transitions, initial_state=s0)
    assert check_weak_compliance(lts, {'q'})[0]

def test_weak_compliance_fails():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'r'})
    transitions = {s0: {'a': {s1}}, s1: {}}
    lts = TransitionSystem(states={s0, s1}, transitions=transitions, initial_state=s0)
    assert not check_weak_compliance(lts, {'q'})[0]

def test_weak_compliance_with_no_qualities_in_lts():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'r'})
    transitions = {s0: {'a': {s1}}, s1: {}}
    lts = TransitionSystem(states={s0, s1}, transitions=transitions, initial_state=s0)
    assert not check_weak_compliance(lts, {'q1'})[0]

def test_weak_compliance_with_multiple_qualities():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q','r'})
    s2 = State('s2', qualities={'r'})
    transitions = {
        s0: {'a': {s1}},
        s1: {'b': {s2}},
        s2: {'c': {s1}}
    }
    lts = TransitionSystem(states={s0, s1, s2}, transitions=transitions, initial_state=s0)
    assert check_weak_compliance(lts, {'q', 'r'})[0]

def test_weak_compliance_with_multiple_qualities_fail():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q','r'})
    s2 = State('s2', qualities={'r'})
    transitions = {
        s0: {'a': {s1}},
        s1: {'b': {s2}},
        s2: {'c': {s1}}
    }
    lts = TransitionSystem(states={s0, s1, s2}, transitions=transitions, initial_state=s0)
    assert check_weak_compliance(lts, {'q', 'r'})[0]
    assert not check_stable_system(lts, {'q', 'r'})[0]
    assert not check_weak_compliance(lts, {'p', 't'})[0]