from collections import deque
from NewSemantics.transition_system import TransitionSystem
from pprint import pformat

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

def check_stable_system(lts, qualities_Q):
    """
    Checks the CTL formula: for all q in Q, s0 |= AG(q => AG q).
    
    Args:
        lts (Lts): The labeled transition system.
        qualities_Q (set): A set of quality names to check.

    Returns:
        bool: True if the formula holds, False otherwise.
    """
    for q in qualities_Q:
        S_not_q = {s for s in lts.states() if not lts.satisfies_quality(s, q)}
        S_ef_not_q = backward_bfs(lts, S_not_q)
        S_ag_q = lts.states().difference(S_ef_not_q)
        S_implication = S_not_q.union(S_ag_q)
        S_reachable = forward_bfs(lts, lts.initial_state())

        if not S_reachable.issubset(S_implication):
            return False

    return True

def check_weak_compliance(lts, qualities_Q):
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
    
    # Step 1: Find states satisfying EF(Q)
    # The set S_Q should contain all states that have *any* quality from qualities_Q.
    S_Q = {s for s in lts.states() for q in qualities_Q if lts.satisfies_quality(s, q)}
    print("--------------------")
    print(f"S_Q = {pformat(S_Q)}")
    print("--------------------")
    S_ef_q = backward_bfs(lts, S_Q)
    print("--------------------")
    print(f"S_ef_q = {pformat(S_ef_q)}")
    print("--------------------")


    # Step 2: Find states satisfying AX(false)
    S_ax_false = {s for s in lts.states() if not lts.get_successors(s)}
    print("--------------------")
    print(f"S_ax_false = {pformat(S_ax_false)}")
    print("--------------------")

    # Step 3: Find states satisfying the conjunction (AX(false) and Q)
    # A state is in this set if it's deadlocked AND has a quality from qualities_Q.
    S_ax_false_and_q = S_ax_false.intersection(S_Q)
    print("--------------------")
    print(f"S_ax_false_and_q = {pformat(S_ax_false_and_q)}")
    print("--------------------")


    # Step 4: Find states satisfying the disjunction ((EF(Q)) or (AX(false) and Q))
    S_disjunction = S_ef_q.union(S_ax_false_and_q)
    print("--------------------")
    print(f"S_disjunction = {pformat(S_disjunction)}")
    print("--------------------")
    

    # Step 5: Find all states reachable from the initial state
    S_reachable = forward_bfs(lts, lts.initial_state())
    print("--------------------")
    print(f"S_reachable = {pformat(S_reachable)}")
    print("--------------------")

    # Step 6: Check if the property holds for all reachable states
    for s in S_reachable:
        if s not in S_disjunction:
            print(f"failing state {s}")
            return False
    return True
    # if S_reachable.issubset(S_disjunction):
    #     return True
    # else:
    #     return False
