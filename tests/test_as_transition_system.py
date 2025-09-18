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
from NewSemantics.transition_system import MarkingGm

def pretty_print(transitions: dict[Any, set[Any]]):
    for state, next_states in transitions.items():
        print(f"{str(state)} -> {'. '.join([str(s) for s in next_states])})")

def test_simple_real_gm_as_ts_combined():
    # This tests reading a simple goal model and converting it to a transition system
    # based on the =>^* relation (not the -> relation).
    # the =>^* relation is as defined *after* the definition of the GoalModel.
    # This is the default behavior of as_transition_system.
    # The difference can be seen that Task=?? and q=? goes to Task=TF and q=T in one step,
    # and not to Task=TF and q=? as in the other test.

    gm = read_istar_model("tests/data/simple_gm.txt")
    initial_markings = get_markings(gm)
    ts = gm.as_transition_system()
    state_dict = {'Task': {s for s in ElementStatus},
                  'q': {s for s in QualityStatus}}
    expected_states = generate_combinations(state_dict)
    expected_states_set = {MarkingGm(dict(s)) for s in expected_states}

    # Assert states
    assert ts.states() == expected_states_set

    # Assert initial state
    expected_initial_state = MarkingGm(initial_markings)
    assert ts.initial_state() == expected_initial_state

    # Define expected transitions as MarkingGm objects
    expected_transitions = {
        MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.FULFILLED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.UNKNOWN}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.DENIED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.DENIED})
        },
        MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.DENIED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.UNKNOWN}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.UNKNOWN})
        },
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_TRUE, 'q': QualityStatus.FULFILLED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_TRUE, 'q': QualityStatus.UNKNOWN}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_TRUE, 'q': QualityStatus.DENIED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
    }
    # Check that transitions match expected
    assert ts.transitions == expected_transitions
    # Optionally, print transitions for manual inspection
    # print("Transitions:")
    # pretty_print(ts.transitions)
    # Check stable system and weak compliance
    assert check_stable_system(ts, {'q'}) is True
    assert check_weak_compliance(ts, {'q'}) is True

def test_simple_real_gm_as_ts_original():
    # This tests reading a simple goal model and converting it to a transition system
    # based on the -> relation (not the =>^* relation).
    # the -> relation is as defined in the definition of the GoalModel.
    # This is done by passing original=True to as_transition_system.
    # The difference can be seen that Task=?? and q=? goes to Task=TF and q=? in one step,
    # and not to Task=TF and q=T as in the previous test.

    gm = read_istar_model("tests/data/simple_gm.txt")
    initial_markings = get_markings(gm)
    ts = gm.as_transition_system(True)
    # print("Transitions:")
    # pretty_print(ts.transitions)
    state_dict = {'Task': {s for s in ElementStatus},
                  'q': {s for s in QualityStatus}}
    expected_states = generate_combinations(state_dict)
    expected_states_set = {MarkingGm(dict(s)) for s in expected_states}

    # Assert states
    assert ts.states() == expected_states_set

    # Assert initial state
    expected_initial_state = MarkingGm(initial_markings)
    assert ts.initial_state() == expected_initial_state

    # Define expected transitions as MarkingGm objects
    expected_transitions = {
        MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.FULFILLED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_TRUE, 'q': QualityStatus.FULFILLED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.DENIED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.DENIED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.UNKNOWN}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_TRUE, 'q': QualityStatus.DENIED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.DENIED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED}): set(),
        MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.DENIED}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.FULFILLED})
        },
        MarkingGm({'Task': ElementStatus.TRUE_TRUE, 'q': QualityStatus.UNKNOWN}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.UNKNOWN})
        },
        MarkingGm({'Task': ElementStatus.UNKNOWN, 'q': QualityStatus.UNKNOWN}): {
            MarkingGm({'Task': ElementStatus.TRUE_FALSE, 'q': QualityStatus.UNKNOWN})
        },
    }
    # Check that transitions match expected
    assert ts.transitions == expected_transitions
    # Optionally, print transitions for manual inspection
    # print("Transitions:")
    # pretty_print(ts.transitions)
    # Check stable system and weak compliance
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
