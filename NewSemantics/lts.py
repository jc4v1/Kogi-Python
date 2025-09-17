from collections import deque

class Lts:
    """
    Represents a Labeled Transition System.
    """
    def __init__(self, states, actions, transitions, initial_state):
        self._states = set(states)
        self.actions = set(actions)
        self.transitions = transitions  # A dict {s: {s_prime for (s, a, s_prime) in transitions}}
        self._initial_state = initial_state
        self.predecessors = self._compute_predecessors()

    def states(self):
        return self._states
    
    def initial_state(self):
        return self._initial_state

    def _compute_predecessors(self):
        predecessors = {s: set() for s in self.states()}
        for s, next_states in self.transitions.items():
            for next_s in next_states:
                predecessors[next_s].add(s)
        return predecessors

    def get_successors(self, state):
        return self.transitions.get(state, set())

    def get_predecessors(self, state):
        return self.predecessors.get(state, set())

    def satisfies_quality(self, state, quality):
        # Placeholder for quality check
        return quality in state.qualities if hasattr(state, 'qualities') else False

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

class LtsCombined:
    def __init__(self,goal_model, petri_net, event_mapping, initial_state) -> None:
        self.goal_model = goal_model
        self.petri_net = petri_net
        self.event_mapping = event_mapping
        self._initial_state = initial_state
    
    def states(self):
        return set()
    
    def initial_state(self):
        return self._initial_state
    
class StateCombined:
    def __init__(self, gm_state,pm_state):
        self._gm_state = gm_state
        self._pm_state = pm_state
        
    def gm_state(self):
        return self._gm_state
    
    def pm_state(self):
        return self._pm_state   
    