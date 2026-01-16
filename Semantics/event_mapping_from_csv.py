import csv
from typing import Dict, List

def read_event_mapping_csv(file_path: str) -> Dict[str, List[List[str]]]:
    """
    Read CSV with columns: Event, Intentional Element
    Returns mapping: { event: [ [intentional_elem], ... ] }
    If a row has an event but no intentional element the value will be an empty list.
    """
    mapping: Dict[str, List[List[str]]] = {}
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        # skip the first line (header)
        next(reader, None)
        for row in reader:
            if not row:
                continue
            event = row[0].strip()
            if not event:
                continue
            element = ""
            if len(row) > 1:
                element = row[1].strip()
            if event not in mapping:
                mapping[event] = []
            if element:
                mapping[event].append([element])
    return mapping


def event_mapping_for_petri_net(event_map: Dict[str, List[List[str]]], petri_net) -> Dict[str, List[List[str]]]:
    """
    Convert an event-keyed mapping (e.g. {'e1': [['T1']]}) to a transition-keyed mapping
    using the transitions' labels. Returns a dict mapping transition names to the
    corresponding event sequences. If a transition's label has no entry in
    `event_map`, an empty list is used.

    Example:
      event_map = {'e1': [['T1']]}
      resulting mapping for a transition with name 't2' and label 'e1' will be
      {'t2': [['T1']]}
    """
    mapping_by_transition: Dict[str, List[List[str]]] = {}
    # Some Petri net transition objects have attributes `name` and `label`.
    for t in getattr(petri_net, 'net').transitions:
        label = getattr(t, 'label', None)
        # Prefer label lookup; fall back to transition name if present in event_map
        if label and label in event_map:
            mapping_by_transition[t.name] = event_map[label]
        elif t.name in event_map:
            mapping_by_transition[t.name] = event_map[t.name]
        else:
            mapping_by_transition[t.name] = []
    return mapping_by_transition
