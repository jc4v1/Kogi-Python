import pytest
from NewSemantics.algorithms import check_stable_system, forward_bfs, backward_bfs, check_weak_compliance
from NewSemantics.transition_system import State, TransitionSystem
from NewSemantics.goal_model import GoalModel
from NewSemantics.istar_processor import read_istar_model
from NewSemantics.petri_net_processor import read_petri_net

def test_simple_real_gm_as_lts():
    gm = read_istar_model("tests/data/simple_gm.txt")
    lts = gm.as_lts()
    assert lts.states() == set()
    assert lts.initial_state() == None
    assert lts.transitions == {}