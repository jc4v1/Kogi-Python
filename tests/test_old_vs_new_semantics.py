import pytest
from NewSemantics.goal_model import GoalModel as NewGoalModel
from Implementation.goal_model import GoalModel as OldGoalModel
from Implementation.enums import ElementStatus, LinkType, QualityStatus

def test_and_the_same():
    old_model = create_model(OldGoalModel())
    new_model = create_model(NewGoalModel())
    trace = ["e1", "e2"]
    for event in trace:
        old_model.process_event(event)
        new_model.process_event(event)

    elements = ["T1", "T2", "G"]
    for element in elements:
        assert get_element_status(old_model,element) == get_element_status(new_model,element) == ElementStatus.TRUE_FALSE

def test_difference():
    old_model = create_model(OldGoalModel())
    new_model = create_model(NewGoalModel())
    trace = ["eg"]
    for event in trace:
        old_model.process_event(event)
        new_model.process_event(event)

    elements = ["T1", "T2"]
    for element in elements:
        assert get_element_status(old_model,element) == get_element_status(new_model,element) == ElementStatus.UNKNOWN

    # difference between old and new semantics
    # The pand rules says that G and only be TRUE_FALSE if all its sub-elements are TRUE_FALSE
    # The old semantics just sets G to TRUE_FALSE regardless of the status of its sub-elements
    old_model._get_element_status("G") == ElementStatus.TRUE_FALSE
    new_model._get_element_status("G") == ElementStatus.UNKNOWN

def create_model(gm):
    # Create elements
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

def get_element_status(model, element):
    if element in model.goals:
        return model.goals[element]
    elif element in model.tasks:
        return model.tasks[element]
    else: return None
