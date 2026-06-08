import json
from Semantics.goal_model import GoalModel
from Semantics.enums import LinkType


def _resolve_actor_legacy_name(
    raw_name: str,
    actor_name: str,
    duplicate_actor_names: set[str],
    used_names: set[str],
    qualified: bool,
) -> str:
    if qualified:
        base = f"({actor_name}) {raw_name}"
    elif raw_name in duplicate_actor_names:
        base = f"({actor_name}) {raw_name}"
    else:
        base = raw_name

    if base not in used_names:
        used_names.add(base)
        return base

    idx = 2
    while f"{base} #{idx}" in used_names:
        idx += 1
    resolved = f"{base} #{idx}"
    used_names.add(resolved)
    return resolved


def _resolve_dependum_legacy_name(
    raw_name: str,
    source_actor_name: str,
    target_actor_name: str,
    duplicate_dependum_names: set[str],
    used_dependum_names: set[str],
    qualified: bool,
) -> str:
    if qualified:
        base = raw_name
    elif raw_name in duplicate_dependum_names:
        base = f"({source_actor_name}) {raw_name} ({target_actor_name})"
    else:
        base = raw_name

    if base not in used_dependum_names:
        used_dependum_names.add(base)
        return base

    idx = 2
    while f"{base} #{idx}" in used_dependum_names:
        idx += 1
    resolved = f"{base} #{idx}"
    used_dependum_names.add(resolved)
    return resolved


def _add_legacy_element(model: GoalModel, node_type: str, legacy_name: str) -> None:
    if node_type == "istar.Task":
        model.add_task(legacy_name)
    elif node_type == "istar.Goal":
        model.add_goal(legacy_name)
    elif node_type == "istar.Quality":
        model.add_quality(legacy_name)

def read_istar_model(file_path, qualified: bool = False):
    """Process the iStar goal model file."""

    # Parse the model
    with open(file_path, "r") as file:
        json_content = file.read()
    data = json.loads(json_content)
    model = GoalModel()
    positions = {}
    used_legacy_names = set()
    used_dependum_names = set()

    node_id_to_actor_name = {}
    for actor in data["actors"]:
        node_id_to_actor_name[actor["id"]] = actor["text"]
        for node in actor["nodes"]:
            node_id_to_actor_name[node["id"]] = actor["text"]

    actor_name_counts = {}
    for actor in data["actors"]:
        for node in actor["nodes"]:
            if node["type"] in {"istar.Task", "istar.Goal", "istar.Quality"}:
                actor_name_counts[node["text"]] = actor_name_counts.get(node["text"], 0) + 1

    dependum_name_counts = {}
    for dep in data.get("dependencies", []):
        if dep["type"] in {"istar.Task", "istar.Goal", "istar.Quality"}:
            dependum_name_counts[dep["text"]] = dependum_name_counts.get(dep["text"], 0) + 1

    dependum_names = set(dependum_name_counts.keys())
    duplicate_dependum_names = {name for name, count in dependum_name_counts.items() if count > 1}

    if qualified and duplicate_dependum_names:
        raise ValueError("Duplicated Dependum")

    duplicate_actor_names = {name for name, count in actor_name_counts.items() if count > 1}
    duplicate_actor_names |= {name for name in actor_name_counts if name in dependum_names}

    # Process nodes
    nodes_by_id = {}
    for actor in data["actors"]:
        actor_name = actor["text"]
        nodes_by_id[actor["id"]] = {
            "id": actor["id"],
            "text": actor["text"],
            "type": actor["type"],
        }
        for node in actor["nodes"]:
            legacy_name = _resolve_actor_legacy_name(
                node["text"],
                actor_name,
                duplicate_actor_names,
                used_legacy_names,
                qualified,
            )
            nodes_by_id[node["id"]] = {
                "id": node["id"],
                "text": legacy_name,
                "type": node["type"]
            }
            positions.update({legacy_name: (node["x"], node["y"])})
            _add_legacy_element(model, node["type"], legacy_name)

    for dependency in data.get("dependencies", []):
        source_actor_name = node_id_to_actor_name[dependency["source"]]
        target_actor_name = node_id_to_actor_name[dependency["target"]]
        legacy_dependum_name = _resolve_dependum_legacy_name(
            dependency["text"],
            source_actor_name,
            target_actor_name,
            duplicate_dependum_names,
            used_dependum_names,
            qualified,
        )
        source_text = nodes_by_id[dependency["source"]]["text"]
        target_text = nodes_by_id[dependency["target"]]["text"]
        nodes_by_id[dependency["id"]] = {
            "id": dependency["id"],
            "text": legacy_dependum_name,
            "type": dependency["type"],
        }
        positions.update({legacy_dependum_name: (dependency["x"], dependency["y"])})
        _add_legacy_element(model, dependency["type"], legacy_dependum_name)

        model.add_dependency(
            source=source_text,
            target=target_text,
            dependum=legacy_dependum_name,
            dependum_type=dependency["type"],
        )

    # Process links and requirements
    requirements = {}
    for link in data["links"]:
        target = nodes_by_id[link["target"]]["text"]
        source = nodes_by_id[link["source"]]["text"]

        if link["type"] == "istar.AndRefinementLink":
            model.add_link(target, source, LinkType.AND)
            if source not in requirements:
                requirements[source] = []
            if not requirements[source] or not isinstance(
                requirements[source][-1], list
            ):
                requirements[source].append([])
            requirements[source][-1].append(target)
        elif link["type"] == "istar.OrRefinementLink":
            model.add_link(target, source, LinkType.OR)
            if source not in requirements:
                requirements[source] = []
            requirements[source].append([target])
        elif link["type"] == "istar.ContributionLink":
            if link.get("label") == "make":
                model.add_link(target, source, LinkType.MAKE)
            elif link.get("label") == "break":
                model.add_link(target, source, LinkType.BREAK)
        elif link["type"] == "istar.DependencyLink":
            source_type = nodes_by_id[link["source"]]["type"]
            target_type = nodes_by_id[link["target"]]["type"]
            if source_type != "istar.Actor" and target_type != "istar.Actor":
                model.add_link(target, source, LinkType.DEPENDENCY)

    model.requirements = requirements
    model.istar_positions = positions
    
    model.istar_width = data["diagram"]["width"]
    model.istar_height = data["diagram"]["height"]
    
    # Add event mappings
    for i, element in enumerate(sorted(list(_get_leaves(model)))):
        model.add_event_mapping(f"e{i+1}->{element.lower()}", element)
        
    return model

def _get_leaves(model):
    links = model.links
    parents = set()
    children = set()

    for parent, child, _ in links:
        parents.add(parent)
        children.add(child)

    # Leaves are nodes that appear as children but never as parents
    leaves = children - parents
    return leaves