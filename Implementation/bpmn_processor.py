"""
BPMN Processor
Developed by Juanita Caballero-Villalobos
Date: January 23, 2025.

    Process a BPMN file and return unique traces.

    Parameters:
        file_path (str): The path to the BPMN file.

    Returns:
        List[List[str]]: A list of unique traces, where each trace is a list of activity names.
"""

import pm4py
import os
from typing import List

def get_bpmn_file_path() -> str:
    while True:
        file_path = input("Enter BPMN file path: ")
        if os.path.isfile(file_path):
            return file_path
        else:
            print("Invalid file path. Please try again.")

def process_bpmn_file(file_path: str) -> List[List[str]]:
    bpmn_model = pm4py.read_bpmn(file_path)
    net, initial_marking, final_marking = pm4py.convert_to_petri_net(bpmn_model)
    log = pm4py.play_out(net, initial_marking, final_marking)
    variants = pm4py.get_variants(log)
    return [[event['concept:name'] for event in variant_trace[0]] for variant_trace in variants.values()]

if __name__ == "__main__":
    try:
        bpmn_path = get_bpmn_file_path()
        traces = process_bpmn_file(bpmn_path)
        print(f"Total: {len(traces)}, Unique: {len(traces)}")
        for i, trace in enumerate(traces):
            print(f"Trace {i}: {trace}")
    except Exception as e:
        print(f"Error: {e}")