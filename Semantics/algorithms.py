from collections import deque
from typing import Any


class CheckResult:
    """A simple result monad for checks.

    Represents either success (ok=True) or failure (ok=False) with
    an optional list of counter-example traces (each trace is a tuple
    of actions).
    """
    def __init__(self, ok: bool, counter_examples: list[tuple[Any, ...]] | None = None):
        self.ok = ok
        self.counter_examples = counter_examples or []

    @classmethod
    def success(cls):
        return cls(True, [])

    @classmethod
    def failure(cls, traces: list[tuple[Any, ...]] | set[tuple[Any, ...]]):
        # ensure a list of tuples (sorted shortest-first)
        traces_list = list(traces)
        traces_list = [tuple(t) for t in traces_list]
        traces_list.sort(key=len)
        return cls(False, traces_list)

    def is_ok(self) -> bool:
        return self.ok

    def is_err(self) -> bool:
        return not self.ok

    def map(self, fn):
        if self.ok:
            return CheckResult.success()
        return self

    def __repr__(self) -> str:  # pragma: no cover - small helper
        return f"CheckResult(ok={self.ok}, counter_examples={self.counter_examples})"
    
    def __str__(self) -> str:  # pragma: no cover - small helper
        return self.print_counter_examples()

    def print_counter_examples(self) -> str:
        """Return a human-readable string describing the result and any counter-examples."""
        lines: list[str] = []
        if self.ok:
            lines.append("True")
        else:
            lines.append("False")
            lines.append(f"Counter-examples ({len(self.counter_examples)}):")
            for trace in self.counter_examples:
                lines.append(f"  {trace}")
        return "\n".join(lines)

def pretty_format(states: set[Any]) -> str:
    return "-------------------\n" + f"[\n" + ",\n".join(f"  {str(s)}" for s in states) + "\n]" + "\n-------------------"
 
# pformat = pretty_format # Use our custom formatter by default


def reconstruct_trace_from_parent_map(parent_map: dict[Any, tuple[Any, Any]], state: Any) -> list[Any]:
    """Reconstruct an action trace from a parent map mapping node -> (prev_node, action).

    Returns list of actions from the initial node to `state`.
    """
    actions_rev: list[Any] = []
    cur = state
    while True:
        prev = parent_map.get(cur)
        if not prev:
            break
        pstate, pact = prev
        if pstate is None:
            break
        actions_rev.append(pact)
        cur = pstate
    actions_rev.reverse()
    return actions_rev

def forward_bfs(lts, start_state):
    """
    Performs a forward BFS from a single start state.
    
    Args:
        lts (Lts): The labeled transition system.
        start_state: The state to start the search from.

    Returns:
        set: A set of all states reachable from the start state.
    """
    queue = deque([start_state])
    reachable = {start_state}

    # parent_map: state -> (previous_state, action) to reconstruct a
    # single (shortest) trace per state. We record only the first
    # discovered predecessor which yields BFS shortest-path traces and
    # avoids combinatorial explosion of all possible traces.
    parent_map: dict[Any, tuple[Any, Any]] = {start_state: (None, None)}

    while queue:
        current_s = queue.popleft()
        actions = lts.actions()
        
        for action in actions:
            successors = lts.get_successors(current_s, action)
            for next_s in successors:
                if next_s not in reachable:
                    parent_map[next_s] = (current_s, action)
                    reachable.add(next_s)
                    queue.append(next_s)

    # Reconstruct a single shortest trace for each reachable state and
    # attach it as a list-of-actions under the attribute `trace` where possible.
    for s in reachable:
        trace = reconstruct_trace_from_parent_map(parent_map, s)
        try:
            # attach a single shortest trace as `trace` (list of actions)
            s.trace = trace
        except Exception:
            # Skip states that cannot have attributes set
            pass

    return reachable

def backward_bfs(lts, target_states):
    """
    Performs a backward BFS from a set of target states.
    
    Args:
        lts (Lts): The labeled transition system.
                    return CheckResult.failure(counterexamples)
    Returns:
        set: A set of all states that can reach any of the target states.
    """
    queue = deque(target_states)
    reachable = set(target_states)
    
    while queue:
        current_s = queue.popleft()
        for prev_s in lts.get_predecessors(current_s):
            if prev_s not in reachable:
                reachable.add(prev_s)
                queue.append(prev_s)
    return reachable

def check_stable_system(lts, qualities_Q, debug=False):
    """
    Checks the CTL formula: for all q in Q, s0 |= AG(q => AG q).
    
    Args:
        lts (Lts): The labeled transition system.
        qualities_Q (set): A set of quality names to check.

    Returns:
        bool: True if the formula holds, False otherwise.
    """
    failing_states = set()
    counterexamples: set[Any] = set()
    success = True

    # Helper: find an action sequence from `start` to any state in `targets`.
    def _find_action_path(start: Any, targets: set[Any]) -> list[Any]:
        if start in targets:
            return []
        q = deque([start])
        visited = {start}
        parent: dict[Any, tuple[Any, Any]] = {start: (None, None)}
        while q:
            cur = q.popleft()
            # prefer enabled actions when available
            try:
                actions = list(lts.get_enabled_actions(cur))
            except Exception:
                actions = list(lts.actions())
            for action in actions:
                for nxt in lts.get_successors(cur, action):
                    if nxt in visited:
                        continue
                    parent[nxt] = (cur, action)
                    if nxt in targets:
                        # reconstruct using shared helper
                        return reconstruct_trace_from_parent_map(parent, nxt)
                    visited.add(nxt)
                    q.append(nxt)
        return []

    # Compute reachable states once (also populates `trace` on states via forward_bfs)
    S_reachable = forward_bfs(lts, lts.initial_state())

    for q in qualities_Q:
        S_not_q = {s for s in lts.states() if not lts.satisfies_quality(s, q)}
        S_ef_not_q = backward_bfs(lts, S_not_q)
        S_ag_q = lts.states().difference(S_ef_not_q)
        S_implication = S_not_q.union(S_ag_q)

        # use the global `counterexamples` set declared above

        if debug:
            print("=================================")
            print(f"States not satisfying {q}: {pretty_format(S_not_q)}")
            print(f"States satisfying EF(not {q}): {pretty_format(S_ef_not_q)}")
            print(f"States satisfying AG({q}): {pretty_format(S_ag_q)}")
            print(f"States satisfying the implication (not {q} or AG {q}): {pretty_format(S_implication)}")
            print(f"Reachable states from initial state: {pretty_format(S_reachable)}")
            print("=================================")

        for s in S_reachable:
            if s not in S_implication:
                failing_states.add(s)
                if debug:
                    print(f"failing state stability for quality {q}: {str(s)}")
                success = False

                # Build counterexample trace: initial -> ... -> s (from s.trace if available)
                init_trace = []
                if hasattr(s, 'trace') and s.trace:
                    try:
                        init_trace = list(s.trace)
                    except Exception:
                        init_trace = list(s.trace)

                # then s -> ... -> t where t satisfies not q
                suffix = _find_action_path(s, S_not_q)

                full_trace = tuple(init_trace + suffix)
                counterexamples.add(full_trace)

    if not success:
        return CheckResult.failure(counterexamples)
    return CheckResult.success()

def check_weak_compliance(lts, qualities_Q, debug=False):
    """
    Checks the CTL formula: AG((EF(Q)) or (AX(false) and Q)).

    Args:
        lts (Lts): The labeled transition system.
        qualities_Q (set): A set of quality names to check.

    Returns:
        bool: True if the formula holds, False otherwise.
    """
    # This formula holds for all q in qualities_Q, so we only need to check one.
    # We will assume Q is a single quality, or the formula is for the combined set.
    # The structure of your request implies the latter.
    
    failing_states: set[Any] = set()
    # Step 1: Find states satisfying EF(Q)
    # The set S_Q should contain all states that have *any* quality from qualities_Q.
    S_Q = {s for s in lts.states() if all(lts.satisfies_quality(s, q) for q in qualities_Q)}
    # S_Q = {s for s in lts.states() for q in qualities_Q if lts.satisfies_quality(s, q)}
    S_ef_q = backward_bfs(lts, S_Q)


    # Step 2: Find states satisfying AX(false)
    S_ax_false = {s for s in lts.states() if not lts.get_successors(s)}

    # Step 3: Find states satisfying the conjunction (AX(false) and Q)
    # A state is in this set if it's deadlocked AND has a quality from qualities_Q.
    S_ax_false_and_q = S_ax_false.intersection(S_Q)

    # Step 4: Find states satisfying the disjunction ((EF(Q)) or (AX(false) and Q))
    S_disjunction = S_ef_q.union(S_ax_false_and_q)
    
    # Step 5: Find all states reachable from the initial state
    S_reachable = forward_bfs(lts, lts.initial_state())

    if debug:
        print("=================================")
        print(f"States satisfying Q: {pretty_format(S_Q)}")
        print(f"States satisfying EF(Q): {pretty_format(S_ef_q)}")
        print(f"States satisfying AX(false): {pretty_format(S_ax_false)}")
        print(f"States satisfying AX(false) and Q: {pretty_format(S_ax_false_and_q)}")
        print(f"States satisfying the disjunction: {pretty_format(S_disjunction)}")
        print(f"Reachable states from initial state: {pretty_format(S_reachable)}")
        print("=================================")
    
    # Step 6: Check if the property holds for all reachable states
    success = True
    for s in S_reachable:
        if s not in S_disjunction:
            failing_states.add(s)
            if debug:
                print(f"failing state weak comliance {str(s)}")
            success = False
    # produce set of traces (tuples) as counterexamples
    counterexamples = set()
    for s in failing_states:
        if hasattr(s, 'trace') and s.trace is not None:
            try:
                counterexamples.add(tuple(s.trace))
            except Exception:
                counterexamples.add(tuple(list(s.trace)))
    if not success:
        return CheckResult.failure(counterexamples)
    return CheckResult.success()
    
    # if S_reachable.issubset(S_disjunction):
    #     return True
    # else:
    #     return False
