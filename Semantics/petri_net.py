from Semantics.transition_system import TransitionSystem
from Semantics.transition_system import MarkingPn  # Use MarkingPn for Petri net states


class PetriNet():
    def __init__(self,net,init,final,positions):
        self.net = net
        self.positions = positions

    def transitions(self):
        transitions_dict = {}
        for transition in self.net.transitions:
            input_places = []
            output_places = []

            # Get input places from incoming arcs
            for arc in transition.in_arcs:
                input_places.append(arc.source.name)

            # Get output places from outgoing arcs
            for arc in transition.out_arcs:
                output_places.append(arc.target.name)

            transitions_dict[transition.name] = [input_places, output_places]
        return transitions_dict
    
    def enabled_transitions(self,markings): 
       return [ t for t, actions in self.transitions().items() if all(p in markings for p in actions[0] ) ]
    
    def initial_place(self):
        inital_places = [p for p in [p1.name for p1 in self.net.places] if not any(p in actions[1] for t, actions in self.transitions().items())]
        if len(inital_places) != 1:
            raise Exception(f"Number of initial places is not equal to one {inital_places}")
        else: 
            return inital_places[0]
        
    def transition_names(self): 
        return sorted([t.name for t in self.net.transitions])
    
    def set_event_mapping(self, model):
        model.event_mapping = {}
        for t in self.net.transitions:
            model.add_event_mapping(t.name, t.label if t.label != t.name else [])
            
    def min_max(self):
        positions = self.positions['places'] + self.positions['transitions']
        min_x = min(p[0] for p in positions)
        min_y = min(p[1] for p in positions)
        max_x = max(p[0] for p in positions)
        max_y = max(p[1] for p in positions)
        return ((min_x,min_y),(max_x,max_y))

    def as_transition_system(self):
        """
        Converts the Petri net to a TransitionSystem instance using MarkingPn for states,
        and includes actions (transition names).
        """
        from collections import deque

        initial_marking = {p.name: 1 if p.name == self.initial_place() else 0 for p in self.net.places}
        initial_state = MarkingPn(initial_marking)
        visited = set()
        transitions: dict[MarkingPn, dict[str, set[MarkingPn]]] = {}
        queue = deque([initial_state])

        while queue:
            current_state = queue.popleft()
            if current_state in visited:
                continue
            visited.add(current_state)
            transitions[current_state] = {}

            enabled = self.enabled_transitions([p for p, v in current_state._markings.items() if v > 0])
            for t_name in enabled:
                next_marking = dict(current_state._markings)
                input_places, output_places = self.transitions()[t_name]
                for p in input_places:
                    next_marking[p] -= 1
                for p in output_places:
                    next_marking[p] += 1
                for p in next_marking:
                    next_marking[p] = max(0, next_marking[p])
                next_state = MarkingPn(next_marking)
                transitions[current_state].setdefault(t_name, set()).add(next_state)
                if next_state not in visited:
                    queue.append(next_state)

        return TransitionSystem(
            states=visited,
            transitions=transitions,
            initial_state=initial_state
        )