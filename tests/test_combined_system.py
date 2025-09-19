import pytest
from NewSemantics.istar_processor import read_istar_model
from NewSemantics.petri_net_processor import read_petri_net
from NewSemantics.transition_system import combine_goal_model_and_petri_net

# @pytest.mark.skip(reason="Temporarily disabled")
def test_simple_combined_system():
    gm = read_istar_model("tests/data/simple_gm.txt")
    pn = read_petri_net("tests/data/simple_pm.pnml")
    lts = combine_goal_model_and_petri_net(gm, pn, event_mapping=None)

 