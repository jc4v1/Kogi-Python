from Semantics.goal_model import GoalModel
# rest of your imports
import pytest
from Semantics.enums import ElementStatus, LinkType
from tests.utilities import check_markings, set_markings




def test_pie_rule_task():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_goal("G")
    executed = gm.try_pie_rule("T")
    assert executed
    check_markings(gm, {"T": ElementStatus.SATISFIED, "G": ElementStatus.UNKNOWN})
     
def test_pie_rule_goal():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_goal("G")
    executed = gm.try_pie_rule("G")
    assert executed
    check_markings(gm, {"G": ElementStatus.SATISFIED, "T": ElementStatus.UNKNOWN})

def test_pie_rule_not_leaf():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_task("T1")
    gm.add_link("T","T1", LinkType.AND)
    executed = gm.try_pie_rule("T")
    assert not executed
    check_markings(gm, {"T": ElementStatus.UNKNOWN, "T1": ElementStatus.UNKNOWN})

def test_pand_rule_goal():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("T","T1", LinkType.AND)
    gm.add_link("T","T2", LinkType.AND) 
    set_markings(gm, {"T1": ElementStatus.SATISFIED, "T2": ElementStatus.SATISFIED})
    executed = gm.try_pand_s_rule("T")
    assert executed
    check_markings(gm, {"T": ElementStatus.SATISFIED, "T1": ElementStatus.SATISFIED, "T2": ElementStatus.SATISFIED})

def test_pand_pending_propagation():
    gm = GoalModel()
    gm.add_goal("G")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("G", "T1", LinkType.AND)
    gm.add_link("G", "T2", LinkType.AND)
    set_markings(gm, {"T1": ElementStatus.SATISFIED, "T2": ElementStatus.PENDING})

    executed = gm.try_pand_p_rule("G")
    assert executed
    check_markings(gm, {"G": ElementStatus.PENDING, "T1": ElementStatus.SATISFIED, "T2": ElementStatus.PENDING})

def test_pand_unknown_no_propagation():
    gm = GoalModel()
    gm.add_goal("G")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("G", "T1", LinkType.AND)
    gm.add_link("G", "T2", LinkType.AND)
    set_markings(gm, {"T1": ElementStatus.SATISFIED, "T2": ElementStatus.UNKNOWN})

    executed = gm.try_pand_s_rule("G")
    assert not executed
    executed = gm.try_pand_p_rule("G")
    assert not executed
    check_markings(gm, {"G": ElementStatus.UNKNOWN, "T1": ElementStatus.SATISFIED, "T2": ElementStatus.UNKNOWN})

def test_por_rule_goal():
    gm = GoalModel()
    gm.add_task("T")
    gm.add_task("T1")
    gm.add_task("T2")
    set_markings(gm, {"T1": ElementStatus.SATISFIED})
    gm.add_link("T","T1", LinkType.OR)
    gm.add_link("T","T2", LinkType.OR) 
    executed = gm.try_por_s_rule("T")
    assert executed
    check_markings(gm, {"T": ElementStatus.SATISFIED, "T1": ElementStatus.SATISFIED, "T2": ElementStatus.UNKNOWN})

def test_pmake_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("T1")
    gm.set_element_status("T1", ElementStatus.SATISFIED)
    gm.add_task("T2")
    gm.add_link("Q","T1", LinkType.MAKE)
    gm.add_link("Q","T2", LinkType.MAKE) 
    gm.fire_element("Q")
    check_markings(gm, {"Q": ElementStatus.SATISFIED, "T1": ElementStatus.SATISFIED, "T2": ElementStatus.UNKNOWN})

def test_pbreak_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.set_element_status("T2", ElementStatus.SATISFIED)
    gm.add_link("Q","T1", LinkType.BREAK)
    gm.add_link("Q","T2", LinkType.BREAK) 
    gm.fire_element("Q")
    check_markings(gm, {"Q": ElementStatus.DENIED, "T1": ElementStatus.UNKNOWN, "T2": ElementStatus.SATISFIED})

def test_pmake_pending_propagation():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("Q", "T1", LinkType.MAKE)
    gm.add_link("Q", "T2", LinkType.MAKE)
    set_markings(gm, {"T1": ElementStatus.PENDING, "T2": ElementStatus.UNKNOWN})

    gm.fire_element("Q")
    check_markings(gm, {"Q": ElementStatus.UNKNOWN, "T1": ElementStatus.PENDING, "T2": ElementStatus.UNKNOWN})

def test_pbreak_pending_propagation():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("Q", "T1", LinkType.BREAK)
    gm.add_link("Q", "T2", LinkType.BREAK)
    set_markings(gm, {"T1": ElementStatus.PENDING, "T2": ElementStatus.UNKNOWN})

    executed = gm.try_pbreak_rule("Q")
    assert executed
    check_markings(gm, {"Q": ElementStatus.UNKNOWN, "T1": ElementStatus.PENDING, "T2": ElementStatus.UNKNOWN})

def test_pmake_unknown_no_propagation():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("Q", "T1", LinkType.MAKE)
    gm.add_link("Q", "T2", LinkType.MAKE)
    set_markings(gm, {"T1": ElementStatus.UNKNOWN, "T2": ElementStatus.UNKNOWN})

    executed = gm.try_pmake_rule("Q")
    assert not executed
    check_markings(gm, {"Q": ElementStatus.UNKNOWN, "T1": ElementStatus.UNKNOWN, "T2": ElementStatus.UNKNOWN})

def test_pbreak_unknown_no_propagation():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("Q", "T1", LinkType.BREAK)
    gm.add_link("Q", "T2", LinkType.BREAK)
    set_markings(gm, {"T1": ElementStatus.UNKNOWN, "T2": ElementStatus.UNKNOWN})

    executed = gm.try_pbreak_rule("Q")
    assert not executed
    check_markings(gm, {"Q": ElementStatus.UNKNOWN, "T1": ElementStatus.UNKNOWN, "T2": ElementStatus.UNKNOWN})

def test_bpfulfill_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("M")
    gm.add_task("B")
    set_markings(gm, {"Q": ElementStatus.DENIED, "M": ElementStatus.SATISFIED, "B": ElementStatus.SATISFIED})
    gm.add_link("Q","M", LinkType.MAKE)
    gm.add_link("Q","B", LinkType.BREAK) 
    executed = gm.try_pmake_rule("Q")
    assert not executed
    executed = gm.try_pbreak_rule("Q")
    assert not executed
    executed = gm.try_bpfulfill_rule("Q")
    assert executed
    check_markings(gm, {"Q": ElementStatus.SATISFIED, "M": ElementStatus.SATISFIED, "B": ElementStatus.PENDING})

def test_bpfulfill_transitive_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("M")
    gm.add_link("Q","M", LinkType.MAKE)
    gm.add_task("B")
    gm.add_link("Q","B", LinkType.BREAK) 
    gm.add_task("BB1")
    gm.add_link("B","BB1", LinkType.AND)
    gm.add_task("BB2")
    gm.add_link("B","BB2", LinkType.AND)
    gm.add_task("BB3")
    gm.add_link("B","BB3", LinkType.OR)
    gm.add_task("BB4")
    set_markings(gm, {"Q": ElementStatus.DENIED, 
                      "M": ElementStatus.SATISFIED, 
                      "B": ElementStatus.SATISFIED, 
                      "BB1": ElementStatus.SATISFIED, 
                      "BB2": ElementStatus.SATISFIED, 
                      "BB3": ElementStatus.SATISFIED,
                      "BB4": ElementStatus.UNKNOWN})
    gm.add_link("B","BB4", LinkType.OR)
    executed = gm.try_pmake_rule("Q")
    assert not executed
    executed = gm.try_pbreak_rule("Q")
    assert not executed
    executed = gm.try_bpfulfill_rule("Q")
    assert executed
    check_markings(gm, {"Q": ElementStatus.SATISFIED, 
                        "M": ElementStatus.SATISFIED, 
                        "B": ElementStatus.PENDING, 
                        "BB1": ElementStatus.PENDING, 
                        "BB2": ElementStatus.PENDING, 
                        "BB3": ElementStatus.PENDING,
                        "BB4": ElementStatus.UNKNOWN})
    
def test_bpdeny_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("M")
    gm.add_task("B")
    set_markings(gm, {"Q": ElementStatus.SATISFIED, "M": ElementStatus.SATISFIED, "B": ElementStatus.SATISFIED})
    gm.add_link("Q","M", LinkType.MAKE)
    gm.add_link("Q","B", LinkType.BREAK) 
    executed = gm.try_pmake_rule("Q")
    assert not executed
    executed = gm.try_pbreak_rule("Q")
    assert not executed
    executed = gm.try_bpdeny_rule("Q")
    assert executed
    check_markings(gm, {"Q": ElementStatus.DENIED, "M": ElementStatus.PENDING, "B": ElementStatus.SATISFIED})

def test_bpdeny_transitive_rule():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_task("M")
    gm.add_link("Q","M", LinkType.MAKE)
    gm.add_task("B")
    gm.add_link("Q","B", LinkType.BREAK) 
    gm.add_task("MM1")
    gm.add_link("M","MM1", LinkType.AND)
    gm.add_task("MM2")
    gm.add_link("M","MM2", LinkType.AND)
    gm.add_task("MM3")
    gm.add_link("M","MM3", LinkType.OR)
    gm.add_task("MM4")
    gm.add_link("M","MM4", LinkType.OR)
    set_markings(gm, {"Q": ElementStatus.SATISFIED, 
                      "M": ElementStatus.SATISFIED, 
                      "B": ElementStatus.SATISFIED,
                      "MM1": ElementStatus.SATISFIED,
                      "MM2": ElementStatus.SATISFIED,
                      "MM3": ElementStatus.SATISFIED,
                      "MM4": ElementStatus.UNKNOWN})
    executed = gm.try_pmake_rule("Q")
    assert not executed
    executed = gm.try_pbreak_rule("Q")
    assert not executed
    executed = gm.try_bpdeny_rule("Q")
    assert executed
    check_markings(gm, {"Q": ElementStatus.DENIED, 
                        "M": ElementStatus.PENDING, 
                        "B": ElementStatus.SATISFIED,
                        "MM1": ElementStatus.PENDING,
                        "MM2": ElementStatus.PENDING,
                        "MM3": ElementStatus.PENDING,
                        "MM4": ElementStatus.UNKNOWN})

def test_propagation():
    gm = GoalModel()
    gm.add_quality("Q0")
    gm.add_goal("G")
    gm.add_task("T")
    gm.add_link("Q0","G", LinkType.MAKE)
    gm.add_link("G","T", LinkType.AND)
    
    gm.fire_element("T")
    
    assert {"T", "G", "Q0"} == gm.changed_elements
    
    check_markings(gm, {"Q0": ElementStatus.SATISFIED, "G": ElementStatus.SATISFIED, "T": ElementStatus.SATISFIED})
    

def test_propagation_failed():
    gm = GoalModel()
    gm.add_quality("Q0")
    gm.add_goal("G")
    gm.add_task("T")
    gm.add_link("Q0","G", LinkType.MAKE)
    gm.add_link("G","T", LinkType.AND)
    
    gm.fire_element("G")
    
    assert set() == gm.changed_elements
    
    check_markings(gm, {"Q0": ElementStatus.UNKNOWN, "G": ElementStatus.UNKNOWN, "T": ElementStatus.UNKNOWN})
    
def test_propagation_two_parents():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_goal("P1")
    gm.add_task("CP12")
    gm.add_goal("P2")
    gm.add_task("CP2")
    gm.add_link("Q","P1", LinkType.MAKE)
    gm.add_link("P1","CP12", LinkType.AND)
    gm.add_link("P2","CP12", LinkType.AND)
    gm.add_link("P2","CP2", LinkType.AND)
    
    gm.fire_element("CP2")
    assert {"CP2"} == gm.changed_elements
    gm.fire_element("CP12")
    assert {"CP12", "P2", "P1", "Q"} == gm.changed_elements

def test_bpfulfill_propagation_jump():
    gm = GoalModel()
    gm.add_quality("Q")
    gm.add_goal("M")
    gm.add_goal("B")
    gm.add_task("BB1")
    gm.add_task("BB2")
    gm.add_task("BB2B")
    set_markings(gm, {"Q": ElementStatus.DENIED, 
                      "M": ElementStatus.SATISFIED, 
                      "B": ElementStatus.SATISFIED, 
                      "BB1": ElementStatus.SATISFIED, 
                      "BB2": ElementStatus.UNKNOWN, 
                      "BB2B": ElementStatus.SATISFIED})
    gm.add_link("Q","M", LinkType.MAKE)
    gm.add_link("Q","B", LinkType.BREAK)
    gm.add_link("B","BB1", LinkType.OR)
    gm.add_link("B","BB2", LinkType.OR)
    gm.add_link("BB2","BB2B", LinkType.OR)
    executed = gm.try_bpfulfill_rule("Q")
    assert executed
    check_markings(gm, {"Q": ElementStatus.SATISFIED, 
                        "M": ElementStatus.SATISFIED, 
                        "B": ElementStatus.PENDING, 
                        "BB1": ElementStatus.PENDING, 
                        "BB2": ElementStatus.UNKNOWN, 
                        "BB2B": ElementStatus.PENDING})  

def test_por_pending_propagation():
    gm = GoalModel()
    gm.add_goal("G")
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_link("G", "T1", LinkType.OR)
    gm.add_link("G", "T2", LinkType.OR)
    set_markings(gm, {"T1": ElementStatus.PENDING, "T2": ElementStatus.UNKNOWN})
    
    executed = gm.try_por_p_rule("G")
    assert executed
    check_markings(gm, {"G": ElementStatus.PENDING, "T1": ElementStatus.PENDING, "T2": ElementStatus.UNKNOWN})  


