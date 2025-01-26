from typing import Dict, List, Tuple, Set
from enums import ElementStatus, LinkType, LinkStatus

class GoalModel:
    def __init__(self):
        self.tasks: Dict[str, ElementStatus] = {}
        self.goals: Dict[str, ElementStatus] = {}
        self.qualities: Dict[str, ElementStatus] = {}
        self.links: List[Tuple[str, str, LinkType, LinkStatus]] = []
        self.requirements: Dict[str, List[List[str]]] = {}
        self.event_mapping: Dict[str, str] = {}
        self.execution_count: Dict[str, int] = {}
        self.last_activated_link: Tuple[str, str, LinkType, LinkStatus] = None

    def add_task(self, task_id: str):
        self.tasks[task_id] = ElementStatus.UNKNOWN
        self.execution_count[task_id] = 0

    def add_goal(self, goal_id: str):
        self.goals[goal_id] = ElementStatus.UNKNOWN

    def add_quality(self, quality_id: str):
        self.qualities[quality_id] = ElementStatus.UNKNOWN

    def add_link(self, parent: str, child: str, link_type: LinkType):
        self.links.append((parent, child, link_type, LinkStatus.UNKNOWN))

    def add_event_mapping(self, event: str, target: str):
        self.event_mapping[event] = target

    def process_event(self, event: str):
        print(f"\nProcessing event: {event}")
        if event not in self.event_mapping:
            return

        target = self.event_mapping[event]
        
        if target in self.tasks:
            self.tasks[target] = ElementStatus.ACTIVATED
            self.execution_count[target] += 1
            print(f"Task {target} activated and execution count increased to {self.execution_count[target]}")
        elif target in self.goals:
            self.goals[target] = ElementStatus.ACHIEVED
            print(f"Goal {target} activated directly by event")

        affected_parents = self._update_links_with_child(target)
        self._evaluate_goals(affected_parents)
        self._evaluate_qualities()

    def _update_links_with_child(self, child: str) -> Set[str]:
        affected_parents = set()
        for i, (parent, link_child, link_type, _) in enumerate(self.links):
            if link_child == child:
                # Check if child is partially activated/achieved
                if (child in self.tasks and self.tasks[child] == ElementStatus.PARTIALLY_ACTIVATED) or \
                   (child in self.goals and self.goals[child] == ElementStatus.PARTIALLY_ACHIEVED):
                    self.links[i] = (parent, child, link_type, LinkStatus.PARTIALLY_ACTIVATED)
                    print(f"Updated link {parent} <- {child} to PARTIALLY_ACTIVATED due to partial child status")
                else:
                    self.links[i] = (parent, child, link_type, LinkStatus.ACTIVATED)
                    print(f"Updated link {parent} <- {child} to ACTIVATED")
                    affected_parents.add(parent)  # Only add to affected_parents if fully activated
                self.last_activated_link = self.links[i]
        return affected_parents

    def _evaluate_goals(self, goals_to_check: Set[str]):
        processed_elements = set()
        elements_to_process = goals_to_check.copy()
        
        while elements_to_process:
            current = elements_to_process.pop()
            if current in processed_elements:
                continue
                
            if current not in self.goals and current not in self.tasks:
                continue

            if current in self.requirements:
                required_elements = self.requirements[current]
                achieved = False
                partially_achieved = False

                for requirement_set in required_elements:
                    all_activated = all(
                        self._is_element_activated(elem) and not self._is_partially_activated(elem)
                        for elem in requirement_set
                    )
                    any_activated = any(
                        (self._is_element_activated(elem) and not self._is_partially_activated(elem)) or
                        self._is_partially_activated(elem)
                        for elem in requirement_set
                    )

                    if all_activated:
                        achieved = True
                        break
                    elif any_activated:
                        partially_achieved = True

                if achieved:
                    if current in self.goals:
                        self.goals[current] = ElementStatus.ACHIEVED
                    else:
                        self.tasks[current] = ElementStatus.ACTIVATED
                    print(f"Goal/Task {current} achieved/activated")
                    affected_parents = self._set_links_for_child(current, LinkStatus.ACTIVATED)
                    elements_to_process.update(affected_parents)
                elif partially_achieved:
                    if current in self.goals:
                        self.goals[current] = ElementStatus.PARTIALLY_ACHIEVED
                    else:
                        self.tasks[current] = ElementStatus.PARTIALLY_ACTIVATED
                    print(f"Goal/Task {current} partially achieved/activated")
                    self._set_links_for_child(current, LinkStatus.PARTIALLY_ACTIVATED)
                    
            processed_elements.add(current)

    def _set_links_for_child(self, child: str, status: LinkStatus) -> Set[str]:
        affected_parents = set()
        for i, (parent, link_child, link_type, _) in enumerate(self.links):
            if link_child == child:
                self.links[i] = (parent, child, link_type, status)
                print(f"Updated link {parent} <- {child} to {status.value}")
                self.last_activated_link = self.links[i]
                if status != LinkStatus.PARTIALLY_ACTIVATED:
                    affected_parents.add(parent)
                    self._propagate_status_change(parent)
        return affected_parents

    def _is_element_activated(self, element: str) -> bool:
        if element in self.tasks:
            return self.tasks[element] in [ElementStatus.ACTIVATED, ElementStatus.PARTIALLY_ACTIVATED]
        elif element in self.goals:
            return self.goals[element] in [ElementStatus.ACHIEVED, ElementStatus.PARTIALLY_ACHIEVED]
        return False

    def _is_partially_activated(self, element: str) -> bool:
        if element in self.tasks:
            return self.tasks[element] == ElementStatus.PARTIALLY_ACTIVATED
        elif element in self.goals:
            return self.goals[element] == ElementStatus.PARTIALLY_ACHIEVED
        return False

    def _should_be_partially_activated(self, element: str) -> bool:
        related_links = [(p, c, t, s) for p, c, t, s in self.links if p == element]
        return any(status == LinkStatus.PARTIALLY_ACTIVATED for _, _, _, status in related_links)

    def _should_be_deactivated(self, element: str) -> bool:
        related_links = [(p, c, t, s) for p, c, t, s in self.links if p == element]
        return any(status == LinkStatus.DEACTIVATED for _, _, _, status in related_links)

    def _propagate_achievement(self, element: str, link_status: LinkStatus = None):
        for i, (parent, child, link_type, _) in enumerate(self.links):
            if child == element and link_status in [LinkStatus.ACTIVATED, LinkStatus.DEACTIVATED]:
                self.links[i] = (parent, child, link_type, link_status)
                self.last_activated_link = self.links[i]
                print(f"Propagating achievement: Updated link {parent} <- {child} to {link_status.value}")
                self._propagate_status_change(parent)

    def _propagate_status_change(self, element: str):
        if element in self.goals:
            if self._should_be_partially_activated(element):
                self.goals[element] = ElementStatus.PARTIALLY_ACHIEVED
                print(f"Goal {element} set to PARTIALLY_ACHIEVED due to propagation")
            elif self._should_be_deactivated(element):
                self.goals[element] = ElementStatus.DEACTIVATED
                print(f"Goal {element} set to DEACTIVATED due to propagation")
        elif element in self.tasks:
            if self._should_be_partially_activated(element):
                self.tasks[element] = ElementStatus.PARTIALLY_ACTIVATED
                print(f"Task {element} set to PARTIALLY_ACTIVATED due to propagation")
            elif self._should_be_deactivated(element):
                self.tasks[element] = ElementStatus.DEACTIVATED
                print(f"Task {element} set to DEACTIVATED due to propagation")

    def _evaluate_qualities(self):
        for quality in self.qualities:
            make_links = []
            break_links = []
            
            for parent, child, link_type, status in self.links:
                if parent == quality and status == LinkStatus.ACTIVATED:  # Only consider ACTIVATED links
                    if link_type == LinkType.MAKE:
                        make_links.append(child)
                    elif link_type == LinkType.BREAK:
                        break_links.append(child)

            if self.last_activated_link and self.last_activated_link[0] == quality and self.last_activated_link[3] == LinkStatus.ACTIVATED:
                parent, child, link_type, _ = self.last_activated_link
                if link_type == LinkType.MAKE:
                    self.qualities[quality] = ElementStatus.FULFILLED
                    print(f"Quality {quality} fulfilled due to MAKE links: {make_links}")
                    self._deactivate_break_links(quality)
                elif link_type == LinkType.BREAK:
                    self.qualities[quality] = ElementStatus.DENIED
                    print(f"Quality {quality} denied due to BREAK links: {break_links}")
                    self._handle_quality_denial(quality, make_links)

    def _deactivate_break_links(self, quality: str):
        for i, (parent, child, link_type, status) in enumerate(self.links):
            if parent == quality and link_type == LinkType.BREAK and status == LinkStatus.ACTIVATED:
                self.links[i] = (parent, child, link_type, LinkStatus.DEACTIVATED)
                print(f"Deactivated BREAK link {parent} <- {child}")
                # Start deactivation chain for the child
                if child in self.tasks and self.tasks[child] in [ElementStatus.ACTIVATED, ElementStatus.PARTIALLY_ACTIVATED]:
                    self._handle_deactivation(child, True)
                elif child in self.goals and self.goals[child] in [ElementStatus.ACHIEVED, ElementStatus.PARTIALLY_ACHIEVED]:
                    self._handle_deactivation(child, True)

    def _handle_quality_denial(self, quality: str, make_links: List[str]):
        for child in make_links:
            for i, (parent, link_child, link_type, status) in enumerate(self.links):
                if parent == quality and link_child == child and link_type == LinkType.MAKE:
                    self.links[i] = (parent, child, link_type, LinkStatus.DEACTIVATED)
                    print(f"Deactivated MAKE link {parent} <- {child}")
                    self._handle_deactivation(child, True)

    def _handle_deactivation(self, element: str, deactivate_subtree: bool):
        if element in self.goals:
            self.goals[element] = ElementStatus.DEACTIVATED
            print(f"Goal {element} deactivated")
        elif element in self.tasks:
            self.tasks[element] = ElementStatus.DEACTIVATED
            print(f"Task {element} deactivated")

        if deactivate_subtree:
            # Find all links where the deactivated element is a parent
            for i, (parent, child, link_type, status) in enumerate(self.links):
                if parent == element and status in [LinkStatus.ACTIVATED, LinkStatus.PARTIALLY_ACTIVATED]:
                    self.links[i] = (parent, child, link_type, LinkStatus.DEACTIVATED)
                    print(f"Deactivating link {parent} <- {child}")
                    # Recursively deactivate the child element and its subtree
                    if child in self.tasks and self.tasks[child] in [ElementStatus.ACTIVATED, ElementStatus.PARTIALLY_ACTIVATED]:
                        self._handle_deactivation(child, True)
                    elif child in self.goals and self.goals[child] in [ElementStatus.ACHIEVED, ElementStatus.PARTIALLY_ACHIEVED]:
                        self._handle_deactivation(child, True)