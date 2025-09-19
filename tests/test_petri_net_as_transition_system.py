import pytest
from typing import Any
from NewSemantics.algorithms import check_stable_system, forward_bfs, backward_bfs, check_weak_compliance
from NewSemantics.transition_system import State, TransitionSystem
from NewSemantics.goal_model import GoalModel
from NewSemantics.istar_processor import read_istar_model
from NewSemantics.petri_net_processor import read_petri_net
from pprint import pp
from Implementation.enums import ElementStatus, QualityStatus
from tests.utilities import pretty_print_states, states_to_str, transitions_to_str, pretty_print
from NewSemantics.transition_system import MarkingPn

# @pytest.mark.skip(reason="Temporarily disabled")
def test_simple_real_pm_as_ts():
    pn = read_petri_net("tests/data/simple_pm.pnml")
    ts = pn.as_transition_system()
    pretty_print(ts.transitions)

    # Example: expected states and transitions for a simple net with two places and one transition
    expected_states_set = {
        MarkingPn({'p1': 1, 'p2': 0}),
        MarkingPn({'p1': 0, 'p2': 1}),
    }
    expected_initial_state = MarkingPn({'p1': 1, 'p2': 0})
    expected_transitions = {
        MarkingPn({'p1': 1, 'p2': 0}): {'t1': {MarkingPn({'p1': 0, 'p2': 1})}},
        MarkingPn({'p1': 0, 'p2': 1}): {},
    }

    assert ts.states() == expected_states_set
    assert ts.initial_state() == expected_initial_state
    assert ts.transitions == expected_transitions

# @pytest.mark.skip(reason="Temporarily disabled")
def test_demo_pm_as_ts():
    pn = read_petri_net("Data/demo.pnml")
    ts = pn.as_transition_system()
    pretty_print_states(ts.states())
    pretty_print(ts.transitions)

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

    expected_transitions_str = """({p0} -t_1-> {p1, p2})
({p1, p2} -t_2-> {p2, p3})
({p1, p2} -t_3-> {p1, p4})
({p1, p4} -t_2-> {p3, p4})
{p10} -> {}
({p2, p3} -t_3-> {p3, p4})
({p3, p4} -t_4-> {p5})
({p5} -t_5-> {p6})
({p5} -t_6-> {p6})
({p6} -t_7-> {p7})
({p7} -t_8-> {p8})
({p8} -t_10-> {p9})
({p8} -t_9-> {p10})
({p9} -t_11-> {p7})"""

    actual_states_str = states_to_str(ts.states())
    actual_transitions_str = transitions_to_str(ts.transitions)

    assert actual_states_str.strip() == expected_states_str.strip()
    assert actual_transitions_str.strip() == expected_transitions_str.strip()