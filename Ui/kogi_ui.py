from Implementation.enums import ElementStatus, QualityStatus, LinkType
from Implementation.goal_model import GoalModel
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML

# Global variable model to hold a goal model instance
# The variable model is set in create_interface function and
# in reset_model_with_trace function
model: GoalModel | None = None

# Visualization Functions (adapted to work with your GoalModel)

def get_status_color_from_your_model(element_id):
    global model
    """Get color based on element status using your model's data structures"""
    if element_id in model.qualities:
        status = model.qualities[element_id]
        if status == QualityStatus.UNKNOWN:
            return 'white'
        elif status == QualityStatus.FULFILLED:
            return 'lightgreen'
        elif status == QualityStatus.DENIED:
            return 'lightcoral'
    else:
        status = model.tasks.get(element_id) or model.goals.get(element_id)
        if status == ElementStatus.UNKNOWN:
            return 'white'
        elif status == ElementStatus.TRUE_FALSE:
            return 'lightgreen'
        elif status == ElementStatus.TRUE_TRUE:
            return 'lightblue'
    return 'white'

def create_goal_model_visualization():
    global model
    """Create visualization using your actual GoalModel data"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left side: Goal Model Structure
    ax1.set_title("Goal Model Structure", fontsize=14, fontweight='bold')
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.set_aspect('equal')
    
    # Define positions for elements
    positions = {
        'Q1': (5, 9),
        'G1': (2, 7), 'G2': (5, 7), 'G3': (8, 7),
        'T1': (1, 5), 'T2': (3, 5), 'T3': (4, 5), 'T4': (5, 5),
        'T5': (6, 5), 'T6': (1, 3), 'T7': (2, 3), 'T8': (8, 3)
    }
    
    # Draw elements using your model's actual data
    for element_id, (x, y) in positions.items():
        color = get_status_color_from_your_model(element_id)
        
        if element_id.startswith('Q'):
            # Quality - cloud shape
            cloud = FancyBboxPatch((x-0.4, y-0.3), 0.8, 0.6, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=color, edgecolor='black', linewidth=2)
            ax1.add_patch(cloud)
            # Show actual status from your model
            status_text = f"{element_id}\n{model._format_status(model.qualities[element_id])}"
            ax1.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=8)
        elif element_id.startswith('G'):
            # Goal - ellipse
            ellipse = patches.Ellipse((x, y), 0.8, 0.5, 
                                    facecolor=color, edgecolor='black', linewidth=2)
            ax1.add_patch(ellipse)
            status_text = f"{element_id}\n{model._format_status(model.goals[element_id])}"
            ax1.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=8)
        else:
            # Task - hexagon
            hexagon = patches.RegularPolygon((x, y), 6, radius=0.4, 
                                          facecolor=color, edgecolor='black', linewidth=2)
            ax1.add_patch(hexagon)
            status_text = f"{element_id}\n{model._format_status(model.tasks[element_id])}"
            ax1.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=8)
    
    # Draw links using your model's actual links
    for parent, child, link_type, status in model.links:
        if parent in positions and child in positions:
            px, py = positions[parent]
            cx, cy = positions[child]
            
            # Determine arrow style based on link type from your enums
            if link_type == LinkType.MAKE:
                color = 'green'
                style = '->'
            elif link_type == LinkType.BREAK:
                color = 'red'
                style = '->'
            elif link_type == LinkType.AND:
                        arrow_color = 'purple'
                        style = '->'
            elif link_type == LinkType.OR:
                        arrow_color = 'orange'
                        style = '->'
            else:
                color = 'blue'
                style = '->'
            
            ax1.annotate('', xy=(cx, cy), xytext=(px, py),
                        arrowprops=dict(arrowstyle=style, color=color, lw=2))
    
    ax1.set_xticks([])
    ax1.set_yticks([])
    
    # Right side: Process Model with Mappings (using your event_mapping)
    ax2.set_title("Process Model & Event Mappings", fontsize=14, fontweight='bold')
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    
    # Draw process transitions using your actual event mappings
    events = list(model.event_mapping.keys())
    for i, event in enumerate(events):
        x_pos = (i + 1) * (8 / len(events)) + 1
        y_level = 5
        
        # Process transition as rectangle
        rect = FancyBboxPatch((x_pos-0.3, y_level-0.2), 0.6, 0.4,
                            boxstyle="round,pad=0.05",
                            facecolor='lightgray', edgecolor='black')
        ax2.add_patch(rect)
        ax2.text(x_pos, y_level, event, ha='center', va='center', fontweight='bold')
        
        # Show mapping using your actual event_mapping data
        targets = model.event_mapping[event]
        if isinstance(targets[0], list):
            target_str = ', '.join(targets[0])
        else:
            target_str = targets[0][0] if isinstance(targets[0], list) else str(targets[0])
        
        ax2.text(x_pos, y_level-0.8, f"→ {target_str}", 
                ha='center', va='center', fontsize=8)
    
    ax2.set_xticks([])
    ax2.set_yticks([])
    
    plt.tight_layout()
    return fig

# Interactive Controls 

def create_interactive_controls():
    global model
    """Create interactive controls that use your GoalModel's process_event method"""
    
    # Process transition dropdown using your actual event mappings
    process_dropdown = widgets.Dropdown(
        options=list(model.event_mapping.keys()),
        value=list(model.event_mapping.keys())[0],
        description='Event:',
        disabled=False,
    )
    
    # Execute button
    execute_button = widgets.Button(
        description='Execute Event',
        disabled=False,
        button_style='success',
        tooltip='Execute the selected event using your process_event method'
    )
    
    # Reset button
    reset_button = widgets.Button(
        description='Reset Model',
        disabled=False,
        button_style='warning',
        tooltip='Reset the model to initial state'
    )
    
    # Output areas
    trace_output = widgets.Output()
    status_output = widgets.Output()
    viz_output = widgets.Output()
    
    def execute_event(b):
        """Execute selected event using your GoalModel's process_event method"""
        with status_output:
            clear_output(wait=True)
            selected_event = process_dropdown.value
            
            print(f"Executing event: {selected_event}")
            
            # Use your actual process_event method
            model.process_event(selected_event)
            
            print(f"Event {selected_event} processed successfully")
            
            # Show current quality status using your model's data
            print("\nCurrent Status:")
            for quality_id, status in model.qualities.items():
                formatted_status = model._format_status(status)
                print(f"  {quality_id}: {formatted_status}")
        
        update_trace_display()
        update_visualization()
    
    def reset_model(b):
        """Reset the model using your create_model logic"""
        global model
        model = create_model_from_your_code()
        
        with status_output:
            clear_output(wait=True)
            print("Model reset to initial state")
        
        with trace_output:
            clear_output(wait=True)
            print("Event sequence: []")
        
        update_visualization()
    
    def update_trace_display():
        """Update the trace display"""
        with trace_output:
            clear_output(wait=True)
            # You can access execution history through your model if available
            # For now, we'll show the current state
            print("Current Model State:")
            print(f"Execution counts: {model.execution_count}")
    
    def update_visualization():
        """Update the visualization using your model data"""
        with viz_output:
            clear_output(wait=True)
            fig = create_goal_model_visualization()
            plt.show()
            plt.close()
    
    # Connect event handlers
    execute_button.on_click(execute_event)
    reset_button.on_click(reset_model)
    
    # Create layout
    controls = widgets.HBox([process_dropdown, execute_button, reset_button])
    
    # Initial displays
    update_trace_display()
    update_visualization()
    
    return controls, trace_output, status_output, viz_output

# Trace and Evolution Visualization Functions

def create_trace_visualization():
    global model
    """Create horizontal trace timeline showing only events"""
    trace_output = widgets.Output()
    
    # Global variable to track executed events
    if not hasattr(create_trace_visualization, 'executed_events'):
        create_trace_visualization.executed_events = []
    
    def update_trace_display():
        with trace_output:
            clear_output(wait=True)
            
            # Create horizontal trace timeline
            trace_html = """
            <div style='border: 2px solid #ccc; padding: 15px; margin: 10px; background-color: #f9f9f9;'>
                <h3>Trace Execution Timeline</h3>
            """
            
            if not create_trace_visualization.executed_events:
                trace_html += "<p>No events executed yet. Select an event and click 'Execute Event' to start.</p>"
            else:
                # Create horizontal event sequence
                trace_html += "<div style='display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: bold;'>"
                trace_html += "<span style='color: #666;'>trace ⟨</span>"
                
                for i, event in enumerate(create_trace_visualization.executed_events):
                    if i > 0:
                        trace_html += "<span style='color: #666;'>,</span>"
                    trace_html += f"<span style='color: #2E86AB; margin: 0 5px;'>{event}</span>"
                
                trace_html += "<span style='color: #666;'>⟩</span>"
                trace_html += "</div>"
            
            trace_html += "</div>"
            display(HTML(trace_html))
    
    return trace_output, update_trace_display


def create_evolution_visualization():
    global model
    """Create evolution view with proper mapping visualization"""
    evolution_out = widgets.Output()
    
    def update_evolution():
        with evolution_out:
            clear_output(wait=True)
            
            # Get executed events
            executed_events = getattr(create_trace_visualization, 'executed_events', [])
            
            # Build mapping from events to elements
            event_to_element_mapping = {}
            
            # Try to get mappings from your model
            try:
                if hasattr(model, 'events') and hasattr(model, 'get_mapping'):
                    for event in model.events:
                        mapped_element = model.get_mapping(event)
                        if mapped_element:
                            event_to_element_mapping[event] = mapped_element
                else:
                    # Fallback: define mappings based on your model structure
                    event_to_element_mapping = {
                        'e1': 'T1', 'e2': 'T2', 'e3': 'T3', 'e4': 'T4',
                        'e5': 'T5', 'e6': 'T6', 'e7': 'T7', 'e8': 'T8'
                    }
            except:
                # Default mappings if model access fails
                event_to_element_mapping = {
                    'e1': 'T1', 'e2': 'T2', 'e3': 'T3', 'e4': 'T4',
                    'e5': 'T5', 'e6': 'T6', 'e7': 'T7', 'e8': 'T8'
                }
            
            # Get which elements should be highlighted
            highlighted_elements = set()
            for executed_event in executed_events:
                if executed_event in event_to_element_mapping:
                    highlighted_elements.add(event_to_element_mapping[executed_event])
            
            # Display the evolution view
            display(HTML(f"""
            <div style='background-color: #2d2d2d; padding: 20px; border-radius: 8px; font-family: "Segoe UI", Arial, sans-serif;'>
                <div style='text-align: center; margin-bottom: 20px;'>
                    <div style='background-color: #404040; color: #ffffff; padding: 10px; border-radius: 4px; display: inline-block; min-width: 100px;'>
                        {executed_events[-1] if executed_events else 'Initial State'}
                    </div>
                    <div style='color: #b0b0b0; margin-top: 8px; font-size: 12px;'>Current Event</div>
                </div>
                
                <div style='display: flex; justify-content: space-between; max-width: 400px; margin: 0 auto;'>
                    <div style='text-align: center;'>
                        <div style='color: #ffffff; font-weight: 600; margin-bottom: 15px;'>Process</div>
                        {''.join([
                            f'<div style="background-color: {"#28a745" if event in executed_events else "#404040"}; '
                            f'color: #ffffff; padding: 8px 12px; margin: 5px 0; border-radius: 4px; '
                            f'border: {"2px solid #ffffff" if event == (executed_events[-1] if executed_events else None) else "1px solid #666"};">'
                            f'{event}</div>'
                            for event in ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8']
                        ])}
                    </div>
                    
                    <div style='display: flex; align-items: center; margin: 0 20px;'>
                        <div style='color: #4a90e2; font-size: 24px;'>→</div>
                    </div>
                    
                    <div style='text-align: center;'>
                        <div style='color: #ffffff; font-weight: 600; margin-bottom: 15px;'>Elements</div>
                        {''.join([
                            f'<div style="background-color: {"#28a745" if element in highlighted_elements else "#6c757d"}; '
                            f'color: #ffffff; padding: 8px 12px; margin: 5px 0; border-radius: 4px; '
                            f'border: 1px solid #666;">{element}</div>'
                            for element in ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8']
                        ])}
                        {''.join([
                            f'<div style="background-color: #6c757d; color: #ffffff; padding: 8px 12px; '
                            f'margin: 5px 0; border-radius: 50%; border: 1px solid #666;">{goal}</div>'
                            for goal in ['G1', 'G2', 'G3', 'Q1']
                        ])}
                    </div>
                </div>
                
                <div style='text-align: center; margin-top: 20px; color: #b0b0b0; font-size: 12px;'>
                    {'Mapping: ' + ', '.join([f"{k} → {v}" for k, v in event_to_element_mapping.items() if k in executed_events]) if executed_events else 'No mappings executed'}
                </div>
            </div>
            """))
    
    return evolution_out, update_evolution


def create_dual_model_visualization():
    global model
    """Create side-by-side goal model and process model visualization"""
    viz_output = widgets.Output()
    
    def update_dual_visualization():
        with viz_output:
            clear_output(wait=True)
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))
            
            # Left side: Goal Model
            ax1.set_title("Goal Model Structure", fontsize=16, fontweight='bold', pad=20)
            ax1.set_xlim(0, 10)
            ax1.set_ylim(0, 12)
            ax1.set_aspect('equal')
            
            # Define positions for goal model elements
            positions = {
                'Q1': (5, 10.5),
                'G1': (2, 8.5), 'G2': (5, 8.5), 'G3': (8, 8.5),
                'T1': (1, 6), 'T2': (2.5, 6), 'T3': (4, 6), 'T4': (5.5, 6),
                'T5': (7, 6), 'T6': (1, 3.5), 'T7': (3, 3.5), 'T8': (8, 3.5)
            }
            
            # Draw goal model elements
            for element_id, (x, y) in positions.items():
                color = get_status_color_from_your_model(element_id)
                
                if element_id.startswith('Q'):
                    # Quality - cloud shape
                    cloud = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8, 
                                         boxstyle="round,pad=0.15", 
                                         facecolor=color, edgecolor='black', linewidth=2)
                    ax1.add_patch(cloud)
                    status_text = f"{element_id}\n{model._format_status(model.qualities[element_id])}"
                    ax1.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10)
                elif element_id.startswith('G'):
                    # Goal - ellipse
                    ellipse = patches.Ellipse((x, y), 1.0, 0.6, 
                                            facecolor=color, edgecolor='black', linewidth=2)
                    ax1.add_patch(ellipse)
                    status_text = f"{element_id}\n{model._format_status(model.goals[element_id])}"
                    ax1.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10)
                else:
                    # Task - hexagon
                    hexagon = patches.RegularPolygon((x, y), 6, radius=0.5, 
                                                  facecolor=color, edgecolor='black', linewidth=2)
                    ax1.add_patch(hexagon)
                    status_text = f"{element_id}\n{model._format_status(model.tasks[element_id])}"
                    ax1.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=9)
            
            # Draw links in goal model
            for parent, child, link_type, status in model.links:
                if parent in positions and child in positions:
                    px, py = positions[parent]
                    cx, cy = positions[child]
                    
                    if link_type == LinkType.MAKE:
                        arrow_color = 'green'
                        style = '->'
                    elif link_type == LinkType.BREAK:
                        arrow_color = 'red'
                        style = '->'
                    elif link_type == LinkType.AND:
                        arrow_color = 'purple'
                        style = '->'
                    elif link_type == LinkType.OR:
                        arrow_color = 'orange'
                        style = '->'
                    else:
                        arrow_color = 'blue'
                        style = '->'
                    
                    ax1.annotate('', xy=(cx, cy), xytext=(px, py),
                                arrowprops=dict(arrowstyle=style, color=arrow_color, lw=2))
            
            ax1.set_xticks([])
            ax1.set_yticks([])
            ax1.grid(True, alpha=0.3)
            
            # Right side: Process Model
            ax2.set_title("Process Model & Event Mappings", fontsize=16, fontweight='bold', pad=20)
            ax2.set_xlim(0, 10)
            ax2.set_ylim(0, 12)
            
            # Draw process model as a sequence
            events = list(model.event_mapping.keys())
            y_positions = [10, 8.5, 7, 5.5, 4, 2.5, 1, 0.5]  # Different heights for visual appeal
            
            for i, event in enumerate(events):
                if i < len(y_positions):
                    x_pos = 2
                    y_pos = y_positions[i]
                    
                    # Process transition as rectangle
                    rect = FancyBboxPatch((x_pos-0.4, y_pos-0.25), 0.8, 0.5,
                                        boxstyle="round,pad=0.05",
                                        facecolor='lightgray', edgecolor='black', linewidth=2)
                    ax2.add_patch(rect)
                    ax2.text(x_pos, y_pos, event, ha='center', va='center', fontweight='bold', fontsize=12)
                    
                    # Show mapping with arrow
                    targets = model.event_mapping[event]
                    if isinstance(targets[0], list):
                        target_str = ', '.join(targets[0])
                    else:
                        target_str = targets[0][0] if isinstance(targets[0], list) else str(targets[0])
                    
                    # Arrow pointing to mapping
                    ax2.annotate('', xy=(x_pos + 1.5, y_pos), xytext=(x_pos + 0.5, y_pos),
                                arrowprops=dict(arrowstyle='->', color='black', lw=2))
                    
                    # Target box
                    target_rect = FancyBboxPatch((x_pos + 1.5, y_pos-0.2), 2.5, 0.4,
                                               boxstyle="round,pad=0.05",
                                               facecolor='lightyellow', edgecolor='gray')
                    ax2.add_patch(target_rect)
                    ax2.text(x_pos + 2.75, y_pos, target_str, ha='center', va='center', fontsize=10)
            
            ax2.set_xticks([])
            ax2.set_yticks([])
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            plt.close()
    
    return viz_output, update_dual_visualization

# Main Interface with New Layout
def create_interface(create_model_func):
    global model
    model = create_model_func()  # Ensure model is initialized
    """Display the interface with trace timeline and dual model view"""
    controls, trace_out, status_out, viz_out = create_interactive_controls()
    # Header
    header = widgets.HTML(f"""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1 style='color: #2E86AB; margin-bottom: 10px;'> A unfied view - Interactive High-Level Business Requirements Evaluation</h1>
        <!-- <p style='font-size: 14px; color: #666;'>Using your actual GoalModel class from: {"implementation_path"}</p> -->
    </div>
    """)
    
    # Legend - more compact
    legend = widgets.HTML("""
    <div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 12px; border: 1px solid #ccc;'>
    <div style='font-weight: bold; margin-bottom: 8px; text-align: center;'>Conventions</div>
    <div><strong>Colors:</strong> 🤍 Unknown | 🟢 Satisfied/Fulfilled | 🔵 Executed Pending | 🔴 Denied</div>
    <div><strong>Shapes:</strong> ☁️ Quality | ⭕ Goal | ⬡ Task | ⬜ Process Transition</div>
    </div>
    """)
    
    # Controls section
    controls_section = widgets.VBox([
        widgets.HTML("<h3>Controls</h3>"),
        controls,
        status_out
    ])
    
    # Create trace and dual visualization
    trace_out_new, update_trace = create_trace_visualization()
    evolution_out, update_evolution = create_evolution_visualization()
    dual_viz_out, update_dual_viz = create_dual_model_visualization()
    
    # Modified execute function to update all displays
    def execute_event_with_trace(b):
        """Execute event and update all displays"""
        selected_event = controls.children[0].value  # Get dropdown value
        
        with status_out:
            clear_output(wait=True)
            print(f"🚀 Executing event: {selected_event}")
            
            # Add to trace
            create_trace_visualization.executed_events.append(selected_event)
            
            # Use your actual process_event method
            model.process_event(selected_event)
            
            print(f"✅ Event {selected_event} processed!")
            
            # Show current quality status
            print("\n📊 Current Status:")
            for quality_id, status in model.qualities.items():
                formatted_status = model._format_status(status)
                print(f"🎯 {quality_id}: {formatted_status}")
        
        # Update all displays
        update_trace()
        update_evolution()
        update_dual_viz()
    
    def reset_model_with_trace(b,create_model_func):
        """Reset model and clear trace"""
        global model
        model = create_model_func()
        create_trace_visualization.executed_events = []
        
        with status_out:
            clear_output(wait=True)
            print("🔄 Model and trace reset to initial state")
        
        update_trace()
        update_evolution()
        update_dual_viz()
    
    # Clear any existing event handlers to prevent duplicates
    controls.children[1]._click_handlers.callbacks.clear()  # Execute button
    controls.children[2]._click_handlers.callbacks.clear()  # Reset button
    
    # Connect new event handlers
    controls.children[1].on_click(execute_event_with_trace)  # Execute button
    controls.children[2].on_click(lambda b: reset_model_with_trace(b, create_model_func))    # Reset button
    
    # Create main tab structure
    main_tab = widgets.Tab()
    
    # Main tab content with trace timeline, evolution view, and dual models
    main_content = widgets.VBox([
        controls_section,
        trace_out_new,
        widgets.HTML("<h3>Evolution View</h3>"),
        evolution_out,
        widgets.HTML("<h3>Model Views</h3>"),
        dual_viz_out
    ])
    
    # Statistics tab (simplified)
    # stats_content = create_statistics_view()
    
    # main_tab.children = [main_content, stats_content]
    main_tab.children = [main_content]
    main_tab.set_title(0, 'Main Interface')
    # main_tab.set_title(1, 'Statistics')
    
    # Initial visualization
    update_trace()
    update_evolution()
    update_dual_viz()
    
    # Complete interface
    interface = widgets.VBox([
        header,
        legend,
        main_tab
    ])
    
    return interface