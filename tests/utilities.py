
from Implementation.enums import ElementStatus, QualityStatus

def check_markings(model, expected_markings : dict[ str, ElementStatus | QualityStatus ]) -> None:
    for element, expected_status in expected_markings.items():
        actual_status = get_element_status(model, element)
        assert expected_status == actual_status, f"Element {element}: expected {expected_status}, got {actual_status}"

def set_markings(model, markings: dict[ str, ElementStatus | QualityStatus ]) -> None:
    for element, status in markings.items():
        set_element_status(model, element, status)

def get_element_status(model, element:str) -> ElementStatus | QualityStatus |  None:
    if element in model.goals:
        return model.goals[element]
    elif element in model.tasks:
        return model.tasks[element]
    elif element in model.qualities:
        return model.qualities[element]
    else: return None

def set_element_status(model, element:str, status:ElementStatus | QualityStatus) -> None:
    if element in model.goals:
        model.goals[element] = status
    elif element in model.tasks:
        model.tasks[element] = status
    elif element in model.qualities:
        model.qualities[element] = status
    else: 
        raise ValueError(f"Element {element} not found in model.")
