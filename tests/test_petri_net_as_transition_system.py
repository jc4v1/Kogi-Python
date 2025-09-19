import pytest
from typing import Any
from NewSemantics.algorithms import check_stable_system, forward_bfs, backward_bfs, check_weak_compliance
from NewSemantics.transition_system import State, TransitionSystem
from NewSemantics.goal_model import GoalModel
from NewSemantics.istar_processor import read_istar_model
from NewSemantics.petri_net_processor import read_petri_net
from pprint import pp
from Implementation.enums import ElementStatus, QualityStatus
from tests.utilities import generate_combinations
from NewSemantics.transition_system import MarkingPn

def transitions_to_str(transitions: dict[Any, set[Any]]) -> str:
    lines = []
    for state, next_states in sorted(list(transitions.items())):
        lines.append(f"({str(state)} -> {', '.join([str(s) for s in sorted(next_states)])})")
    return "\n".join(lines)

def pretty_print(transitions: dict[Any, set[Any]]):
    print(transitions_to_str(transitions))

def states_to_str(states: set[MarkingPn]) -> str:
    return "{\n" + ',\n '.join([str(s) for s in sorted(states)]) + "\n}"

def pretty_print_states(states: set[MarkingPn]):
    print(states_to_str(states))

# @pytest.mark.skip(reason="Temporarily disabled")
def test_simple_real_pm_as_ts():
    pn = read_petri_net("tests/data/simple_pm.pnml")
    ts = pn.as_transition_system()

    # Example: expected states and transitions for a simple net with two places and one transition
    expected_states_set = {
        MarkingPn({'p1': 1, 'p2': 0}),
        MarkingPn({'p1': 0, 'p2': 1}),
    }
    expected_initial_state = MarkingPn({'p1': 1, 'p2': 0})
    expected_transitions = {
        MarkingPn({'p1': 1, 'p2': 0}): {MarkingPn({'p1': 0, 'p2': 1})},
        MarkingPn({'p1': 0, 'p2': 1}): set(),
    }

    assert ts.states() == expected_states_set
    assert ts.initial_state() == expected_initial_state
    assert ts.transitions == expected_transitions

def test_demo_pm_as_ts():
    pn = read_petri_net("Data/demo.pnml")
    ts = pn.as_transition_system()

    expected_states_str = """{
{p0},
 {p1, p2},
 {p1, p4},
 {p10},
 {p2, p3},
 {p3, p4},
 {p5},
 {p6},
 {p7},
 {p8},
 {p9}
}"""

    expected_transitions_str = """({p0} -> {p1, p2})
({p1, p2} -> {p1, p4}, {p2, p3})
({p1, p4} -> {p3, p4})
({p10} -> )
({p2, p3} -> {p3, p4})
({p3, p4} -> {p5})
({p5} -> {p6})
({p6} -> {p7})
({p7} -> {p8})
({p8} -> {p10}, {p9})
({p9} -> {p7})"""

    actual_states_str = states_to_str(ts.states())
    actual_transitions_str = transitions_to_str(ts.transitions)

    assert actual_states_str.strip() == expected_states_str.strip()
    assert actual_transitions_str.strip() == expected_transitions_str.strip()