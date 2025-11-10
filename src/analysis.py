from src.parser import PetriNet
from dd.autoref import BDD
import pulp
import time

"""
    Task 4 & 5: Deadlock Detection and Optimization using ILP + BDD (dd version)
"""

# ---------------------------------------------------------------------------
# Helper: Converts the BDD into ILP constraints
# ---------------------------------------------------------------------------
def add_bdd_constraints_to_ilp(prob, bdd_manager, Reachable, M_vars, place_ids):
    """
    Constrains the ILP model `M_vars` to only allow solutions
    that are present in the `Reachable` BDD.
    
    This uses a DNF (Disjunctive Normal Form) approach. The BDD
    is a "disjunction" (OR) of all its satisfying assignments ("cubes").
    We add indicator variables to force the ILP to pick one.
    """
    
    # 1. Get all reachable markings (cubes) from the BDD.
    # Each 'model' is a dict like {'p1': 1, 'p2': 0, ...}
    markings = list(bdd_manager.pick_iter(Reachable, care_vars=place_ids))
    
    if not markings:
        # No reachable states. Add a constraint that is impossible to satisfy.
        prob += (pulp.lpSum(M_vars[pid] for pid in place_ids) <= -1)
        return

    # 2. Create one "indicator" variable for each reachable marking.
    z_vars = [pulp.LpVariable(f"z_{i}", cat='Binary') for i in range(len(markings))]

    # 3. Add constraint: The solver MUST pick exactly ONE marking.
    prob += (pulp.lpSum(z_vars) == 1)

    # 4. Add "Big-M" constraints to link 'z' vars to 'M' vars.
    # For each marking i:
    #   If z_i is 1, then M_vars MUST equal marking i.
    for i, model in enumerate(markings):
        for pid in place_ids:
            if model.get(pid, 0) == 1:
                # If we pick z_i, M_vars[pid] must be 1.
                # M_vars[pid] >= z_i
                prob += (M_vars[pid] >= z_vars[i])
            else:
                # If we pick z_i, M_vars[pid] must be 0.
                # M_vars[pid] <= 1 - z_i
                prob += (M_vars[pid] <= 1 - z_vars[i])

# ---------------------------------------------------------------------------
# Task 4: Deadlock detection
# ---------------------------------------------------------------------------
def find_deadlock(net: PetriNet, Reachable, P_vars):
    print("\n--- Starting Task 4: Deadlock Detection (ILP + BDD) ---")
    start_time = time.time()

    if Reachable is None or P_vars is None:
        print("Error: BDD not provided. Run symbolic analysis first.")
        return None

    place_ids = net.place_ids
    bdd = P_vars[0].bdd  # Get the BDD manager from a variable

    # --- 1. Setup ILP Problem ---
    prob = pulp.LpProblem("DeadlockFinder", pulp.LpMinimize) # Objective doesn't matter
    M_vars = {pid: pulp.LpVariable(pid, cat='Binary') for pid in place_ids}

    # --- 2. Add Dead Marking Constraints (ILP formulation) ---
    # A marking is dead if *every* transition is *disabled*.
    # Disabled(t) => sum(M_p for p in pre(t)) <= |pre(t)| - 1
    for t_id, trans in net.transitions.items():
        if not trans['pre']: continue # Skip transitions with no inputs
        
        pre_place_sum = pulp.lpSum(M_vars[pid] for pid in trans['pre'])
        prob += (pre_place_sum <= len(trans['pre']) - 1)

    # --- 3. Add BDD Constraints ---
    print("Converting BDD to ILP constraints...")
    add_bdd_constraints_to_ilp(prob, bdd, Reachable, M_vars, place_ids)
    
    # --- 4. Solve the problem ---
    print("Solving ILP...")
    prob.solve(pulp.PULP_CBC_CMD(msg=0)) # Suppress solver output
    end_time = time.time()

    if pulp.LpStatus[prob.status] == 'Optimal':
        print("Result: Reachable deadlock found.")
        deadlock_marking = {pid for pid in place_ids if M_vars[pid].value() == 1}
        print(f"Deadlock marking: {deadlock_marking}")
        print(f"Deadlock analysis took {end_time - start_time:.6f} seconds.")
        return deadlock_marking
    else:
        print("Result: No reachable deadlock found.")
        print(f"Deadlock analysis took {end_time - start_time:.6f} seconds.")
        return None

# ---------------------------------------------------------------------------
# Task 5: Optimization over reachable markings
# ---------------------------------------------------------------------------
def optimize_on_reachable(net: PetriNet, Reachable, P_vars, C_weights: dict):
    print("\n--- Starting Task 5: Optimization (ILP + BDD) ---")
    start_time = time.time()

    if Reachable is None or P_vars is None:
        print("Error: BDD not provided. Run symbolic analysis first.")
        return None, None

    place_ids = net.place_ids
    bdd = P_vars[0].bdd

    # --- 1. Setup ILP Problem ---
    prob = pulp.LpProblem("OptimizeMarking", pulp.LpMaximize)
    M_vars = {pid: pulp.LpVariable(pid, cat='Binary') for pid in place_ids}

    # --- 2. Set Objective Function ---
    objective = pulp.lpSum(C_weights.get(pid, 0) * M_vars[pid] for pid in place_ids)
    prob += objective

    # --- 3. Add BDD Constraints ---
    print("Converting BDD to ILP constraints...")
    add_bdd_constraints_to_ilp(prob, bdd, Reachable, M_vars, place_ids)

    # --- 4. Solve the problem ---
    print("Solving ILP...")
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    end_time = time.time()

    if pulp.LpStatus[prob.status] == 'Optimal':
        print("Result: Optimal reachable marking found.")
        optimal_marking = {pid for pid in place_ids if M_vars[pid].value() == 1}
        obj_value = pulp.value(prob.objective)
        print(f"Optimal marking: {optimal_marking}")
        print(f"Objective value: {obj_value}")
        print(f"Optimization analysis took {end_time - start_time:.6f} seconds.")
        return optimal_marking, obj_value
    else:
        print("Result: No optimal solution found.")
        print(f"Optimization analysis took {end_time - start_time:.6f} seconds.")
        return None, None