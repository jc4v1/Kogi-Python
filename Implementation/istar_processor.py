from enum import Enum
import json
from google.colab import files

class LinkType(Enum):
    AND = "AND"
    OR = "OR"
    MAKE = "MAKE"
    BREAK = "BREAK"

class GoalModel:
    def __init__(self):
        self.tasks = set()
        self.goals = set()
        self.qualities = set()
        self.links = []
        self.requirements = {}
        self.event_mappings = {}

    def add_task(self, task_id): self.tasks.add(task_id)
    def add_goal(self, goal_id): self.goals.add(goal_id)
    def add_quality(self, quality_id): self.qualities.add(quality_id)
    def add_link(self, source, target, link_type): self.links.append((target, source, link_type))  # Cambiado el orden
    def add_event_mapping(self, event, task): self.event_mappings[event] = task

def process_istar_model():
    """Process iStar model file and generate demo_model.py"""
    print("Please upload your iStar goal model file (.txt format)")
    uploaded = files.upload()
    
    for filename, content in uploaded.items():
        try:
            # Parse model
            json_content = content.decode('utf-8')
            data = json.loads(json_content)
            model = GoalModel()
            
            # Process nodes
            nodes_by_id = {}
            for actor in data['actors']:
                for node in actor['nodes']:
                    nodes_by_id[node['id']] = {
                        'id': node['id'],
                        'text': node['text'],
                        'type': node['type']
                    }
                    if node['type'] == 'istar.Task': model.add_task(node['text'])
                    elif node['type'] == 'istar.Goal': model.add_goal(node['text'])
                    elif node['type'] == 'istar.Quality': model.add_quality(node['text'])
            
            # Process links and requirements
            requirements = {}
            for link in data['links']:
                target= nodes_by_id[link['source']]['text']  # Cambiado a target
                source = nodes_by_id[link['target']]['text']  # Cambiado a source
                
                if link['type'] == 'istar.AndRefinementLink':
                    model.add_link(target, source, LinkType.AND)
                    if source not in requirements: requirements[source] = []
                    if not requirements[source] or not isinstance(requirements[source][-1], list):
                        requirements[source].append([])
                    requirements[source][-1].append(target)
                    
                elif link['type'] == 'istar.OrRefinementLink':
                    model.add_link(target, source, LinkType.OR)
                    if source not in requirements: requirements[source] = []
                    requirements[source].append([target])
                    
                elif link['type'] == 'istar.ContributionLink':
                    if link.get('label') == 'make':
                        model.add_link(target, source, LinkType.MAKE)
                    elif link.get('label') == 'break':
                        model.add_link(target, source, LinkType.BREAK)
            
            model.requirements = requirements
            
            # Add event mappings
            for i, task in enumerate(sorted(list(model.tasks))):
                model.add_event_mapping(f"e{i+1}", task)
            
            # Generate code
            code = ["from goal_model import GoalModel", "from enums import LinkType\n", "def create_model():",
                   "    model = GoalModel()\n"]
            
            code.extend([f"    model.add_task(\"{task}\")" for task in sorted(model.tasks)])
            code.append("")
            code.extend([f"    model.add_goal(\"{goal}\")" for goal in sorted(model.goals)])
            code.append("")
            code.extend([f"    model.add_quality(\"{quality}\")" for quality in sorted(model.qualities)])
            code.append("")
            
            for target, source, link_type in model.links:  # Cambiado a target, source
                code.append(f"    model.add_link(\"{target}\", \"{source}\", LinkType.{link_type.name})")
            code.append("")
            
            if model.requirements:
                code.append("    model.requirements = {")
                for source, reqs in model.requirements.items():  # Cambiado a source
                    code.append(f"        \"{source}\": {str(reqs)},")
                code.append("    }")
            code.append("")
            
            for event, task in model.event_mappings.items():
                code.append(f"    model.add_event_mapping(\"{event}\", \"{task}\")")
            code.append("")
            code.append("    return model\n")  # Added 4 spaces before return and a newline after
            
            # Save to demo_model.py
            with open("demo_model.py", 'w') as f:
                f.write("\n".join(code))
            
            print(f"\nGenerated demo_model.py successfully!")
            print("\nModel Structure:")
            print(f"Tasks: {sorted(list(model.tasks))}")
            print(f"Goals: {sorted(list(model.goals))}")
            print(f"Qualities: {sorted(list(model.qualities))}")
            print(f"Number of links: {len(model.links)}")
            print(f"Number of requirements: {len(model.requirements)}")
            
        except Exception as e:
            print(f"Error processing file {filename}: {str(e)}")

if __name__ == "__main__":
    process_istar_model()
