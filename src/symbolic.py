from src.parser import PetriNet
from pyeda.inter import exprvars, expr, And, Or
import time

"""
    Task 3: Computes all reachable markings using BDDs.
"""
def get_symbolic_reachable(net: PetriNet):

    print("\n--- Starting Task 3: Symbolic Reachability (BDD) ---")
    start_time = time.time()

    place_ids = net.place_ids # Get consistent, sorted list
    n = len(place_ids)
    
    if n == 0:
        print("Error: No places found in Petri net.")
        return None, None
        
    # --- 1. Create BDD variables ---
    P_vars = exprvars('p', n)
    P_prime_vars = exprvars('pp', n)
    
    P_map = {pid: P_vars[i] for i, pid in enumerate(place_ids)}
    P_prime_map = {pid: P_prime_vars[i] for i, pid in enumerate(place_ids)}
    
    # --- 2. Create Initial Marking BDD ---
    m0_literals = []
    for pid in place_ids:
        if pid in net.initial_marking:
            m0_literals.append(P_map[pid])
        else:
            m0_literals.append(~P_map[pid])
    
    Reachable_bdd = And(*m0_literals)
    
    # --- 3. Create Transition Relation BDD T(P, P') ---
    T_bdds = []
    for t_id, trans in net.transitions.items():
        
        pre_bdd = And(*(P_map[pid] for pid in trans['pre']))
        post_bdd = And(*(P_prime_map[pid] for pid in trans['post']))
        
        frame_bdds = []
        for pid in place_ids:
            # Place is NOT in pre-set (doesn't get consumed)
            # AND Place is NOT in post-set (doesn't get produced)
            if pid not in trans['pre'] and pid not in trans['post']:
                # Its state must be equivalent
                frame_bdds.append(P_map[pid].equivalent(P_prime_map[pid])) 
            
            # Place IS in pre-set (consumed)
            # AND Place is NOT in post-set (not produced)
            elif pid in trans['pre'] and pid not in trans['post']:
                # It must become empty
                frame_bdds.append(~P_prime_map[pid])
            
            # Place is NOT in pre-set (not consumed)
            # AND Place IS in post-set (produced)
            elif pid not in trans['pre'] and pid in trans['post']:
                # It must become full (this is already in post_bdd)
                pass # Handled by post_bdd
                
            # Place IS in pre-set (consumed)
            # AND Place IS in post-set (produced)
            elif pid in trans['pre'] and pid in trans['post']:
                # It must become full (this is already in post_bdd)
                pass # Handled by post_bdd

        T_t = And(pre_bdd, post_bdd, *frame_bdds)
        T_bdds.append(T_t)
        
    T = Or(*T_bdds)
    
    # --- 4. Perform Symbolic Image Computation ---
    P_prime_to_P = {P_prime_vars[i]: P_vars[i] for i in range(n)}
    
    Frontier_bdd = Reachable_bdd
    while not Frontier_bdd.is_zero():
        # Img(P') = exists P: (Frontier(P) & T(P, P'))
        
        # MODIFIED: Unpack P_vars with a '*'
        Img_P_prime = (Frontier_bdd & T).smoothing(*P_vars)
        
        # Img(P) = Img(P') [ P' -> P ]
        Img_P = Img_P_prime.compose(P_prime_to_P)
        
        New_bdd = Img_P & ~Reachable_bdd
        
        Reachable_bdd = Reachable_bdd | New_bdd
        Frontier_bdd = New_bdd
        
    end_time = time.time()
    
    # --- 5. Report Results ---
    # .satisfy_count() gives the number of satisfying assignments.
    # Since our BDD is over all n P_vars, this is the number of markings.
    num_markings = Reachable_bdd.satisfy_count()
    
    print(f"Symbolically found {num_markings} reachable markings.")
    print(f"Symbolic computation took {end_time - start_time:.6f} seconds.")
    
    return Reachable_bdd, P_vars