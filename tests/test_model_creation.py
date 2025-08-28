import pytest
from NewSemantics.goal_model import GoalModel
from Implementation.enums import ElementStatus, LinkType, QualityStatus

def test_goal_model_creation():
    gm = GoalModel()
    assert isinstance(gm, GoalModel)
    
def test_pie_rule_task():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_goal("G")
    executed = gm.try_pie_rule("T")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T")
    assert ElementStatus.UNKNOWN == gm.get_element_status("G")
     
def test_pie_rule_goal():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_goal("G")
    executed = gm.try_pie_rule("G")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("G")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T")

def test_pie_rule_not_leaf():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_task("T1")
    gm.add_link("T","T1", LinkType.AND)
    executed = gm.try_pie_rule("T")
    assert not executed
    assert ElementStatus.UNKNOWN == gm.get_element_status("T")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T1")

def test_pand_rule_goal():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("T","T1", LinkType.AND)
    gm.add_link("T","T2", LinkType.AND) 
    executed = gm.try_pand_rule("T")
    assert not executed
    assert ElementStatus.UNKNOWN == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T")
    executed = gm.try_pie_rule("T1")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T")
    executed = gm.try_pand_rule("T")
    assert not executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T")
    executed = gm.try_pie_rule("T2")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T2")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T")
    executed = gm.try_pand_rule("T")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T2")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T")

def test_por_rule_goal():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("T","T1", LinkType.OR)
    gm.add_link("T","T2", LinkType.OR) 
    executed = gm.try_por_rule("T")
    assert not executed
    assert ElementStatus.UNKNOWN == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T")
    executed = gm.try_pie_rule("T1")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T")
    executed = gm.try_por_rule("T")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T")

def test_pmake_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("Q","T1", LinkType.MAKE)
    gm.add_link("Q","T2", LinkType.MAKE) 
    executed = gm.try_pmake_rule("Q")
    assert not executed
    assert ElementStatus.UNKNOWN == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert QualityStatus.UNKNOWN == gm.get_quality_status("Q")
    executed = gm.try_pie_rule("T1")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert QualityStatus.UNKNOWN == gm.get_quality_status("Q")
    executed = gm.try_pmake_rule("Q")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert QualityStatus.FULFILLED == gm.get_quality_status("Q")

def test_pbreak_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("Q","T1", LinkType.BREAK)
    gm.add_link("Q","T2", LinkType.BREAK) 
    executed = gm.try_pbreak_rule("Q")
    assert not executed
    assert ElementStatus.UNKNOWN == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert QualityStatus.UNKNOWN == gm.get_quality_status("Q")
    executed = gm.try_pie_rule("T2")
    assert executed
    assert ElementStatus.UNKNOWN == gm.get_element_status("T1")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T2")
    assert QualityStatus.UNKNOWN == gm.get_quality_status("Q")
    executed = gm.try_pmake_rule("Q")
    assert not executed
    assert ElementStatus.UNKNOWN == gm.get_element_status("T1")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T2")
    assert QualityStatus.UNKNOWN == gm.get_quality_status("Q")
    executed = gm.try_pbreak_rule("Q")
    assert executed
    assert ElementStatus.UNKNOWN == gm.get_element_status("T1")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T2")
    assert QualityStatus.DENIED == gm.get_quality_status("Q")
