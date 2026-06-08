from __future__ import annotations

from textwrap import fill

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

try:
    from GoRep.paths import ensure_repo_root_on_path
except ModuleNotFoundError:
    from paths import ensure_repo_root_on_path

ensure_repo_root_on_path()

from Semantics.goccva.pipeline import ABSENCE


def _wrapped(text: object, width: int = 18) -> str:
    return fill(str(text), width=width)


def render_pipeline_overview():
    """Render a compact graphical overview of the GoRep pipeline."""
    stages = [
        ("Inputs", "Event log\nProcess model\nGoal model\nTargets"),
        ("GoCCvA", "Align trace and model\nCompute target status\nRender gamma*"),
        ("ReLIGn support", "Build local instance graph\nFind local anomalous fragments"),
        ("High-level anomalies", "Skipped\nInserted\nRepeated\nReplaced\nSwapped"),
        ("Repair candidates", "Add\nDelete/forbid\nSwap\nControlled loop"),
        ("Multicriteria decision", "Fitness\nPrecision risk\nGoal fulfillment\nSoundness"),
    ]
    fig, ax = plt.subplots(figsize=(16, 4.6))
    ax.set_axis_off()
    x_positions = range(len(stages))

    for i, (title, body) in enumerate(stages):
        ax.text(
            i,
            0.62,
            title,
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.45", fc="#EAF2FF", ec="#1F4E79", lw=1.5),
        )
        ax.text(
            i,
            0.18,
            body,
            ha="center",
            va="center",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.4", fc="#FFFFFF", ec="#888888", lw=1.0),
        )
        if i < len(stages) - 1:
            ax.annotate(
                "",
                xy=(i + 0.68, 0.62),
                xytext=(i + 0.30, 0.62),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#333333"),
            )

    ax.set_xlim(-0.55, len(stages) - 0.45)
    ax.set_ylim(-0.12, 0.95)
    ax.set_title("GoRep step-by-step: from goal-oriented alignments to repair recommendations", fontsize=15)
    return ax


def render_paper_takeaways():
    """Render paper takeaways as an incorporation matrix."""
    rows = [
        {
            "source": "GoCCvA",
            "takeaway": "Do not judge a trace only by control-flow fitness; inspect target satisfaction over the alignment.",
            "incorporation": "gamma* = alignment moves + target status evolution.",
        },
        {
            "source": "Grohs et al. 2024",
            "takeaway": "Log/model moves are too low level; lift them to process-level patterns.",
            "incorporation": "Skipped, inserted, repeated, replaced, and swapped anomaly patterns.",
        },
        {
            "source": "ReLIGn",
            "takeaway": "Local Instance Graphs make anomalous fragments inspectable and repairable locally.",
            "incorporation": "LIG-like graph per trace variant; later replace with ReLIGn frequent subgraphs.",
        },
        {
            "source": "Armas-Cervantes et al. 2017",
            "takeaway": "Repair should be interactive/incremental to avoid overgeneralization.",
            "incorporation": "Candidates are recommendations with precision risk, not automatic model edits.",
        },
        {
            "source": "Polyvyanyy et al. 2016",
            "takeaway": "Repair is an optimization under change costs and impact on fitness.",
            "incorporation": "Weighted scoring combines fitness gain, change cost, support, and goal delta.",
        },
    ]
    return pd.DataFrame(rows)


def render_alignment_move_graph(detailed: list[dict], trace_id: int = 1):
    """Render the real PM4Py alignment moves for one analysed trace variant."""
    item = next((row for row in detailed if row.get("trace_id") == trace_id), None)
    if item is None:
        raise ValueError(f"Trace id {trace_id} not found.")

    graph = nx.DiGraph()
    colors = []
    labels = {}
    for idx, (log_side, model_side) in enumerate(item.get("pm4py_alignment", []), start=1):
        if log_side == ABSENCE and model_side != ABSENCE:
            move_type = "model move\n(skipped in log)"
            color = "#FDE68A"
            label = f"MOVE {idx}\nM: {_wrapped(model_side, 20)}"
        elif model_side == ABSENCE and log_side != ABSENCE:
            move_type = "log move\n(extra in log)"
            color = "#FCA5A5"
            label = f"MOVE {idx}\nL: {_wrapped(log_side, 20)}"
        elif log_side != model_side:
            move_type = "replacement"
            color = "#C4B5FD"
            label = f"MOVE {idx}\nL: {_wrapped(log_side, 16)}\nM: {_wrapped(model_side, 16)}"
        else:
            move_type = "sync"
            color = "#BBF7D0"
            label = f"MOVE {idx}\n{_wrapped(log_side, 20)}"
        graph.add_node(idx, move_type=move_type)
        labels[idx] = label
        colors.append(color)
        if idx > 1:
            graph.add_edge(idx - 1, idx)

    width = max(12, graph.number_of_nodes() * 1.9)
    fig, ax = plt.subplots(figsize=(width, 4))
    pos = {node: (node, 0) for node in graph.nodes}
    nx.draw_networkx_edges(graph, pos, ax=ax, arrows=True, arrowstyle="-|>", arrowsize=18, edge_color="#555")
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_color=colors, node_size=3100, edgecolors="#111827", linewidths=1.2)
    nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax, font_size=8)
    ax.set_axis_off()
    ax.set_title(f"Real alignment moves for trace variant {trace_id}", fontsize=14)
    return ax


def render_theta_heatmap(theta_rows: pd.DataFrame, trace_id: int = 1):
    """Render target status evolution for one trace as a compact heatmap."""
    subset = theta_rows[theta_rows["trace_id"] == trace_id].copy()
    if subset.empty:
        raise ValueError(f"No theta rows for trace id {trace_id}.")

    status_rank = {"unknown": 0, "pending": 1, "denied": 2, "satisfied": 3}
    colors = {
        "unknown": "#E5E7EB",
        "pending": "#FDE68A",
        "denied": "#FCA5A5",
        "satisfied": "#BBF7D0",
    }
    targets = list(dict.fromkeys(subset["target"]))
    steps = sorted(subset["step"].unique())

    fig, ax = plt.subplots(figsize=(max(9, len(steps) * 0.75), 1.2 + len(targets) * 0.75))
    for y, target in enumerate(targets):
        target_rows = subset[subset["target"] == target].set_index("step")
        for x, step in enumerate(steps):
            status = target_rows.loc[step, "status"] if step in target_rows.index else "unknown"
            ax.add_patch(plt.Rectangle((x, y), 1, 1, facecolor=colors.get(status, "#FFFFFF"), edgecolor="#FFFFFF"))
            ax.text(x + 0.5, y + 0.5, str(status)[:3], ha="center", va="center", fontsize=8)

    ax.set_xlim(0, len(steps))
    ax.set_ylim(0, len(targets))
    ax.set_xticks([x + 0.5 for x in range(len(steps))], labels=[str(s) for s in steps])
    ax.set_yticks([y + 0.5 for y in range(len(targets))], labels=targets)
    ax.invert_yaxis()
    ax.set_xlabel("Alignment step")
    ax.set_title(f"Theta target-status evolution for trace variant {trace_id}")
    return ax


def render_candidate_decision_tree():
    """Render the rule of thumb for add/delete/swap/loop decisions."""
    graph = nx.DiGraph()
    nodes = {
        "start": "High-level\nanomaly",
        "goal": "Does it harm\ntargets?",
        "positive": "Is it a positive\nworkaround?",
        "delete": "Delete / forbid\nor add guard",
        "add": "Add controlled\nbehavior",
        "repeat": "Repeated recovery\nbehavior?",
        "loop": "Controlled loop",
        "swap": "Swap / replace\nlocal order",
        "score": "Score candidates:\nfitness, precision,\ngoals, cost, soundness",
    }
    for node, label in nodes.items():
        graph.add_node(node, label=label)
    edges = [
        ("start", "goal", ""),
        ("goal", "delete", "yes"),
        ("goal", "positive", "no/unclear"),
        ("positive", "add", "yes"),
        ("positive", "repeat", "no"),
        ("repeat", "loop", "yes"),
        ("repeat", "swap", "no"),
        ("delete", "score", ""),
        ("add", "score", ""),
        ("loop", "score", ""),
        ("swap", "score", ""),
    ]
    graph.add_edges_from((src, dst, {"label": label}) for src, dst, label in edges)
    pos = {
        "start": (0, 0),
        "goal": (2, 0),
        "delete": (4, 1.2),
        "positive": (4, -1.0),
        "add": (6, -0.2),
        "repeat": (6, -1.8),
        "loop": (8, -1.2),
        "swap": (8, -2.4),
        "score": (10, 0),
    }
    fig, ax = plt.subplots(figsize=(15, 5))
    labels = nx.get_node_attributes(graph, "label")
    edge_labels = nx.get_edge_attributes(graph, "label")
    nx.draw_networkx_edges(graph, pos, ax=ax, arrows=True, arrowstyle="-|>", arrowsize=18, width=1.5)
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_size=3200, node_color="#EFF6FF", edgecolors="#1F4E79", linewidths=1.4)
    nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax, font_size=9, font_weight="bold")
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, ax=ax, font_size=9)
    ax.set_axis_off()
    ax.set_title("How GoRep decides whether to add, delete/forbid, swap, or loop", fontsize=14)
    return ax


def render_candidate_score_breakdown(ranking: pd.DataFrame, top_n: int = 5):
    if ranking.empty:
        raise ValueError("Ranking is empty.")
    score_cols = ["fitness_score", "precision_score", "goal_score", "similarity_score", "support_score"]
    plot_df = ranking.head(top_n).set_index("candidate_id")[score_cols]
    ax = plot_df.plot(kind="bar", figsize=(12, 4.8), ylim=(0, 1), rot=0)
    ax.set_ylabel("Normalized criterion score")
    ax.set_title("Why candidates are ranked: multicriteria score components")
    ax.legend(loc="upper right")
    return ax
