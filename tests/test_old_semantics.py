from Implementation.enums import LinkType, ElementStatus, QualityStatus
from Implementation.goal_model import GoalModel
from utilities import *

# CELL 2 - Model Creation Function
def create_model_from_paper():
    """Create the goal model using your existing create_model function logic"""
    model = GoalModel()
    
    # Add tasks
    tasks = ["PT", "FS", "AP", "IP", "UE", "RA", "DMP", "O", "G"]
    for task in tasks:
        model.add_task(task)
    
    # Add goals
    goals = ["DB", "DP"]
    for goal in goals:
        model.add_goal(goal)
    
    # Add quality
    model.add_quality("DPA")
    
    # Add links (from your code)
    model.add_link("DPA", "DB", LinkType.BREAK)
    model.add_link("DPA", "AP", LinkType.MAKE)
    model.add_link("DPA", "DP", LinkType.MAKE)
    model.add_link("DB", "PT", LinkType.AND)
    model.add_link("DB", "FS", LinkType.AND)
    model.add_link("DP", "IP", LinkType.AND)
    model.add_link("DP", "DMP", LinkType.AND)
    model.add_link("IP", "UE", LinkType.AND)
    model.add_link("IP", "RA", LinkType.AND)
    model.add_link("DMP", "O", LinkType.OR)
    model.add_link("DMP", "G", LinkType.OR)
    
    # Add requirements
    model.requirements = {
        "DMP": [['G'], ['O']],
        "IP": [['UE', 'RA']],
        "DP": [['IP', 'DMP']],
        "DB": [['PT', 'FS']]
    }
    
    # Add event mappings
    events = {
        "pt": "PT",
        "fs": "FS",
        "ap": "AP",
        "ue": "UE",
        "ra": "RA",
        "o": "O",
        "g": "G"
    }
    for event, target in events.items():
        model.add_event_mapping(event, target)
    return model

def test_transitions():
    gm = create_model_from_paper()
    check_markings(gm,{"PT":ElementStatus.UNKNOWN,
                   "FS":ElementStatus.UNKNOWN,
                   "DB":ElementStatus.UNKNOWN,
                   "DPA":QualityStatus.UNKNOWN
                    })
    gm.process_event("pt")
    gm.process_event("fs")
    gm.print_markings()
    check_markings(gm,{"PT":ElementStatus.TRUE_FALSE,
                   "FS":ElementStatus.TRUE_FALSE,
                   "DB":ElementStatus.TRUE_FALSE,
                   "DPA":QualityStatus.DENIED
                    })
    