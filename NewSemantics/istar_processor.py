import json
from NewSemantics.goal_model import GoalModel
from Implementation.enums import LinkType

def read_istar_model(file_path):
    """Process the iStar goal model file."""

    # Parse the model
    with open(file_path, "r") as file:
        json_content = file.read()
    data = json.loads(json_content)
    model = GoalModel()
    positions = {}

    # Process nodes
    nodes_by_id = {}
    for actor in data["actors"]:
        for node in actor["nodes"]:
            nodes_by_id[node["id"]] = {
                "id": node["id"],
                "text": node["text"],
                "type": node["type"]
            }
            positions.update({node["text"]: (node["x"],node["y"])})
            if node["type"] == "istar.Task":
                model.add_task(node["text"])
            elif node["type"] == "istar.Goal":
                model.add_goal(node["text"])
            elif node["type"] == "istar.Quality":
                model.add_quality(node["text"])

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

    model.requirements = requirements
    model.positions = positions

    # Add event mappings
    for i, task in enumerate(sorted(list(model.tasks))):
        model.add_event_mapping(f"e{i+1}", task)
    
    return model
