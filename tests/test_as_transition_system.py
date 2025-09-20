import pytest
from typing import Any
from NewSemantics.algorithms import check_stable_system, check_weak_compliance
from NewSemantics.istar_processor import read_istar_model
from Implementation.enums import ElementStatus, QualityStatus
from tests.utilities import pretty_print_states, states_to_str, transitions_to_str, pretty_print
from NewSemantics.transition_system import MarkingGm

# @pytest.mark.skip(reason="Temporarily disabled")
def test_simple_real_gm_as_ts_combined():
    gm = read_istar_model("tests/data/simple_gm.txt")
    initial_markings = gm.get_markings()
    ts = gm.as_transition_system()

    pretty_print_states(ts.states())
    pretty_print(ts.transitions)

    expected_states_set = {
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED}),
        MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.UNKNOWN}),
    }

    # Assert states
    assert ts.states() == expected_states_set

    # Assert initial state
    expected_initial_state = MarkingGm(initial_markings)
    assert ts.initial_state() == expected_initial_state

    # Define expected transitions as MarkingGm objects
    expected_transitions = {
       MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.UNKNOWN}): {
            'Task': {MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})}
        },
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED}): {
            'Task': {MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})}
        },
    }
    # Check that transitions match expected
    assert ts.transitions == expected_transitions
    # Optionally, print transitions for manual inspection
    # print("Transitions:")
    # pretty_print(ts.transitions)
    # Check stable system and weak compliance
    assert check_stable_system(ts, {'q'})[0]
    assert check_weak_compliance(ts, {'q'})[0]

# @pytest.mark.skip(reason="Temporarily disabled")
def test_simple_real_gm_as_ts_original():
    gm = read_istar_model("tests/data/simple_gm.txt")
    initial_markings = gm.get_markings()
    ts = gm.as_transition_system(True)
    pretty_print(ts.transitions)
    # Assert states
    expected_states_set = {
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.UNKNOWN}),
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED}),
        MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.UNKNOWN}),
    }
    assert ts.states() == expected_states_set

    # Assert initial state
    expected_initial_state = MarkingGm(initial_markings)
    assert ts.initial_state() == expected_initial_state

    # Define expected transitions as MarkingGm objects
    expected_transitions = {
        MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.UNKNOWN}): 
            {'Task': {MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.UNKNOWN})}},
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.UNKNOWN}): 
            {'q': {MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})}},
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED}): {},
    }
    # Check that transitions match expected
    assert ts.transitions == expected_transitions
    # Optionally, print transitions for manual inspection
    # print("Transitions:")
    # pretty_print(ts.transitions)
    # Check stable system and weak compliance
    assert check_stable_system(ts, {'q'})[0]
    assert check_weak_compliance(ts, {'q'})[0]

# @pytest.mark.skip(reason="Temporarily disabled")
def test_more_complex_gm():
    gm = read_istar_model("tests/data/more-complex_gm.txt")
    initial_markings = gm.get_markings()
    ts = gm.as_transition_system()
    # pretty_print(ts.transitions)
    print(f"Initial state: {ts.initial_state()}")
    print(f"Number of states: {len(ts.states())}")
    print(f"Number of transitions: {sum(len(v) for v in ts.transitions.values())}") 
    assert check_stable_system(ts, {'q1', 'q2'})[0]
    assert check_weak_compliance(ts, {'q1', 'q2'})[0]

def test_gm_with_break():
    gm = read_istar_model("tests/data/gm_with_break.txt")
    initial_markings = gm.get_markings()
    ts = gm.as_transition_system()
    # pretty_print(ts.transitions)
    print(f"Initial state: {ts.initial_state()}")
    print(f"Number of states: {len(ts.states())}")
    print(f"Number of transitions: {sum(len(v) for v in ts.transitions.values())}") 
    assert not check_stable_system(ts, {'q1'})[0]
    assert check_weak_compliance(ts, {'q1'})[0] 

# @pytest.mark.skip(reason="temporarily disabled")
def test_security_gm():
    gm = read_istar_model("Data/example_from_paper.txt")
    ts = gm.as_transition_system()
    # pretty_print(ts.transitions)
    print(f"Initial state: {ts.initial_state()}")
    print(f"Number of states: {len(ts.states())}")
    print(f"Number of transitions: {sum(len(v) for v in ts.transitions.values())}") 
    assert not check_stable_system(ts, {'DPA'})[0]
    assert check_weak_compliance(ts, {'DPA'})[0]
    
# @pytest.mark.skip(reason="temporarily disabled")
def test_airport_gm():
    gm = read_istar_model("tests/data/airport_gm.txt")
    ts = gm.as_transition_system()
    # pretty_print(ts.transitions)
    print(f"Initial state: {ts.initial_state()}")
    print(f"Number of states: {len(ts.states())}")
    print(f"Number of transitions: {sum(len(v) for v in ts.transitions.values())}") 
    assert check_stable_system(ts, {'nothing'})[0]
    assert check_stable_system(ts, {'Delay at arrival measured appropriately', 'Extraordinary circumstances documented appropriately'})[0]
    assert check_weak_compliance(ts, {'Delay at arrival measured appropriately', 'Extraordinary circumstances documented appropriately'})[0]