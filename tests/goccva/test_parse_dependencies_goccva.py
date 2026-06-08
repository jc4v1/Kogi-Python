import os
from Semantics.enums import ElementStatus, LinkType
from Semantics.parsers.istar_processor import read_istar_model


def _fixture_path(name: str) -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data", name))


def test_break_dependency_execution_statuses_before_t1_after_t1_after_t4():
    model = read_istar_model(_fixture_path("gm_break1.txt"))
    model.kogi = False
    
    # Before executing T1
    assert model.get_element_status("T1") == ElementStatus.UNKNOWN
    assert model.get_element_status("T3") == ElementStatus.UNKNOWN
    assert model.get_element_status("T4") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q1") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q2") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q3") == ElementStatus.UNKNOWN
    assert model.get_element_status("T5") == ElementStatus.UNKNOWN

    # After executing T1
    model.fire_element("T1")
    assert model.get_element_status("T1") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q2") == ElementStatus.SATISFIED
    assert model.get_element_status("T3") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q1") == ElementStatus.SATISFIED
    assert model.get_element_status("T4") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q3") == ElementStatus.DENIED
    assert model.get_element_status("T5") == ElementStatus.UNKNOWN

    # After executing T4
    model.fire_element("T4")
    assert model.get_element_status("T1") == ElementStatus.PENDING
    assert model.get_quality_status("Q2") == ElementStatus.UNKNOWN
    assert model.get_element_status("T3") == ElementStatus.PENDING
    assert model.get_quality_status("Q1") == ElementStatus.DENIED
    assert model.get_element_status("T4") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q3") == ElementStatus.UNKNOWN
    assert model.get_element_status("T5") == ElementStatus.UNKNOWN


def test_make_backprop():
    model = read_istar_model(_fixture_path("gm_break1.txt"))
    model.kogi = False
    
    # Before executing T1
    assert model.get_element_status("T1") == ElementStatus.UNKNOWN
    assert model.get_element_status("T3") == ElementStatus.UNKNOWN
    assert model.get_element_status("T4") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q1") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q2") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q3") == ElementStatus.UNKNOWN
    assert model.get_element_status("T5") == ElementStatus.UNKNOWN

    # After executing T1
    model.fire_element("T1")
    assert model.get_element_status("T1") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q2") == ElementStatus.SATISFIED
    assert model.get_element_status("T3") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q1") == ElementStatus.SATISFIED
    assert model.get_element_status("T4") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q3") == ElementStatus.DENIED
    assert model.get_element_status("T5") == ElementStatus.UNKNOWN

    # After executing T5
    model.fire_element("T5")
    assert model.get_element_status("T1") == ElementStatus.PENDING
    assert model.get_quality_status("Q2") == ElementStatus.UNKNOWN
    assert model.get_element_status("T3") == ElementStatus.PENDING
    assert model.get_quality_status("Q1") == ElementStatus.UNKNOWN
    assert model.get_element_status("T4") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q3") == ElementStatus.SATISFIED
    assert model.get_element_status("T5") == ElementStatus.SATISFIED


def test_break2_execution_statuses_before_t1_after_t1():
    model = read_istar_model(_fixture_path("gm_break2.txt"))
    model.kogi = False

    # Before executing T1
    assert model.get_element_status("T1") == ElementStatus.UNKNOWN
    assert model.get_element_status("T2") == ElementStatus.UNKNOWN
    assert model.get_element_status("T3") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q1") == ElementStatus.UNKNOWN
    assert model.get_quality_status("Q2") == ElementStatus.UNKNOWN

    # After executing T1
    model.fire_element("T1")
    assert model.get_element_status("T1") == ElementStatus.SATISFIED
    assert model.get_quality_status("Q1") == ElementStatus.DENIED
    assert model.get_quality_status("Q2") == ElementStatus.UNKNOWN
    assert model.get_element_status("T2") == ElementStatus.UNKNOWN
    assert model.get_element_status("T3") == ElementStatus.PENDING


def test_goccva_complex_multi_actor_execution_steps():
    model = read_istar_model(_fixture_path("gm_GoCCvA.txt"))
    model.kogi = False

    def snapshot() -> dict[str, ElementStatus]:
        statuses: dict[str, ElementStatus] = {}
        for task in model.tasks:
            statuses[task] = model.get_element_status(task)
        for goal in model.goals:
            statuses[goal] = model.get_element_status(goal)
        for quality in model.qualities:
            statuses[quality] = model.get_quality_status(quality)
        return statuses

    # After step 1: Identity verified by System
    model.fire_element("Identity verified by System")
    assert snapshot() == {
        "Format Data Regular Needs": ElementStatus.UNKNOWN,
        "Format Data Special Needs": ElementStatus.UNKNOWN,
        "Provide Records": ElementStatus.UNKNOWN,
        "Identity denied": ElementStatus.UNKNOWN,
        "Identity verified by System": ElementStatus.SATISFIED,
        "Verify identity": ElementStatus.UNKNOWN,
        "Data access provided": ElementStatus.UNKNOWN,
        "Identity verified by Officer": ElementStatus.SATISFIED,
        "Identity verified": ElementStatus.SATISFIED,
        "data easily accesible": ElementStatus.UNKNOWN,
            "(Hospital Officer) data easily accesible": ElementStatus.UNKNOWN,
        "confidentiality": ElementStatus.UNKNOWN,
        "appropriate measures": ElementStatus.SATISFIED,
    }

    # After step 2: Provide Records
    model.fire_element("Provide Records")
    assert snapshot() == {
        "Format Data Regular Needs": ElementStatus.UNKNOWN,
        "Format Data Special Needs": ElementStatus.UNKNOWN,
        "Provide Records": ElementStatus.SATISFIED,
        "Identity denied": ElementStatus.UNKNOWN,
        "Identity verified by System": ElementStatus.SATISFIED,
        "Verify identity": ElementStatus.UNKNOWN,
        "Data access provided": ElementStatus.UNKNOWN,
        "Identity verified by Officer": ElementStatus.SATISFIED,
        "Identity verified": ElementStatus.SATISFIED,
        "data easily accesible": ElementStatus.UNKNOWN,
            "(Hospital Officer) data easily accesible": ElementStatus.UNKNOWN,
        "confidentiality": ElementStatus.UNKNOWN,
        "appropriate measures": ElementStatus.SATISFIED,
    }

    # After step 3: Format Data Special Needs
    model.fire_element("Format Data Special Needs")
    assert snapshot() == {
        "Format Data Regular Needs": ElementStatus.UNKNOWN,
        "Format Data Special Needs": ElementStatus.SATISFIED,
        "Provide Records": ElementStatus.SATISFIED,
        "Identity denied": ElementStatus.UNKNOWN,
        "Identity verified by System": ElementStatus.SATISFIED,
        "Verify identity": ElementStatus.UNKNOWN,
        "Data access provided": ElementStatus.SATISFIED,
        "Identity verified by Officer": ElementStatus.SATISFIED,
        "Identity verified": ElementStatus.SATISFIED,
        "data easily accesible": ElementStatus.SATISFIED,
            "(Hospital Officer) data easily accesible": ElementStatus.SATISFIED,
        "confidentiality": ElementStatus.UNKNOWN,
        "appropriate measures": ElementStatus.SATISFIED,
    }

    # After step 4: Format Data Regular Needs
    model.fire_element("Format Data Regular Needs")
    assert snapshot() == {
        "Format Data Regular Needs": ElementStatus.SATISFIED,
        "Format Data Special Needs": ElementStatus.PENDING,
        "Provide Records": ElementStatus.SATISFIED,
        "Identity denied": ElementStatus.UNKNOWN,
        "Identity verified by System": ElementStatus.SATISFIED,
        "Verify identity": ElementStatus.UNKNOWN,
        "Data access provided": ElementStatus.PENDING,
        "Identity verified by Officer": ElementStatus.SATISFIED,
        "Identity verified": ElementStatus.SATISFIED,
        "data easily accesible": ElementStatus.UNKNOWN,
            "(Hospital Officer) data easily accesible": ElementStatus.DENIED,
        "confidentiality": ElementStatus.UNKNOWN,
        "appropriate measures": ElementStatus.SATISFIED,
    }


def test_dep_q_q_q_b():
    model = read_istar_model(_fixture_path("gm_dep_quality_quality_goal.txt"))
    model.kogi = False
    model.fire_element("T1")
    
    def snapshot() -> dict[str, ElementStatus]:
        statuses: dict[str, ElementStatus] = {}
        for task in model.tasks:
            statuses[task] = model.get_element_status(task)
        for goal in model.goals:
            statuses[goal] = model.get_element_status(goal)
        for quality in model.qualities:
            statuses[quality] = model.get_quality_status(quality)
        return statuses

    expected = {
        "T1": ElementStatus.SATISFIED,
        "T2": ElementStatus.UNKNOWN,
        "Q1": ElementStatus.SATISFIED,
        "D1": ElementStatus.SATISFIED,
        "Q3": ElementStatus.SATISFIED,
    }

    snapshot_statuses = snapshot()

    for name, status in expected.items():
        assert snapshot_statuses.get(name) == status
            
    model.fire_element("T2")
    
    expected = {
        "T1": ElementStatus.PENDING,
        "T2": ElementStatus.SATISFIED,
        "Q1": ElementStatus.DENIED,
        "D1": ElementStatus.UNKNOWN,
        "Q3": ElementStatus.UNKNOWN,
    }
    snapshot_statuses = snapshot()

    for name, status in expected.items():
        print(name, snapshot_statuses.get(name), status)
        assert snapshot_statuses.get(name) == status


def test_dep_q_q_g_b():
    model = read_istar_model(_fixture_path("gm_dep_quality_quality_goal.txt"))
    model.kogi = False
    model.fire_element("T3")
    
    def snapshot() -> dict[str, ElementStatus]:
        statuses: dict[str, ElementStatus] = {}
        for task in model.tasks:
            statuses[task] = model.get_element_status(task)
        for goal in model.goals:
            statuses[goal] = model.get_element_status(goal)
        for quality in model.qualities:
            statuses[quality] = model.get_quality_status(quality)
        return statuses

    expected = {
        "T3": ElementStatus.SATISFIED,
        "T4": ElementStatus.UNKNOWN,
        "Q2": ElementStatus.SATISFIED,
        "D2": ElementStatus.SATISFIED,
        "G1": ElementStatus.SATISFIED,
    }

    snapshot_statuses = snapshot()

    for name, status in expected.items():
        assert snapshot_statuses.get(name) == status
        
    model.fire_element("T4")
    
    expected = {
        "T3": ElementStatus.PENDING,
        "T4": ElementStatus.SATISFIED,
        "Q2": ElementStatus.DENIED,
        "D2": ElementStatus.UNKNOWN,
        "G1": ElementStatus.PENDING,
    }
    snapshot_statuses = snapshot()

    for name, status in expected.items():
        print(name, snapshot_statuses.get(name), status)
        assert snapshot_statuses.get(name) == status


def test_dep_q_g_q_b():
    model = read_istar_model(_fixture_path("gm_dep_quality_quality_goal.txt"))
    model.kogi = False
    model.fire_element("T5")
    
    def snapshot() -> dict[str, ElementStatus]:
        statuses: dict[str, ElementStatus] = {}
        for task in model.tasks:
            statuses[task] = model.get_element_status(task)
        for goal in model.goals:
            statuses[goal] = model.get_element_status(goal)
        for quality in model.qualities:
            statuses[quality] = model.get_quality_status(quality)
        return statuses

    q6_key = "(Actor 2) Q6" if "(Actor 2) Q6" in model.qualities else "Q6"

    expected = {
        "T5": ElementStatus.SATISFIED,
        "T6": ElementStatus.UNKNOWN,
        "Q4": ElementStatus.SATISFIED,
        "D3": ElementStatus.SATISFIED,
        q6_key: ElementStatus.SATISFIED,
    }

    snapshot_statuses = snapshot()

    for name, status in expected.items():
        assert snapshot_statuses.get(name) == status
        
    model.fire_element("T6")
    
    expected = {
        "T5": ElementStatus.PENDING,
        "T6": ElementStatus.SATISFIED,
        "Q4": ElementStatus.DENIED,
        "D3": ElementStatus.PENDING,
        q6_key: ElementStatus.UNKNOWN,
    }
    snapshot_statuses = snapshot()

    for name, status in expected.items():
        print(name, snapshot_statuses.get(name), status)
        assert snapshot_statuses.get(name) == status


def test_dep_g_g_q_b():
    model = read_istar_model(_fixture_path("gm_dep_quality_quality_goal.txt"))
    model.kogi = False
    model.fire_element("T9")
    q6_key = "(Actor 1) Q6" if "(Actor 1) Q6" in model.qualities else "Q6"
    
    def snapshot() -> dict[str, ElementStatus]:
        statuses: dict[str, ElementStatus] = {}
        for task in model.tasks:
            statuses[task] = model.get_element_status(task)
        for goal in model.goals:
            statuses[goal] = model.get_element_status(goal)
        for quality in model.qualities:
            statuses[quality] = model.get_quality_status(quality)
        return statuses

    expected = {
        "T9": ElementStatus.SATISFIED,
        "T10": ElementStatus.UNKNOWN,
        "G3": ElementStatus.SATISFIED,
        q6_key: ElementStatus.SATISFIED,
        "D5": ElementStatus.SATISFIED,
        "Q7": ElementStatus.SATISFIED,
    }

    snapshot_statuses = snapshot()

    for name, status in expected.items():
        assert snapshot_statuses.get(name) == status
        
    model.fire_element("T10")
    
    expected = {
        "T9": ElementStatus.PENDING,
        "T10": ElementStatus.SATISFIED,
        "G3": ElementStatus.PENDING,
        q6_key: ElementStatus.DENIED,
        "D5": ElementStatus.PENDING,
        "Q7": ElementStatus.UNKNOWN,
    }
    snapshot_statuses = snapshot()

    for name, status in expected.items():
        print(name, snapshot_statuses.get(name), status)
        assert snapshot_statuses.get(name) == status


def test_dep_g_g_q_b_m():
    model = read_istar_model(_fixture_path("gm_dep_quality_quality_goal.txt"))
    model.kogi = False
    model.fire_element("T9")
    q6_key = "(Actor 1) Q6" if "(Actor 1) Q6" in model.qualities else "Q6"
    
    def snapshot() -> dict[str, ElementStatus]:
        statuses: dict[str, ElementStatus] = {}
        for task in model.tasks:
            statuses[task] = model.get_element_status(task)
        for goal in model.goals:
            statuses[goal] = model.get_element_status(goal)
        for quality in model.qualities:
            statuses[quality] = model.get_quality_status(quality)
        return statuses

    expected = {
        "T9": ElementStatus.SATISFIED,
        "T10": ElementStatus.UNKNOWN,
        "T11": ElementStatus.UNKNOWN,
        "G3": ElementStatus.SATISFIED,
        q6_key: ElementStatus.SATISFIED,
        "D5": ElementStatus.SATISFIED,
        "Q7": ElementStatus.SATISFIED,
        "D5": ElementStatus.SATISFIED,
        "Q8": ElementStatus.DENIED,
    }

    snapshot_statuses = snapshot()

    for name, status in expected.items():
        print(name, snapshot_statuses.get(name), status)
        assert snapshot_statuses.get(name) == status
        
    model.fire_element("T11")
    
    expected = {
        "T9": ElementStatus.PENDING,
        "T10": ElementStatus.UNKNOWN,
        "T11": ElementStatus.SATISFIED,
        "G3": ElementStatus.PENDING,
        q6_key: ElementStatus.UNKNOWN,
        "D5": ElementStatus.PENDING,
        "Q7": ElementStatus.UNKNOWN,
        "Q8": ElementStatus.SATISFIED,
    }
    snapshot_statuses = snapshot()

    for name, status in expected.items():
        print(name, snapshot_statuses.get(name), status)
        assert snapshot_statuses.get(name) == status


def test_back_prop_execution_steps():
    model = read_istar_model(_fixture_path("gm_back_prop_test.txt"))
    model.kogi = False

    def snapshot() -> dict[str, ElementStatus]:
        statuses: dict[str, ElementStatus] = {}
        for task in model.tasks:
            statuses[task] = model.get_element_status(task)
        for goal in model.goals:
            statuses[goal] = model.get_element_status(goal)
        for quality in model.qualities:
            statuses[quality] = model.get_quality_status(quality)
        return statuses

    # After step 1: Identity verified by Officer
    model.fire_element("Identity verified by Officer")
    assert snapshot() == {
        "Format Data Regular Needs": ElementStatus.UNKNOWN,
        "Format Data Special Needs": ElementStatus.UNKNOWN,
        "Provide Records": ElementStatus.UNKNOWN,
        "Data access provided": ElementStatus.UNKNOWN,
        "Identity verified by Officer": ElementStatus.SATISFIED,
        "data easily accesible": ElementStatus.UNKNOWN,
    }

    # After step 2: Provide Records
    model.fire_element("Provide Records")
    assert snapshot() == {
        "Format Data Regular Needs": ElementStatus.UNKNOWN,
        "Format Data Special Needs": ElementStatus.UNKNOWN,
        "Provide Records": ElementStatus.SATISFIED,
        "Data access provided": ElementStatus.UNKNOWN,
        "Identity verified by Officer": ElementStatus.SATISFIED,
        "data easily accesible": ElementStatus.UNKNOWN,
    }

    # After step 3: Format Data Special Needs
    model.fire_element("Format Data Special Needs")
    assert snapshot() == {
        "Format Data Regular Needs": ElementStatus.UNKNOWN,
        "Format Data Special Needs": ElementStatus.SATISFIED,
        "Provide Records": ElementStatus.SATISFIED,
        "Data access provided": ElementStatus.SATISFIED,
        "Identity verified by Officer": ElementStatus.SATISFIED,
        "data easily accesible": ElementStatus.SATISFIED,
    }

    # After step 4: Format Data Regular Needs
    model.fire_element("Format Data Regular Needs")
    assert snapshot() == {
        "Format Data Regular Needs": ElementStatus.SATISFIED,
        "Format Data Special Needs": ElementStatus.PENDING,
        "Provide Records": ElementStatus.SATISFIED,
        "Data access provided": ElementStatus.PENDING,
        "Identity verified by Officer": ElementStatus.SATISFIED,
        "data easily accesible": ElementStatus.DENIED,
    }


def test_dep_q_g_g_b():
    model = read_istar_model(_fixture_path("gm_dep_quality_quality_goal.txt"))
    model.kogi = False
    model.fire_element("T7")
    
    def snapshot() -> dict[str, ElementStatus]:
        statuses: dict[str, ElementStatus] = {}
        for task in model.tasks:
            statuses[task] = model.get_element_status(task)
        for goal in model.goals:
            statuses[goal] = model.get_element_status(goal)
        for quality in model.qualities:
            statuses[quality] = model.get_quality_status(quality)
        return statuses

    expected = {
        "T7": ElementStatus.SATISFIED,
        "T8": ElementStatus.UNKNOWN,
        "Q5": ElementStatus.SATISFIED,
        "D4": ElementStatus.SATISFIED,
        "G2": ElementStatus.SATISFIED,
    }

    snapshot_statuses = snapshot()

    for name, status in expected.items():
        assert snapshot_statuses.get(name) == status
        
    model.fire_element("T8")
    
    expected = {
            "T7": ElementStatus.PENDING,
            "T8": ElementStatus.SATISFIED,
            "Q5": ElementStatus.DENIED,
            "D4": ElementStatus.PENDING,
            "G2": ElementStatus.PENDING,
    }
    snapshot_statuses = snapshot()

    for name, status in expected.items():
        print(name, snapshot_statuses.get(name), status)
        assert snapshot_statuses.get(name) == status
