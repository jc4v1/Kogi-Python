import pytest
from NewSemantics.algorithms import check_stable_system, forward_bfs, backward_bfs, check_weak_compliance
from NewSemantics.lts import State, Lts
# --- Fixtures to set up test data ---

@pytest.fixture
def simple_lts():
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q'})
    s2 = State('s2', qualities={'p', 'q'})
    
    transitions = {
        s0: {s1},
        s1: {s2},
        s2: {s0}
    }
    
    return Lts(states={s0, s1, s2}, actions={'a'}, transitions=transitions, initial_state=s0)

@pytest.fixture
def stable_lts():
    # LTS where quality 'p' is persistent from s0
    # s0 -> s1 -> s2, all have 'p'
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'p'})
    s2 = State('s2', qualities={'p'})
    s3 = State('s3', qualities={'q'}) # A state reachable but not from a path with 'p'
    
    transitions = {
        s0: {s1},
        s1: {s2},
        s3: {s3}
    }
    
    return Lts(states={s0, s1, s2, s3}, actions={'a'}, transitions=transitions, initial_state=s0)

@pytest.fixture
def non_stable_lts():
    # LTS where quality 'p' is NOT persistent from s0
    # s0 -> s1, s0 has 'p', s1 does not
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q'})
    
    transitions = {
        s0: {s1},
        s1: {s1}
    }
    
    return Lts(states={s0, s1}, actions={'a'}, transitions=transitions, initial_state=s0)

# --- Test Functions for the Lts class methods ---

def test_weakly_complient_lts_get_successors(simple_lts):
    s0, s1, s2 = sorted(list(simple_lts.states), key=lambda x: x.name)
    assert simple_lts.get_successors(s0) == {s1}
    assert simple_lts.get_successors(s2) == {s0}
    assert simple_lts.get_successors(State('s_nonexistent')) == set()

def test_weakly_complient_lts_get_predecessors(simple_lts):
    s0, s1, s2 = sorted(list(simple_lts.states), key=lambda x: x.name)
    assert simple_lts.get_predecessors(s0) == {s2}
    assert simple_lts.get_predecessors(s1) == {s0}
    assert simple_lts.get_predecessors(State('s_nonexistent')) == set()

# --- Test Functions for BFS algorithms ---

def test_forward_bfs(simple_lts):
    s0, s1, s2 = sorted(list(simple_lts.states), key=lambda x: x.name)
    assert forward_bfs(simple_lts, s0) == {s0, s1, s2}
    assert forward_bfs(simple_lts, s2) == {s0, s1, s2}

def test_backward_bfs(simple_lts):
    s0, s1, s2 = sorted(list(simple_lts.states), key=lambda x: x.name)
    # Find all states that can reach s1
    assert backward_bfs(simple_lts, {s1}) == {s0, s1, s2}
    # Find all states that can reach s0
    assert backward_bfs(simple_lts, {s0}) == {s0, s1, s2}

# --- Test Functions for the main check_stable_system algorithm ---

def test_check_stable_system_holds(stable_lts):
    qualities_to_check = {'p'}
    assert check_stable_system(stable_lts, qualities_to_check) is True

def test_check_stable_system_fails(non_stable_lts):
    qualities_to_check = {'p'}
    assert check_stable_system(non_stable_lts, qualities_to_check) is False

def test_check_stable_system_multiple_qualities(simple_lts):
    # s0 has 'p', s1 has 'q', s2 has 'p' and 'q'
    # Check if 'p' is persistent from s0 (s0 -> s1 -> s2 -> s0). It is NOT, because s1 does not have p.
    assert check_stable_system(simple_lts, {'p'}) is False
    # Check if 'q' is persistent from s0. It is NOT, because s0 does not have q.
    assert check_stable_system(simple_lts, {'q'}) is False

def test_check_stable_system_deadlock_case():
    # LTS with a deadlock state that satisfies the property
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'p', 'q'})
    s2 = State('s2', qualities={'q'})
    
    transitions = {
        s0: {s1},
        s1: {}, # s1 is a deadlock state
    }
    
    lts = Lts(states={s0, s1, s2}, actions={'a'}, transitions=transitions, initial_state=s0)
    
    # AG(q => AG q) should hold because q is satisfied in s1 (deadlock), and no other state
    # reachable from s0 satisfies q
    assert check_stable_system(lts, {'q'}) is True
    assert check_stable_system(lts, {'p'}) is True

@pytest.fixture
def weakly_complient_lts_holds_cycle():
    # s0 -> s1 -> s2 -> s1. 
    # s1 has 'q', so EF(q) is always true for all reachable states.
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q'})
    s2 = State('s2', qualities={'r'})
    
    transitions = {
        s0: {s1},
        s1: {s2},
        s2: {s1}
    }
    
    return Lts(states={s0, s1, s2}, actions={'a'}, transitions=transitions, initial_state=s0)

@pytest.fixture
def weakly_complient_lts_holds_deadlock():
    # s0 -> s1 (deadlock). s1 has 'q'.
    # From s0, EF(q) holds. From s1, it's a deadlock, and it has 'q', so the condition holds.
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'q'})

    transitions = {
        s0: {s1},
        s1: {}
    }
    
    return Lts(states={s0, s1}, actions={'a'}, transitions=transitions, initial_state=s0)

@pytest.fixture
def weakly_complient_lts_fails():
    # s0 -> s1 (deadlock). Neither s0 nor s1 has 'q'.
    # The condition EF(q) is false for all reachable states.
    # The condition AX(false) and Q is false for all states.
    s0 = State('s0', qualities={'p'})
    s1 = State('s1', qualities={'r'})

    transitions = {
        s0: {s1},
        s1: {}
    }
    
    return Lts(states={s0, s1}, actions={'a'}, transitions=transitions, initial_state=s0)

# --- Test Functions for the check_weak_compliance algorithm ---

def test_weak_compliance_holds_with_cycle(weakly_complient_lts_holds_cycle):
    # The system can always reach a state with 'q'
    assert check_weak_compliance(weakly_complient_lts_holds_cycle, {'q'}) is True

def test_weak_compliance_holds_with_deadlock(weakly_complient_lts_holds_deadlock):
    # The deadlock state s1 satisfies the second part of the disjunction (AX(false) and Q)
    assert check_weak_compliance(weakly_complient_lts_holds_deadlock, {'q'}) is True

def test_weak_compliance_fails(weakly_complient_lts_fails):
    # The reachable states (s0, s1) do not satisfy the condition
    assert check_weak_compliance(weakly_complient_lts_fails, {'q'}) is False

def test_weak_compliance_with_no_qualities_in_lts(weakly_complient_lts_fails):
    # No states have the quality 'q', so it should fail
    assert check_weak_compliance(weakly_complient_lts_fails, {'q'}) is False

def test_weak_compliance_with_multiple_qualities(weakly_complient_lts_holds_cycle):
    # Q can be a set of qualities
    assert check_weak_compliance(weakly_complient_lts_holds_cycle, {'p', 'q'}) is True