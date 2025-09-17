# from pm4py.visualization.petri_net import visualizer as pn_vis
# from pm4py.objects.petri_net.utils import reachability_graph
# from pm4py.visualization.transition_system import visualizer as ts_visualizer
# from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
# from pm4py.objects.petri_net.importer import importer as pnml_importer
# from NewSemantics.goal_model import GoalModel
# import xml.etree.ElementTree as ET
# from pprint import pp

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
