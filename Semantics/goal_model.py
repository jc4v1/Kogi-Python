from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
from typing_extensions import Self
from Semantics.enums import ElementStatus, LinkType
from Semantics.transition_system import TransitionSystem
from Semantics.markings import MarkingGm
import copy
import functools
from Semantics.petri_net import PetriNet

import os

debug = False  # Toggle to True for debug tracing in fire_elements and try_any_rule.
               # To enable from outside:  from Semantics.goal_model import debug; debug = True
               # From CLI:  KOGI_DEBUG=1 pytest ...

def printd(*args, **kwargs):
    if debug or os.environ.get("KOGI_DEBUG"):
        print(*args, **kwargs)

# Decorator to print successful rule applications
def log_rule(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        arg_str = ", ".join([repr(a) for a in args[1:]] + [f"{k}={v!r}" for k, v in kwargs.items()])
        result = func(*args, **kwargs)
        if result:
            print(f"Rule {func.__name__} applied successfully on arguments ({arg_str})")
        return result
    return wrapper


@dataclass(frozen=True)
class Dependency:
    source: str
    target: str
    dependum: str
    dependum_type: str


class _Place:
    def __init__(self, name):
        self.name = name


class _Transition:
    def __init__(self, name, label):
        self.name = name
        self.label = label
        self.in_arcs = []
        self.out_arcs = []


class _Arc:
    def __init__(self, source, target):
        self.source = source
        self.target = target


class _Net:
    def __init__(self, places, transitions, arcs):
        self.places = places
        self.transitions = transitions
        self.arcs = arcs


class GoalModel:
    def __init__(self, kogi: bool = False):
        self.tasks: Dict[str, ElementStatus] = {}
        self.goals: Dict[str, ElementStatus] = {}
        self.qualities: Dict[str, ElementStatus] = {}
        self.links: List[Tuple[str, str, LinkType]] = []
        self.dependencies: List[Dependency] = []
        self.requirements: Dict[str, List[List[str]]] = {}
        self.event_mapping: Dict[str, Set[str]] = {}
        self.execution_count: Dict[str, int] = {}
        self.changed_elements: Set[str] = set()
        self.positions: Dict[str,Tuple[float,float]] = {}
        self.istar_positions: Dict[str,Tuple[float,float]] = {}
        self.istar_width: float | None = None
        self.istar_height: float | None = None
        self.kogi: bool = kogi

    def elements(self) -> Set[str]:
        return set(self.tasks.keys()) | set(self.goals.keys()) | set(self.qualities.keys())

    def reset(self):
        for e in self.tasks:
            self.tasks[e] = ElementStatus.UNKNOWN
        for e in self.goals:
            self.goals[e] = ElementStatus.UNKNOWN
        for e in self.qualities:
            self.qualities[e] = ElementStatus.UNKNOWN
        for e in self.execution_count:
            self.execution_count[e] = 0
        self.changed_elements = set()

    def add_task(self, task_id: str):
        self.tasks[task_id] = ElementStatus.UNKNOWN
        self.execution_count[task_id] = 0

    def add_goal(self, goal_id: str):
        self.goals[goal_id] = ElementStatus.UNKNOWN

    def add_quality(self, quality_id: str):
        self.qualities[quality_id] = ElementStatus.UNKNOWN

    def add_link(self, parent: str, child: str, link_type: LinkType):
        self.links.append((parent, child, link_type))

    def add_dependency(self, source: str, target: str, dependum: str, dependum_type: str):
        self.dependencies.append(
            Dependency(
                source=source,
                target=target,
                dependum=dependum,
                dependum_type=dependum_type,
            )
        )

    def add_event_mapping(self, event: str, target):
        if isinstance(target, (list, set, tuple)):
            self.event_mapping[event] = set(target)
        else:
            self.event_mapping[event] = {target}

    def _format_status(self, status):
        if isinstance(status, ElementStatus):
            if status == ElementStatus.UNKNOWN:
                return "𝕌"
            elif status == ElementStatus.SATISFIED:
                return "𝕊"
            elif status == ElementStatus.PENDING:
                return "ℙ"
            elif status == ElementStatus.DENIED:
                return "𝔻"
        return str(status)

    def _get_node_status(self, element: str) -> ElementStatus:
        if element in self.qualities:
            return self.get_quality_status(element) or ElementStatus.UNKNOWN
        return self.get_element_status(element) or ElementStatus.UNKNOWN

    def _get_element_type(self, element: str) -> str:
        if element in self.qualities:
            return 'Quality'
        elif element in self.goals:
            return 'Goal'
        elif element in self.tasks:
            return 'Task'
        return 'Unknown'

    def goals_alt(self) -> Set[str]:
        return set(self.goals.keys())

    def qualities_alt(self) -> Set[str]:
        return set(self.qualities.keys())

    def leaves(self) -> Set[str]:
        return {eid for eid in self.tasks if self.is_leaf(eid)}

    def initial_marking(self) -> Dict[str, ElementStatus]:
        return {eid: ElementStatus.UNKNOWN for eid in list(self.tasks) + list(self.goals) + list(self.qualities)}

    def compute_target_sets(self, target: str) -> Tuple[Set[str], Set[str], Set[str]]:
        leafs = self.leaves()
        make_set: Set[str] = set()
        break_set: Set[str] = set()

        if target in self.qualities:
            for parent_id, child_id, link_type in self.links:
                if parent_id != target or link_type not in {LinkType.MAKE, LinkType.BREAK}:
                    continue

                contributing_leafs = self._transitive_operational_leafs(child_id, leafs)
                if link_type == LinkType.MAKE:
                    make_set.update(contributing_leafs)
                elif link_type == LinkType.BREAK:
                    break_set.update(contributing_leafs)
        else:
            make_set = self._transitive_operational_leafs(target, leafs)
            for element_id in leafs:
                ancestors = self._transitive_parents(element_id) | {element_id}
                for quality_id in self.qualities_alt():
                    contribution_type = self._eventual_contribution_type(target, quality_id)
                    if contribution_type == LinkType.MAKE and any(self._contribution_value(parent_id, quality_id) == LinkType.BREAK for parent_id in ancestors):
                        break_set.add(element_id)
                    if contribution_type == LinkType.BREAK and any(self._contribution_value(parent_id, quality_id) == LinkType.MAKE for parent_id in ancestors):
                        break_set.add(element_id)

        nr_set = leafs - (make_set | break_set)
        return make_set, break_set, nr_set

    def _transitive_operational_leafs(
        self,
        element: str,
        leafs: Set[str],
        seen: Optional[Set[str]] = None,
    ) -> Set[str]:
        """Return executable leaf tasks that can operationally satisfy element."""
        seen = set() if seen is None else seen
        if element in seen:
            return set()
        seen.add(element)

        result = {element} if element in leafs else set()
        for child_id in self._operational_children(element):
            result |= self._transitive_operational_leafs(child_id, leafs, seen)
        return result

    def _operational_children(self, element: str) -> Set[str]:
        """Return refinement/dependency children that can contribute to element satisfaction."""
        result = {
            link[1]
            for link in self.links
            if link[0] == element and link[2] in {LinkType.AND, LinkType.OR, LinkType.MAKE, LinkType.BREAK}
        }

        for dep in self.dependencies:
            if dep.source == element or dep.dependum == element:
                result.add(dep.target)
        return result

    def _contribution_value(self, src: str, tgt: str) -> Optional[LinkType]:
        """Return MAKE or BREAK if there is a contribution link from src to quality tgt, else None."""
        for link in self.links:
            if link[0] == tgt and link[1] == src and link[2] in {LinkType.MAKE, LinkType.BREAK}:
                return link[2]
        return None

    def _parents(self, element: str) -> Set[str]:
        return {link[0] for link in self.links if link[1] == element and link[2] != LinkType.DEPENDENCY}

    def _children(self, element: str) -> Set[str]:
        """Return all direct children of element via refinement/contribution links and dependencies."""
        result = set()
        for link in self.links:
            if link[0] == element and link[2] in {LinkType.AND, LinkType.OR, LinkType.MAKE, LinkType.BREAK}:
                result.add(link[1])
        for dep in self.dependencies:
            if dep.dependum == element and dep.target is not None:
                result.add(dep.target)
        return result

    def _transitive_children(self, element: str, seen: Optional[Set[str]] = None) -> Set[str]:
        """Return all transitive children of element."""
        seen = set() if seen is None else seen
        result = set()
        for child_id in self._children(element):
            if child_id not in seen:
                seen.add(child_id)
                result.add(child_id)
                result |= self._transitive_children(child_id, seen)
        return result

    def _transitive_parents(self, element: str, seen: Optional[Set[str]] = None) -> Set[str]:
        """Return all transitive parents of element."""
        seen = set() if seen is None else seen
        result = set()
        for parent_id in self._parents(element):
            if parent_id not in seen:
                seen.add(parent_id)
                result.add(parent_id)
                result |= self._transitive_parents(parent_id, seen)
        return result

    def _eventual_contribution_type(self, source_id: str, quality_id: str) -> Optional[LinkType]:
        """Walk up from source_id to find the first contribution link to quality_id."""
        for parent_id in self._transitive_parents(source_id) | {source_id}:
            value = self._contribution_value(parent_id, quality_id)
            if value is not None:
                return value
        return None

    def _is_all_quality_dependency_link(self, parent: str, child: str) -> bool:
        for dep in self.dependencies:
            is_target_to_dependum = dep.target == parent and dep.dependum == child
            is_dependum_to_source = dep.dependum == parent and dep.source == child
            if not (is_target_to_dependum or is_dependum_to_source):
                continue
            if (
                dep.target in self.qualities
                and dep.dependum in self.qualities
                and dep.source in self.qualities
            ):
                return True
        return False

    def element_exists(self, element: str) -> bool:
        return element in self.tasks or element in self.goals

    def is_leaf(self, element):
        in_dependency = any(dep.dependum == element 
                          or dep.source == element 
                          for dep in self.dependencies)
        if in_dependency:
            return False
        return not any(link[0] == element and link[2] != LinkType.DEPENDENCY for link in self.links)

    def get_element_status(self, element: str) -> ElementStatus | None:
        if element in self.tasks:
            return self.tasks[element]
        elif element in self.goals:
            return self.goals[element]
        return None

    def set_element_status(self, element: str, status:ElementStatus) -> None:
        if element in self.tasks:
            self.tasks[element] = status
        elif element in self.goals:
            self.goals[element] = status
        else:
            raise ValueError(f"Element {element} does not exist in tasks or goals.")

    def get_quality_status(self, quality: str) -> ElementStatus | None:
        return self.qualities.get(quality, None)

    def set_quality_status(self, quality: str, status: ElementStatus) -> None:
        if quality not in self.qualities:
            raise ValueError(f"Quality '{quality}' does not exist.")
        self.qualities[quality] = status

    # --- Rule methods ---
    def try_pie_rule(self, element : str) -> Set[str]:
        if self.element_exists(element) and self.is_leaf(element) and not self.get_element_status(element) == ElementStatus.SATISFIED:
            self.set_element_status(element,ElementStatus.SATISFIED)
            return {element}
        return set()

    def try_pand_s_rule(self, element: str) -> Set[str]:
        and_links = [link for link in self.links if link[0] == element and link[2] == LinkType.AND]
        if not and_links:
            return set()
        statuses = [self.get_element_status(link[1]) for link in and_links]
        all_satisfied = all(s == ElementStatus.SATISFIED for s in statuses)
        current = self.get_element_status(element)

        if all_satisfied and current != ElementStatus.SATISFIED:
            self.set_element_status(element, ElementStatus.SATISFIED)
            return {element}
        return set()

    def try_pand_p_rule(self, element: str) -> Set[str]:
        and_links = [link for link in self.links if link[0] == element and link[2] == LinkType.AND]
        if not and_links:
            return set()
        statuses = [self.get_element_status(link[1]) for link in and_links]
        all_satisfied = all(s == ElementStatus.SATISFIED for s in statuses)
        has_pending = any(s == ElementStatus.PENDING for s in statuses)
        current = self.get_element_status(element)

        if all_satisfied or current == ElementStatus.PENDING:
            return set()
        if has_pending and current != ElementStatus.PENDING:
            self.set_element_status(element, ElementStatus.PENDING)
            return {element}
        return set()

    def try_por_s_rule(self, element: str) -> Set[str]:
        or_links = [link for link in self.links if link[0] == element and link[2] == LinkType.OR]
        if not or_links:
            return set()
        any_satisfied = any(self.get_element_status(link[1]) == ElementStatus.SATISFIED for link in or_links)
        current = self.get_element_status(element)

        if any_satisfied and current != ElementStatus.SATISFIED:
            self.set_element_status(element, ElementStatus.SATISFIED)
            return {element}
        return set()

    def try_por_p_rule(self, element: str) -> Set[str]:
        or_links = [link for link in self.links if link[0] == element and link[2] == LinkType.OR]
        if not or_links:
            return set()
        any_satisfied = any(self.get_element_status(link[1]) == ElementStatus.SATISFIED for link in or_links)
        any_pending = any(self.get_element_status(link[1]) == ElementStatus.PENDING for link in or_links)
        current = self.get_element_status(element)

        if any_satisfied and current != ElementStatus.SATISFIED:
            return set()
        if any_pending and current not in (ElementStatus.SATISFIED, ElementStatus.PENDING):
            self.set_element_status(element, ElementStatus.PENDING)
            return {element}
        if current == ElementStatus.SATISFIED and not any_satisfied and any_pending:
            self.set_element_status(element, ElementStatus.PENDING)
            return {element}
        return set()

    def try_pdep_p_rule(self, element: str) -> Set[str]:
        changed: Set[str] = set()
        for dep in self.dependencies:
            if dep.dependum != element:
                continue
            target_status = self._get_node_status(dep.target)
            if target_status not in {ElementStatus.DENIED, ElementStatus.PENDING}:
                continue
            denied_or_unknown = ElementStatus.UNKNOWN if not self.kogi else ElementStatus.DENIED
            dependum_status = denied_or_unknown if dep.dependum in self.qualities else ElementStatus.PENDING
            if self._get_node_status(dep.dependum) != dependum_status:
                if dep.dependum in self.qualities:
                    self.set_quality_status(dep.dependum, dependum_status)
                else:
                    self.set_element_status(dep.dependum, dependum_status)
            if dep.source in self.elements():
                source_status = denied_or_unknown if dep.source in self.qualities else ElementStatus.PENDING
                if self._get_node_status(dep.source) != source_status:
                    if dep.source in self.qualities:
                        self.set_quality_status(dep.source, source_status)
                    else:
                        self.set_element_status(dep.source, source_status)
                    changed.add(dep.source)
        return changed

    def try_pdep_s_rule(self, element: str) -> Set[str]:
        changed: Set[str] = set()
        for dep in self.dependencies:
            if dep.dependum != element:
                continue
            if self._get_node_status(dep.target) != ElementStatus.SATISFIED:
                continue
            if self._get_node_status(dep.dependum) != ElementStatus.SATISFIED:
                if dep.dependum in self.qualities:
                    self.set_quality_status(dep.dependum, ElementStatus.SATISFIED)
                else:
                    self.set_element_status(dep.dependum, ElementStatus.SATISFIED)
            if dep.source in self.elements() and self._get_node_status(dep.source) != ElementStatus.SATISFIED:
                if dep.source in self.qualities:
                    self.set_quality_status(dep.source, ElementStatus.SATISFIED)
                else:
                    self.set_element_status(dep.source, ElementStatus.SATISFIED)
                changed.add(dep.source)
        return changed

    def try_pmake_rule(self, quality: str) -> Set[str]:
        make_links = [link for link in self.links if link[0] == quality and link[2] == LinkType.MAKE]
        if not make_links:
            return set()
        current = self.get_quality_status(quality)
        if (current in (ElementStatus.SATISFIED, ElementStatus.DENIED)):
            return set()
        any_satisfied = any(self.get_element_status(link[1]) == ElementStatus.SATISFIED for link in make_links)
        any_pending = any(self.get_element_status(link[1]) == ElementStatus.PENDING for link in make_links)

        if any_satisfied and current != ElementStatus.SATISFIED:
            self.set_quality_status(quality, ElementStatus.SATISFIED)
            return {quality}
        return set()

    def try_pbreak_rule(self, quality: str) -> Set[str]:
        break_links = [link for link in self.links if link[0] == quality and link[2] == LinkType.BREAK]
        if not break_links:
            return set()
        current = self.get_quality_status(quality)
        if (current in (ElementStatus.SATISFIED, ElementStatus.DENIED)):
            return set()
        any_satisfied = any(self.get_element_status(link[1]) == ElementStatus.SATISFIED for link in break_links)
        any_pending = any(self.get_element_status(link[1]) == ElementStatus.PENDING for link in break_links)

        if any_satisfied and current != ElementStatus.DENIED:
            self.set_quality_status(quality, ElementStatus.DENIED)
            return {quality}
        if current == ElementStatus.DENIED and not any_satisfied and any_pending:
            self.set_quality_status(quality, ElementStatus.UNKNOWN)
            return {quality}
        if any_pending and current not in (ElementStatus.SATISFIED, ElementStatus.DENIED):
            self.set_quality_status(quality, ElementStatus.UNKNOWN)
            return {quality}
        return set()

    def try_pquality_p_rule(self, quality: str) -> Set[str]:
        children = [link[1] for link in self.links if link[0] == quality and link[2] in (LinkType.MAKE, LinkType.BREAK)]
        if not children:
            return set()
        if self.get_quality_status(quality) == ElementStatus.PENDING:
            return set()
        if (all(self.get_element_status(c) in (ElementStatus.PENDING, ElementStatus.UNKNOWN) for c in children) and
           any(self.get_element_status(c) == ElementStatus.PENDING for c in children)): 
            self.set_quality_status(quality, ElementStatus.UNKNOWN)
            return {quality}
        return set()

    def try_bpfulfill_rule(self, quality: str) -> Set[str]:
        make_links = [link for link in self.links if link[0] == quality and link[2] == LinkType.MAKE]
        if (any(self.get_element_status(link[1]) == ElementStatus.SATISFIED for link in make_links)
            and self.get_quality_status(quality) == ElementStatus.DENIED):
            self.set_quality_status(quality,ElementStatus.SATISFIED)
            changed: Set[str] = {quality}
            break_elements = [link[1] for link in self.links if link[0] == quality
                              and link[2] == LinkType.BREAK
                              and self.get_element_status(link[1]) == ElementStatus.SATISFIED]
            back_changed = self._back_propagate(break_elements)
            if not self.kogi:
                changed |= back_changed
            return changed
        return set()

    def try_bpdeny_rule(self, quality: str) -> Set[str]:
        break_links = [link for link in self.links if link[0] == quality and link[2] == LinkType.BREAK]
        if (any(self.get_element_status(link[1]) == ElementStatus.SATISFIED for link in break_links)
            and self.get_quality_status(quality) == ElementStatus.SATISFIED):
            self.set_quality_status(quality,ElementStatus.DENIED)
            changed: Set[str] = {quality}
            make_elements = [link[1] for link in self.links if link[0] == quality
                             and link[2] == LinkType.MAKE
                             and self.get_element_status(link[1]) == ElementStatus.SATISFIED]
            back_changed = self._back_propagate(make_elements)
            if not self.kogi:
                changed |= back_changed
            return changed
        return set()

    def _back_propagate(self, elements: List[str]) -> Set[str]:
        """Back-propagate denied status from satisfied elements through their refinements and dependencies."""
        def true_false_refinements(element: str, visited: Set[str]) -> Set[str]:
            result = {element}
            if element in visited:
                return result
            visited.add(element)
            refinements = [link[1] for link in self.links if link[0] == element and link[2] != LinkType.DEPENDENCY]
            result.update(refinements)
            for e in refinements:
                result.update(true_false_refinements(e, visited))
            for dep in self.dependencies:
                if dep.source == element:
                    result.add(dep.dependum)
                    result.add(dep.target)
                    result.update(true_false_refinements(dep.dependum, visited))
                    result.update(true_false_refinements(dep.target, visited))
            return result

        changed: Set[str] = set()
        for elem in elements:
            affected = true_false_refinements(elem, set())
            for e in affected:
                if e in self.qualities:
                    if self.get_quality_status(e) == ElementStatus.SATISFIED:
                        self.set_quality_status(e, ElementStatus.UNKNOWN)
                        changed.add(e)
                else:
                    if self.get_element_status(e) == ElementStatus.SATISFIED:
                        self.set_element_status(e, ElementStatus.PENDING)
                        changed.add(e)
        return changed

    def try_any_rule(self, element: str) -> Tuple[Set[str], Optional[str]]:
        printd(f"  [try_any_rule] checking '{element}' status={self.get_element_status(element) if element in self.tasks or element in self.goals else self.get_quality_status(element)}")
        rules = (self.try_pdep_p_rule, self.try_pdep_s_rule, self.try_pie_rule,
                  self.try_por_p_rule, self.try_por_s_rule,
                  self.try_pand_p_rule, self.try_pand_s_rule, self.try_pmake_rule, self.try_pbreak_rule,
                  self.try_pquality_p_rule,
                  self.try_bpfulfill_rule, self.try_bpdeny_rule)
        if self.kogi:
            rules = [r for r in rules if not r.__name__.endswith('_p_rule')]
        for rule in rules:
            result = rule(element)
            if result:
                rn = rule.__name__
                printd(f"  [try_any_rule] -> '{element}' matched rule '{rn}', changed={result}")
                return result, rn
        printd(f"  [try_any_rule] -> '{element}' no rule matched")
        return set(), None

    # --- Firing and event processing ---
    def fire_element(self, element: str) -> None:
        self.changed_elements.clear()
        self.fire_elements({element})

    def _parents_of(self, elements: Set[str]) -> Set[str]:
        parent_set: Set[str] = set()
        for c in elements:
            parent_set.update(self._parents(c))
            for dep in self.dependencies:
                if dep.target == c:
                    parent_set.add(dep.dependum)
        return parent_set

    def fire_elements(self, elements: Set[str]) -> None:
        printd(f"\n[fire_elements] called with: {elements}")
        for e in elements:
            changed, rule_name = self.try_any_rule(e)
            if changed:
                printd(f"[fire_elements] '{e}' changed -> {changed} (rule={rule_name})")
                self.changed_elements.update(changed)
                parent_set = self._parents_of(changed)
                printd(f"[fire_elements] parent_set={parent_set}")
                self.fire_elements(parent_set)
            else:
                printd(f"[fire_elements] '{e}' -> no rule applied")

    def process_event(self, event: str) -> None:
        for element in sorted(self.event_mapping.get(event, [])):
            self.fire_element(element)

    def process_only_one_element(self, element: str) -> Tuple[Set[str], Optional[str]]:
        """Fire a single element without propagating changes to parents."""
        self.changed_elements.clear()
        changed, rule_name = self.try_any_rule(element)
        if changed:
            self.changed_elements.update(changed)
        return changed, rule_name
    
    # --- Marking and transition system methods ---
    def get_markings(self) -> dict[str, ElementStatus]:
        return {**self.tasks, **self.goals, **self.qualities}

    def set_markings(self, markings: Dict[str, ElementStatus]) -> None:
        for element, status in markings.items():
            if element in self.tasks:
                self.tasks[element] = status
            elif element in self.goals:
                self.goals[element] = status
            elif element in self.qualities:
                self.qualities[element] = status

    def copy(self) -> Self:
        return copy.deepcopy(self)

    def _get_elements(self, original:bool) -> set[str]:
        if original:
            return set(self.tasks.keys()) | set(self.goals.keys()) | set(self.qualities.keys())
        else:
            return set(self.tasks.keys()) | set(self.goals.keys())

    def as_transition_system(self, original: bool = False) -> TransitionSystem[MarkingGm]:
        from collections import deque
        initial_markings = self.get_markings()
        initial_state = MarkingGm(initial_markings)
        elements = self._get_elements(original)
        visited = set()
        transitions: dict[MarkingGm, dict[str, set[MarkingGm]]] = {}
        queue = deque([initial_state])
        while queue:
            current_state = queue.popleft()
            if current_state in visited:
                continue
            visited.add(current_state)
            transitions[current_state] = {}
            for element in elements:
                next_model = self.copy()
                next_model.set_markings(current_state._markings)
                if original:
                    changed, _rule_name = next_model.try_any_rule(element)
                else:
                    next_model.fire_element(element)
                next_markings = next_model.get_markings()
                next_state = MarkingGm(next_markings)
                if original:
                    if changed:
                        transitions[current_state].setdefault(element, set()).add(next_state)
                        if next_state not in visited:
                            queue.append(next_state)
                else:
                    transitions[current_state].setdefault(element, set()).add(next_state)
                    if next_state not in visited:
                        queue.append(next_state)
        return TransitionSystem(
            states=visited,
            transitions=transitions,
            initial_state=initial_state
        )

    def print_final_status(self):
        print("\n" + "="*50)
        print("FINAL STATUS OF ALL ELEMENTS")
        print("="*50)

    def print_markings(self):
        print("\nCurrent Markings:")
        print("Tasks:")
        for task_id, status in self.tasks.items():
            print(f"  {task_id}: {self._format_status(status)}")
        print("Goals:")
        for goal_id, status in self.goals.items():
            print(f"  {goal_id}: {self._format_status(status)}")
        print("Qualities:")
        for quality_id, status in self.qualities.items():
            print(f"  {quality_id}: {self._format_status(status)}")
        print("-" * 50)
        
    def all_events(self) -> list[str]:
        return self.goals_and_tasks()
    
    def goals_and_tasks(self) -> list[str]:
        return list(self.goals.keys()) + list(self.tasks.keys())
    
    def get_events(self) -> list[str]:
        return list(self.leaves())

    @staticmethod
    def _canonical_element_key(value: str) -> str:
        import re
        value = re.sub(r'\s+\([A-Z]\)\s*$', '', value.strip())
        return re.sub(r'\s+', ' ', value).casefold()

    def canonicalize_activity_mapping(
        self,
        activity_mapping: Dict[str, Set[str]],
    ) -> Dict[str, Set[str]]:
        elements = self.elements()
        by_key: Dict[str, Set[str]] = {}
        for element in elements:
            by_key.setdefault(self._canonical_element_key(element), set()).add(element)

        canonical_mapping: Dict[str, Set[str]] = {}
        for activity, mapped_elements in activity_mapping.items():
            resolved_elements: Set[str] = set()
            for element in mapped_elements:
                if element in elements:
                    resolved_elements.add(element)
                    continue
                matches = by_key.get(self._canonical_element_key(element), set())
                resolved_elements.add(next(iter(matches)) if len(matches) == 1 else element)
            canonical_mapping[activity] = resolved_elements
        return canonical_mapping
        
    def _build_petri_net(self, event_names):
        place = _Place("p1")
        places = [place]
        transitions = []
        arcs = []
        for event in event_names:
            t = _Transition(event, event)
            arc_in = _Arc(place, t)
            t.in_arcs.append(arc_in)
            arcs.append(arc_in)
            arc_out = _Arc(t, place)
            t.out_arcs.append(arc_out)
            arcs.append(arc_out)
            transitions.append(t)
        net = _Net(places, transitions, arcs)
        positions = {
            'places': [(0.68, 0.75, "p1")],
            'transitions': [
                (1.99 + i*0.4, 0.75 + (i%2)*0.60 - 0.3, t.name, t.label) for i, t in enumerate(transitions)
            ]
        }
        init = {"p1": 1}
        final = {}
        petri_net = PetriNet(net, init, final, positions)
        self.event_mapping = {}
        for t in net.transitions:
            self.add_event_mapping(t.name, t.name)
        return petri_net

    def generate_all_events_petri_net(self):
        return self._build_petri_net(self.get_events())

    def generate_all_events_petri_net_simple(self):
        return self._build_petri_net(list(self.elements()))
