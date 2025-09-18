import pytest
import itertools
from typing import Any
from NewSemantics.algorithms import check_stable_system, forward_bfs, backward_bfs, check_weak_compliance
from NewSemantics.transition_system import State, TransitionSystem
from NewSemantics.goal_model import GoalModel
from NewSemantics.istar_processor import read_istar_model
from NewSemantics.petri_net_processor import read_petri_net
from pprint import pp
from Implementation.enums import ElementStatus, QualityStatus
from tests.utilities import get_markings

def pretty_print(transitions: dict[Any, set[Any]]):
    for state, next_states in transitions.items():
        print(f"{str(state)} -> {'. '.join([str(s) for s in next_states])})")

def test_simple_real_gm_as_lts():
    gm = read_istar_model("tests/data/simple_gm.txt")
    # pp(gm.__dict__)
    # pp(get_markings(gm))
    ts = gm.as_transition_system()
    state_dict = {'Task': {s for s in ElementStatus},
                  'q': {s for s in QualityStatus}}
    expected_states = generate_combinations(state_dict)
    # pp(expected_states)
    pp(len(ts.states()))
    pretty_print(ts.transitions)
    # for t in ts.transitions:
    #     pp(t.items)
    #     print()
    # assert ts.states() == expected_states
    # assert ts.initial_state() == None
    # assert ts.transitions == {}
    assert check_stable_system(ts, {'q'}) is True
    assert check_weak_compliance(ts, {'q'}) is True


def generate_combinations(data: dict[str, set[ElementStatus|QualityStatus]]) -> set[frozenset[tuple[str, ElementStatus|QualityStatus]]]:
    """
    Generates all possible combinations from a dictionary where keys map to sets of values.
    Each combination is a dictionary containing one value for each key.

    Args:
        data: A dictionary mapping strings to sets of strings.
              Example: {'color': {'red', 'blue'}, 'size': {'S', 'M'}}

    Returns:
        A set of frozensets, where each frozenset represents an immutable dictionary
        of a unique combination.
        Example: {
            frozenset({'color': 'red', 'size': 'S'}.items()),
            frozenset({'color': 'red', 'size': 'M'}.items()),
            frozenset({'color': 'blue', 'size': 'S'}.items()),
            frozenset({'color': 'blue', 'size': 'M'}.items())
        }
    """
    if not data:
        return {frozenset()}

    keys = list(data.keys())
    value_sets = [data[key] for key in keys]

    # itertools.product computes the Cartesian product of the value sets
    combinations = itertools.product(*value_sets)

    # We need to build dictionaries from the combinations and make them hashable
    result_set = set()
    for combo in combinations:
        # Create a dictionary for the current combination
        combo_dict = dict(zip(keys, combo))
        # Convert to a frozenset of items to make it hashable for the outer set
        result_set.add(frozenset(combo_dict.items()))

    return result_set
