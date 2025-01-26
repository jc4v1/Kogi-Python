import sys
import os
from typing import List, Dict
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Implementation.goal_model import GoalModel
from Implementation.enums import LinkType, ElementStatus

def create_model():
    model = GoalModel()
    
    # Add tasks
    tasks = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
    for task in tasks:
        model.add_task(task)
    
    # Add goals
    goals = ["G1", "G2", "G3"]
    for goal in goals:
        model.add_goal(goal)
    
    # Add quality
    model.add_quality("Q1")
    
    # Add links
    model.add_link("G3", "T8", LinkType.AND)
    model.add_link("T1", "T6", LinkType.AND)
    model.add_link("G1", "T2", LinkType.OR)
    model.add_link("Q1", "G2", LinkType.BREAK)
    model.add_link("Q1", "G1", LinkType.MAKE)
    model.add_link("G1", "T1", LinkType.OR)
    model.add_link("G3", "T1", LinkType.AND)
    model.add_link("T1", "T7", LinkType.AND)
    model.add_link("G2", "T3", LinkType.AND)
    model.add_link("G2", "T5", LinkType.AND)
    model.add_link("G2", "T4", LinkType.AND)
    
    # Add requirements
    model.requirements = {
        "G3": [['T8', 'T1']],
        "T1": [['T6', 'T7']],
        "G1": [['T2'], ['T1']],
        "G2": [['T3', 'T5', 'T4']]
    }
    
    # Add event mappings
    events = {
        "e1": "G1", 
        "e2": "T2", 
        "e3": [["T3", "G1"]],
        "e4": "T4", 
        "e5": "T5", 
        "e6": "T6",
        "e7": "T7", 
        "e8": "T8"
    }
    for event, target in events.items():
        model.add_event_mapping(event, target)
    
    return model

def print_summary_table(traces, results):
    # Get all elements from the model
    model = create_model()
    all_elements = {
        **model.tasks,
        **model.goals,
        **model.qualities
    }
    
    # Calculate satisfaction percentages and traces for each element
    element_stats = {}
    total_traces = len(traces)
    
    for element in all_elements:
        satisfied_count = 0
        satisfied_trace_nums = []
        
        for i, trace_result in enumerate(results):
            final_state = trace_result['states'][-1]
            element_type = None
            if element in final_state['tasks']:
                element_type = 'tasks'
            elif element in final_state['goals']:
                element_type = 'goals'
            elif element in final_state['qualities']:
                element_type = 'qualities'
                
            if element_type:
                state = final_state[element_type][element]
                if ((element_type == 'qualities' and state == ElementStatus.FULFILLED) or
                    (element_type == 'goals' and state == ElementStatus.ACHIEVED) or
                    (element_type == 'tasks' and state == ElementStatus.ACTIVATED)):
                    satisfied_count += 1
                    satisfied_trace_nums.append(i + 1)
        
        satisfaction_percentage = (satisfied_count / total_traces) * 100 if total_traces > 0 else 0
        element_stats[element] = {
            'percentage': satisfaction_percentage,
            'traces': satisfied_trace_nums
        }
    
    # Print table only once
    print("\nSummary Table:")
    print("-" * 40)
    print(f"{'Intentional Element':<20}{'  '} {'% Satisfaction':<15}\n {'Satisfied Traces':<45}")
    print("-" * 40)
    
    for element in sorted(element_stats.keys()):
        stats = element_stats[element]
        traces_details = []
        for trace_num in stats['traces']:
            trace = traces[trace_num - 1]
            trace_str = ', '.join(trace)
            traces_details.append(trace_str)
        traces_str = '\n'+'\n'.join(traces_details)
        print(f"{element:<20} {stats['percentage']:>6.1f}%   \n     {traces_str:<45}")
        print("-" * 40)
    #print("-" * 40)

def analyze_traces(traces: List[List[str]], target_elements: List[str]):
    results = []
    satisfied_traces = []
    summary_printed = False  # Flag to control summary printing
    
    for i, trace in enumerate(traces):
        model = create_model()
        trace_result = {
            'trace_number': i + 1,
            'events': trace,
            'states': []
        }
        
        satisfied = False
        
        for event in trace:
            model.process_event(event)
            trace_result['states'].append({
                'event': event,
                'qualities': model.qualities.copy(),
                'goals': model.goals.copy(),
                'tasks': model.tasks.copy()
            })
        
        for target in target_elements:
            if target in model.qualities and model.qualities[target] == ElementStatus.FULFILLED:
                satisfied = True
            elif target in model.goals and model.goals[target] == ElementStatus.ACHIEVED:
                satisfied = True
            elif target in model.tasks and model.tasks[target] == ElementStatus.ACTIVATED:
                satisfied = True
        
        if satisfied:
            satisfied_traces.append(trace)
        
        results.append(trace_result)
        print(f"\nTrace {i+1} ({' -> '.join(trace)}):")
        for target in target_elements:
            if target in model.qualities:
                print(f"{target} final state: {model.qualities[target]}")
            elif target in model.goals:
                print(f"{target} final state: {model.goals[target]}")
            elif target in model.tasks:
                print(f"{target} final state: {model.tasks[target]}")
    
    print("\nSatisfied Traces:")
    for idx, trace in enumerate(satisfied_traces, 1):
        print(f"Trace #{idx}: [{', '.join(trace)}]")
    
    # Print summary table only once after all traces are processed
    if not summary_printed:
        print_summary_table(traces, results)
        summary_printed = True
    
    return results

def export_results(results: List[Dict], filename: str = 'trace_analysis.json'):
    folder = os.path.join("App", "Outputs")
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    
    with open(file_path, 'w') as f:
        json.dump(results, f, default=str, indent=2)
    
    print(f"Results exported to: {file_path}")

def main():
    traces = [
        ["e6", "e2", "e3", "e4", "e5", "e7", "e8"],
        ["e6", "e2", "e3", "e4", "e5", "e7", "e1"],
        ["e6", "e3", "e2", "e4", "e5", "e7", "e1"],
        ["e6", "e3", "e2", "e4", "e5", "e7", "e8"]
    ]
    target_elements = ["Q1"]
    
    results = analyze_traces(traces, target_elements)
    export_results(results)

if __name__ == "__main__":
    main()