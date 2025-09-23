import itertools
from NewSemantics.enums import ElementStatus, QualityStatus
from typing import Any

def check_markings(model, expected_markings : dict[ str, ElementStatus | QualityStatus ]) -> None:
    for element, expected_status in expected_markings.items():
        actual_status = get_element_status(model, element)
        assert expected_status == actual_status, f"Element {element}: expected {expected_status}, got {actual_status}"

def set_markings(model, markings: dict[ str, ElementStatus | QualityStatus ]) -> None:
    for element, status in markings.items():
        set_element_status(model, element, status)

def get_element_status(model, element:str) -> ElementStatus | QualityStatus |  None:
    if element in model.goals:
        return model.goals[element]
    elif element in model.tasks:
        return model.tasks[element]
    elif element in model.qualities:
        return model.qualities[element]
    else: return None

def set_element_status(model, element:str, status:ElementStatus | QualityStatus) -> None:
    if element in model.goals:
        model.goals[element] = status
    elif element in model.tasks:
        model.tasks[element] = status
    elif element in model.qualities:
        model.qualities[element] = status
    else: 
        raise ValueError(f"Element {element} not found in model.")
    
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

def transitions_to_str(transitions: dict[Any, dict[str, set[Any]]]) -> str:
    lines = []
    for state in sorted(transitions):
        action_dict = transitions[state]
        if not action_dict:
            lines.append(f"{str(state)} -> {{}}")
        else:
            for action, next_states in sorted(action_dict.items()):
                if next_states:
                    targets = ', '.join([str(s) for s in sorted(next_states)])
                    lines.append(f"({str(state)} -{action}-> {targets})")
                else:
                    lines.append(f"{str(state)} -> {{}}")
    return "\n".join(lines)

def pretty_print(transitions: dict[Any, dict[str, set[Any]]]):
    print(transitions_to_str(transitions))

def states_to_str(states: set[Any]) -> str:
    return "{\n" + ',\n '.join([str(s) for s in sorted(states)]) + "\n}"

def pretty_print_states(states: set[Any]):
    print(states_to_str(states))
