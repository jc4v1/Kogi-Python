from typing import Dict, List, Tuple, Set
from typing_extensions import Self
from Semantics.enums import ElementStatus, QualityStatus, LinkType, LinkStatus
from Semantics.transition_system import TransitionSystem, MarkingGm
import itertools
import functools
from Semantics.petri_net import PetriNet

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

class GoalModel:
    def __init__(self):
        self.tasks: Dict[str, ElementStatus] = {}
        self.goals: Dict[str, ElementStatus] = {}
        self.qualities: Dict[str, QualityStatus] = {}
        self.links: List[Tuple[str, str, LinkType, LinkStatus]] = []
        self.requirements: Dict[str, List[List[str]]] = {}
        self.event_mapping: Dict[str, List[List[str]]] = {}
        self.execution_count: Dict[str, int] = {}
        self.last_activated_link: Tuple[str, str, LinkType, LinkStatus] = None
        self.changed_elements: Set[str] = set()
        self.positions: Dict[str,Tuple[float,float]] = {}
        self.istar_positions: Dict[str,Tuple[float,float]] = {}
        self.istar_width: float | None = None
        self.istar_height: float | None = None

    def reset(self):
        for e in self.tasks:
            self.tasks[e] = ElementStatus.UNKNOWN
        for e in self.goals:
            self.goals[e] = ElementStatus.UNKNOWN
        for e in self.qualities:
            self.qualities[e] = QualityStatus.UNKNOWN
        self.links = [(l[0],l[1],l[2],LinkStatus.UNKNOWN) for l in self.links]
        for e in self.execution_count:
            self.execution_count[e] = 0
        self.last_activated_link = None
        self.changed_elements = set()

    def add_task(self, task_id: str):
        self.tasks[task_id] = ElementStatus.UNKNOWN
        self.execution_count[task_id] = 0

    def add_goal(self, goal_id: str):
        self.goals[goal_id] = ElementStatus.UNKNOWN

    def add_quality(self, quality_id: str):
        self.qualities[quality_id] = QualityStatus.UNKNOWN

    def add_link(self, parent: str, child: str, link_type: LinkType):
        self.links.append((parent, child, link_type, LinkStatus.UNKNOWN))

    def add_event_mapping(self, event: str, target):
        if isinstance(target, list):
            self.event_mapping[event] = target
        else:
            self.event_mapping[event] = [[target]]

    def _format_status(self, status):
        if isinstance(status, ElementStatus):
            if status == ElementStatus.UNKNOWN:
                return "(?, ?)"
            elif status == ElementStatus.TRUE_FALSE:
                return "(⊤, ⊥)"
            elif status == ElementStatus.TRUE_TRUE:
                return "(⊤, ⊤)"
        elif isinstance(status, QualityStatus):
            if status == QualityStatus.UNKNOWN:
                return "(?)"
            elif status == QualityStatus.FULFILLED:
                return "(⊤)"
            elif status == QualityStatus.DENIED:
                return "(⊥)"
        return str(status)

    def _get_element_status(self, element: str) -> ElementStatus:
        if element in self.tasks:
            return self.tasks[element]
        elif element in self.goals:
            return self.goals[element]
        return ElementStatus.UNKNOWN

    def _get_element_type(self, element: str) -> str:
        if element in self.qualities:
            return 'Quality'
        elif element in self.goals:
            return 'Goal'
        elif element in self.tasks:
            return 'Task'
        return 'Unknown'

    def _parents(self, element: str) -> Set[str]:
        return {link[0] for link in self.links if link[1] == element}

    def element_exists(self, element: str) -> bool:
        return element in self.tasks or element in self.goals

    def is_leaf(self, element):
        return not any(link[0] == element for link in self.links)

    def get_element_status(self, element: str) -> ElementStatus | None:
        if element in self.tasks:
            return self.tasks[element]
        elif element in self.goals:
            return self.goals[element]
        return None

    def set_element_status(self, element: str, status:ElementStatus) -> None:
        if element in self.tasks:
            old_status = self.tasks[element]
            self.tasks[element] = status
        elif element in self.goals:
            old_status = self.goals[element]
            self.goals[element] = status
        else:
            raise ValueError(f"Element {element} does not exist in tasks or goals.")

    def get_quality_status(self, quality: str) -> QualityStatus | None:
        return self.qualities.get(quality, None)

    def set_quality_status(self, quality: str, status: QualityStatus) -> None:
        old_status = self.qualities[quality]
        self.qualities[quality] = status

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

    # --- Rule methods ---
    def try_pie_rule(self, element : str) -> bool:
        if self.element_exists(element) and self.is_leaf(element) and not self.get_element_status(element) == ElementStatus.TRUE_FALSE:
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

    def try_any_rule(self, element: str) -> bool:
        return (self.try_pie_rule(element) or
                self.try_por_rule(element) or
                self.try_pand_rule(element) or
                self.try_pmake_rule(element) or
                self.try_pbreak_rule(element) or
                self.try_bpfulfill_rule(element) or
                self.try_bpdeny_rule(element))

    # --- Firing and event processing ---
    def fire_element(self,element: str) -> None:
        self.changed_elements.clear()
        self.fire_elements({element})

    def fire_elements(self, elements: Set[str]) -> None:
        for e in elements:
            if self.try_any_rule(e):
                self.changed_elements.add(e)
                self.fire_elements(self._parents(e))

    def process_event(self, event: str) -> None:
        for target_set in self.event_mapping[event]:
            for element in target_set:
                self.fire_element(element)

    # --- Marking and transition system methods ---
    def get_markings(self) -> dict[str, ElementStatus | QualityStatus]:
        return {**self.tasks, **self.goals, **self.qualities}

    def set_markings(self, markings: Dict[str, ElementStatus | QualityStatus]) -> None:
        for element, status in markings.items():
            if element in self.tasks:
                self.tasks[element] = status
            elif element in self.goals:
                self.goals[element] = status
            elif element in self.qualities:
                self.qualities[element] = status

    def copy(self) -> Self:
        import copy
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
                    rule_applied = next_model.try_any_rule(element)
                else:
                    next_model.fire_element(element)
                next_markings = next_model.get_markings()
                next_state = MarkingGm(next_markings)
                if original:
                    if rule_applied:
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

    # --- Statistics and printing ---
    def generate_statistics(self, traces: List[List[str]], results: List[Dict]):
        print("\n" + "="*80)
        print("GOAL MODEL EVALUATION STATISTICS")
        print("="*80)
        total_traces = len(traces)
        all_elements = list(self.tasks.keys()) + list(self.goals.keys()) + list(self.qualities.keys())
        element_stats = {}
        for element in all_elements:
            satisfied_count = 0
            executed_pending_count = 0
            satisfied_traces = []
            executed_pending_traces = []
            for i, trace_result in enumerate(results):
                final_state = trace_result['states'][-1]
                if element in final_state['qualities']:
                    if final_state['qualities'][element] == 'fulfilled':
                        satisfied_count += 1
                        satisfied_traces.append(i + 1)
                elif element in final_state['goals']:
                    if final_state['goals'][element] == 'true_false':
                        satisfied_count += 1
                        satisfied_traces.append(i + 1)
                    elif final_state['goals'][element] == 'true_true':
                        executed_pending_count += 1
                        executed_pending_traces.append(i + 1)
                elif element in final_state['tasks']:
                    if final_state['tasks'][element] == 'true_false':
                        satisfied_count += 1
                        satisfied_traces.append(i + 1)
                    elif final_state['tasks'][element] == 'true_true':
                        executed_pending_count += 1
                        executed_pending_traces.append(i + 1)
            element_stats[element] = {
                'satisfied_count': satisfied_count,
                'executed_pending_count': executed_pending_count,
                'unsatisfied_count': total_traces - satisfied_count - executed_pending_count,
                'satisfied_percentage': (satisfied_count / total_traces) * 100,
                'executed_pending_percentage': (executed_pending_count / total_traces) * 100,
                'satisfied_traces': satisfied_traces,
                'executed_pending_traces': executed_pending_traces
            }
        print(f"\n{'Element':<12} {'Type':<8} {'Satisfied %':<12} {'Exec.Pend %':<12} {'Unsatisfied %':<14} {'Satisfied Traces'}")
        print("-" * 90)
        for element in sorted(element_stats.keys()):
            stats = element_stats[element]
            element_type = self._get_element_type(element)
            unsatisfied_percentage = 100 - stats['satisfied_percentage'] - stats['executed_pending_percentage']
            traces_str = ', '.join(map(str, stats['satisfied_traces'])) if stats['satisfied_traces'] else 'None'
            print(f"{element:<12} {element_type:<8} {stats['satisfied_percentage']:>10.1f}% "
                  f"{stats['executed_pending_percentage']:>10.1f}% {unsatisfied_percentage:>12.1f}% {traces_str}")
        print(f"\n{'='*80}")
        print("QUALITY ANALYSIS")
        print("="*80)
        for quality in self.qualities.keys():
            quality_stats = element_stats[quality]
            print(f"\nQuality {quality}:")
            print(f"  Fulfilled in {quality_stats['satisfied_count']}/{total_traces} traces ({quality_stats['satisfied_percentage']:.1f}%)")
            print(f"  Traces where fulfilled: {', '.join(map(str, quality_stats['satisfied_traces'])) if quality_stats['satisfied_traces'] else 'None'}")
        print(f"\n{'='*80}")
        print("TRACE PATTERN ANALYSIS")
        print("="*80)
        successful_traces = []
        unsuccessful_traces = []
        for i, trace_result in enumerate(results):
            final_state = trace_result['states'][-1]
            if 'Q1' in final_state['qualities'] and final_state['qualities']['Q1'] == 'fulfilled':
                successful_traces.append({'index': i + 1, 'trace': traces[i]})
            else:
                unsuccessful_traces.append({'index': i + 1, 'trace': traces[i]})
        print(f"Successful traces: {len(successful_traces)} ({len(successful_traces)/total_traces*100:.1f}%)")
        for trace_info in successful_traces:
            print(f"  Trace {trace_info['index']}: {' -> '.join(trace_info['trace'])}")
        print(f"\nUnsuccessful traces: {len(unsuccessful_traces)} ({len(unsuccessful_traces)/total_traces*100:.1f}%)")
        for trace_info in unsuccessful_traces:
            print(f"  Trace {trace_info['index']}: {' -> '.join(trace_info['trace'])}")
        print("="*80)
        return element_stats

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
        
    def get_events(self) -> list[str]:
        leaves = [e for e in list(self.goals.keys()) + list(self.tasks.keys()) if e not in {link[0] for link in self.links}]
        return leaves
        
    def generate_all_events_petri_net(self):
        event_names = self.get_events()
        # Minimal Petri net classes for construction
        class Place:
            def __init__(self, name):
                self.name = name

        class Transition:
            def __init__(self, name, label):
                self.name = name
                self.label = label
                self.in_arcs = []
                self.out_arcs = []

        class Arc:
            def __init__(self, source, target):
                self.source = source
                self.target = target

        class Net:
            def __init__(self, places, transitions, arcs):
                self.places = places
                self.transitions = transitions
                self.arcs = arcs

        # Create one place
        place = Place("p1")
        places = [place]

        # Create transitions and arcs
        transitions = []
        arcs = []
        counter = 1
        for event in event_names:
            t = Transition("t"+str(counter),event)
            counter += 1
            # Arc from place to transition
            arc_in = Arc(place, t)
            t.in_arcs.append(arc_in)
            arcs.append(arc_in)
            # Arc from transition to place
            arc_out = Arc(t, place)
            t.out_arcs.append(arc_out)
            arcs.append(arc_out)
            transitions.append(t)

        net = Net(places, transitions, arcs)

        # Positions for drawing (optional, simple layout)
        positions = {
            'places': [(0.68, 0.75, "p1")],
            'transitions': [
                (1.99 + i*0.4, 0.75 + (i%2)*0.60 - 0.3, t.name, t.label) for i, t in enumerate(transitions)
            ]
        }

        # Initial marking: one token in p1
        init = {"p1": 1}
        final = {}

        petri_net = PetriNet(net, init, final, positions)
        self.event_mapping = {}
        for t in net.transitions:
            self.add_event_mapping(t.name, t.label)

        return petri_net