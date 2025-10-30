import argparse
import sys
from src.parser import parse_pnml
from src.explicit import get_explicit_reachable
from src.symbolic import get_symbolic_reachable
from src.analysis import find_deadlock, optimize_on_reachable

def main():
    parser = argparse.ArgumentParser(description="Petri Net Analyzer for CO2011")
    parser.add_argument(
        '--file', 
        type=str, 
        required=True, 
        help="Path to the input PNML file."
    )
    parser.add_argument(
        '--task',
        type=str,
        required=True,
        choices=['explicit', 'symbolic', 'deadlock', 'optimize', 'all'],
        help="The task to perform."
    )
    
    args = parser.parse_args()
    
    # --- Task 1: Parsing ---
    # This task is always run first
    net = parse_pnml(args.file)
    if net is None:
        sys.exit(1) # Exit if parsing failed

    # --- Run selected tasks ---
    
    if args.task == 'explicit':
        get_explicit_reachable(net)

    elif args.task == 'symbolic':
        get_symbolic_reachable(net)

    elif args.task == 'deadlock':
        # Task 4 depends on Task 3
        Reachable_bdd, P_vars = get_symbolic_reachable(net)
        if Reachable_bdd:
            find_deadlock(net, Reachable_bdd, P_vars)

    elif args.task == 'optimize':
        # Task 5 depends on Task 3
        # As an example, we'll use a cost function
        # that maximizes the total number of tokens.
        print("Using example cost function: Maximize total tokens.")
        c_weights = {pid: 1 for pid in net.place_ids}
        
        Reachable_bdd, P_vars = get_symbolic_reachable(net)
        if Reachable_bdd:
            optimize_on_reachable(net, Reachable_bdd, P_vars, c_weights)

    elif args.task == 'all':
        # Run all tasks in order
        get_explicit_reachable(net)
        
        Reachable_bdd, P_vars = get_symbolic_reachable(net)
        
        if Reachable_bdd:
            find_deadlock(net, Reachable_bdd, P_vars)
            
            print("\nUsing example cost function: Maximize total tokens.")
            c_weights = {pid: 1 for pid in net.place_ids}
            optimize_on_reachable(net, Reachable_bdd, P_vars, c_weights)

if __name__ == "__main__":
    main()