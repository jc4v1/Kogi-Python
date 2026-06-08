from typing import Dict, Sequence, Set, Tuple

from Semantics.goal_model import GoalModel


TargetSets = Dict[str, Tuple[Set[str], Set[str], Set[str]]]


def compute_target_sets(goal_model: GoalModel, targets: Sequence[str]) -> TargetSets:
    return {
        target: goal_model.compute_target_sets(target)
        for target in targets
    }


def target_sets_as_rows(target_sets: TargetSets) -> list[dict]:
    rows = []
    for target, (make_set, break_set, nr_set) in target_sets.items():
        rows.append({
            "target": target,
            "MakeSet": ", ".join(sorted(make_set)),
            "BreakSet": ", ".join(sorted(break_set)),
            "NRSet": ", ".join(sorted(nr_set)),
        })
    return rows
