from Semantics.goal_model import GoalModel
from Semantics.enums import ElementStatus, LinkType
from tests.utilities import check_markings


def build_no_dependency_goal_model() -> GoalModel:
    gm = GoalModel()
    for task in ["Break", "Submit Declaration", "Break by Admin"]:
        gm.add_task(task)
    for goal in ["Money reimbursed", "Money Reimbursed (Dependum)", "Money Reimbursed by Admin", "Transaction Finished"]:
        gm.add_goal(goal)
    for quality in ["Increase employee satisfaction", "adequate declaration handling"]:
        gm.add_quality(quality)
    gm.add_link("Money reimbursed","Submit Declaration", LinkType.AND)
    gm.add_link("Money Reimbursed (Dependum)", "Money reimbursed", LinkType.OR)
    gm.add_link("Money Reimbursed by Admin", "Money Reimbursed (Dependum)", LinkType.OR)
    gm.add_link("Transaction Finished", "Money Reimbursed by Admin", LinkType.AND)
    gm.add_link("Increase employee satisfaction", "Money reimbursed", LinkType.MAKE)
    gm.add_link("Increase employee satisfaction", "Break", LinkType.BREAK)
    gm.add_link("adequate declaration handling", "Transaction Finished", LinkType.MAKE)
    gm.add_link("adequate declaration handling", "Break by Admin", LinkType.BREAK)
    return gm


def test_no_dependency_goal_model_initial_state():
    gm = build_no_dependency_goal_model()
    gm.kogi = False

    assert gm.leaves() == {"Break", "Break by Admin", "Submit Declaration"}
    gm.fire_element("Submit Declaration")
    gm.fire_element("Break")
    check_markings(
        gm,
        {
            "Break": ElementStatus.SATISFIED,
            "Submit Declaration": ElementStatus.PENDING,
            "Break by Admin": ElementStatus.UNKNOWN,
            "Money reimbursed": ElementStatus.PENDING,
            "Money Reimbursed (Dependum)": ElementStatus.PENDING,
            "Money Reimbursed by Admin": ElementStatus.PENDING,
            "Transaction Finished": ElementStatus.PENDING,
            "Increase employee satisfaction": ElementStatus.DENIED,
            "adequate declaration handling": ElementStatus.UNKNOWN,
        },
    )


def test_or_break_chain_with_and_parent():
    gm = GoalModel()
    gm.kogi = False
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_goal("G1")
    gm.add_goal("G2")
    gm.add_quality("Q1")

    gm.add_link("Q1", "T1", LinkType.BREAK)
    gm.add_link("G1", "T2", LinkType.OR)
    gm.add_link("Q1", "G1", LinkType.MAKE)
    gm.add_link("G2", "G1", LinkType.AND)

    gm.fire_element("T2")

    check_markings(gm, {
        "T2": ElementStatus.SATISFIED,
        "G1": ElementStatus.SATISFIED,
        "Q1": ElementStatus.SATISFIED,
        "G2": ElementStatus.SATISFIED,
        "T1": ElementStatus.UNKNOWN,
    })

    gm.fire_element("T1")

    check_markings(gm, {
        "Q1": ElementStatus.DENIED,
        "G1": ElementStatus.PENDING,
        "T2": ElementStatus.PENDING,
        "G2": ElementStatus.PENDING,
        "T1": ElementStatus.SATISFIED,
    })


def test_or_break_chain_with_or_parent():
    gm = GoalModel()
    gm.kogi = False
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_goal("G1")
    gm.add_goal("G2")
    gm.add_quality("Q1")

    gm.add_link("Q1", "T1", LinkType.BREAK)
    gm.add_link("G1", "T2", LinkType.AND)
    gm.add_link("Q1", "G1", LinkType.MAKE)
    gm.add_link("G2", "G1", LinkType.OR)

    gm.fire_element("T2")

    check_markings(gm, {
        "T2": ElementStatus.SATISFIED,
        "G1": ElementStatus.SATISFIED,
        "Q1": ElementStatus.SATISFIED,
        "G2": ElementStatus.SATISFIED,
        "T1": ElementStatus.UNKNOWN,
    })

    gm.fire_element("T1")

    check_markings(gm, {
        "Q1": ElementStatus.DENIED,
        "G1": ElementStatus.PENDING,
        "T2": ElementStatus.PENDING,
        "G2": ElementStatus.PENDING,
        "T1": ElementStatus.SATISFIED,
    })


def test_pending_reset_quality():
    gm = GoalModel()
    gm.kogi = False
    gm.add_task("T1")
    gm.add_task("T2")
    gm.add_task("T3")
    gm.add_quality("Q1")
    gm.add_quality("Q2")
    gm.add_link("Q1", "T1", LinkType.MAKE)
    gm.add_link("Q1", "T2", LinkType.BREAK)
    gm.add_link("Q2", "T2", LinkType.MAKE)
    gm.add_link("Q2", "T3", LinkType.BREAK)
    
    gm.fire_element("T1")
    gm.fire_element("T2")
    gm.fire_element("T3")
    
    assert gm.get_element_status("T1") == ElementStatus.PENDING
    assert gm.get_element_status("T2") == ElementStatus.PENDING
    assert gm.get_quality_status("Q1") == ElementStatus.UNKNOWN
