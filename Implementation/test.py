from bpmn_processor import get_bpmn_file_path
from bpmn_processor import select_file
from istar_processor import process_istar_model

def main():

   #1. Recieve a BPMN Model (XML), generate and format the traces.

 bpmn_processor()

 process_istar_model()


# Assigns the PATHS for the different variables.
if __name__ == "__main__":
 #   BPMN_FILE_PATH = "Data\DEMO.bpmn"
    ISTAR_FILE_PATH = "Data\Demo.json"
    MAPPING_FILE_PATH = "Data\Mapping1to1.xlsx"
    main()
