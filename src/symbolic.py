from src.parser import PetriNet
from dd.autoref import BDD
import time

"""
    Task 3: Symbolic Reachability using real BDDs (dd.autoref)
"""

def get_symbolic_reachable(net: PetriNet):
    print("\n--- Starting Task 3: Symbolic Reachability (BDD) ---")
    start_time = time.time()

    place_ids = net.place_ids
    n = len(place_ids)
    if n == 0:
        print("Error: No places found in Petri net.")
        return None, None

    # --- 1. Initialize BDD manager and variables ---
    bdd = BDD()
    for pid in place_ids:
        bdd.add_var(pid)    # current state p
        bdd.add_var(f" {pid}' ")  # next state p'

    # --- 2. Initial marking ---
    m0 = bdd.true
    for pid in place_ids:
        if pid in net.initial_marking:
            m0 &= bdd.var(pid)
        else:
            m0 &= ~bdd.var(pid)

    Reachable = m0
    Frontier = m0

    # --- 3. Build Transition Relation T(P, P') ---
    T = bdd.false
    for t_id, t in net.transitions.items():
        pre = bdd.true
        post = bdd.true
        frame = bdd.true

        # Preconditions: all pre places must have tokens
        for p in t['pre']:
            pre &= bdd.var(p)

        # Postconditions: all post places will have tokens
        for p in t['post']:
            post &= bdd.var(f"{p}'")

        # Frame conditions: unchanged places keep same value
        for p in place_ids:
            if p not in t['pre'] and p not in t['post']:
                # unaffected -> remain the same
                eq = (~bdd.var(p) & ~bdd.var(f"{p}'")) | (bdd.var(p) & bdd.var(f"{p}'"))
                frame &= eq

            elif p in t['pre'] and p not in t['post']:
                # p is input -> consumed
                frame &= ~bdd.var(f"{p}'")

            elif p not in t['pre'] and p in t['post']:
                # p is output -> produced -> already handled by post
                pass
            
            elif p in t['pre'] and p in t['post']:
                # stays full
                frame &= bdd.var(f"{p}'")

        T_t = pre & post & frame
        T |= T_t

    # --- 4. Symbolic reachability fixpoint iteration ---
    rename_map = {f"{p}'": p for p in place_ids}

    iteration = 0
    while Frontier != bdd.false:
        iteration += 1
        print(f"Iteration {iteration}...")

        # Img(P') = ∃P. (Frontier(P) ∧ T(P,P'))
        Img_P_prime = bdd.exist(place_ids, Frontier & T)

        # Img(P) = Img(P') with renamed vars
        Img_P = bdd.let(rename_map, Img_P_prime)

        New = Img_P & ~Reachable
        if New == bdd.false:
            break

        Reachable |= New
        Frontier = New

    end_time = time.time()

    # --- 5. Report results ---
    markings = list(bdd.pick_iter(Reachable, care_vars=place_ids))
    num_markings = len(markings)

    print(f"Symbolically found {num_markings} reachable markings.")
    print(f"Symbolic computation took {end_time - start_time:.6f} seconds.")

    return Reachable, [bdd.var(p) for p in place_ids]
