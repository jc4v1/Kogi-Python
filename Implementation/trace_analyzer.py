from typing import List
from goal_model import GoalModel
from demo_model import create_model
from enums import ElementStatus

def analyze_traces(trazas_unicas: List[List[str]], target_elements: List[str]):
    """
    Analyze each trace using the goal model and check target satisfaction.
    Args:
        trazas_unicas: List of traces, where each trace is a list of events
        target_elements: List of target elements to check (e.g., ['Q1'])
    """
    results = []
    
    # Analyze each trace
    for i, trace in enumerate(trazas_unicas):
        print(f"\nAnalyzing trace {i + 1}:")
        print(f"Events: {' -> '.join(trace)}")
        
        # Create fresh model for each trace (resets all states to UNKNOWN)
        model = create_model()
        
        # Process all events in the trace
        for event in trace:
            model.process_event(event)
        
        # Check target satisfaction after processing all events
        satisfied = True
        for target in target_elements:
            if target in model.qualities:
                satisfied = satisfied and model.qualities[target] == ElementStatus.FULFILLED
            elif target in model.goals:
                satisfied = satisfied and model.goals[target] == ElementStatus.ACHIEVED
            elif target in model.tasks:
                satisfied = satisfied and model.tasks[target] == ElementStatus.ACTIVATED
        
        # Store results
        results.append({
            'trace_number': i + 1,
            'trace': trace,
            'satisfies_targets': satisfied
        })
        
        # Print result for this trace
        print(f"\nTrace {i + 1} Results:")
        print(f"Events: {' -> '.join(trace)}")
        print(f"Satisfies targets: {'Yes' if satisfied else 'No'}")
        if target_elements[0] in model.qualities:
            print(f"Final {target_elements[0]} state: {model.qualities[target_elements[0]].value}")
        elif target_elements[0] in model.goals:
            print(f"Final {target_elements[0]} state: {model.goals[target_elements[0]].value}")
        print("-" * 30)
    
    return results

if __name__ == "__main__":
    analyze_traces()