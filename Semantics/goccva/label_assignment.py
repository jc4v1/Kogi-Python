from typing import Dict, Sequence, Set

from Semantics.goccva.target_sets import TargetSets


ABSENCE = ">>"


def move_activity(move: Sequence[str], *, include_model_fallback: bool = False) -> str:
    if not move:
        return ABSENCE
    log_activity = move[0] if len(move) > 0 and move[0] is not None else ABSENCE
    if log_activity != ABSENCE:
        return log_activity
    if include_model_fallback and len(move) > 1 and move[1] is not None:
        return move[1]
    return ABSENCE


def map_move(activity_mapping: Dict[str, Set[str]], move: Sequence[str]) -> Set[str]:
    activity = move_activity(move)
    if activity == ABSENCE:
        return set()
    return activity_mapping.get(activity, set())


def map_move_for_label(activity_mapping: Dict[str, Set[str]], move: Sequence[str]) -> Set[str]:
    activity = move_activity(move, include_model_fallback=True)
    if activity == ABSENCE:
        return set()
    return activity_mapping.get(activity, set())


def label_mapped_elements(
    target: str,
    mapped_elements: Set[str],
    target_sets: TargetSets,
) -> str:
    if not mapped_elements:
        return "ND"

    make_set, break_set, nr_set = target_sets[target]
    if mapped_elements & make_set:
        return "M"
    if mapped_elements & break_set:
        return "B"
    if mapped_elements & nr_set:
        return "NR"
    return "ND"


def label_move(
    target: str,
    move: Sequence[str],
    activity_mapping: Dict[str, Set[str]],
    target_sets: TargetSets,
) -> str:
    return label_mapped_elements(
        target=target,
        mapped_elements=map_move_for_label(activity_mapping, move),
        target_sets=target_sets,
    )
