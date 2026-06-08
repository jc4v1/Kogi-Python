from Semantics.goal_model import GoalModel
from Semantics.enums import ElementStatus, LinkType
from utilities import check_markings, set_markings

def test_pand_rule_goal():
    gm = GoalModel()
    gm.kogi = True
    gm.add_task("T")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("T","T1", LinkType.AND)
    gm.add_link("T","T2", LinkType.AND) 
    set_markings(gm, {"T1": ElementStatus.SATISFIED, "T2": ElementStatus.SATISFIED})
    gm.fire_element("T")
    check_markings(gm, {"T": ElementStatus.SATISFIED, "T1": ElementStatus.SATISFIED, "T2": ElementStatus.SATISFIED})

def test_por_rule_goal():
    gm = GoalModel()
    gm.kogi = True
    gm.add_task("T")
    gm.add_task("T1")
    gm.add_task("T2")
    set_markings(gm, {"T1": ElementStatus.SATISFIED})
    gm.add_link("T","T1", LinkType.OR)
    gm.add_link("T","T2", LinkType.OR) 
    gm.fire_element("T")
    check_markings(gm, {"T": ElementStatus.SATISFIED, "T1": ElementStatus.SATISFIED, "T2": ElementStatus.UNKNOWN})