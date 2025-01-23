import pm4py
from google.colab import files
from typing import List, Dict, Any

def process_bpmn_file() -> List[List[str]]:
    """
    Process a BPMN file and return unique traces.
    """
    print("Por favor, sube tu archivo BPMN cuando aparezca el botón")
    uploaded = files.upload()
    file_name = list(uploaded.keys())[0]

    # Load and convert BPMN to Petri net
    bpmn_model = pm4py.read_bpmn(file_name)
    net, initial_marking, final_marking = pm4py.convert_to_petri_net(bpmn_model)

    # Generate log and get variants
    log = pm4py.play_out(net, initial_marking, final_marking)
    print("Total traces:", len(log))
    
    variants = pm4py.get_variants(log)
    print("Different variants:", len(variants))

    # Extract unique traces
    unique_traces = []
    for variant_trace in variants.values():
        activities = [event['concept:name'] for event in variant_trace[0]]
        unique_traces.append(activities)

    # Print traces for verification
    print("\nTrazas únicas encontradas:")
    for i, trace in enumerate(unique_traces):
        print(f"Traza {i}: {trace}")

    # Example of processing first trace
    if unique_traces:
        first_trace = unique_traces[0]
        print(f"\nRecorriendo la primera traza:")
        for j, activity in enumerate(first_trace):
            print(f"Posición {j}: {activity}")

    return unique_traces

if __name__ == "__main__":
    trazas = process_bpmn_file()