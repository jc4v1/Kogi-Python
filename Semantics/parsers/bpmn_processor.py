from Semantics.petri_net import PetriNet

import pm4py


def read_from_bpmn(process_model_path: str) -> tuple[PetriNet, dict[str, set[str]]]:
    """Build a PetriNet wrapper and identity event mapping from a BPMN file."""
    bpmn_model = pm4py.read_bpmn(process_model_path)
    net, initial_marking, final_marking = pm4py.convert_to_petri_net(bpmn_model)

    petri_net = PetriNet(net, initial_marking, final_marking, {})
    mapping = {
        event: {event}
        for events in petri_net.get_default_event_mapping().values()
        for event in events
    }
    petri_net.convert_bpmn_net(mapping)

    return petri_net, mapping
