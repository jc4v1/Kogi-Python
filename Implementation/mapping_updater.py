import pandas as pd
import re

def update_event_mappings(mapping_path):
    try:
        # Read the mapping file
        df = pd.read_csv(mapping_path) if mapping_path.endswith('.csv') else pd.read_excel(mapping_path)
        print(f"\nFound {len(df)} mappings:\n{df}")

        # Generate new mapping code
        new_mappings = [f'    model.add_event_mapping("{row["Event"]}", "{row["Task"]}")' for _, row in df.iterrows()]

        # Update demo_model.py
        with open('Implementation\demo_model.py', 'r') as f:
            content = f.read()
        sections = re.split(r'(\s*model\.add_event_mapping.*?\n)+', content, flags=re.DOTALL)
        pre_mapping, post_mapping = sections[0].rstrip(), '\n    ' + sections[-1].lstrip() if len(sections) > 2 else ""
        new_content = pre_mapping + "\n\n" + "\n".join(new_mappings) + "\n\n" + post_mapping
        with open('Implementation\demo_model.py', 'w') as f:
            f.write(new_content)
        print("\nSuccessfully updated demo_model.py!")
        print(f"Added {len(new_mappings)} new mappings.")
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        print("Make sure your file has 'Event' and 'Task' columns.")

if __name__ == "__main__":
    update_event_mappings()