
from Implementation.enums import ElementStatus

def check_markings(model, expected_markings):
    for element, expected_status in expected_markings.items():
        actual_status = get_element_status(model, element)
        assert expected_status == actual_status, f"Element {element}: expected {expected_status}, got {actual_status}"

def set_markings(model, markings):
    for element, status in markings.items():
        set_element_status(model, element, status)

def get_element_status(model, element:str) -> ElementStatus | None:
    if element in model.goals:
        return model.goals[element]
    elif element in model.tasks:
        return model.tasks[element]
    else: return None

def set_element_status(model, element:str, status:ElementStatus) -> None:
    if element in model.goals:
        model.goals[element] = status
    elif element in model.tasks:
        model.tasks[element] = status
    else: 
        raise ValueError(f"Element {element} not found in model.")
