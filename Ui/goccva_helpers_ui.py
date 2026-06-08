import pandas as pd
from IPython.display import HTML, display

from Semantics.goccva.label_assignment import ABSENCE, label_mapped_elements
from Semantics.goccva.target_sets import compute_target_sets


MOVE_COLORS = {
    "M": "#7EE081",
    "B": "#FF7A7A",
    "NR": "#D9D9D9",
    "ND": "#BDBDBD",
}

MARKING_COLORS = {
    "S": "#7EE081",
    "P": "#74B9FF",
    "D": "#FF7A7A",
    "U": "#FFFFFF",
}

CLASS_COLORS = {
    "optimal alignment": "#008000",
    "non-optimal alignment": "#D00000",
}

FULFILMENT_COLORS = {
    "strong fulfilled": "#008000",
    "weak fulfilled": "#D98200",
    "non-fulfilled": "#D00000",
}


def create_activity_abbreviations(abbrev_dict):
    return abbrev_dict


def cell_style(value, kind):
    if kind == "move":
        color = MOVE_COLORS.get(value, "#FFFFFF")
    elif kind == "marking":
        color = MARKING_COLORS.get(value, "#FFFFFF")
    else:
        color = "#FFFFFF"

    return (
        f"background-color:{color}; "
        "color:#000000; "
        "text-align:center; "
        "font-weight:700; "
        "border:1px solid #555;"
    )


def trace_to_abbrev(trace, activity_abbreviations):
    return [activity_abbreviations.get(activity, activity) for activity in trace]


def split_case_label(label):
    alignment, fulfilment = label.split(" + ")
    return alignment.strip(), fulfilment.strip()


def classify_case(case):
    alignment_class, fulfilment_class = split_case_label(case["requested_case"])
    return alignment_class, fulfilment_class


def _status_to_marking_symbol(status):
    value = "" if status is None else str(status).strip().lower()
    mapping = {
        "s": "S",
        "satisfied": "S",
        "p": "P",
        "pending": "P",
        "d": "D",
        "denied": "D",
        "u": "U",
        "unknown": "U",
    }
    return mapping.get(value, "U")


def _goal_class_to_fulfilment(goal_class):
    key = str(goal_class or "").strip().lower().replace("_", "-").replace(" ", "-")
    mapping = {
        "strongly-compliant": "strong fulfilled",
        "strogly-compliant": "strong fulfilled",
        "weakly-compliant": "weak fulfilled",
        "non-compliant": "non-fulfilled",
        "strong-fulfilled": "strong fulfilled",
        "strongly-fulfilled": "strong fulfilled",
        "weak-fulfilled": "weak fulfilled",
        "weakly-fulfilled": "weak fulfilled",
        "non-fulfilled": "non-fulfilled",
    }
    return mapping.get(key, "non-fulfilled")


def _traditional_class_to_alignment(traditional_class):
    key = str(traditional_class or "").strip().lower()
    if key == "optimal":
        return "optimal alignment"
    return "non-optimal alignment"


def _target_order_from_contribution(contribution_to_targets):
    ordered_targets = []
    for row in contribution_to_targets or []:
        if not isinstance(row, dict):
            continue
        target = row.get("target")
        if target and target not in ordered_targets:
            ordered_targets.append(target)
    return ordered_targets


def _target_rows_from_detailed_trace(trace_item, ordered_targets):
    alignment_steps = trace_item.get("goal_oriented_alignment", [])
    theta_targets = []
    for step in alignment_steps:
        for theta in step.get("theta", []):
            target = theta.get("target")
            if target and target not in theta_targets:
                theta_targets.append(target)

    targets = [t for t in ordered_targets if t in theta_targets]
    if not targets:
        targets = trace_item.get("targets", [])
    if not targets:
        targets = theta_targets

    rows = {
        target: {
            "name": target,
            "labels": [],
            "markings": [],
        }
        for target in targets
    }

    for step in alignment_steps:
        theta_by_target = {
            theta.get("target"): theta
            for theta in step.get("theta", [])
            if isinstance(theta, dict)
        }
        for target in targets:
            theta = theta_by_target.get(target, {})
            rows[target]["labels"].append(theta.get("label", "ND"))
            rows[target]["markings"].append(_status_to_marking_symbol(theta.get("status")))

    return rows


def _case_from_analysis(case, summary_row, trace_item, ordered_targets):
    requested_case = (
        f"{_traditional_class_to_alignment(summary_row.get('traditional_class'))} + "
        f"{_goal_class_to_fulfilment(summary_row.get('goal_class'))}"
    )

    pm4py_alignment = trace_item.get("pm4py_alignment", [])
    log_trace = [
        (log_move if log_move is not None else ABSENCE)
        for log_move, _ in pm4py_alignment
    ]
    model_trace = [
        (model_move if model_move is not None else ABSENCE)
        for _, model_move in pm4py_alignment
    ]

    return {
        "requested_case": requested_case,
        "trace": log_trace,  # Now built from the alignment, not the input
        "model_trace": model_trace,
        "why": case.get("why", ""),
        "target_rows": _target_rows_from_detailed_trace(trace_item, ordered_targets),
    }


def get_target_rows(case, target_computation_func):
    if target_computation_func is None:
        raise ValueError(
            "target_computation_func is required. "
            "Pass a function that receives a trace and returns target rows."
        )

    return target_computation_func(case["trace"])


def get_model_row(trace, activity_abbreviations, model_trace=None, extra_activity_marker="≫"):
    if model_trace is None:
        model_trace = trace

    model_row = []
    for activity in model_trace:
        if activity is None or activity == ABSENCE:
            model_row.append(extra_activity_marker)
        else:
            model_row.append(activity_abbreviations.get(activity, activity))

    return model_row


def render_activity_legend(activity_abbreviations):
    abbrev_items = "; ".join(
        f"{abbrev} = {activity}"
        for activity, abbrev in sorted(activity_abbreviations.items())
    )

    html = f"""
    <div style="font-family:Arial, sans-serif; font-size:13px; margin-top:10px; margin-bottom:18px;">
      <b>Activity abbreviations:</b> {abbrev_items}.
    </div>
    """
    display(HTML(html))


def render_label_legend():
    html = """
    <div style="font-family:Arial, sans-serif; font-size:12px; margin-top:12px;">
      <b>Move labels:</b>
      <span style="background:#DFF2E1; padding:2px 6px; margin-left:8px;">M</span> MSet(t)
      <span style="background:#FADDDD; padding:2px 6px; margin-left:8px;">B</span> BSet(t)
      <span style="background:#F2F2F2; padding:2px 6px; margin-left:8px;">NR</span> NRSet(t)
      <span style="background:#F2F2F2; padding:2px 6px; margin-left:8px;">ND</span> not in alphabet
      <br>
      <b>Markings:</b>
      <span style="background:#DDEBFF; padding:2px 6px; margin-left:8px;">P</span> pending
      <span style="background:#DFF2E1; padding:2px 6px; margin-left:8px;">S</span> satisfied
      <span style="background:#FADDDD; padding:2px 6px; margin-left:8px;">D</span> denied
      <span style="background:#FFFFFF; border:1px solid #DDD; padding:2px 6px; margin-left:8px;">U</span> unknown
    </div>
    """
    display(HTML(html))


def build_target_computation_func(goal_model, targets, activity_mapping=None):
    target_sets_by_target = compute_target_sets(goal_model, targets)
    activity_mapping = activity_mapping or {}

    def target_func(trace):
        rows = {}

        for target in target_sets_by_target:
            labels = []
            markings = []
            current_marking = "U"

            for activity in trace:
                mapped_elements = activity_mapping.get(activity, {activity})
                label = label_mapped_elements(
                    target=target,
                    mapped_elements=set(mapped_elements),
                    target_sets=target_sets_by_target,
                )

                if label == "M":
                    current_marking = "S"
                elif label == "B":
                    current_marking = "D"

                labels.append(label)
                markings.append(current_marking)

            rows[target] = {
                "name": target,
                "labels": labels,
                "markings": markings,
            }

        return rows

    return target_func
