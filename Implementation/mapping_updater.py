import pandas as pd
from google.colab import files
import re

def update_event_mappings():
    """
    Process Excel/CSV file with event-task mappings and update demo_model.py
    """
    print("Por favor, sube tu archivo de mapeos (CSV o XLSX)")
    uploaded = files.upload()
    filename = list(uploaded.keys())[0]
    
    try:
        # Read the mapping file
        if filename.endswith('.csv'):
            df = pd.read_csv(filename)
        else:
            df = pd.read_excel(filename)
            
        print("\nMapeos encontrados:")
        print(df)
        
        # Generate new mapping code
        new_mappings = []
        for _, row in df.iterrows():
            # Use Event and Task column names instead of evento and tarea
            new_mappings.append(f'    model.add_event_mapping("{row["Event"]}", "{row["Task"]}")')
        
        # Read current demo_model.py
        with open('demo_model.py', 'r') as f:
            content = f.read()
        
        # Split content into sections
        sections = re.split(r'(\s*model\.add_event_mapping.*?\n)+', content, flags=re.DOTALL)
        
        # Find the section before and after mappings
        pre_mapping = sections[0].rstrip()  # Remove trailing whitespace
        post_mapping = '\n    ' + sections[-1].lstrip() if len(sections) > 2 else ""  # Preserve indentation for return
        
        # Create new content with proper spacing
        new_content = pre_mapping + "\n\n" + "\n".join(new_mappings) + "\n\n" + post_mapping
        
        # Write updated content back to file
        with open('demo_model.py', 'w') as f:
            f.write(new_content)
            
        print("\nArchivo demo_model.py actualizado exitosamente!")
        print(f"Se agregaron {len(new_mappings)} mapeos nuevos.")
        
    except Exception as e:
        print(f"Error procesando el archivo: {str(e)}")
        print("Asegúrate que tu archivo tiene las columnas 'Event' y 'Task'")

if __name__ == "__main__":
    update_event_mappings()