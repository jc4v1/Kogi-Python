from collections import deque

class Lts:
    """
    Represents a Labeled Transition System.
    """
    def __init__(self, states, actions, transitions, initial_state):
        self.states = set(states)
        self.actions = set(actions)
        self.transitions = transitions  # A dict {s: {s_prime for (s, a, s_prime) in transitions}}
        self.initial_state = initial_state
        self.predecessors = self._compute_predecessors()

    def _compute_predecessors(self):
        predecessors = {s: set() for s in self.states}
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
