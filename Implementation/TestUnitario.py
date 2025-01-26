from goal_model import GoalModel
from enums import LinkType, ElementStatus

def create_model():
    model = GoalModel()
    
    # Add tasks
    tasks = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
    for task in tasks:
        model.add_task(task)
    
    # Add goals
    goals = ["G1", "G2", "G3"]
    for goal in goals:
        model.add_goal(goal)
    
    # Add quality
    model.add_quality("Q1")
    
    # Add links
    model.add_link("G3", "T8", LinkType.AND)
    model.add_link("T1", "T6", LinkType.AND)
    model.add_link("G1", "T2", LinkType.OR)
    model.add_link("Q1", "G2", LinkType.BREAK)
    model.add_link("Q1", "G1", LinkType.MAKE)
    model.add_link("G1", "T1", LinkType.OR)
    model.add_link("G3", "T1", LinkType.AND)
    model.add_link("T1", "T7", LinkType.AND)
    model.add_link("G2", "T3", LinkType.AND)
    model.add_link("G2", "T5", LinkType.AND)
    model.add_link("G2", "T4", LinkType.AND)
    
    # Add requirements
    model.requirements = {
        "G3": [['T8', 'T1']],
        "T1": [['T6', 'T7']],
        "G1": [['T2'], ['T1']],
        "G2": [['T3', 'T5', 'T4']]
    }
    
    # Add event mappings
    events = {
        "e1": "T1", "e2": "T2", "e3": "T3",
        "e4": "T4", "e5": "T5", "e6": "T6",
        "e7": "T7", "e8": "T8"
    }
    for event, target in events.items():
        model.add_event_mapping(event, target)
    
    return model

def print_model_state(model):
    print("\nModel State:")
    print("\nTasks:")
    for task, status in model.tasks.items():
        print(f"{task}: {status}")
    
    print("\nGoals:")
    for goal, status in model.goals.items():
        print(f"{goal}: {status}")
    
    print("\nQualities:")
    for quality, status in model.qualities.items():
        print(f"{quality}: {status}")

def main():
    print("Goal Model Trace Analyzer")
    print("Enter events (e1-e8) separated by commas (e.g., e1,e2,e3)")
    
    # Get trace input
    trace_input = input("Enter trace: ")
    events = [e.strip() for e in trace_input.split(",")]
    
    # Create and process model
    model = create_model()
    print("\nInitial state:")
    #print_model_state(model)
    
    print("\nProcessing events...")
    for event in events:
        print(f"\nProcessing {event}:")
        model.process_event(event)
        #print_model_state(model)

if __name__ == "__main__":
    main()