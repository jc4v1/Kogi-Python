import os
from Semantics.enums import ElementStatus, LinkType
from Semantics.parsers.istar_processor import read_istar_model


def _fixture_path(name: str) -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "data", name))


def _has_link(model, parent: str, child: str, ltype: LinkType) -> bool:
    return any(link[0] == parent and link[1] == child and link[2] == ltype for link in model.links)

def test_goal_dependency_model_exposes_dependency_object_and_dependency_links():
    model = read_istar_model(_fixture_path("gm_goal_dep.txt"))

    assert _has_link(model, "Q1", "G1", LinkType.DEPENDENCY)
    assert _has_link(model, "T1", "Q1", LinkType.DEPENDENCY)

    assert len(model.dependencies) == 1
    dep = model.dependencies[0]
    assert dep.source == "G1"
    assert dep.target == "T1"
    assert dep.dependum == "Q1"
    assert dep.dependum_type == "istar.Quality"

    assert model.get_element_status("T1") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q1") == ElementStatus.UNKNOWN
    assert model.get_element_status("G1") == ElementStatus.UNKNOWN
    
    model.fire_element("T1")

    assert model.get_element_status("T1") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q1") == ElementStatus.SATISFIED
    assert model.get_element_status("G1") == ElementStatus.SATISFIED


def test_all_qualities_dependency_model_is_read_correctly():
    model = read_istar_model(_fixture_path("gm_all_qualities.txt"))

    assert set(model.tasks.keys()) == {"T1"}
    assert set(model.goals.keys()) == set()
    assert set(model.qualities.keys()) == {"Q1", "Q2", "Q3"}

    assert _has_link(model, "Q1", "T1", LinkType.MAKE)
    assert _has_link(model, "Q1", "Q2", LinkType.DEPENDENCY)
    assert _has_link(model, "Q2", "Q3", LinkType.DEPENDENCY)

    assert len(model.dependencies) == 1
    dep = model.dependencies[0]
    assert dep.source == "Q3"
    assert dep.target == "Q1"
    assert dep.dependum == "Q2"
    assert dep.dependum_type == "istar.Quality"


def test_all_qualities_dependency_model_executes_dependency_chain():
    model = read_istar_model(_fixture_path("gm_all_qualities.txt"))

    assert model.get_element_status("T1") == ElementStatus.UNKNOWN

    assert model.get_quality_status("Q1") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q2") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q3") == ElementStatus.UNKNOWN

    model.fire_element("T1")

    assert model.get_element_status("T1") == ElementStatus.SATISFIED

    assert model.get_quality_status("Q1") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q2") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q3") == ElementStatus.SATISFIED

def test_break_dependency_model_structure_after_reading_goal_model():
    model = read_istar_model(_fixture_path("gm_break1.txt"))

    assert set(model.tasks.keys()) == {"T1", "T3", "T4", "T5"}
    assert set(model.goals.keys()) == set()
    assert set(model.qualities.keys()) == {"Q1", "Q2", "Q3"}

    assert _has_link(model, "T1", "Q2", LinkType.DEPENDENCY)
    assert _has_link(model, "Q2", "T3", LinkType.DEPENDENCY)
    assert _has_link(model, "Q1", "T3", LinkType.MAKE)
    assert _has_link(model, "Q1", "T4", LinkType.BREAK)
    assert _has_link(model, "Q3", "T5", LinkType.MAKE)
    assert _has_link(model, "Q3", "T3", LinkType.BREAK)

    assert len(model.dependencies) == 1
    dep = model.dependencies[0]
    assert dep.source == "T3"
    assert dep.target == "T1"
    assert dep.dependum == "Q2"
    assert dep.dependum_type == "istar.Quality"





def test_failed_Q1_denied():
    model = read_istar_model(_fixture_path("gm_break1.txt"))

    model.set_element_status("T1", ElementStatus.PENDING)
    model.set_element_status("T3", ElementStatus.PENDING)
    model.set_element_status("T4", ElementStatus.PENDING)
    model.set_element_status("T5", ElementStatus.SATISFIED)
    model.set_quality_status("Q1", ElementStatus.UNKNOWN)
    model.set_quality_status("Q2", ElementStatus.DENIED)
    model.set_quality_status("Q3", ElementStatus.SATISFIED)

    model.fire_element("T4")

    assert model.get_element_status("T1") == ElementStatus.PENDING
    assert model.get_quality_status("Q2") == ElementStatus.DENIED
    assert model.get_element_status("T3") == ElementStatus.PENDING
    assert model.get_quality_status("Q1") == ElementStatus.DENIED
    assert model.get_element_status("T4") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q3") == ElementStatus.SATISFIED
    assert model.get_element_status("T5") == ElementStatus.SATISFIED




def test_target_actor_model_structure():
    model = read_istar_model(_fixture_path("gm_target_actor.txt"))

    assert set(model.tasks.keys()) == {"Task", "Dependum"}
    assert set(model.goals.keys()) == set()
    assert set(model.qualities.keys()) == {"Quality Dependee"}

    # DependencyLink Dependum→Quality Dependee is stored; Actor 2→Dependum is skipped
    assert _has_link(model, "Quality Dependee", "Dependum", LinkType.DEPENDENCY)
    assert not _has_link(model, "Dependum", "Actor 2", LinkType.DEPENDENCY)
    assert _has_link(model, "Quality Dependee", "Task", LinkType.MAKE)

    assert len(model.dependencies) == 1
    dep = model.dependencies[0]
    assert dep.source == "Actor 2"
    assert dep.target == "Quality Dependee"
    assert dep.dependum == "Dependum"
    assert dep.dependum_type == "istar.Task"


def test_target_actor_model_execution_of_task():
    model = read_istar_model(_fixture_path("gm_target_actor.txt"))

    # Before
    assert model.get_element_status("Task") == ElementStatus.UNKNOWN
    assert model.get_element_status("Dependum") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Quality Dependee") == ElementStatus.UNKNOWN

    model.fire_element("Task")

    # Task satisfies itself (leaf), which satisfies Quality Dependee (make),
    # which propagates through the dependency link to satisfy Dependum (por/dependency)
    assert model.get_element_status("Task") == ElementStatus.SATISFIED
    assert model.get_quality_status("Quality Dependee") == ElementStatus.SATISFIED
    assert model.get_element_status("Dependum") == ElementStatus.SATISFIED

def test_source_actor_model_structure():
    model = read_istar_model(_fixture_path("gm_source_actor.txt"))

    assert set(model.tasks.keys()) == {"Task Depender", "Dependum"}

    assert _has_link(model, "Dependum", "Task Depender", LinkType.DEPENDENCY)

    assert len(model.dependencies) == 1
    dep = model.dependencies[0]
    assert dep.source == "Task Depender"
    assert dep.target == "Actor 2"
    assert dep.dependum == "Dependum"
    assert dep.dependum_type == "istar.Task"

# The test does not work. The "Task Depender" task is not a leaf
# because it depends on something from Actor 2. 
# Thus the pie rule does not fire. 
# Probably the intention was to have "Task Depender" being the dependee instead of the depnder and
# fire "Task Depender" to make the Dependum satisfied.
# However, the way the assertions are written, this does not seem to be the case either.

# def test_source_actor_model_execution_of_task():
#     model = read_istar_model(_fixture_path("gm_source_actor.txt"))

#     # Before
#     assert model.get_element_status("Task Depender") == ElementStatus.UNKNOWN
#     assert model.get_element_status("Dependum") == ElementStatus.UNKNOWN

#     model.fire_element("Task Depender")

#     # Task satisfies itself (leaf), which satisfies Quality Dependee (make),
#     # which propagates through the dependency link to satisfy Dependum (por/dependency)
#     assert model.get_element_status("Task Depender") == ElementStatus.SATISFIED
#     assert model.get_element_status("Dependum") == ElementStatus.UNKNOWN


def test_goccva_complex_multi_actor_model_structure():
    """Test complex scenario model structure with multiple actors and inter-actor dependencies."""
    model = read_istar_model(_fixture_path("gm_GoCCvA.txt"))

    # Verify model structure
    assert "Verify identity" in model.tasks
    assert "Identity verified by System" in model.tasks
    assert "Format Data Special Needs" in model.tasks
    assert "Data access provided" in model.goals
    assert "Identity verified by Officer" in model.goals
    assert "data easily accesible" in model.qualities

    # Check depenums are correctly identified (inter-actor dependencies)
    assert len(model.dependencies) == 3
    dependum_texts = {dep.dependum for dep in model.dependencies}
    assert "Identity verified" in dependum_texts
    assert "appropriate measures" in dependum_texts
    assert "data easily accesible" in dependum_texts



















