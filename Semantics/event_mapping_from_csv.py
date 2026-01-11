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
