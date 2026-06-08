from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import pairwise
from typing import Iterable

import networkx as nx
import pandas as pd

try:
    from GoRep.paths import ensure_repo_root_on_path
except ModuleNotFoundError:
    from paths import ensure_repo_root_on_path

ensure_repo_root_on_path()

from Semantics.goccva.pipeline import ABSENCE


def _class_key(value: object) -> str:
    return str(value or "").strip().lower().replace("_", "-").replace(" ", "-")


def _is_goal_problem(goal_class: object) -> bool:
    return "weak" in _class_key(goal_class) or "non" in _class_key(goal_class)


def _move_pattern(left: str, right: str) -> tuple[str | None, str | None]:
    # In the local GoCCvA pipeline the tuple is (log side, model side).
    if left == ABSENCE and right != ABSENCE:
        return "skipped", right
    if right == ABSENCE and left != ABSENCE:
        return "inserted", left
    # A pair with two different visible labels is not a synchronous move. In this
    # pipeline we do not create a "replaced" pattern from such pairs; replacements
    # should be explained by the surrounding log/model moves or a future explicit
    # replacement detector.
    return None, None


def build_lig(trace: list[str], trace_id: int) -> nx.DiGraph:
    graph = nx.DiGraph(trace_id=trace_id)
    for index, activity in enumerate(trace, start=1):
        graph.add_node(index, label=activity)
        if index > 1:
            graph.add_edge(index - 1, index, relation="directly-follows")
    return graph


def derive_alignment_patterns(detailed: list[dict], summary: list[dict], variants: Counter) -> pd.DataFrame:
    summary_by_id = {row["trace_id"]: row for row in summary}
    rows = []
    for item in detailed:
        trace_id = item["trace_id"]
        trace = item.get("trace", [])
        frequency = variants.get(tuple(trace), 1)
        summary_row = summary_by_id.get(trace_id, {})
        goal_class = summary_row.get("goal_class")
        traditional_class = summary_row.get("traditional_class")

        for left, right in item.get("pm4py_alignment", []):
            pattern, activity = _move_pattern(left, right)
            if pattern:
                rows.append(
                    {
                        "trace_id": trace_id,
                        "frequency": frequency,
                        "pattern": pattern,
                        "activity": activity,
                        "traditional_class": traditional_class,
                        "goal_class": goal_class,
                        "source": "pm4py alignment",
                    }
                )

        expected_counts = Counter()
        observed_counts = Counter(trace)
        model_order = []
        for left, right in item.get("pm4py_alignment", []):
            if right != ABSENCE:
                expected_counts[right] += 1
                if right not in model_order:
                    model_order.append(right)
        for activity, count in observed_counts.items():
            extra = count - expected_counts.get(activity, 0)
            if extra > 0:
                rows.append(
                    {
                        "trace_id": trace_id,
                        "frequency": frequency,
                        "pattern": "repeated",
                        "activity": activity,
                        "traditional_class": traditional_class,
                        "goal_class": goal_class,
                        "source": "trace frequency vs alignment",
                    }
                )

        model_position = {activity: index for index, activity in enumerate(model_order)}
        for left_activity, right_activity in pairwise(trace):
            if left_activity in model_position and right_activity in model_position:
                if model_position[left_activity] > model_position[right_activity]:
                    rows.append(
                        {
                            "trace_id": trace_id,
                            "frequency": frequency,
                            "pattern": "swapped",
                            "activity": f"{right_activity} before {left_activity}",
                            "traditional_class": traditional_class,
                            "goal_class": goal_class,
                            "source": "trace order vs model order",
                        }
                    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "trace_id",
                "frequency",
                "pattern",
                "activity",
                "traditional_class",
                "goal_class",
                "source",
            ]
        )
    return pd.DataFrame(rows).drop_duplicates()


def target_status_evidence(detailed: list[dict]) -> pd.DataFrame:
    rows = []
    for item in detailed:
        for step_index, step in enumerate(item.get("goal_oriented_alignment", []), start=1):
            left, right = step.get("move", ("", ""))
            for theta in step.get("theta", []):
                rows.append(
                    {
                        "trace_id": item["trace_id"],
                        "step": step_index,
                        "model_move": left,
                        "log_move": right,
                        "target": theta["target"],
                        "label": theta["label"],
                        "status": theta["status"],
                    }
                )
    return pd.DataFrame(rows)


def anomaly_target_evidence(patterns: pd.DataFrame, theta_rows: pd.DataFrame) -> pd.DataFrame:
    if patterns.empty or theta_rows.empty:
        return pd.DataFrame()

    evidence = []
    final_status = (
        theta_rows.sort_values("step")
        .groupby(["trace_id", "target"], as_index=False)
        .tail(1)
    )
    for _, pattern in patterns.iterrows():
        trace_targets = final_status[final_status["trace_id"] == pattern["trace_id"]]
        for _, target in trace_targets.iterrows():
            evidence.append(
                {
                    "trace_id": int(pattern["trace_id"]),
                    "frequency": int(pattern["frequency"]),
                    "pattern": pattern["pattern"],
                    "activity": pattern["activity"],
                    "target": target["target"],
                    "target_status": target["status"],
                    "goal_class": pattern["goal_class"],
                    "repair_pressure": _is_goal_problem(pattern["goal_class"])
                    or target["status"] != "satisfied",
                }
            )
    return pd.DataFrame(evidence).drop_duplicates()


@dataclass(frozen=True)
class RepairCandidate:
    candidate_id: str
    operation: str
    trigger: str
    description: str
    affected_targets: tuple[str, ...]
    support: int
    fitness_gain: float
    precision_risk: float
    structural_change_cost: float
    goal_delta: float
    soundness_required: str


def generate_repair_candidates(evidence: pd.DataFrame) -> list[RepairCandidate]:
    if evidence.empty:
        return []

    candidates = []
    grouped = (
        evidence.groupby(["pattern", "activity"], as_index=False)
        .agg(
            support=("frequency", "sum"),
            affected_targets=("target", lambda values: tuple(sorted(set(values)))),
            pressure=("repair_pressure", "max"),
        )
        .sort_values("support", ascending=False)
    )

    counter = 1
    for _, row in grouped.iterrows():
        pattern = row["pattern"]
        activity = row["activity"]
        support = int(row["support"])
        targets = tuple(row["affected_targets"])

        if pattern == "skipped":
            candidates.append(
                RepairCandidate(
                    f"R{counter}",
                    "add/delete decision",
                    f"{pattern}:{activity}",
                    f"Decide whether to add a controlled bypass for skipped '{activity}' or delete/forbid the bypass if it harms goals.",
                    targets,
                    support,
                    fitness_gain=0.45,
                    precision_risk=0.70,
                    structural_change_cost=0.30,
                    goal_delta=-0.20 if row["pressure"] else 0.05,
                    soundness_required="workflow-net soundness after bypass insertion/removal",
                )
            )
        elif pattern == "inserted":
            candidates.append(
                RepairCandidate(
                    f"R{counter}",
                    "add",
                    f"{pattern}:{activity}",
                    f"Consider adding observed activity '{activity}' at the aligned local context if it is a positive workaround.",
                    targets,
                    support,
                    fitness_gain=0.35,
                    precision_risk=0.45,
                    structural_change_cost=0.25,
                    goal_delta=0.10 if row["pressure"] else 0.20,
                    soundness_required="sound insertion between reached and leaving markings",
                )
            )
        elif pattern == "repeated":
            candidates.append(
                RepairCandidate(
                    f"R{counter}",
                    "controlled loop",
                    f"{pattern}:{activity}",
                    f"Add a guarded loop for repeated '{activity}' only if the repetition corresponds to recovery behavior.",
                    targets,
                    support,
                    fitness_gain=0.30,
                    precision_risk=0.35,
                    structural_change_cost=0.25,
                    goal_delta=0.25,
                    soundness_required="loop must preserve option to complete and avoid dead transitions",
                )
            )
        else:
            candidates.append(
                RepairCandidate(
                    f"R{counter}",
                    "swap/replace",
                    f"{pattern}:{activity}",
                    f"Evaluate a local reorder or replacement repair for '{activity}'.",
                    targets,
                    support,
                    fitness_gain=0.25,
                    precision_risk=0.25,
                    structural_change_cost=0.20,
                    goal_delta=0.30,
                    soundness_required="local replacement must preserve proper completion",
                )
            )
        counter += 1

    return candidates


def score_candidates(
    candidates: Iterable[RepairCandidate],
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    weights = weights or {
        "fitness": 0.25,
        "precision": 0.25,
        "goal": 0.30,
        "similarity": 0.10,
        "support": 0.10,
    }
    candidates = list(candidates)
    if not candidates:
        return pd.DataFrame()

    max_support = max(candidate.support for candidate in candidates) or 1
    rows = []
    for candidate in candidates:
        fitness_score = (candidate.fitness_gain + 1) / 2
        precision_score = 1 - candidate.precision_risk
        goal_score = (candidate.goal_delta + 1) / 2
        similarity_score = 1 - candidate.structural_change_cost
        support_score = candidate.support / max_support
        overall = (
            weights["fitness"] * fitness_score
            + weights["precision"] * precision_score
            + weights["goal"] * goal_score
            + weights["similarity"] * similarity_score
            + weights["support"] * support_score
        )
        rows.append(
            {
                **candidate.__dict__,
                "fitness_score": round(fitness_score, 3),
                "precision_score": round(precision_score, 3),
                "goal_score": round(goal_score, 3),
                "similarity_score": round(similarity_score, 3),
                "support_score": round(support_score, 3),
                "overall_score": round(overall, 3),
            }
        )
    return pd.DataFrame(rows).sort_values("overall_score", ascending=False)


def lig_summary(detailed: list[dict]) -> pd.DataFrame:
    rows = []
    for item in detailed:
        graph = build_lig(item.get("trace", []), item["trace_id"])
        rows.append(
            {
                "trace_id": item["trace_id"],
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "activities": " | ".join(
                    data["label"] for _, data in graph.nodes(data=True)
                ),
            }
        )
    return pd.DataFrame(rows)


def pattern_glossary() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "pattern": "skipped",
                "low-level signal": "model move",
                "meaning": "The process model expected an activity, but the log did not execute it.",
                "repair intuition": "Decide whether to forbid the bypass or add a controlled alternative path.",
            },
            {
                "pattern": "inserted",
                "low-level signal": "log move",
                "meaning": "The log executed an extra activity that the process model did not match.",
                "repair intuition": "Add the behavior only if it is a positive/accepted workaround.",
            },
            {
                "pattern": "repeated",
                "low-level signal": "extra occurrence compared with model-side alignment",
                "meaning": "An activity appears more often than expected.",
                "repair intuition": "Add a guarded loop if repetition is legitimate recovery behavior.",
            },
            {
                "pattern": "swapped",
                "low-level signal": "observed local order contradicts model-side order",
                "meaning": "Two activities occur in the opposite order.",
                "repair intuition": "Consider reordering, a swap template, or a parallel/choice structure.",
            },
        ]
    )


def gorep_function_map() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "step": "GoCCvA baseline",
                "function": "run_huba_analysis",
                "file": "GoRep/gorep_huba.py",
                "output": "summary, detailed, contribution_to_targets",
            },
            {
                "step": "Target status evidence",
                "function": "target_status_evidence",
                "file": "GoRep/gorep_repair.py",
                "output": "Theta/status row per target per alignment step",
            },
            {
                "step": "Anomaly patterns",
                "function": "derive_alignment_patterns",
                "file": "GoRep/gorep_repair.py",
                "output": "skipped/inserted/repeated/swapped patterns",
            },
            {
                "step": "Goal impact",
                "function": "anomaly_target_evidence",
                "file": "GoRep/gorep_repair.py",
                "output": "which anomaly affects which target",
            },
            {
                "step": "Repair candidates",
                "function": "generate_repair_candidates",
                "file": "GoRep/gorep_repair.py",
                "output": "candidate add/delete/swap/loop repair templates",
            },
            {
                "step": "Candidate ranking",
                "function": "score_candidates",
                "file": "GoRep/gorep_repair.py",
                "output": "multicriteria candidate ranking",
            },
        ]
    )


def render_lig(detailed: list[dict], trace_id: int = 1, ax=None):
    """Render a lightweight Local Instance Graph for one analysed trace variant."""
    import matplotlib.pyplot as plt

    item = next((row for row in detailed if row.get("trace_id") == trace_id), None)
    if item is None:
        raise ValueError(f"Trace id {trace_id} not found in detailed analysis.")

    graph = build_lig(item.get("trace", []), trace_id)
    labels = {
        node: f"{node}. {data['label']}"
        for node, data in graph.nodes(data=True)
    }
    pos = {node: (node, 0) for node in graph.nodes}

    if ax is None:
        width = max(10, graph.number_of_nodes() * 2.2)
        _, ax = plt.subplots(figsize=(width, 3.2))

    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=18,
        edge_color="#555555",
        width=1.8,
    )
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_size=2600,
        node_color="#F8FAFC",
        edgecolors="#1F2937",
        linewidths=1.4,
    )
    nx.draw_networkx_labels(
        graph,
        pos,
        labels=labels,
        ax=ax,
        font_size=9,
        font_weight="bold",
    )
    ax.set_title(f"LIG-like local instance graph for trace variant {trace_id}")
    ax.set_axis_off()
    return ax
