import json
from pathlib import Path
import re

import pandas as pd
from pm4py.objects.log.obj import EventLog

from Semantics.goccva.pipeline import analyse_no_pm
from Semantics.goccva.helpers import load_logs
from Semantics.parsers.istar_processor import read_istar_model
from Semantics.parsers.event_mapping_from_csv import read_event_mapping_csv


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _no_pm_dir() -> Path:
    return _project_root() / "tests" / "data" / "goccva" / "no_pm"


def _fixtures():
    case_dir = _no_pm_dir()
    goal_model = read_istar_model(str(case_dir / "gm_unique2.txt"))
    _, noisy_log = load_logs(str(case_dir / "goccva_logs.json"))
    filtered_log = EventLog()
    for trace in noisy_log:
        trace_labels = [event["concept:name"] for event in trace]
        if trace_labels == [
            "Verify identity",
            "(System) Identity verified",
            "Format Data Special Needs",
            "Provide Records",
        ]:
            filtered_log.append(trace)
            break
    targets = ["Data access provided", "data easily accesible"]
    activity_mapping = read_event_mapping_csv(str(case_dir / "mapping.csv"))
    return goal_model, filtered_log, targets, activity_mapping


def _read_relaxed_json(path: Path):
    text = path.read_text(encoding="utf-8")
    normalized = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(normalized)


def test_analyse_no_pm_detailed_matches_expected() -> None:
    case_dir = _no_pm_dir()
    goal_model, noisy_log, targets, activity_mapping = _fixtures()

    _, detailed, _ = analyse_no_pm(goal_model, noisy_log, targets, activity_mapping)

    expected = _read_relaxed_json(case_dir / "expected_details.json")
    assert json.loads(json.dumps(detailed)) == expected


def test_analyse_no_pm_summary_matches_expected() -> None:
    case_dir = _no_pm_dir()
    goal_model, noisy_log, targets, activity_mapping = _fixtures()

    summary, _, _ = analyse_no_pm(goal_model, noisy_log, targets, activity_mapping)

    expected_csv = (case_dir / "expected_summary.csv").read_text(encoding="utf-8")
    assert pd.DataFrame(summary).to_csv(index=False, lineterminator="\n") == expected_csv


def test_analyse_no_pm_targets_match_expected() -> None:
    case_dir = _no_pm_dir()
    goal_model, noisy_log, targets, activity_mapping = _fixtures()

    _, _, target_rows = analyse_no_pm(goal_model, noisy_log, targets, activity_mapping)

    expected_csv = (case_dir / "expected_targets.csv").read_text(encoding="utf-8")
    assert pd.DataFrame(target_rows).to_csv(index=False, lineterminator="\n") == expected_csv
