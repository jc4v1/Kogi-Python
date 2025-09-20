from collections import deque
from typing import Any

def pretty_format(states: set[Any]) -> str:
    return "-------------------\n" + f"[\n" + ",\n".join(f"  {str(s)}" for s in states) + "\n]" + "\n-------------------"
 
# pformat = pretty_format # Use our custom formatter by default

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
    
    while queue:
        current_s = queue.popleft()
        for next_s in lts.get_successors(current_s):
            if next_s not in reachable:
                reachable.add(next_s)
                queue.append(next_s)
    return reachable

def backward_bfs(lts, target_states):
    """
    Performs a backward BFS from a set of target states.
    
    Args:
        lts (Lts): The labeled transition system.
        target_states (set): The set of states to start the search from.

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
    failing_states = {}
    success = True
    for q in qualities_Q:
        S_not_q = {s for s in lts.states() if not lts.satisfies_quality(s, q)}
        S_ef_not_q = backward_bfs(lts, S_not_q)
        S_ag_q = lts.states().difference(S_ef_not_q)
        S_implication = S_not_q.union(S_ag_q)
        S_reachable = forward_bfs(lts, lts.initial_state())

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
                if q not in failing_states:
                    failing_states[q] = set()
                failing_states[q].add(s)
                if debug:
                    print(f"failing state stability for quality {q}: {str(s)}")
                success = False
    if not success: 
        return (False, failing_states)
    return (True, {})

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
    return (success, failing_states)
    
    # if S_reachable.issubset(S_disjunction):
    #     return True
    # else:
    #     return False
