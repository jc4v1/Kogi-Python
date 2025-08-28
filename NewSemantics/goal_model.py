from typing import Dict, List, Tuple, Set
from typing_extensions import Self
from Implementation.enums import ElementStatus, QualityStatus, LinkType, LinkStatus
from Implementation.goal_model import GoalModel as BaseGoalModel

class GoalModel(BaseGoalModel):
    def try_pie_rule(self, element : str) -> bool:
        if self.element_exists(element) and self.is_leaf(element):
            self.set_element_status(element,ElementStatus.TRUE_FALSE)
            return True
        return False
        
    def try_pand_rule(self, element: str) -> bool:
        and_links = [link for link in self.links if link[0] == element and link[2] == LinkType.AND]
        if all(self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE for link in and_links):
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
                true_true_refinements = self.true_false_refinements(elem,set())
                for e in true_true_refinements:
                    self.set_element_status(e, ElementStatus.TRUE_TRUE)
            return True
        return False

    def true_false_refinements(self, element: str, visited: Set[str]) -> Set[str]:
        result = {element}
        if element in visited:
            return result
        visited.add(element)  
        refinements = [link[1] for link in self.links if link[0] == element 
                       and self.get_element_status(link[1]) == ElementStatus.TRUE_FALSE]
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
            self.tasks[element] = status
        elif element in self.goals:
            self.goals[element] = status
            
    def is_leaf(self, element):
        return not any(link[0] == element for link in self.links)

    def get_quality_status(self, quality: str) -> QualityStatus | None:
        return self.qualities.get(quality, None)
    
    def set_quality_status(self, quality: str, status: QualityStatus) -> None:
        self.qualities[quality] = status
