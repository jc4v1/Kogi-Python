import pytest
from NewSemantics.goal_model import GoalModel as NewGoalModel
from Implementation.goal_model import GoalModel as OldGoalModel
from Implementation.enums import ElementStatus, LinkType, QualityStatus
from tests.utilities import check_markings, set_markings

def test_and_the_same():
    old_model = create_model(OldGoalModel())
    new_model = create_model(NewGoalModel())
    trace = ["e1", "e2"]
    for event in trace:
        old_model.process_event(event)
        new_model.process_event(event)

    markings = {"G": ElementStatus.TRUE_FALSE, "T1": ElementStatus.TRUE_FALSE, "T2": ElementStatus.TRUE_FALSE}

    check_markings(old_model, markings)
    check_markings(new_model, markings)

def test_difference_and_TRUE_TRUE():
    old_model = create_model(OldGoalModel())
    new_model = create_model(NewGoalModel())
    markings = {"G": ElementStatus.UNKNOWN, "T1": ElementStatus.TRUE_TRUE, "T2": ElementStatus.TRUE_FALSE}
    set_markings(old_model, markings)
    set_markings(new_model, markings)
    trace = ["eg"]
    for event in trace:
        old_model.process_event(event)
        new_model.process_event(event)

    markings_old = {"G": ElementStatus.TRUE_FALSE, "T1": ElementStatus.TRUE_TRUE, "T2": ElementStatus.TRUE_FALSE}

    # The difference is, that according to the pand rule, both T1 and T2 should be TRUE_FALSE to make G TRUE_FALSE.
    # Question is, should the pand rule be changed, to also allow for TRUE_FALSE if one of the sub-elements is TRUE_TRUE?

    markings_new = {"G": ElementStatus.UNKNOWN, "T1": ElementStatus.TRUE_TRUE, "T2": ElementStatus.TRUE_FALSE}
    check_markings(old_model, markings_old)
    check_markings(new_model, markings_new) 

def test_difference_and_UNKNOWN():
    old_model = create_model(OldGoalModel())
    new_model = create_model(NewGoalModel())
    markings = {"G": ElementStatus.UNKNOWN, "T1": ElementStatus.UNKNOWN, "T2": ElementStatus.UNKNOWN}
    set_markings(old_model, markings)
    set_markings(new_model, markings)
    trace = ["eg"]
    for event in trace:
        old_model.process_event(event)
        new_model.process_event(event)

    markings_old = {"G": ElementStatus.TRUE_FALSE, "T1": ElementStatus.UNKNOWN, "T2": ElementStatus.UNKNOWN}
    
    # The old model allows to set G to TRUE_FALSE, even if both T1 and T2 are UNKNOWN.
    # The new model requires both T1 and T2 to be TRUE_FALSE to set G to TRUE_FALSE.
    
    markings_new = {"G": ElementStatus.UNKNOWN, "T1": ElementStatus.UNKNOWN, "T2": ElementStatus.UNKNOWN}

    check_markings(old_model, markings_old)
    check_markings(new_model, markings_new) 

def create_model(gm):
    gm.add_goal("G")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("G", "T1", LinkType.AND)
    gm.add_link("G", "T2", LinkType.AND)
    gm.requirements = {
        "G": [['T1', 'T2']]
    }
    gm.add_event_mapping("eg", "G")
    gm.add_event_mapping("e1", "T1")
    gm.add_event_mapping("e2", "T2")
    return gm

