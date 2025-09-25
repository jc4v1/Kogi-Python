from pm4py.visualization.petri_net import visualizer as pn_vis
from pm4py.objects.petri_net.utils import reachability_graph
from pm4py.visualization.transition_system import visualizer as ts_visualizer
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
from pm4py.objects.petri_net.importer import importer as pnml_importer
from Semantics.goal_model import GoalModel
from Semantics.petri_net import PetriNet
import xml.etree.ElementTree as ET
from pprint import pp

def read_petri_net(filename):
    net, init, final = pnml_importer.apply(filename)
    positions = extract_pnml_layout(filename)
    return PetriNet(net, init, final, positions)

def extract_pnml_layout(pnml_path):
    """
    Extract (x, y) positions for places and transitions from a PNML file,
    regardless of namespaces.

    Returns:
        dict: {element_id: (x, y), ...}
    """
    tree = ET.parse(pnml_path)
    root = tree.getroot()

    layout = {}
    layout['places'] = []
    layout['transitions'] = []

    for node in root.iter():
        kind = _local(node.tag)
        if kind not in ("place", "transition"):
            continue

        node_id = node.get("id")
        if not node_id:
            continue

        pos = None

        # 1) Prefer <graphics> that are DIRECT children of the node
        direct_graphics = [c for c in list(node) if _local(c.tag) == "graphics"]

        # 2) Some tools put <graphics> inside <toolspecific> under the node
        if not direct_graphics:
            for c in list(node):
                if _local(c.tag) == "toolspecific":
                    direct_graphics.extend([gc for gc in list(c) if _local(gc.tag) == "graphics"])

        # Search for a <position> inside the chosen <graphics> blocks
        for g in direct_graphics:
            for p in g.iter():
                if _local(p.tag) == "position":
                    x = _parse_float(p.get("x"))
                    y = _parse_float(p.get("y"))
                    if x is not None and y is not None:
                        pos = (x, y)
                        break
            if pos is not None:
                break

        # Fallback (last resort): scan descendants, but avoid label positions under <name>
        if pos is None:
            for g in node.iter():
                if _local(g.tag) == "graphics":
                    # Make sure this graphics isn't under a <name> (that would be label position)
                    parent_is_name = any(_local(a.tag) == "name" for a in _ancestry(g, stop=node))
                    if parent_is_name:
                        continue
                    for p in g.iter():
                        if _local(p.tag) == "position":
                            x = _parse_float(p.get("x"))
                            y = _parse_float(p.get("y"))
                            if x is not None and y is not None:
                                pos = (x, y)
                                break
                    if pos is not None:
                        break

        if pos is not None:
            # scale_x = 0.8/38.0
            # scale_y = 3.5/299.5
            # scale = (scale_x + scale_y)/2
            scale = 1/90
            new_pos_x = pos[0]*scale
            new_pos_y = pos[1]*scale
            if kind == 'place':
                layout['places'].append((new_pos_x,new_pos_y,node_id))
            else:                
                layout['transitions'].append((new_pos_x,new_pos_y,node_id, next((c.text for c in node.iter() if c.tag == 'text'), None)))

    return layout

def _local(tag):
    """Return the local tag name without namespace."""
    return tag.split('}', 1)[-1]  # works for both namespaced and non-namespaced

def _parse_float(v):
    if v is None:
        return None
    # tolerate comma decimals just in case
    try:
        return float(v.replace(',', '.'))
    except Exception:
        return None

def _ancestry(elem, stop=None):
    """Yield ancestors of elem up to (but not including) 'stop' if provided."""
    # xml.etree doesn't give parent pointers, so walk from root
    # and record the path to elem.
    root = elem
    while root.getparent if hasattr(root, 'getparent') else None:
        # Only available in lxml; ElementTree lacks getparent.
        # This function becomes a no-op under ElementTree.
        root = root.getparent()
    # For ElementTree (no parent pointers), we can’t cheaply find ancestry;
    # return empty to avoid misclassification.
    return []

