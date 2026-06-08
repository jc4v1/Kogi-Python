from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pandas as pd
from pm4py.objects.petri_net.utils import check_soundness, petri_utils
from pm4py.visualization.petri_net import visualizer as pn_visualizer

try:
    from GoRep.paths import GOREP_DIR, ensure_repo_root_on_path
except ModuleNotFoundError:
    from paths import GOREP_DIR, ensure_repo_root_on_path

ensure_repo_root_on_path()

from Semantics.goccva.pipeline import analyse
from Semantics.petri_net import PetriNet as WrappedPetriNet


REPAIRED_DIR = GOREP_DIR / "repaired_models"


@dataclass
class RepairVariant:
    name: str
    operation: str
    trigger: str
    description: str
    petri_net: WrappedPetriNet


def _clone_wrapped_net(petri_net: WrappedPetriNet) -> WrappedPetriNet:
    net, init, final = deepcopy((petri_net.net, petri_net.init, petri_net.final))
    return WrappedPetriNet(
        net,
        init,
        final,
        deepcopy(petri_net.positions),
    )


def _transition_matches(transition, activity: str) -> bool:
    return activity in {getattr(transition, "label", None), getattr(transition, "name", None)}


def _fresh(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _places(net):
    return list(getattr(net, "places", []))


def _first_initial_place(wrapped: WrappedPetriNet):
    marked = [place for place, tokens in wrapped.init.items() if tokens > 0]
    if marked:
        return marked[0]
    places = _places(wrapped.net)
    return places[0] if places else None


def add_global_self_loop(wrapped: WrappedPetriNet, activity: str) -> WrappedPetriNet:
    """Concrete add operation: allow an observed activity as a guarded self-loop at the initial marking."""
    repaired = _clone_wrapped_net(wrapped)
    place = _first_initial_place(repaired)
    if place is None:
        return repaired
    transition = petri_utils.add_transition(repaired.net, name=_fresh("add"), label=activity)
    petri_utils.add_arc_from_to(place, transition, repaired.net)
    petri_utils.add_arc_from_to(transition, place, repaired.net)
    return repaired


def forbid_activity_by_hiding(wrapped: WrappedPetriNet, activity: str) -> WrappedPetriNet:
    """Concrete delete/forbid operation: hide matching visible transitions from log alignment."""
    repaired = _clone_wrapped_net(wrapped)
    for transition in repaired.net.transitions:
        if _transition_matches(transition, activity):
            transition.label = None
    return repaired


def add_controlled_loop_near_activity(wrapped: WrappedPetriNet, activity: str) -> WrappedPetriNet:
    """Concrete loop operation: add a duplicate self-loop transition around matching transition output places."""
    repaired = _clone_wrapped_net(wrapped)
    matched = [t for t in repaired.net.transitions if _transition_matches(t, activity)]
    if not matched:
        return add_global_self_loop(repaired, activity)
    for transition in matched:
        output_places = [arc.target for arc in transition.out_arcs]
        for place in output_places:
            loop = petri_utils.add_transition(repaired.net, name=_fresh("loop"), label=activity)
            petri_utils.add_arc_from_to(place, loop, repaired.net)
            petri_utils.add_arc_from_to(loop, place, repaired.net)
    return repaired


def add_swap_shortcut(wrapped: WrappedPetriNet, activity: str) -> WrappedPetriNet:
    """Concrete swap/replacement approximation: add an activity self-loop to tolerate local reordering."""
    return add_global_self_loop(wrapped, activity)


def apply_candidate_repair(wrapped: WrappedPetriNet, candidate_row) -> RepairVariant:
    operation = str(candidate_row.get("operation", ""))
    trigger = str(candidate_row.get("trigger", ""))
    activity = trigger.split(":", 1)[1] if ":" in trigger else trigger

    if "delete" in operation or "forbid" in operation:
        repaired = forbid_activity_by_hiding(wrapped, activity)
    elif "loop" in operation:
        repaired = add_controlled_loop_near_activity(wrapped, activity)
    elif "swap" in operation or "replace" in operation:
        repaired = add_swap_shortcut(wrapped, activity)
    else:
        repaired = add_global_self_loop(wrapped, activity)

    return RepairVariant(
        name=str(candidate_row.get("candidate_id", "candidate")),
        operation=operation,
        trigger=trigger,
        description=str(candidate_row.get("description", "")),
        petri_net=repaired,
    )


def check_repair_soundness(variant: RepairVariant) -> dict:
    net = variant.petri_net.net
    im = variant.petri_net.init
    fm = variant.petri_net.final
    result = {
        "candidate_id": variant.name,
        "operation": variant.operation,
        "trigger": variant.trigger,
    }
    try:
        result["wfnet"] = bool(check_soundness.check_wfnet(net))
    except Exception as exc:
        result["wfnet"] = False
        result["wfnet_error"] = str(exc)
    try:
        result["easy_soundness"] = bool(check_soundness.check_easy_soundness_net_in_fin_marking(net, im, fm))
    except Exception as exc:
        result["easy_soundness"] = False
        result["easy_soundness_error"] = str(exc)
    return result


def export_repair_variant(variant: RepairVariant, out_dir: str | Path = REPAIRED_DIR) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in variant.name)
    path = out_dir / f"{safe}_{variant.operation.replace('/', '_').replace(' ', '_')}.pnml"
    variant.petri_net.write_pnml(str(path))
    return path


def rerun_goccva_for_variant(
    variant: RepairVariant,
    inputs,
    analysis_log,
):
    try:
        return analyse(
            inputs.goal_model,
            variant.petri_net,
            analysis_log,
            inputs.targets,
            inputs.activity_mapping,
            initial_marking=None,
        )
    except Exception as exc:
        return None, None, None, str(exc)


def compare_summary(before_summary: list[dict], after_summary: list[dict], label: str) -> pd.DataFrame:
    def counts(summary):
        total = len(summary) or 1
        optimal = sum(row.get("traditional_class") == "optimal" for row in summary)
        strong = sum("strong" in str(row.get("goal_class", "")).lower() for row in summary)
        weak = sum("weak" in str(row.get("goal_class", "")).lower() for row in summary)
        non = total - strong - weak
        avg_fitness = sum(float(row.get("fitness") or 0) for row in summary) / total
        return {
            "optimal_cases": optimal,
            "optimal_pct": round(optimal * 100 / total, 1),
            "strong_goal_cases": strong,
            "weak_goal_cases": weak,
            "non_goal_cases": non,
            "avg_fitness": round(avg_fitness, 3),
        }

    rows = [{"model": "before", **counts(before_summary)}, {"model": label, **counts(after_summary)}]
    df = pd.DataFrame(rows)
    numeric = ["optimal_cases", "strong_goal_cases", "weak_goal_cases", "non_goal_cases", "avg_fitness"]
    delta = {"model": "delta"}
    for col in numeric:
        delta[col] = df.loc[1, col] - df.loc[0, col]
    delta["optimal_pct"] = df.loc[1, "optimal_pct"] - df.loc[0, "optimal_pct"]
    return pd.concat([df, pd.DataFrame([delta])], ignore_index=True)


def render_petri_net_png(wrapped: WrappedPetriNet, path: str | Path, title: str | None = None) -> Path:
    """Render a wrapped Petri net to a PNG file using PM4Py."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        gviz = pn_visualizer.apply(wrapped.net, wrapped.init, wrapped.final)
        pn_visualizer.save(gviz, str(path))
    except Exception:
        _render_petri_net_matplotlib(wrapped, path, title=title)
    return path


def render_pnml_file_png(pnml_path: str | Path, path: str | Path, title: str | None = None) -> Path:
    """Read a PNML file, then render that PNML through the wrapped PM4Py net path."""
    from Semantics.parsers.petri_net_processor import read_petri_net

    wrapped = read_petri_net(str(pnml_path))
    return render_petri_net_png(wrapped, path, title=title or str(pnml_path))


def petri_net_pm4py_visualization(wrapped: WrappedPetriNet):
    """Return a PM4Py Graphviz visualization object for a wrapped Petri net."""
    return pn_visualizer.apply(wrapped.net, wrapped.init, wrapped.final)


def pnml_file_pm4py_visualization(pnml_path: str | Path):
    """Read a PNML file and return its PM4Py visualization object."""
    from Semantics.parsers.petri_net_processor import read_petri_net

    wrapped = read_petri_net(str(pnml_path))
    return petri_net_pm4py_visualization(wrapped)


def soundness_function_map() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "function": "check_repair_soundness",
                "file": "GoRep/gorep_repair_ops.py",
                "purpose": "Wrapper used by GoRep to report soundness/correctness checks for each repaired Petri net.",
            },
            {
                "function": "pm4py.objects.petri_net.utils.check_soundness.check_wfnet",
                "file": "PM4Py library",
                "purpose": "Checks whether the net has workflow-net structure.",
            },
            {
                "function": "pm4py.objects.petri_net.utils.check_soundness.check_easy_soundness_net_in_fin_marking",
                "file": "PM4Py library",
                "purpose": "Checks whether PM4Py can treat the net as easy-sound for alignment/evaluation.",
            },
            {
                "function": "rerun_goccva_for_variant",
                "file": "GoRep/gorep_repair_ops.py",
                "purpose": "Correctness-by-evaluation: re-run GoCCvA on the repaired model and compare behavior/goal results.",
            },
            {
                "function": "compare_summary",
                "file": "GoRep/gorep_repair_ops.py",
                "purpose": "Computes before/after changes in fitness and goal-satisfaction classes.",
            },
        ]
    )


def _render_petri_net_matplotlib(wrapped: WrappedPetriNet, path: Path, title: str | None = None) -> None:
    import matplotlib.pyplot as plt
    import networkx as nx

    graph = nx.DiGraph()
    places = sorted(list(wrapped.net.places), key=lambda place: place.name)
    transitions = sorted(list(wrapped.net.transitions), key=lambda transition: transition.name)

    for place in places:
        graph.add_node(("p", place.name), label=place.name, kind="place")
    for transition in transitions:
        label = transition.label if transition.label is not None else transition.name
        graph.add_node(("t", transition.name), label=label, kind="transition")

    for arc in wrapped.net.arcs:
        src = arc.source
        dst = arc.target
        src_key = ("p", src.name) if src in places else ("t", src.name)
        dst_key = ("p", dst.name) if dst in places else ("t", dst.name)
        graph.add_edge(src_key, dst_key)

    try:
        for node in graph.nodes:
            if node[0] == "p":
                graph.nodes[node]["layer"] = 0
            else:
                graph.nodes[node]["layer"] = 1
        pos = nx.multipartite_layout(graph, subset_key="layer")
    except Exception:
        pos = nx.spring_layout(graph, seed=9, k=1.0)

    node_colors = ["#FFFFFF" if node[0] == "p" else "#DBEAFE" for node in graph.nodes]
    node_shapes = {"p": "o", "t": "s"}

    fig_width = max(14, min(28, len(graph.nodes) * 0.55))
    fig, ax = plt.subplots(figsize=(fig_width, 9))
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        arrows=True,
        arrowstyle="-|>",
        arrowsize=10,
        edge_color="#555555",
        width=1.0,
    )
    for kind, shape in node_shapes.items():
        nodes = [node for node in graph.nodes if node[0] == kind]
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=nodes,
            node_shape=shape,
            node_color=[node_colors[list(graph.nodes).index(node)] for node in nodes],
            edgecolors="#111827",
            linewidths=1.0,
            node_size=700 if kind == "p" else 1100,
            ax=ax,
        )
    labels = {node: data["label"] for node, data in graph.nodes(data=True)}
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=6, ax=ax)
    ax.set_axis_off()
    ax.set_title(title or "Petri net")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def render_petri_net_process_style_png(
    wrapped: WrappedPetriNet,
    path: str | Path,
    title: str | None = None,
) -> Path:
    """Render a Petri net in a paper-style process diagram using PNML coordinates."""
    import textwrap

    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    place_pos = {name: (x, y) for x, y, name in wrapped.positions.get("places", [])}
    trans_pos = {
        name: (x, y)
        for x, y, name, *_ in wrapped.positions.get("transitions", [])
    }

    # Repaired transitions may not exist in the original PNML layout. Place them
    # close to their connected places so the repair remains visible.
    for transition in wrapped.net.transitions:
        if transition.name in trans_pos:
            continue
        connected = []
        for arc in list(transition.in_arcs) + list(transition.out_arcs):
            other = arc.source if arc.target == transition else arc.target
            if hasattr(other, "name") and other.name in place_pos:
                connected.append(place_pos[other.name])
        if connected:
            avg_x = sum(x for x, _ in connected) / len(connected)
            avg_y = sum(y for _, y in connected) / len(connected)
            trans_pos[transition.name] = (avg_x + 0.15, avg_y - 0.55)

    # If any place lacks a coordinate, put it near connected transitions.
    for place in wrapped.net.places:
        if place.name in place_pos:
            continue
        connected = []
        for arc in list(place.in_arcs) + list(place.out_arcs):
            other = arc.source if arc.target == place else arc.target
            if hasattr(other, "name") and other.name in trans_pos:
                connected.append(trans_pos[other.name])
        if connected:
            avg_x = sum(x for x, _ in connected) / len(connected)
            avg_y = sum(y for _, y in connected) / len(connected)
            place_pos[place.name] = (avg_x + 0.45, avg_y)

    all_points = list(place_pos.values()) + list(trans_pos.values())
    min_x = min(x for x, _ in all_points) - 1.1
    max_x = max(x for x, _ in all_points) + 1.1
    min_y = min(y for _, y in all_points) - 1.0
    max_y = max(y for _, y in all_points) + 1.0

    fig, ax = plt.subplots(figsize=(16, 7.5))
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(max_y, min_y)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title(title or "Petri net", fontsize=13, fontweight="bold", pad=12)

    def node_position(node):
        if node.name in place_pos:
            return place_pos[node.name]
        return trans_pos[node.name]

    for arc in wrapped.net.arcs:
        if not hasattr(arc.source, "name") or not hasattr(arc.target, "name"):
            continue
        if arc.source.name not in place_pos and arc.source.name not in trans_pos:
            continue
        if arc.target.name not in place_pos and arc.target.name not in trans_pos:
            continue
        x1, y1 = node_position(arc.source)
        x2, y2 = node_position(arc.target)
        arrow = FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="->",
            mutation_scale=11,
            linewidth=1.2,
            color="#222222",
            shrinkA=14,
            shrinkB=16,
            connectionstyle="arc3,rad=0.0",
        )
        ax.add_patch(arrow)

    for place in wrapped.net.places:
        if place.name not in place_pos:
            continue
        x, y = place_pos[place.name]
        circle = Circle((x, y), 0.24, facecolor="white", edgecolor="#222222", linewidth=1.3, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y - 0.38, place.name, ha="center", va="top", fontsize=7, fontstyle="italic")

    for transition in wrapped.net.transitions:
        if transition.name not in trans_pos:
            continue
        x, y = trans_pos[transition.name]
        label = transition.label if transition.label is not None else transition.name
        is_hidden = transition.label is None or str(label).startswith("t_tau") or str(label).lower() in {"tau", "none"}
        if is_hidden:
            rect = Rectangle((x - 0.08, y - 0.35), 0.16, 0.7, facecolor="black", edgecolor="black", zorder=4)
            ax.add_patch(rect)
            ax.text(x, y + 0.55, transition.name, ha="center", va="bottom", fontsize=6, fontstyle="italic")
        else:
            width = 1.65
            height = 0.78
            rect = Rectangle((x - width / 2, y - height / 2), width, height, facecolor="white", edgecolor="#333333", linewidth=1.2, zorder=4)
            ax.add_patch(rect)
            wrapped_label = "\n".join(textwrap.wrap(str(label), width=15))
            ax.text(x, y, wrapped_label, ha="center", va="center", fontsize=6.5, fontweight="bold", zorder=5)

    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path
