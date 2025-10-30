from src.parser import PetriNet
import pulp
import time
"""
    Task 4 & 5: Deadlock Detection and Optimization using ILP + BDD
"""

def find_deadlock(net: PetriNet, Reachable_bdd, P_vars):

    print("\n--- Starting Task 4: Deadlock Detection (ILP + BDD) ---")
    start_time = time.time()

    if Reachable_bdd is None or P_vars is None:
        print("Error: BDD not provided. Run symbolic analysis first.")
        return None

    # --- 1. Setup ILP Problem ---
    prob = pulp.LpProblem("DeadlockFinder", pulp.LpMinimize) # Objective is a dummy
    
    place_ids = net.place_ids
    n = len(place_ids)
    M_vars = {pid: pulp.LpVariable(pid, cat='Binary') for pid in place_ids}
    
    # --- 2. Add Dead Marking Constraints ---
    # A marking is dead if *every* transition is *disabled*.
    # A transition 't' is disabled if it's not enabled.
    # Enabled(t) = AND(p in pre(t)) M_p = 1
    # Disabled(t) = NOT(Enabled(t)) = OR(p in pre(t)) M_p = 0
    # In ILP: sum(M_p for p in pre(t)) <= |pre(t)| - 1
    
    deadlock_constraints_added = 0
    for t_id, trans in net.transitions.items():
        if not trans['pre']: continue # Skip transitions with no inputs
        
        pre_place_sum = pulp.lpSum(M_vars[pid] for pid in trans['pre'])
        prob += pre_place_sum <= len(trans['pre']) - 1
        deadlock_constraints_added += 1
        
    if deadlock_constraints_added == 0:
        print("Warning: No transitions have preconditions. No dead marking possible.")
        return None

    # --- 3. Add Reachable BDD Constraints (CNF) ---
    print("Converting BDD to CNF for ILP... (this may take a moment)")
    Reachable_cnf = Reachable_bdd.to_cnf()
    print(f"BDD converted to {len(Reachable_cnf.clauses)} CNF clauses.")
    
    var_to_pid = {P_vars[i].name: place_ids[i] for i in range(n)}
    
    for clause in Reachable_cnf.clauses:
        # A clause is like (p1 | ~p2 | p3)
        # ILP constraint: M_p1 + (1 - M_p2) + M_p3 >= 1
        lp_clause = []
        for literal in clause:
            var, is_positive = literal
            pid = var_to_pid[var.name]
            
            if is_positive:
                lp_clause.append(M_vars[pid])
            else:
                lp_clause.append(1 - M_vars[pid])
                
        prob += pulp.lpSum(lp_clause) >= 1
        
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

def optimize_on_reachable(net: PetriNet, Reachable_bdd, P_vars, C_weights: dict):
    
    print("\n--- Starting Task 5: Optimization (ILP + BDD) ---")
    start_time = time.time()
    
    if Reachable_bdd is None or P_vars is None:
        print("Error: BDD not provided. Run symbolic analysis first.")
        return None, None

    # --- 1. Setup ILP Problem ---
    prob = pulp.LpProblem("OptimizeMarking", pulp.LpMaximize)
    
    place_ids = net.place_ids
    n = len(place_ids)
    M_vars = {pid: pulp.LpVariable(pid, cat='Binary') for pid in place_ids}
    
    # --- 2. Set Objective Function ---
    objective = pulp.lpSum(C_weights.get(pid, 0) * M_vars[pid] for pid in place_ids)
    prob += objective
    
    # --- 3. Add Reachable BDD Constraints (CNF) ---
    print("Converting BDD to CNF for ILP... (this may take a moment)")
    Reachable_cnf = Reachable_bdd.to_cnf()
    print(f"BDD converted to {len(Reachable_cnf.clauses)} CNF clauses.")
    
    var_to_pid = {P_vars[i].name: place_ids[i] for i in range(n)}
    
    for clause in Reachable_cnf.clauses:
        lp_clause = []
        for literal in clause:
            var, is_positive = literal
            pid = var_to_pid[var.name]
            if is_positive: lp_clause.append(M_vars[pid])
            else: lp_clause.append(1 - M_vars[pid])
        prob += pulp.lpSum(lp_clause) >= 1
        
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