import os

import pytest

from Semantics.parsers.istar_processor import read_istar_model


def _fixture_path(name: str) -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "data", name))


def _tests_data_fixture_path(name: str) -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "data", name))


def test_uniqueness_fixture_exposes_disambiguated_element_names():
    goal_model = read_istar_model(_fixture_path("gm_uniqueness_test.txt"))

    assert goal_model.elements() == {
        "G1",
        "Q1",
        "Quality",
        "duplicated name 2",
        "(Actor 1) duplicated name 1",
        "(Actor 2) duplicated name 1",
        "(Actor 2) duplicated name 2",
        "(Actor 2) duplicated name 1 (Actor 1)",
        "(Actor 2) duplicated name 1 (Actor)",
    }


def test_uniqueness_fixture_raises_when_qualified():
    with pytest.raises(ValueError, match="Duplicated Dependum"):
        read_istar_model(_fixture_path("gm_uniqueness_test.txt"), qualified=True)


def test_uniqueness_test2_fixture_exposes_disambiguated_element_names():
    goal_model = read_istar_model(_fixture_path("gm_uniqueness_test2.txt"))

    assert goal_model.elements() == {
        "(Actor 2) duplicated name 1",
        "(Actor 2) duplicated name 2",
        "Q1",
        "(Actor 1) duplicated name 1",
        "Quality",
        "G1",
        "duplicated name 1",
        "duplicated name 2",
        "new name 2",
    }


def test_uniqueness_test2_fixture_elements_are_fully_qualified_when_requested():
    goal_model = read_istar_model(_fixture_path("gm_uniqueness_test2.txt"), qualified=True)

    assert goal_model.elements() == {
        "(Actor 2) duplicated name 1",
        "(Actor 2) duplicated name 2",
        "(Actor 2) Q1",
        "(Actor 1) duplicated name 1",
        "(Actor 1) Quality",
        "(Actor) G1",
        "duplicated name 1",
        "duplicated name 2",
        "new name 2",
    }


def test_one_actor_fixture_elements_are_not_qualified_by_default():
    goal_model = read_istar_model(_tests_data_fixture_path("gm_one_actor.txt"), qualified=False)

    assert goal_model.elements() == {
        "Task",
        "Goal",
        "Quality",
    }


def test_one_actor_fixture_elements_are_fully_qualified_when_requested():
    goal_model = read_istar_model(_tests_data_fixture_path("gm_one_actor.txt"), qualified=True)

    assert goal_model.elements() == {
        "(Role) Task",
        "(Role) Goal",
        "(Role) Quality",
    }
