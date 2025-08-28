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
    gm.set_element_status("T1", ElementStatus.TRUE_FALSE)
    gm.add_task("T2")
    gm.set_element_status("T2", ElementStatus.TRUE_FALSE)
    gm.add_link("T","T1", LinkType.AND)
    gm.add_link("T","T2", LinkType.AND) 
    executed = gm.try_pand_rule("T")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T2")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T")

def test_por_rule_goal():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_task("T1")
    gm.set_element_status("T1", ElementStatus.TRUE_FALSE)
    gm.add_task("T2")
    gm.add_link("T","T1", LinkType.OR)
    gm.add_link("T","T2", LinkType.OR) 
    executed = gm.try_por_rule("T")
    assert executed
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T1")
    assert ElementStatus.UNKNOWN == gm.get_element_status("T2")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T")

def test_pmake_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("T1")
    gm.set_element_status("T1", ElementStatus.TRUE_FALSE)
    gm.add_task("T2")
    gm.add_link("Q","T1", LinkType.MAKE)
    gm.add_link("Q","T2", LinkType.MAKE) 
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
    gm.set_element_status("T2", ElementStatus.TRUE_FALSE)
    gm.add_link("Q","T1", LinkType.BREAK)
    gm.add_link("Q","T2", LinkType.BREAK) 
    executed = gm.try_pbreak_rule("Q")
    assert executed
    assert ElementStatus.UNKNOWN == gm.get_element_status("T1")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("T2")
    assert QualityStatus.DENIED == gm.get_quality_status("Q")
    
def test_bpfulfill_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.set_quality_status("Q", QualityStatus.DENIED)
    gm.add_task("M")
    gm.set_element_status("M", ElementStatus.TRUE_FALSE)
    gm.add_task("B")
    gm.set_element_status("B", ElementStatus.TRUE_FALSE)
    gm.add_link("Q","M", LinkType.MAKE)
    gm.add_link("Q","B", LinkType.BREAK) 
    executed = gm.try_pmake_rule("Q")
    assert not executed
    executed = gm.try_pbreak_rule("Q")
    assert not executed
    executed = gm.try_bpfulfill_rule("Q")
    assert executed
    assert QualityStatus.FULFILLED == gm.get_quality_status("Q")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("M")   
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("B")   

def test_bpfulfill_transitive_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.set_quality_status("Q", QualityStatus.DENIED)
    gm.add_task("M")
    gm.add_link("Q","M", LinkType.MAKE)
    gm.set_element_status("M", ElementStatus.TRUE_FALSE)
    gm.add_task("B")
    gm.set_element_status("B", ElementStatus.TRUE_FALSE)
    gm.add_link("Q","B", LinkType.BREAK) 
    gm.add_task("BB1")
    gm.add_link("B","BB1", LinkType.AND)
    gm.set_element_status("BB1", ElementStatus.TRUE_FALSE)
    gm.add_task("BB2")
    gm.add_link("B","BB2", LinkType.AND)
    gm.set_element_status("BB2", ElementStatus.TRUE_FALSE)
    gm.add_task("BB3")
    gm.add_link("B","BB3", LinkType.OR)
    gm.set_element_status("BB3", ElementStatus.TRUE_FALSE)
    gm.add_task("BB4")
    gm.add_link("B","BB4", LinkType.OR)
    gm.set_element_status("BB4", ElementStatus.UNKNOWN)
    executed = gm.try_pmake_rule("Q")
    assert not executed
    executed = gm.try_pbreak_rule("Q")
    assert not executed
    executed = gm.try_bpfulfill_rule("Q")
    assert executed
    assert QualityStatus.FULFILLED == gm.get_quality_status("Q")
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("M")   
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("B")   
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("BB1")   
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("BB2")   
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("BB3")   
    assert ElementStatus.UNKNOWN == gm.get_element_status("BB4") 
    
def test_bpdeny_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.set_quality_status("Q", QualityStatus.FULFILLED)
    gm.add_task("M")
    gm.set_element_status("M", ElementStatus.TRUE_FALSE)
    gm.add_task("B")
    gm.set_element_status("B", ElementStatus.TRUE_FALSE)
    gm.add_link("Q","M", LinkType.MAKE)
    gm.add_link("Q","B", LinkType.BREAK) 
    executed = gm.try_pmake_rule("Q")
    assert not executed
    executed = gm.try_pbreak_rule("Q")
    assert not executed
    executed = gm.try_bpdeny_rule("Q")
    assert executed
    assert QualityStatus.DENIED == gm.get_quality_status("Q")
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("M")   
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("B")   

def test_bpdeny_transitive_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.set_quality_status("Q", QualityStatus.FULFILLED)
    gm.add_task("M")
    gm.add_link("Q","M", LinkType.MAKE)
    gm.set_element_status("M", ElementStatus.TRUE_FALSE)
    gm.add_task("B")
    gm.set_element_status("B", ElementStatus.TRUE_FALSE)
    gm.add_link("Q","B", LinkType.BREAK) 
    gm.add_task("MM1")
    gm.add_link("M","MM1", LinkType.AND)
    gm.set_element_status("MM1", ElementStatus.TRUE_FALSE)
    gm.add_task("MM2")
    gm.add_link("M","MM2", LinkType.AND)
    gm.set_element_status("MM2", ElementStatus.TRUE_FALSE)
    gm.add_task("MM3")
    gm.add_link("M","MM3", LinkType.OR)
    gm.set_element_status("MM3", ElementStatus.TRUE_FALSE)
    gm.add_task("MM4")
    gm.add_link("M","MM4", LinkType.OR)
    gm.set_element_status("MM4", ElementStatus.UNKNOWN)
    executed = gm.try_pmake_rule("Q")
    assert not executed
    executed = gm.try_pbreak_rule("Q")
    assert not executed
    executed = gm.try_bpdeny_rule("Q")
    assert executed
    assert QualityStatus.DENIED == gm.get_quality_status("Q")
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("M")   
    assert ElementStatus.TRUE_FALSE == gm.get_element_status("B")   
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("MM1")   
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("MM2")   
    assert ElementStatus.TRUE_TRUE == gm.get_element_status("MM3")   
    assert ElementStatus.UNKNOWN == gm.get_element_status("MM4") 
