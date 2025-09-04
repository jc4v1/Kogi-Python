from typing import Dict, List, Tuple, Set
from typing_extensions import Self
from Implementation.enums import ElementStatus, QualityStatus, LinkType, LinkStatus
from Implementation.goal_model import GoalModel as BaseGoalModel
import functools

# Decorator to print successful rule applications
# The decorator assumes, that the function the decorator is 
# used with, returns a boolean indicating success or failurex
def log_rule(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        arg_str = ", ".join([repr(a) for a in args[1:]] + [f"{k}={v!r}" for k, v in kwargs.items()])
        # print(f"Calling {func.__name__}({arg_str})")
        result = func(*args, **kwargs)
        if result:
            print(f"Rule {func.__name__} applied successfully on arguments ({arg_str})")
        # print(f"Result {func.__name__} is {result}")
        return result
    return wrapper

class GoalModel(BaseGoalModel):
    
    def try_pie_rule(self, element : str) -> bool:
        if self.element_exists(element) and self.is_leaf(element):
            self.set_element_status(element,ElementStatus.TRUE_FALSE)
            return True
        return False
        
    
    def try_pand_rule(self, element: str) -> bool:
        and_links = [link for link in self.links if link[0] == element and link[2] == LinkType.AND]
        if (any(and_links) 
            and all(self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE for link in and_links)):
            self.set_element_status(element,ElementStatus.TRUE_FALSE)
            return True
        return False
        
    
    def try_por_rule(self, element: str) -> bool:
        or_links = [link for link in self.links if link[0] == element and link[2] == LinkType.OR]
        if any(self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE for link in or_links):
            self.set_element_status(element,ElementStatus.TRUE_FALSE)
            return True
        return False

    
    def try_pmake_rule(self, quality: str) -> bool:
        make_links = [link for link in self.links if link[0] == quality and link[2] == LinkType.MAKE]
        if (any(self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE for link in make_links) 
            and self.get_quality_status(quality) == QualityStatus.UNKNOWN):
            self.set_quality_status(quality,QualityStatus.FULFILLED)
            return True
        return False

    
    def try_pbreak_rule(self, quality: str) -> bool:
        break_links = [link for link in self.links if link[0] == quality and link[2] == LinkType.BREAK]
        if (any(self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE for link in break_links)
            and self.get_quality_status(quality) == QualityStatus.UNKNOWN):
            self.set_quality_status(quality,QualityStatus.DENIED)
            return True
        return False
    
    
    def try_bpfulfill_rule(self, quality: str) -> bool:
        make_links = [link for link in self.links if link[0] == quality and link[2] == LinkType.MAKE]
        if (any(self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE for link in make_links)
            and self.get_quality_status(quality) == QualityStatus.DENIED):
            self.set_quality_status(quality,QualityStatus.FULFILLED)
            break_elements = [link[1] for link in self.links if link[0] == quality 
                              and link[2] == LinkType.BREAK
                              and self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE]
            for elem in break_elements:
                true_true_refinements = self.true_false_refinements(elem,set())
                for e in true_true_refinements:
                    if self.get_element_status(e) == ElementStatus.TRUE_FALSE:
                        self.set_element_status(e, ElementStatus.TRUE_TRUE)
            return True
        return False
    
    
    def try_bpdeny_rule(self, quality: str) -> bool:
        break_links = [link for link in self.links if link[0] == quality and link[2] == LinkType.BREAK]
        if (any(self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE for link in break_links)
            and self.get_quality_status(quality) == QualityStatus.FULFILLED):
            self.set_quality_status(quality,QualityStatus.DENIED)
            make_elements = [link[1] for link in self.links if link[0] == quality 
                             and link[2] == LinkType.MAKE
                             and self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE]
            for elem in make_elements:
                true_false_refinements = self.true_false_refinements(elem,set())
                for e in true_false_refinements:
                    if self.get_element_status(e) == ElementStatus.TRUE_FALSE:
                        self.set_element_status(e, ElementStatus.TRUE_TRUE)
            return True
        return False

    def fire_element(self,element: str) -> None:
        self.changed_elements.clear()
        self.fire_elements({element})
        
    def fire_elements(self, elements: Set[str]) -> None:
        for e in elements:
            if self.try_any_rule(e):
                self.changed_elements.add(e)
                self.fire_elements(self._parents(e))
    
    def process_event(self, event: str) -> None:
        print(f"\nProcessing event: {event}")
        for target_set in self.event_mapping.get(event,[]):
            for element in target_set:
                self.fire_element(element)
            
    def _parents(self, element: str) -> Set[str]:
        return {link[0] for link in self.links if link[1] == element}
  
    def try_any_rule(self, element: str) -> bool:
        return (self.try_pie_rule(element) or
                self.try_por_rule(element) or
                self.try_pand_rule(element) or
                self.try_pmake_rule(element) or
                self.try_pbreak_rule(element) or
                self.try_bpfulfill_rule(element) or
                self.try_bpdeny_rule(element))
    
    def true_false_refinements(self, element: str, visited: Set[str]) -> Set[str]:
        result = {element}
        if element in visited:
            return result
        visited.add(element)  
        refinements = [link[1] for link in self.links if link[0] == element]
        result.update(refinements)
        for e in refinements:
            result.update(self.true_false_refinements(e,visited))
        return result
    
    def get_element_status(self, element: str) -> ElementStatus | None:
        if element in self.tasks:
            return self.tasks[element]
        elif element in self.goals:
            return self.goals[element]
        return None
    
    def element_exists(self, element: str) -> bool:
        return element in self.tasks or element in self.goals
    
    def set_element_status(self, element: str, status:ElementStatus) -> None:
        if element in self.tasks:
            old_status = self.tasks[element]
            self.tasks[element] = status
            print(f"Task {element}: {self._format_status(old_status)} -> {self._format_status(self.tasks[element])} {'(executed pending)' if status == ElementStatus.TRUE_TRUE else ''}")
        elif element in self.goals:
            old_status = self.goals[element]
            self.goals[element] = status
            print(f"Goal {element}: {self._format_status(old_status)} -> {self._format_status(self.goals[element])} {'(executed pending)' if status == ElementStatus.TRUE_TRUE else ''}")
        else:
            raise ValueError(f"Element {element} does not exist in tasks or goals.")    
            
    def is_leaf(self, element):
        return not any(link[0] == element for link in self.links)

    def get_quality_status(self, quality: str) -> QualityStatus | None:
        return self.qualities.get(quality, None)
    
    def set_quality_status(self, quality: str, status: QualityStatus) -> None:
        old_status = self.qualities[quality]
        self.qualities[quality] = status
        print(f"Quality {quality}: {self._format_status(old_status)} -> {self._format_status(self.qualities[quality])}")