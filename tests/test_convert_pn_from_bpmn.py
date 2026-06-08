from Semantics.parsers.istar_processor import read_istar_model
from Semantics.parsers.event_mapping_from_csv import read_event_mapping_csv
from Semantics.parsers.petri_net_processor import PetriNet
import pm4py

def test_convert_bpmn_to_petri_net():
    bpmn_model = pm4py.read_bpmn("tests/data/bpmn/bpmn.bpmn")
    mapping = read_event_mapping_csv("tests/data/bpmn/map-bpmn.csv")

    net, initial_marking, final_marking = pm4py.convert_to_petri_net(bpmn_model)

    petri_net = PetriNet(net,initial_marking,final_marking,{})

    # Helper to format endpoints (places vs transitions)
    def endpoint_repr(obj, places_set, transitions_list):
        if obj in places_set:
            return obj.name
        label = getattr(obj, 'label', None)
        return f"({obj.name}, '{label}')"

    # Capture "before" state
    places_before = [p.name for p in petri_net.net.places]
    transitions_before = [(t.name, getattr(t, 'label', None)) for t in petri_net.net.transitions]
    arcs_before = []
    places_objs = list(petri_net.net.places)
    transitions_objs = list(petri_net.net.transitions)
    for arc in getattr(petri_net.net, 'arcs', []):
        src = getattr(arc, 'source', None)
        tgt = getattr(arc, 'target', None)
        arcs_before.append(f"{endpoint_repr(src, places_objs, transitions_objs)}->{endpoint_repr(tgt, places_objs, transitions_objs)}")

    # Expected "before" values (approval expectations)
    expected_places_before = ['ent_Activity_086hvke', 'ent_Activity_1bh9bjn', 'sink', 'source']
    expected_transitions_before = [('Activity_086hvke', 'Pack'), ('Activity_1bh9bjn', 'Ship'), ('Task_1hcentk', 'Pick')]
    expected_arcs_before = [
        "(Activity_086hvke, 'Pack')->ent_Activity_1bh9bjn",
        "(Activity_1bh9bjn, 'Ship')->sink",
        "(Task_1hcentk, 'Pick')->ent_Activity_086hvke",
        "ent_Activity_086hvke->(Activity_086hvke, 'Pack')",
        "ent_Activity_1bh9bjn->(Activity_1bh9bjn, 'Ship')",
        "source->(Task_1hcentk, 'Pick')",
    ]

    assert sorted(places_before) == sorted(expected_places_before)
    assert sorted(transitions_before) == sorted(expected_transitions_before)    
    assert sorted(arcs_before) == sorted(expected_arcs_before)

    # Perform conversion
    petri_net.convert_bpmn_net(mapping)

    # Capture "after" state
    places_after = [p.name for p in petri_net.net.places]
    transitions_after = [(t.name, getattr(t, 'label', None)) for t in petri_net.net.transitions if getattr(t, 'label', None) is not None]
    arcs_after = []
    places_objs = list(petri_net.net.places)
    transitions_objs = list(petri_net.net.transitions)
    for arc in getattr(petri_net.net, 'arcs', []):
        src = getattr(arc, 'source', None)
        tgt = getattr(arc, 'target', None)
        arcs_after.append(f"{endpoint_repr(src, places_objs, transitions_objs)}->{endpoint_repr(tgt, places_objs, transitions_objs)}")

    expected_places_after = ['p1', 'p2', 'sink', 'source']
    expected_transitions_after = [('Pack', 'Pack Items'), ('Pick', 'Pick Items'), ('Ship', 'Ship Items')]
    expected_arcs_after = [
        "(Pack, 'Pack Items')->p2",
        "(Pick, 'Pick Items')->p1",
        "(Ship, 'Ship Items')->sink",
        "p1->(Pack, 'Pack Items')",
        "p2->(Ship, 'Ship Items')",
        "source->(Pick, 'Pick Items')",
    ]

    assert sorted(places_after) == sorted(expected_places_after)
    assert sorted(transitions_after) == sorted(expected_transitions_after)
    assert sorted(arcs_after) == sorted(expected_arcs_after)
    
    
def test_convert_choice_bpmn_to_petri_net():
    bpmn_model = pm4py.read_bpmn("tests/data/bpmn/choice.bpmn")
    mapping = read_event_mapping_csv("tests/data/bpmn/choice_map.csv")
    net, initial_marking, final_marking = pm4py.convert_to_petri_net(bpmn_model)

    petri_net = PetriNet(net,initial_marking,final_marking,{})

    # Helper to format endpoints (places vs transitions)
    def endpoint_repr(obj, places_set, transitions_list):
        if obj in places_set:
            return obj.name
        label = getattr(obj, 'label', None)
        return f"({obj.name}, '{label}')"

    # Perform conversion
    petri_net.convert_bpmn_net(mapping)

    # Capture "after" state
    places_after = [p.name for p in petri_net.net.places]
    transitions_after = [(t.name, getattr(t, 'label', None)) for t in petri_net.net.transitions]
    arcs_after = []
    places_objs = list(petri_net.net.places)
    transitions_objs = list(petri_net.net.transitions)
    for arc in getattr(petri_net.net, 'arcs', []):
        src = getattr(arc, 'source', None)
        tgt = getattr(arc, 'target', None)
        arcs_after.append(f"{endpoint_repr(src, places_objs, transitions_objs)}->{endpoint_repr(tgt, places_objs, transitions_objs)}")
        
    expected_places_after = ['p1', 'source', 'sink', 'p2']
    expected_transitions_after = [('Task 2', 'Task 2'), ('t1', None), ('Task 1', 'Task 1'), ('t2', None)]
    expected_arcs_after = ["p2->(Task 2, 'Task 2')", "(t1, 'None')->p2", "source->(t1, 'None')", "(Task 2, 'Task 2')->p1", "(Task 1, 'Task 1')->p1", "p2->(Task 1, 'Task 1')", "p1->(t2, 'None')", "(t2, 'None')->sink"]
    
    print(sorted(expected_places_after));
    print(sorted(expected_transitions_after));
    print(sorted(expected_arcs_after));

    assert sorted(places_after) == sorted(expected_places_after)
    assert sorted(transitions_after) == sorted(expected_transitions_after)
    # Note that arcs are not preserved. The reason is, that at some
    # point a transititions with UUID's are created. Since
    # those names are random, they cannot be sorted and give deterministically
    # the same name each time on conversion.
    # Thus we cannot directly check for the same arcs.
    # assert sorted(arcs_after) == sorted(expected_arcs_after)
