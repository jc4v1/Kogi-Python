import pytest
from Semantics.istar_processor import read_istar_model
from Semantics.petri_net_processor import read_petri_net
from Semantics.transition_system import combine_goal_model_and_petri_net, Marking, MarkingGm, MarkingPn, ElementStatus, QualityStatus
from tests.utilities import pretty_print, pretty_print_states
from Semantics.enums import ElementStatus, QualityStatus

# @pytest.mark.skip(reason="Temporarily disabled")
def test_simple_combined_system():
    gm = read_istar_model("tests/data/simple_gm.txt")
    pn = read_petri_net("tests/data/simple_pm.pnml")
    lts = combine_goal_model_and_petri_net(gm, pn, event_mapping=pn.get_default_event_mapping())
    print(lts.initial_state())
    pretty_print_states(lts.states())
    pretty_print(lts.transitions)

    # Construct expected initial state
    expected_initial_gm = MarkingGm({"Task": ElementStatus.UNKNOWN, "q": QualityStatus.UNKNOWN})
    expected_initial_pn = MarkingPn({"p1": 1, "p2": 0})
    expected_initial_state = Marking(expected_initial_gm, expected_initial_pn)
    assert lts.initial_state() == expected_initial_state

    # Construct expected states
    state1_gm = MarkingGm({"Task": ElementStatus.UNKNOWN, "q": QualityStatus.UNKNOWN})
    state1_pn = MarkingPn({"p1": 1, "p2": 0})
    state1 = Marking(state1_gm, state1_pn)

    state2_gm = MarkingGm({"Task": ElementStatus.TRUE_FALSE, "q": QualityStatus.FULFILLED})
    state2_pn = MarkingPn({"p1": 0, "p2": 1})
    state2 = Marking(state2_gm, state2_pn)

    expected_states = {state1, state2}
    assert lts.states() == expected_states

    # Construct expected transitions
    expected_transitions = {
        state1: {"t1": {state2}},
        state2: {}
    }
    # Compare transitions
    assert len(lts.transitions) == len(expected_transitions)
    for state, action_dict in expected_transitions.items():
        assert lts.transitions.get(state, {}) == action_dict
        
def test_demo_combined_system():
    gm = read_istar_model("tests/data/security/goal_model.txt")
    pn = read_petri_net("tests/data/security/petri_net.pnml")
    lts = combine_goal_model_and_petri_net(gm, pn, event_mapping=pn.get_default_event_mapping())
    print(lts.initial_state())
    pretty_print(lts.transitions)
    pretty_print_states(lts.states())
    qualities = { q for q, _ in gm.qualities.items()}
    print(f"qualities: {qualities}")
    res = lts.check_stability(qualities)
    assert res.is_err()
    res2 = lts.check_weak_compliance(qualities)
    assert res2.is_ok()

def test_demo_combined_system_fail():
    # We make weak compliance fail by removing the mapping for t_6
    # Thus not all paths in the Petri net ensure that all
    # qualities are fulfilled
    gm = read_istar_model("tests/data/security/goal_model.txt")
    pn = read_petri_net("tests/data/security/petri_net.pnml")
    gm.event_mapping = pn.get_default_event_mapping()
    gm.add_event_mapping('t_6', [])
    em = gm.event_mapping
    print(f"event mapping: {em}")
    lts = combine_goal_model_and_petri_net(gm, pn, event_mapping=em)
    # print(lts.initial_state())
    # pretty_print(lts.transitions)
    # pretty_print_states(lts.states())
    qualities = { q for q, _ in gm.qualities.items()}
    print(f"qualities: {qualities}")
    res = lts.check_stability(qualities)
    assert res.is_err()
    res2 = lts.check_weak_compliance(qualities)
    assert res2.is_err()
