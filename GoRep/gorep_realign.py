from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

try:
    from GoRep.paths import GOREP_DIR
except ModuleNotFoundError:
    from paths import GOREP_DIR


RELIGN_ZIP = Path(r"C:\Users\jcavi\Downloads\ReLIGn-tool-main.zip")
RELIGN_WORK_DIR = GOREP_DIR / "relign_artifacts"
RELIGN_TOOL_DIR = GOREP_DIR / "relign_tool"
HUBA_RELIGN_DIR = GOREP_DIR / "relign_huba"


def relign_environment_status(zip_path: str | Path = RELIGN_ZIP) -> pd.DataFrame:
    zip_path = Path(zip_path)
    rows = [
        ("ReLIGn zip available", zip_path.exists(), str(zip_path)),
        ("Java available", shutil.which("java") is not None, shutil.which("java") or ""),
        ("MySQL client available", shutil.which("mysql") is not None, shutil.which("mysql") or ""),
        ("MySQL server command available", shutil.which("mysqld") is not None, shutil.which("mysqld") or ""),
        ("Graphviz dot available", shutil.which("dot") is not None, shutil.which("dot") or ""),
        ("Docker available", shutil.which("docker") is not None, shutil.which("docker") or ""),
    ]
    if shutil.which("java"):
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            version = (result.stderr or result.stdout).splitlines()[0]
            rows.append(("Java version", True, version))
        except Exception as exc:
            rows.append(("Java version", False, str(exc)))
    if shutil.which("docker"):
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            rows.append(("Docker daemon running", result.returncode == 0, (result.stdout or result.stderr).strip()))
        except Exception as exc:
            rows.append(("Docker daemon running", False, str(exc)))
    return pd.DataFrame(rows, columns=["check", "ok", "detail"])


def relign_mysql_setup_options() -> pd.DataFrame:
    """Return setup options needed before RUN_RELIGN_BIG=True can work."""
    rows = [
        {
            "option": "Native MySQL 8.0.x",
            "what to do": "Install MySQL Server and client, ensure mysql and mysqld are on PATH, create/allow root with no password for local ReLIGn.",
            "command sketch": "winget install Oracle.MySQL",
            "notes": "ReLIGn README says MySQL 8.0.x up to 8.0.34 supports mysql_native_password by default.",
        },
        {
            "option": "MariaDB local server",
            "what to do": "Install MariaDB, set lower_case_table_names=1 under [mysqld], restart service, ensure mysql client is on PATH.",
            "command sketch": "winget install MariaDB.Server",
            "notes": "Matches the ReLIGn README's MariaDB note.",
        },
        {
            "option": "Docker MySQL 8.0.34",
            "what to do": "Start Docker Desktop, then run a MySQL container exposing port 3306 with an empty root password.",
            "command sketch": "docker run --name relign-mysql -e MYSQL_ALLOW_EMPTY_PASSWORD=yes -p 3306:3306 -d mysql:8.0.34",
            "notes": "Requires Docker daemon running. The container must be reachable by the Java jars.",
        },
        {
            "option": "Java 8",
            "what to do": "Install Java 8 and put it before Java 23 on PATH when running ReLIGn.",
            "command sketch": "winget install EclipseAdoptium.Temurin.8.JRE",
            "notes": "The current machine reports Java 23; ReLIGn asks for Java 8.",
        },
        {
            "option": "Graphviz",
            "what to do": "Install Graphviz if you want PM4Py/Graphviz native Petri-net rendering instead of the fallback renderer.",
            "command sketch": "winget install Graphviz.Graphviz",
            "notes": "Notebook has a Matplotlib fallback, but dot gives cleaner PN renders.",
        },
    ]
    return pd.DataFrame(rows)


def extract_relign_sample_artifacts(
    zip_path: str | Path = RELIGN_ZIP,
    out_dir: str | Path = RELIGN_WORK_DIR,
) -> dict[str, Path]:
    """Extract real ReLIGn .g and .subs artifacts from the provided zip."""
    zip_path = Path(zip_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    members = {
        "lig_graph": "ReLIGn-tool-main/data/testBank2000NoRandomNoise/testBank2000NoRandomNoise.g",
        "frequent_subgraphs": "ReLIGn-tool-main/data/testBank2000NoRandomNoise/testBank2000NoRandomNoise.subs",
    }
    extracted = {}
    with zipfile.ZipFile(zip_path) as archive:
        for key, member in members.items():
            target = out_dir / Path(member).name
            target.write_bytes(archive.read(member))
            extracted[key] = target
    return extracted


def extract_relign_tool(
    zip_path: str | Path = RELIGN_ZIP,
    out_dir: str | Path = RELIGN_TOOL_DIR,
) -> Path:
    """Extract the ReLIGn repository so its jar files can be called locally."""
    zip_path = Path(zip_path)
    out_dir = Path(out_dir)
    marker = out_dir / "ReLIGn-tool-main" / "src" / "core" / "big" / "IGInitializer.jar"
    if marker.exists():
        return out_dir / "ReLIGn-tool-main"
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(out_dir)
    return out_dir / "ReLIGn-tool-main"


def prepare_huba_relign_workspace(
    inputs,
    process_model_path: str | Path,
    out_dir: str | Path = HUBA_RELIGN_DIR,
    dataset_name: str = "HubaDomesticDeclarations",
) -> dict[str, Path]:
    """Create a Huba-specific ReLIGn experiment folder with XES and PNML inputs."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / f"{dataset_name}.xes"
    pnml_path = out_dir / f"{dataset_name}_petriNet.pnml"
    xes_exporter.apply(inputs.full_log, str(log_path))
    shutil.copyfile(process_model_path, pnml_path)
    big_dir = out_dir / "big"
    big_dir.mkdir(exist_ok=True)
    return {
        "workspace": out_dir,
        "dataset_name": Path(dataset_name),
        "log_path": log_path,
        "pnml_path": pnml_path,
        "big_dir": big_dir,
        "out_g_file": out_dir / f"{dataset_name}.g",
    }


def run_huba_relign_big(
    workspace: dict[str, Path],
    zip_path: str | Path = RELIGN_ZIP,
    timeout: int = 600,
) -> dict:
    """Run ReLIGn's BIG graph generation for the prepared Huba workspace."""
    tool_root = extract_relign_tool(zip_path)
    big_root = tool_root / "src" / "core" / "big"
    dataset_name = str(workspace["dataset_name"])
    log_path = Path(workspace["log_path"])
    pnml_path = Path(workspace["pnml_path"])
    out_g_file = Path(workspace["out_g_file"])
    conformance_path = Path(workspace["big_dir"])
    graph_path = Path(workspace["big_dir"])

    commands = [
        [
            "java",
            "-jar",
            str(big_root / "ComputePrecision.jar"),
            str(log_path),
            str(pnml_path),
        ],
        [
            "java",
            "-jar",
            str(big_root / "IGInitializer.jar"),
            "0",
            "150000",
            dataset_name,
            "1",
            "100000000",
            str(out_g_file),
            str(log_path),
            str(pnml_path),
            str(conformance_path),
            str(graph_path),
        ],
        [
            "java",
            "-jar",
            str(big_root / "InstanceGraphRules.jar"),
            "0",
            "150000",
            dataset_name,
            "1",
            "100000000",
            str(out_g_file),
            str(log_path),
            str(pnml_path),
            str(conformance_path),
            str(graph_path),
        ],
    ]

    logs = []
    for command in commands:
        result = subprocess.run(
            command,
            cwd=str(tool_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        logs.append(
            {
                "command": " ".join(command),
                "returncode": result.returncode,
                "stdout": result.stdout[-4000:],
                "stderr": result.stderr[-4000:],
            }
        )
        if result.returncode != 0:
            return {"ok": False, "out_g_file": out_g_file, "logs": logs}
    return {"ok": out_g_file.exists(), "out_g_file": out_g_file, "logs": logs}


def build_huba_relign_graph_from_detailed(detailed: list[dict], limit: int = 6) -> nx.DiGraph:
    """Build a Huba-specific ReLIGn-compatible graph from analysed trace variants."""
    graph = nx.DiGraph()
    node_id = 1
    for item in detailed[:limit]:
        previous = None
        for activity in item.get("trace", []):
            current = node_id
            node_id += 1
            graph.add_node(current, label=activity, trace_id=item.get("trace_id"))
            if previous is not None:
                graph.add_edge(previous, current, label=f"{graph.nodes[previous]['label']}__{activity}")
            previous = current
    return graph


def write_graph_as_relign_g(graph: nx.DiGraph, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["XP"]
    for node, data in graph.nodes(data=True):
        lines.append(f"v {node} {data.get('label', node)}")
    for src, dst, data in graph.edges(data=True):
        lines.append(f"e {src} {dst}  {data.get('label', '')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_huba_fragments_as_subs(patterns: pd.DataFrame, path: str | Path, limit: int = 8) -> Path:
    """Write Huba anomaly patterns as ReLIGn-compatible .subs fragments."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    grouped = (
        patterns.groupby(["pattern", "activity"], as_index=False)
        .agg(frequency=("frequency", "sum"))
        .sort_values("frequency", ascending=False)
        .head(limit)
    )
    for _, row in grouped.iterrows():
        pattern = str(row["pattern"])
        activity = str(row["activity"]).replace(" ", "_")
        rows.extend(
            [
                "S",
                f"v 1 {pattern}",
                f"v 2 {activity}",
                f"d 1 2 {pattern}__{activity}",
                "",
            ]
        )
    path.write_text("\n".join(rows), encoding="utf-8")
    return path


def _parse_graph_lines(lines: list[str], max_nodes: int | None = None) -> nx.DiGraph:
    graph = nx.DiGraph()
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] == "v" and len(parts) >= 3:
            node = int(parts[1])
            if max_nodes is None or node <= max_nodes:
                graph.add_node(node, label=parts[2])
        elif parts[0] in {"e", "d"} and len(parts) >= 4:
            src, dst = int(parts[1]), int(parts[2])
            if src in graph and dst in graph:
                graph.add_edge(src, dst, label=parts[3])
    return graph


def read_relign_lig_graph(path: str | Path, max_nodes: int = 35) -> nx.DiGraph:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    graph_lines = []
    for line in lines:
        if line.strip() == "XP" and graph_lines:
            break
        graph_lines.append(line)
    return _parse_graph_lines(graph_lines, max_nodes=max_nodes)


def read_relign_frequent_fragments(path: str | Path, limit: int = 5) -> list[nx.DiGraph]:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    fragments: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip() == "S":
            if current:
                fragments.append(current)
                current = []
            continue
        if line.strip():
            current.append(line)
    if current:
        fragments.append(current)
    return [_parse_graph_lines(fragment) for fragment in fragments[:limit]]


def relign_fragment_summary(fragments: list[nx.DiGraph]) -> pd.DataFrame:
    rows = []
    for index, graph in enumerate(fragments, start=1):
        labels = [data.get("label", "") for _, data in graph.nodes(data=True)]
        rows.append(
            {
                "fragment_id": index,
                "nodes": graph.number_of_nodes(),
                "edges": graph.number_of_edges(),
                "activities": " | ".join(labels),
            }
        )
    return pd.DataFrame(rows)


def render_relign_graph(
    graph: nx.DiGraph,
    title: str = "ReLIGn graph artifact",
    label_width: int = 16,
    node_size: int = 2600,
    figsize: tuple[int, int] | None = None,
):
    figsize = figsize or (max(13, min(26, graph.number_of_nodes() * 1.2)), 8)
    fig, ax = plt.subplots(figsize=figsize)
    if nx.is_directed_acyclic_graph(graph):
        try:
            generations = list(nx.topological_generations(graph))
            pos = {}
            for x, generation in enumerate(generations):
                for y, node in enumerate(generation):
                    pos[node] = (x, -y)
        except Exception:
            pos = nx.spring_layout(graph, seed=7, k=1.7)
    else:
        pos = nx.spring_layout(graph, seed=7, k=1.7)
    labels = {
        node: f"{node}\n" + "\n".join(_wrap_label(data.get("label", str(node)), label_width))
        for node, data in graph.nodes(data=True)
    }
    nx.draw_networkx_edges(graph, pos, ax=ax, arrows=True, arrowstyle="-|>", arrowsize=14, edge_color="#555")
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_color="#EAF2FF", edgecolors="#1F4E79", node_size=node_size)
    nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax, font_size=7, font_weight="bold")
    ax.set_title(title)
    ax.set_axis_off()
    return ax


def _wrap_label(label: object, width: int) -> list[str]:
    import textwrap

    text = str(label).replace("_", " ")
    return textwrap.wrap(text, width=width) or [text]


def relign_graph_label_table(graph: nx.DiGraph) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"node": node, "label": data.get("label", "")}
            for node, data in graph.nodes(data=True)
        ]
    )
