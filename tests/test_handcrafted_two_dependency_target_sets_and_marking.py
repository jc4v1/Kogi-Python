from Semantics.enums import ElementStatus, LinkType
from Semantics.goal_model import GoalModel
from Semantics.parsers.istar_processor import read_istar_model

def _two_dependency_goal_model() -> GoalModel:
    return read_istar_model("tests/data/gm_two_deps.txt", qualified=False)

def test_compute_target_sets_follows_two_dependencies_to_leaf_task() -> None:
    gm = _two_dependency_goal_model()

    make_set, break_set, nr_set = gm.compute_target_sets("Adequate Declaration Handling")

    assert make_set == {"Submit Declaration"}
    assert break_set == set()
    assert nr_set == set()


def test_marking_propagates_satisfied_status_through_two_dependencies() -> None:
    gm = _two_dependency_goal_model()

    gm.fire_element("Submit Declaration")

    markings = gm.get_markings()
    assert markings["Submit Declaration"] == ElementStatus.SATISFIED
    assert markings["Declaration Reviewed"] == ElementStatus.SATISFIED
    assert markings["Declaration Ready For Payment"] == ElementStatus.SATISFIED
    assert markings["Adequate Declaration Handling"] == ElementStatus.SATISFIED
