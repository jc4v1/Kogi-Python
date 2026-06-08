import json
from pathlib import Path
from typing import Dict, Set

import pandas as pd

from Semantics.goccva.pipeline import ABSENCE, analyse, map_move
from Semantics.goccva.helpers import load_logs
from Semantics.enums import ElementStatus
from Semantics.parsers.istar_processor import read_istar_model
from Semantics.parsers.petri_net_processor import read_petri_net
from Semantics.parsers.event_mapping_from_csv import read_event_mapping_csv

def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _case1_dir() -> Path:
    return _project_root() / "tests" / "data" / "goccva" / "case1"


def _fixtures():
    case_dir = _case1_dir()
    goal_model = read_istar_model(str(case_dir / "gm_unique2.txt"))
    petri_net = read_petri_net(str(case_dir / "pm.pnml"))
    _, noisy_log = load_logs(str(case_dir / "goccva_logs.json"))
    print(len(noisy_log))
    targets = ["Data access provided", "data easily accesible"]
    activity_mapping = read_event_mapping_csv(str(case_dir / "mapping.csv"))
    print(dict(activity_mapping))
    # activity_mapping: Dict[str, Set[str]] = {
    #     "(System) Identity verified": {"(System) Identity verified"},
    #     "Format Data Regular Needs": {"Format Data Regular Needs"},
    #     "Format Data Special Needs": {"Format Data Special Needs"},
    #     "Identity denied": {"Identity denied"},
    #     "Provide Records": {"Provide Records"},
    #     "Verify identity": {"Verify identity"},
    # }
    return goal_model, petri_net, noisy_log, targets, activity_mapping


def test_analyse_detailed_matches_expected() -> None:
    case_dir = _case1_dir()
    goal_model, petri_net, noisy_log, targets, activity_mapping = _fixtures()

    _, detailed, _ = analyse(goal_model, petri_net, noisy_log, targets, activity_mapping)

    expected = json.loads((case_dir / "expected_details.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(detailed)) == expected


def test_analyse_summary_matches_expected() -> None:
    case_dir = _case1_dir()
    goal_model, petri_net, noisy_log, targets, activity_mapping = _fixtures()

    summary, _, _ = analyse(goal_model, petri_net, noisy_log, targets, activity_mapping)

    expected_csv = (case_dir / "expected_summary.csv").read_text(encoding="utf-8")
    assert pd.DataFrame(summary).to_csv(index=False, lineterminator="\n") == expected_csv


def test_analyse_targets_match_expected() -> None:
    case_dir = _case1_dir()
    goal_model, petri_net, noisy_log, targets, activity_mapping = _fixtures()

    _, _, target_rows = analyse(goal_model, petri_net, noisy_log, targets, activity_mapping)

    expected_csv = (case_dir / "expected_targets.csv").read_text(encoding="utf-8")
    assert pd.DataFrame(target_rows).to_csv(index=False, lineterminator="\n") == expected_csv


def test_analyse_initial_marking_default_is_unknown() -> None:
    goal_model, petri_net, noisy_log, targets, activity_mapping = _fixtures()

    _, detailed, _ = analyse(goal_model, petri_net, noisy_log, targets, activity_mapping)

    first_theta = detailed[0]["goal_oriented_alignment"][0]["theta"]
    by_target = {item["target"]: item["status"] for item in first_theta}
    assert by_target["data easily accesible"] == "unknown"


def test_analyse_initial_marking_custom_overrides_default() -> None:
    goal_model, petri_net, noisy_log, targets, activity_mapping = _fixtures()

    _, detailed, _ = analyse(
        goal_model,
        petri_net,
        noisy_log,
        targets,
        activity_mapping,
        initial_marking={"data easily accesible": ElementStatus.SATISFIED},
    )

    first_theta = detailed[0]["goal_oriented_alignment"][0]["theta"]
    by_target = {item["target"]: item["status"] for item in first_theta}
    assert by_target["data easily accesible"] == "satisfied"


def test_map_move_log_move_returns_mapping_for_a() -> None:
    """Log move: a is present, b is ABSENCE — mapping for a is returned."""
    activity_mapping: Dict[str, Set[str]] = {
        "Verify identity": {"(System) Identity verified"},
        "Provide Records": {"Provide Records"},
    }
    move = ("Verify identity", ABSENCE)
    assert map_move(activity_mapping, move) == {"(System) Identity verified"}


def test_map_move_sync_move_returns_mapping_for_a() -> None:
    """Sync move: both a and b are present — mapping for a is returned."""
    activity_mapping: Dict[str, Set[str]] = {
        "Verify identity": {"(System) Identity verified"},
        "Provide Records": {"Provide Records"},
    }
    move = ("Verify identity", "Verify identity")
    assert map_move(activity_mapping, move) == {"(System) Identity verified"}


def test_map_move_model_move_returns_empty_set() -> None:
    """Model move: a is ABSENCE, b is present — empty set is returned."""
    activity_mapping: Dict[str, Set[str]] = {
        "Verify identity": {"(System) Identity verified"},
        "Provide Records": {"Provide Records"},
    }
    move = (ABSENCE, "Verify identity")
    assert map_move(activity_mapping, move) == set()


def test_map_move_log_move_not_in_mapping_returns_empty_set() -> None:
    """Log move: a is present but not in the mapping — empty set is returned."""
    activity_mapping: Dict[str, Set[str]] = {
        "Provide Records": {"Provide Records"},
    }
    move = ("Verify identity", ABSENCE)
    assert map_move(activity_mapping, move) == set()
