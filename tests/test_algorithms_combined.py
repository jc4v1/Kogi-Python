import pytest
from NewSemantics.algorithms import check_stable_system, forward_bfs, backward_bfs, check_weak_compliance
from NewSemantics.lts import State, Lts, LtsCombined, StateCombined
from NewSemantics.goal_model import GoalModel
from NewSemantics.istar_processor import read_istar_model
from NewSemantics.petri_net_processor import read_petri_net

# def test_simple_real_system():
#     petri_net = read_petri_net("tests/data/simple_pm.pnml")
#     goal_model = read_istar_model("tests/data/simple_gm.txt")
#     lts = LtsCombined(goal_model, petri_net, {"t": "Task"}, StateCombined({},{"p1":1}))
    
#     assert check_weak_compliance(lts, {'q'}) is True

