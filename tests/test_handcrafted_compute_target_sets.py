from Semantics.enums import LinkType
from Semantics.goal_model import GoalModel
from Semantics.goccva.target_sets import compute_target_sets, target_sets_as_rows


def _handcrafted_goal_model() -> GoalModel:
    gm = GoalModel()

    for task in [
        "Approve Declaration",
        "Handle Payment",
        "Reject Declaration",
        "Request Payment",
        "Save Declaration",
    ]:
        gm.add_task(task)

    for goal in [
        "Payment Completed",
        "Requirements Completed",
        "Declaration Rejected",
        "Rejected By Other Actor",
    ]:
        gm.add_goal(goal)

    gm.add_quality("Declaration Handling")
    gm.add_quality("Employee Satisfaction")

    gm.add_link("Declaration Handling", "Payment Completed", LinkType.MAKE)
    gm.add_link("Payment Completed", "Handle Payment", LinkType.AND)
    gm.add_link("Payment Completed", "Requirements Completed", LinkType.AND)
    gm.add_dependency(
        source="Requirements Completed",
        target="Approve Declaration",
        dependum="Declaration Approved",
        dependum_type="istar.Goal",
    )
    gm.add_dependency(
        source="Requirements Completed",
        target="Request Payment",
        dependum="Payment Requested",
        dependum_type="istar.Goal",
    )

    gm.add_link("Employee Satisfaction", "Declaration Rejected", LinkType.BREAK)
    gm.add_link("Declaration Rejected", "Rejected By Other Actor", LinkType.OR)
    gm.add_link("Declaration Rejected", "Reject Declaration", LinkType.OR)
    gm.add_dependency(
        source="Rejected By Other Actor",
        target="Reject Declaration",
        dependum="External Rejection",
        dependum_type="istar.Goal",
    )

    return gm


def test_quality_make_set_follows_refinements_and_dependencies() -> None:
    gm = _handcrafted_goal_model()

    make_set, break_set, nr_set = gm.compute_target_sets("Declaration Handling")

    assert make_set == {
        "Approve Declaration",
        "Handle Payment",
        "Request Payment",
    }
    assert break_set == set()
    assert nr_set == {
        "Reject Declaration",
        "Save Declaration",
    }


def test_quality_break_set_follows_break_contribution_to_leaf_tasks() -> None:
    gm = _handcrafted_goal_model()

    make_set, break_set, nr_set = gm.compute_target_sets("Employee Satisfaction")

    assert make_set == set()
    assert break_set == {"Reject Declaration"}
    assert nr_set == {
        "Approve Declaration",
        "Handle Payment",
        "Request Payment",
        "Save Declaration",
    }


def test_compute_target_sets_rows_are_sorted_and_named() -> None:
    gm = _handcrafted_goal_model()

    rows = target_sets_as_rows(compute_target_sets(gm, ["Declaration Handling"]))

    assert rows == [
        {
            "target": "Declaration Handling",
            "MakeSet": "Approve Declaration, Handle Payment, Request Payment",
            "BreakSet": "",
            "NRSet": "Reject Declaration, Save Declaration",
        }
    ]
