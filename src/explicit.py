from src.parser import PetriNet
import time
"""
    Task 2: Computes all reachable markings using a Breadth-First Search (BFS).
"""
def get_explicit_reachable(net: PetriNet):
    
    print("\n--- Starting Task 2: Explicit Reachability (BFS) ---")
    start_time = time.time()

    # Use frozenset for markings, as they are immutable and hashable
    initial_marking = frozenset(net.initial_marking)
    
    queue = [initial_marking]
    visited = {initial_marking}
    
    while queue:
        current_marking = queue.pop(0)
        
        enabled_transitions = []
        for t_id, trans in net.transitions.items():
            # A transition is enabled if all its preconditions are met
            if trans['pre'].issubset(current_marking):
                enabled_transitions.append(trans)
        
        for trans in enabled_transitions:
            # Fire the transition
            # 1. Remove tokens from pre-places
            # 2. Add tokens to post-places
            next_marking_set = (current_marking - trans['pre']) | trans['post']
            next_marking = frozenset(next_marking_set)
            
            if next_marking not in visited:
                visited.add(next_marking)
                queue.append(next_marking)
    
    end_time = time.time()
    print(f"Explicitly found {len(visited)} reachable markings.")
    print(f"Explicit computation took {end_time - start_time:.6f} seconds.")
    return visited