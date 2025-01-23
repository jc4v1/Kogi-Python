import pm4py
from tkinter import Tk, filedialog
from typing import List, Any


def process_bpmn_file(file_path: str) -> List[List[str]]:
    """
    Process a BPMN file and return unique traces.
    
    Parameters:
        file_path (str): The path to the BPMN file.

    Returns:
        List[List[str]]: A list of unique traces, where each trace is a list of activity names.
    """
    # Load and convert BPMN to Petri net
    bpmn_model = pm4py.read_bpmn(file_path)
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
    print("\nUnique traces found:")
    for i, trace in enumerate(unique_traces):
        print(f"Trace {i}: {trace}")

    return unique_traces


def select_file() -> str:
    """
    Open a file dialog to select a BPMN file.
    
    Returns:
        str: The path to the selected file.
    """
    root = Tk()
    root.withdraw()  # Hide the root window
    root.update()  # Ensure the Tkinter GUI processes its event loop
    file_path = filedialog.askopenfilename(
        title="Select a BPMN File",
        filetypes=[("BPMN files", "*.bpmn"), ("All files", "*.*")]
    )
    root.destroy()  # Clean up the Tkinter instance
    return file_path



if __name__ == "__main__":
    # Allow file selection via a dialog
    file_path = select_file()
    if file_path:
        try:
            traces = process_bpmn_file(file_path)
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("No file selected.")
