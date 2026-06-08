from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import pm4py
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.obj import EventLog

try:
    from GoRep.paths import REPO_ROOT, ensure_repo_root_on_path
except ModuleNotFoundError:
    from paths import REPO_ROOT, ensure_repo_root_on_path

ensure_repo_root_on_path()

from Semantics.parsers.event_mapping_from_csv import read_event_mapping_csv
from Semantics.goccva.helpers import sequences_to_event_log
from Semantics.goccva.pipeline import analyse
from Semantics.parsers.istar_processor import read_istar_model
from Semantics.parsers.petri_net_processor import read_petri_net


GOAL_MODEL_PATH = "content/TUEReimbursement/gm_huba_new_actor2.txt"
PROCESS_MODEL_PATH = "content/TUEReimbursement/domestic_declaration_ilpn_updated.pnml"
MAPPING_PATH = "content/TUEReimbursement/mapping_huba_new_actor.csv"
LOG_PATH = "content/TUEReimbursement/DomesticDeclarations.xes.gz"

TARGETS = [
    "(Admin) adequate declaration handling",
    "(Employee) Increase employee satisfaction",
]

ACTIVITY_ABBREVIATIONS = {
    "Declaration REJECTED by ADMINISTRATION": "ra",
    "Payment Handled": "ph",
    "Declaration REJECTED by BUDGET OWNER": "rb",
    "Declaration SAVED by EMPLOYEE": "dsv",
    "Declaration APPROVED by ADMINISTRATION": "aa",
    "Declaration REJECTED by EMPLOYEE": "er",
    "Request Payment": "rp",
    "Declaration SUBMITTED by EMPLOYEE": "ds",
    "Declaration APPROVED by BUDGET OWNER": "ba",
    "Declaration FINAL_APPROVED by SUPERVISOR": "as",
    "Declaration REJECTED by SUPERVISOR": "rs",
    "Declaration APPROVED by PRE_APPROVER": "pa",
    "Declaration REJECTED by PRE_APPROVER": "rpa",
    "Declaration REJECTED by MISSING": "rm",
    "t_tau_rev": "tau",
}


@dataclass
class HubaInputs:
    goal_model: object
    petri_net: object
    activity_mapping: dict
    full_log: EventLog
    targets: list[str]
    activity_abbreviations: dict[str, str]


def load_huba_inputs() -> HubaInputs:
    goal_model = read_istar_model(_repo_path(GOAL_MODEL_PATH), qualified=True)
    petri_net = read_petri_net(_repo_path(PROCESS_MODEL_PATH))
    activity_mapping = read_event_mapping_csv(_repo_path(MAPPING_PATH))
    activity_mapping = goal_model.canonicalize_activity_mapping(activity_mapping)
    full_log = log_converter.apply(
        pm4py.read_xes(_repo_path(LOG_PATH)),
        variant=log_converter.Variants.TO_EVENT_LOG,
    )
    return HubaInputs(
        goal_model=goal_model,
        petri_net=petri_net,
        activity_mapping=activity_mapping,
        full_log=full_log,
        targets=list(TARGETS),
        activity_abbreviations=dict(ACTIVITY_ABBREVIATIONS),
    )


def _repo_path(relative_path: str) -> str:
    return str(REPO_ROOT / Path(relative_path))


def traces_from_log(log: EventLog) -> list[list[str]]:
    return [[event["concept:name"] for event in trace] for trace in log]


def variant_frequencies(log: EventLog) -> Counter:
    return Counter(tuple(trace) for trace in traces_from_log(log))


def event_log_from_top_variants(log: EventLog, limit: int = 8) -> tuple[EventLog, Counter]:
    variants = variant_frequencies(log)
    top_sequences = [list(trace) for trace, _ in variants.most_common(limit)]
    return sequences_to_event_log(top_sequences), variants


def run_huba_analysis(inputs: HubaInputs, variant_limit: int = 8):
    analysis_log, variants = event_log_from_top_variants(inputs.full_log, limit=variant_limit)
    summary, detailed, contribution_to_targets = analyse(
        inputs.goal_model,
        inputs.petri_net,
        analysis_log,
        inputs.targets,
        inputs.activity_mapping,
        initial_marking=None,
    )
    return analysis_log, variants, summary, detailed, contribution_to_targets


def log_statistics(log: EventLog) -> pd.DataFrame:
    traces = traces_from_log(log)
    variants = variant_frequencies(log)
    activities = sorted({activity for trace in traces for activity in trace})
    rejection_activities = [activity for activity in activities if "REJECTED" in activity]
    payment_activity = "Payment Handled"
    submission_activity = "Declaration SUBMITTED by EMPLOYEE"

    rows = [
        ("cases", len(traces)),
        ("events", sum(len(trace) for trace in traces)),
        ("activity classes", len(activities)),
        ("trace variants", len(variants)),
        ("cases with payment", sum(payment_activity in trace for trace in traces)),
        (
            "cases with rejection",
            sum(any(activity in rejection_activities for activity in trace) for trace in traces),
        ),
        (
            "cases with resubmission",
            sum(trace.count(submission_activity) > 1 for trace in traces),
        ),
    ]
    return pd.DataFrame(rows, columns=["measure", "value"])


def summary_with_frequency(summary: Iterable[dict], variants: Counter) -> pd.DataFrame:
    rows = []
    for row in summary:
        trace_tuple = tuple(str(row.get("trace", "")).split(" | "))
        rows.append({**row, "frequency": variants.get(trace_tuple, 1)})
    return pd.DataFrame(rows)


def goal_alignment_table(detailed: list[dict], summary: list[dict], variants: Counter) -> pd.DataFrame:
    summary_by_id = {row["trace_id"]: row for row in summary}
    rows = []
    for item in detailed:
        trace_id = item["trace_id"]
        summary_row = summary_by_id.get(trace_id, {})
        trace = item.get("trace", [])
        theta_final = {}
        theta_evolution = {target: [] for target in item.get("targets", [])}
        rendered_moves = []
        for step in item.get("goal_oriented_alignment", []):
            left, right = step.get("move", ("", ""))
            rendered_moves.append(f"({left}, {right})")
            for theta in step.get("theta", []):
                theta_evolution[theta["target"]].append(
                    f"{theta['label']}:{theta['status']}"
                )
                theta_final[theta["target"]] = theta["status"]
        rows.append(
            {
                "trace_id": trace_id,
                "frequency": variants.get(tuple(trace), 1),
                "traditional_class": summary_row.get("traditional_class"),
                "goal_class": summary_row.get("goal_class"),
                "alignment_cost": summary_row.get("alignment_cost"),
                "trace": " | ".join(trace),
                "m_i alignment": " | ".join(rendered_moves),
                "Theta_i final": "; ".join(
                    f"{target}: {status}" for target, status in theta_final.items()
                ),
                "Theta_i evolution": theta_evolution,
            }
        )
    return pd.DataFrame(rows)
