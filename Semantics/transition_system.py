from collections import deque
from typing import TypeVar, Generic, Mapping, Iterator, Any
from pprint import pformat
from Semantics.enums import ElementStatus, QualityStatus
from Semantics.algorithms import check_stable_system, check_weak_compliance

T_STATE = TypeVar('T_STATE')

class TransitionSystem(Generic[T_STATE]):
    """
    Represents a Transition System with actions.
    """
    def __init__(
        self,
        states: set[T_STATE],
        transitions: dict[T_STATE, dict[Any, set[T_STATE]]],
        initial_state: T_STATE
    ):
        self._states: set[T_STATE] = set(states)
        self.transitions = transitions  # Dict[state, Dict[action, Set[state]]]
        self._initial_state = initial_state
        self.predecessors = self._compute_predecessors()

    def states(self) -> set[T_STATE]: 
        return self._states
    
    def initial_state(self) -> T_STATE:
        return self._initial_state

    def _compute_predecessors(self):
        predecessors = {s: set() for s in self.states()}
        for s, action_dict in self.transitions.items():
            for action, next_states in action_dict.items():
                for next_s in next_states:
                    predecessors[next_s].add(s)
        return predecessors

    def get_successors(self, state, action=None):
        if action is None:
            # Return all successors for all actions
            action_dict = self.transitions.get(state, {})
            result = set()
            for next_states in action_dict.values():
                result.update(next_states)
            return result
        else:
            return self.transitions.get(state, {}).get(action, set())

    def get_predecessors(self, state):
        return self.predecessors.get(state, set())

    def satisfies_quality(self, state, quality):
        # Placeholder for quality check
        return quality in state.qualities if hasattr(state, 'qualities') else state._markings.get(quality,QualityStatus.UNKNOWN) == QualityStatus.FULFILLED
    
    def get_enabled_actions(self, state: T_STATE) -> list[Any]:
        """
        Returns the set of enabled actions for a given state.
        """
        return list(set(self.transitions.get(state, {}).keys()))

    def size(self) -> tuple[int, int]:
        """Return a tuple (number_of_states, number_of_transitions).

        number_of_transitions is computed as the total number of target states
        across all actions for all source states (i.e. sum over source->action->|targets|).
        """
        num_states = len(self._states)
        num_transitions = 0
        for action_dict in self.transitions.values():
            for targets in action_dict.values():
                num_transitions += len(targets)
        return num_states, num_transitions

# Define states and their qualities (assuming each state has a 'qualities' attribute)
class State:
    def __init__(self, name, qualities=None):
        self.name = name
        self.qualities = set(qualities) if qualities else set()
    
    def __repr__(self):
        return f"State('{self.name}', qualities={self.qualities})"
    
    def __eq__(self, other):
        return isinstance(other, State) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

class MarkingGm:
    def __init__(self, markings: dict[str,ElementStatus|QualityStatus]):
        self._markings = markings
        self._hash = None
        
    def markings(self) -> dict[str, ElementStatus|QualityStatus]:
        return self._markings
    
    def get_element_status(self, element: str) -> ElementStatus|QualityStatus:
        return self._markings[element]
    
    def __getitem__(self, key: str) -> ElementStatus|QualityStatus:
        return self.get_element_status(key)
    
    def __str__(self):
        items = [f"{key}={self._format_status(value)}" for key, value in sorted(self._markings.items())]
        if not items:
            return "<>"
        return f"<{', '.join(items)}>"
    def __repr__(self):
        return f"MarkingGm(gm={self.markings()})"
        # return str(self.pn_marking)
    
    def __eq__(self, other):
        if not isinstance(other, MarkingGm):
            return NotImplemented
        return self._markings == other._markings

    def __hash__(self):
        if self._hash is None:
            # Hash a frozenset of the dictionary items for a stable hash
            self._hash = hash(frozenset(self._markings.items()))
        return self._hash
    
    def _format_status(self, status):
        """Format status for display"""
        if isinstance(status, ElementStatus):
            if status == ElementStatus.UNKNOWN:
                return "(?, ?)"
            elif status == ElementStatus.TRUE_FALSE:
                return "(⊤, ⊥)"
            elif status == ElementStatus.TRUE_TRUE:
                return "(⊤, ⊤)"
        elif isinstance(status, QualityStatus):
            if status == QualityStatus.UNKNOWN:
                return "(?)"
            elif status == QualityStatus.FULFILLED:
                return "(⊤)"
            elif status == QualityStatus.DENIED:
                return "(⊥)"
        return str(status)    
    def __lt__(self, other):
        if not isinstance(other, MarkingGm):
            return NotImplemented
        return str(self) < str(other)    
    
class MarkingPn:
    """
    Represents a marking (state) of a Petri net.
    """
    def __init__(self, markings: dict[str, int]):
        self._markings = dict(markings)
        
    def markings(self) -> dict[str, int]:
        return self._markings

    def __eq__(self, other):
        return isinstance(other, MarkingPn) and self._markings == other._markings

    def __hash__(self):
        # Hash based on the frozenset of items for immutability
        return hash(frozenset(self._markings.items()))

    def __repr__(self):
        return f"MarkingPn({self._markings})"
    
    def __str__(self):
        marked_places = [p for p, v in sorted(self._markings.items()) if v == 1]
        return "{" + ", ".join(marked_places) + "}"

    def __lt__(self, other):
        if not isinstance(other, MarkingPn):
            return NotImplemented
        # Sort by keys, then by values
        self_items = sorted(self._markings.items())
        other_items = sorted(other._markings.items())
        return self_items > other_items
    
def combine_goal_model_and_petri_net(gm, pn, event_mapping = None) -> 'CombinedTransitionSystem':
    gm_ts = gm.as_transition_system()
    pn_ts = pn.as_transition_system()
    if not event_mapping:
        pn.set_event_mapping(gm)
        event_mapping = gm.event_mapping
    combined_ts = CombinedTransitionSystem(gm_ts, pn_ts, event_mapping)
    return combined_ts

class Marking:
    """
    Represents a combined marking: (GoalModel marking, PetriNet marking)
    """
    def __init__(self, gm_marking: MarkingGm, pn_marking: MarkingPn):
        self.gm_marking = gm_marking
        self.pn_marking = pn_marking

    def __eq__(self, other):
        return (
            isinstance(other, Marking)
            and self.gm_marking == other.gm_marking
            and self.pn_marking == other.pn_marking
        )

    def __hash__(self):
        return hash((self.gm_marking, self.pn_marking))

    def __repr__(self):
        return f"Marking(gm={self.gm_marking}, pn={self.pn_marking})"
        # return str(self.pn_marking)

    def __str__(self):
        return str(self.pn_marking)

    def __lt__(self, other):
        if not isinstance(other, Marking):
            return NotImplemented
        return (str(self.gm_marking), str(self.pn_marking)) < (str(other.gm_marking), str(other.pn_marking))
    
    def satisfies_quality(self, quality):
        return self.gm_marking[quality] == QualityStatus.FULFILLED

class CombinedTransitionSystem:
    """
    Represents a combined transition system of a GoalModel and a PetriNet.
    States are pairs of (MarkingGm, MarkingPn).
    Transitions are based on PetriNet actions and a mapping dict[str, set[str]].
    """
    def __init__(
        self,
        gm_ts: TransitionSystem[MarkingGm],
        pn_ts: TransitionSystem[MarkingPn],
        event_map: dict[str, set[str]]
    ):
        self.gm_ts = gm_ts
        self.pn_ts = pn_ts
        self.event_map = event_map

        self._states: set[Marking] = set()
        self.transitions: dict[Marking,dict[Any,set[Marking]]] = {}
        self._initial_state: Marking
        self._states, self.transitions, self._initial_state = self._compute_combined_ts()
        

    def _compute_combined_ts(self):
        from collections import deque
    
        initial_state = Marking(self.gm_ts.initial_state(), self.pn_ts.initial_state())
        visited = set()
        transitions: dict[Marking, dict[str, set[Marking]]] = {}
        queue = deque([initial_state])
    
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            transitions[current] = {}
    
            # Get enabled PetriNet actions from the PetriNet transition system
            pn_actions = self.pn_ts.get_enabled_actions(current.pn_marking)
            for pn_action in pn_actions:
                pn_successors = self.pn_ts.get_successors(current.pn_marking, pn_action)
                event_sequences = self.event_map.get(pn_action, [])
    
                # If no event sequences, treat as empty event (goal model state unchanged)
                if not event_sequences:
                    event_sequences = [[]]
    
                # Each event_sequence is a list of elements to fire in order
                for event_sequence in event_sequences:
                    gm_successors = {current.gm_marking}
                    for element in event_sequence:
                        next_gm = set()
                        for gm_marking in gm_successors:
                            next_gm.update(self.gm_ts.get_successors(gm_marking, element))
                        if next_gm:
                            gm_successors = next_gm
    
                    for pn_target in pn_successors:
                        for gm_target in gm_successors:
                            next_state = Marking(gm_target, pn_target)
                            transitions[current].setdefault(pn_action, set()).add(next_state)
                            if next_state not in visited:
                                queue.append(next_state)
    
        return visited, transitions, initial_state  
      
    def states(self) -> set[Marking]:
        return self._states

    def initial_state(self) -> Marking:
        return self._initial_state

    def get_successors(self, state, action=None):
        if action is None:
            action_dict = self.transitions.get(state, {})
            result = set()
            for next_states in action_dict.values():
                result.update(next_states)
            return result
        else:
            return self.transitions.get(state, {}).get(action, set())

    def get_predecessors(self, state):
        predecessors = {s: set() for s in self._states}
        for s, action_dict in self.transitions.items():
            for action, next_states in action_dict.items():
                for next_s in next_states:
                    predecessors[next_s].add(s)
        return predecessors.get(state, set())
    
    def satisfies_quality(self, state, quality):
        return state.satisfies_quality(quality)

    def size(self) -> tuple[int, int]:
        """Return a tuple (number_of_states, number_of_transitions).

        number_of_transitions is computed as the total number of target states
        across all actions for all source states.
        """
        num_states = len(self._states)
        num_transitions = 0
        for action_dict in self.transitions.values():
            for targets in action_dict.values():
                num_transitions += len(targets)
        return num_states, num_transitions

    def check_stability(self,qualities, debug=False):
        return check_stable_system(self, qualities, debug)

    def check_weak_compliance(self,qualities, debug=False):
        return check_weak_compliance(self, qualities, debug)

    def check_strong_compliance(self,qualities, debug=False):
        stable = check_stable_system(self, qualities, debug)
        weakly_compliant = check_weak_compliance(self, qualities, debug)
        return (
            stable[0] and weakly_compliant[0],
            stable[1],
            weakly_compliant[1]
        )
