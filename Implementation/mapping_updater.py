import pandas as pd
import re

def update_event_mappings(mapping_path):
    try:
        # Read the mapping file
        df = pd.read_csv(mapping_path) if mapping_path.endswith('.csv') else pd.read_excel(mapping_path)
        
        # Clean column names and handle the column access issue
        df.columns = df.columns.str.strip()
        
        # Debug: Print column information
        print(f"Columns found: {list(df.columns)}")
        
        # Use position-based access instead of column names to avoid the KeyError
        event_col = df.columns[0]  # First column (Event)
        intentional_col = df.columns[1]  # Second column (Intentional Element)
        
        print(f"Using Event column: '{event_col}', Intentional Element column: '{intentional_col}'")
        
        print(f"\nFound {len(df)} mappings:")
        for i, row in df.iterrows():
            print(f"{i}\t\t{row[event_col]};{row[intentional_col]}")

        # Group by Event to identify related targets
        event_groups = df.groupby(event_col)[intentional_col].apply(list).to_dict()
        
        print(f"\nEvent groups: {event_groups}")  # Debug line
                
        # Generate new mapping code
        new_mappings = []
        for event, targets in event_groups.items():
            if len(targets) > 1:
                # Multiple targets for this event
                targets_str = ', '.join(f'"{t}"' for t in targets)
                new_mappings.append(f'    model.add_event_mapping("{event}", [{targets_str}])')
            else:
                # Single target
                new_mappings.append(f'    model.add_event_mapping("{event}", "{targets[0]}")')

        # Update demo_model.py
        with open('Implementation/demo_model.py', 'r') as f:
            content = f.read()
                    
        sections = re.split(r'(\s*model\.add_event_mapping.*?\n)+', content, flags=re.DOTALL)
        pre_mapping = sections[0].rstrip()
        post_mapping = '\n    ' + sections[-1].lstrip() if len(sections) > 2 else ""
                
        new_content = pre_mapping + "\n\n" + "\n".join(new_mappings) + "\n\n" + post_mapping
                
        with open('Implementation/demo_model.py', 'w') as f:
            f.write(new_content)
                    
        print("\nSuccessfully updated demo_model.py!")
        print(f"Added {len(new_mappings)} new mappings.")       
        
        # Print the actual mappings that were added
        print("\nEvent Mappings:")
        for mapping in new_mappings:
            print(mapping)
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        print("Make sure your file has 'Event' and 'Intentional Element' columns.")

if __name__ == "__main__":
    update_event_mappings()