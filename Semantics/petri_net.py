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
        if len(self.net.places) == 1:
            return self.net.places[0].name
        inital_places = [p for p in [p1.name for p1 in self.net.places] if not any(p in actions[1] for t, actions in self.transitions().items())]
        if len(inital_places) != 1:
            raise Exception(f"Number of initial places is not equal to one {inital_places}")
        else: 
            return inital_places[0]
        
    def transition_names(self): 
        return sorted([t.name for t in self.net.transitions])
    
    # def set_event_mapping(self, model):
    #     model.event_mapping = self.get_default_event_mapping()
    
    def get_default_event_mapping(self):
        event_mapping = {}
        for t in self.net.transitions:
            self._add_event_mapping(event_mapping,t.name,t.label if t.label != t.name and t.label is not None else [])
        return event_mapping

    def convert_bpmn_net(self, mapping: dict, separator: str = '|'):
        """Convert BPMN-derived Petri net transition names using an event->intentional-element mapping.

        For transitions whose label (or name) matches a mapping key, rename the transition
        to a composite name combining the event and the mapped intentional element so that
        downstream code can reference transitions consistently. The positions for
        transitions are updated to use the new transition name as well.

        Parameters:
          mapping: dict mapping event -> list of [ [intentional_elem], ... ]
                   e.g. {'e1': [['T1']]}.
          separator: str used to join event and element into a single transition name.
        """
        # Build a map from original transition.name -> list of new names created
        from types import SimpleNamespace
        rename_map = {}

        # Precompute a map from original transition id -> position and label text (if any)
        pos_map = {}
        for entry in self.positions.get('transitions', []):
            if len(entry) >= 3:
                x, y, node_id = entry[0], entry[1], entry[2]
                label_text = entry[3] if len(entry) > 3 else None
                pos_map[node_id] = (x, y, label_text)

        # Iterate over a snapshot of transitions to avoid mutating while iterating
        # Sort transitions by name to ensure deterministic renaming when creating
        # invented/normalized transition names.
        original_transitions = sorted(list(self.net.transitions), key=lambda t: getattr(t, 'name', ''))
        for t in original_transitions:
            original_name = t.name
            label = getattr(t, 'label', None)
            key = label if (label and label in mapping) else (original_name if original_name in mapping else None)
            rows = mapping.get(key, []) if key is not None else []

            # Flatten mapping rows into a list of elements
            elems = []
            for row in rows:
                if isinstance(row, (list, tuple)):
                    for e in row:
                        if e:
                            elems.append(e)
                elif row:
                    elems.append(row)

            if not elems:
                continue

            new_names = []
            # For the original transition use the event key as the name and the first mapped
            # intentional element as the label so it appears as (event, 'T1').
            first_elem = elems[0]
            original_new_name = key
            new_names.append(original_new_name)
            try:
                t.name = original_new_name
            except Exception:
                setattr(t, 'name', original_new_name)
            try:
                t.label = first_elem
            except Exception:
                setattr(t, 'label', first_elem)

            # For remaining elements, create duplicate transition objects with same connectivity
            for dup_elem in elems[1:]:
                dup_name = f"{key}{separator}{dup_elem}"
                new_names.append(dup_name)
                # Create a lightweight transition-like object
                dup_t = SimpleNamespace()
                dup_t.name = dup_name
                dup_t.label = dup_elem
                dup_t.in_arcs = []
                dup_t.out_arcs = []

                # Duplicate incoming arcs (place -> transition)
                for arc in getattr(t, 'in_arcs', []):
                    src_place = arc.source
                    # create surrogate arc object
                    surc_arc = SimpleNamespace(source=src_place, target=dup_t)
                    dup_t.in_arcs.append(surc_arc)
                    # also add to net.arcs so rendering picks it up
                    try:
                        self.net.arcs.append(surc_arc)
                    except Exception:
                        # if net.arcs not list-like, skip
                        pass

                # Duplicate outgoing arcs (transition -> place)
                for arc in getattr(t, 'out_arcs', []):
                    tgt_place = arc.target
                    surc_arc = SimpleNamespace(source=dup_t, target=tgt_place)
                    dup_t.out_arcs.append(surc_arc)
                    try:
                        self.net.arcs.append(surc_arc)
                    except Exception:
                        pass

                # Add the duplicated transition object to net.transitions
                try:
                    self.net.transitions.append(dup_t)
                except Exception:
                    # best-effort: if net.transitions isn't a list, try to setattr
                    if hasattr(self.net, 'transitions'):
                        try:
                            getattr(self.net, 'transitions').append(dup_t)
                        except Exception:
                            pass

                # Add position for duplicate transition if original had a position
                if original_name in pos_map:
                    x, y, label_text = pos_map[original_name]
                    if label_text is not None:
                        self.positions['transitions'].append((x, y, dup_name, label_text))
                    else:
                        self.positions['transitions'].append((x, y, dup_name))

            # record mapping from original name to created names
            rename_map[original_name] = new_names

        # Update positions for the renamed original transitions
        if 'transitions' in self.positions:
            new_transitions = []
            for entry in self.positions['transitions']:
                if len(entry) >= 3:
                    x, y, node_id = entry[0], entry[1], entry[2]
                    rest = entry[3:] if len(entry) > 3 else []
                    # If original transition was renamed, replace node_id with its first new name
                    if node_id in rename_map:
                        new_id = rename_map[node_id][0]
                    else:
                        new_id = node_id
                    if rest:
                        new_transitions.append((x, y, new_id, rest[0]))
                    else:
                        new_transitions.append((x, y, new_id))
                else:
                    new_transitions.append(entry)
            self.positions['transitions'] = new_transitions

        # Normalize place names to p1, p2, ... but keep source/sink place names unchanged
        # Determine incoming/outgoing arcs for places
        place_incoming = {p.name: 0 for p in self.net.places}
        place_outgoing = {p.name: 0 for p in self.net.places}
        # Keep a reference map of original place name -> place object so we can restore preserved names
        original_place_map = {p.name: p for p in self.net.places}
        for arc in getattr(self.net, 'arcs', []):
            src = getattr(arc, 'source', None)
            tgt = getattr(arc, 'target', None)
            if src is not None and hasattr(src, 'name'):
                # if source is a place
                if src.name in place_outgoing:
                    place_outgoing[src.name] += 1
            if tgt is not None and hasattr(tgt, 'name'):
                if tgt.name in place_incoming:
                    place_incoming[tgt.name] += 1

        # Identify places to preserve (no incoming or no outgoing)
        preserve = set()
        for pname in place_incoming:
            if place_incoming.get(pname, 0) == 0 or place_outgoing.get(pname, 0) == 0:
                preserve.add(pname)

        # Build rename mapping for places. Sort places by name so generated
        # invented names (p1, p2, ...) are assigned deterministically.
        place_rename_map = {}
        counter = 1
        for p in sorted(list(self.net.places), key=lambda p: getattr(p, 'name', '')):
            old = p.name
            if old in preserve:
                place_rename_map[old] = old
                continue
            new_name = f"p{counter}"
            counter += 1
            place_rename_map[old] = new_name
            try:
                p.name = new_name
            except Exception:
                setattr(p, 'name', new_name)

        # Update positions for places
        if 'places' in self.positions:
            new_places = []
            for x, y, label in self.positions['places']:
                new_label = place_rename_map.get(label, label)
                new_places.append((x, y, new_label))
            self.positions['places'] = new_places

        # Ensure preserved places keep their original names on the actual place objects
        for preserved_name in preserve:
            place_obj = original_place_map.get(preserved_name)
            if place_obj is not None:
                try:
                    place_obj.name = preserved_name
                except Exception:
                    setattr(place_obj, 'name', preserved_name)

        return rename_map
    
    def _add_event_mapping(self, ev_map, event: str, target):
        if isinstance(target, list):
            ev_map[event] = target
        else:
            ev_map[event] = [[target]]

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
    
    def write_pnml(self, path: str):
        """
        Write the current Petri net to a PNML file at `path`.

        - Places, transitions and arcs are written deterministically (sorted by name)
        - For transitions where label is None and name matches `t<number>` no <name> element is emitted
        - Every arc gets an <inscription><text>1</text></inscription> element
        """
        import xml.etree.ElementTree as ET
        import xml.dom.minidom as md
        import re

        def add_text_element(parent, tag, text):
            elem = ET.SubElement(parent, tag)
            txt = ET.SubElement(elem, "text")
            txt.text = str(text)
            return elem

        pnml = ET.Element("pnml")
        net = ET.SubElement(pnml, "net", id="net1", type="http://www.pnml.org/version-2009/grammar/pnmlcoremodel")

        # Places (deterministic order)
        places = sorted(list(getattr(self.net, "places", [])), key=lambda p: getattr(p, "name", ""))
        for p in places:
            pid = str(getattr(p, "name", ""))
            place_el = ET.SubElement(net, "place", id=pid)
            add_text_element(place_el, "name", pid)

        # Transitions (deterministic order)
        transitions = sorted(list(getattr(self.net, "transitions", [])), key=lambda t: getattr(t, "name", ""))
        t_name_re = re.compile(r"^t\d+$")
        for t in transitions:
            tid = str(getattr(t, "name", ""))
            tr_el = ET.SubElement(net, "transition", id=tid)
            label = getattr(t, "label", None)
            # Omit <name> if label is None and auto-generated tN name
            if not (label is None and t_name_re.match(tid)):
                # prefer label text if present, otherwise use id
                if label is not None and label != tid:
                    add_text_element(tr_el, "name", f"{tid} ({label})")

        # Arcs (deterministic ordering)
        arcs = list(getattr(self.net, "arcs", []))
        def arc_key(a):
            s = getattr(getattr(a, "source", None), "name", str(id(getattr(a, "source", None))))
            t = getattr(getattr(a, "target", None), "name", str(id(getattr(a, "target", None))))
            return (s, t)
        for i, a in enumerate(sorted(arcs, key=arc_key), start=1):
            src = str(getattr(getattr(a, "source", None), "name", ""))
            tgt = str(getattr(getattr(a, "target", None), "name", ""))
            arc_el = ET.SubElement(net, "arc", id=f"a{i}", source=src, target=tgt)
            # Add inscription with value 1
            ins = ET.SubElement(arc_el, "inscription")
            txt = ET.SubElement(ins, "text")
            txt.text = "1"

        # Pretty-print and write file
        rough = ET.tostring(pnml, encoding="utf-8")
        pretty = md.parseString(rough.decode("utf-8")).toprettyxml(indent="  ")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(pretty)