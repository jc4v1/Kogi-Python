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


    def add_task(self, task_id: str):
        self.tasks[task_id] = ElementStatus.UNKNOWN
        self.execution_count[task_id] = 0


    def add_goal(self, goal_id: str):
        self.goals[goal_id] = ElementStatus.UNKNOWN


    def add_quality(self, quality_id: str):
        self.qualities[quality_id] = ElementStatus.UNKNOWN


    def add_link(self, parent: str, child: str, link_type: LinkType):
        self.links.append((parent, child, link_type, LinkStatus.UNKNOWN))


    def add_event_mapping(self, event: str, task: str):
        """Adds a mapping between an event and a task."""
        self.event_mapping[event] = task


    def process_event(self, event: str):
        print(f"\nProcessing event: {event}")
        if event not in self.event_mapping:
            print(f"No task mapping found for event {event}")
            return


        # Step 1: Activate task and increment execution count
        task = self.event_mapping[event]
        self.tasks[task] = ElementStatus.ACTIVATED
        self.execution_count[task] += 1
        print(f"Task {task} activated and execution count increased to {self.execution_count[task]}")


        # Step 2: Update links where task is child
        affected_parents = self._update_links_with_child(task)
       
        # Step 3-4: Evaluate goals and propagate effects
        self._evaluate_goals(affected_parents)
       
        # Step 5: Handle quality propagation
        self._evaluate_qualities()


    def _update_links_with_child(self, child: str) -> Set[str]:
        affected_parents = set()
        for i, (parent, link_child, link_type, _) in enumerate(self.links):
            if link_child == child:
                self.links[i] = (parent, child, link_type, LinkStatus.ACTIVATED)
                affected_parents.add(parent)
                print(f"Updated link {parent} <- {child} to ACTIVATED")
        return affected_parents


    def _evaluate_goals(self, goals_to_check: Set[str]):
        for goal in goals_to_check:
            if goal not in self.goals and goal not in self.tasks:
                continue


            if goal in self.requirements:
                required_elements = self.requirements[goal]
                achieved = False
                partially_achieved = False


                for requirement_set in required_elements:
                    all_activated = all(
                        self._is_element_activated(elem)
                        for elem in requirement_set
                    )
                    any_activated = any(
                        self._is_element_activated(elem)
                        for elem in requirement_set
                    )
                   
                    if all_activated:
                        achieved = True
                        break
                    elif any_activated:
                        partially_achieved = True


                if achieved:
                    if goal in self.goals:
                        self.goals[goal] = ElementStatus.ACHIEVED
                    else:
                        self.tasks[goal] = ElementStatus.ACTIVATED
                    print(f"Goal/Task {goal} achieved/activated")
                    self._propagate_achievement(goal)
                elif partially_achieved:
                    if goal in self.goals:
                        self.goals[goal] = ElementStatus.PARTIALLY_ACHIEVED
                    else:
                        self.tasks[goal] = ElementStatus.PARTIALLY_ACTIVATED
                    print(f"Goal/Task {goal} partially achieved/activated")


    def _is_element_activated(self, element: str) -> bool:
        if element in self.tasks:
            return self.tasks[element] == ElementStatus.ACTIVATED
        elif element in self.goals:
            return self.goals[element] == ElementStatus.ACHIEVED
        return False


    def _propagate_achievement(self, element: str):
        for i, (parent, child, link_type, _) in enumerate(self.links):
            if child == element:
                self.links[i] = (parent, child, link_type, LinkStatus.ACTIVATED)
                print(f"Propagating achievement: Updated link {parent} <- {child} to ACTIVATED")


    def _evaluate_qualities(self):
        for quality in self.qualities:
            make_links = []
            break_links = []


            # Collect MAKE and BREAK links
            for parent, child, link_type, status in self.links:
                if parent == quality:
                    if link_type == LinkType.MAKE and status == LinkStatus.ACTIVATED:
                        make_links.append(child)
                    elif link_type == LinkType.BREAK and status == LinkStatus.ACTIVATED:
                        break_links.append(child)


            # Handle conflicts between MAKE and BREAK
            if break_links:
                self.qualities[quality] = ElementStatus.DENIED
                print(f"Quality {quality} denied due to BREAK links: {break_links}")
                self._handle_quality_denial(quality)
            elif make_links:
                self.qualities[quality] = ElementStatus.FULFILLED
                print(f"Quality {quality} fulfilled due to MAKE links: {make_links}")


    def _handle_quality_denial(self, quality: str):
        for i, (parent, child, link_type, status) in enumerate(self.links):
            if parent == quality:
                if link_type == LinkType.MAKE and status == LinkStatus.ACTIVATED:
                    self.links[i] = (parent, child, link_type, LinkStatus.DEACTIVATED)
                    print(f"Deactivated MAKE link {parent} <- {child}")
                    self._handle_deactivation(child)


    def _handle_deactivation(self, element: str):
        if element in self.goals:
            self.goals[element] = ElementStatus.DEACTIVATED
            print(f"Goal {element} deactivated")
        elif element in self.tasks:
            self.tasks[element] = ElementStatus.DEACTIVATED
            print(f"Task {element} deactivated")


        # Propagate deactivation through links
        for i, (parent, child, link_type, status) in enumerate(self.links):
            if parent == element and status == LinkStatus.ACTIVATED:
                self.links[i] = (parent, child, link_type, LinkStatus.DEACTIVATED)
                print(f"Propagating deactivation: Updated link {parent} <- {child}")
                self._handle_deactivation(child)
