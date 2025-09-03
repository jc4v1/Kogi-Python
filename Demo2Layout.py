# %%
import os
import sys
import json
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import networkx as nx
import numpy as np
from enum import Enum
from typing import Dict, List, Tuple, Set
import pandas as pd
from datetime import datetime


# Project paths setup
project_root = os.path.abspath(".")  # Current directory
implementation_path = os.path.join(project_root, "Implementation")
app_path = os.path.join(project_root, "App")
new_semantics_path = os.path.join(project_root, "NewSemantics") 

# Add paths to sys.path
for path in [implementation_path, app_path, new_semantics_path]:
    if path not in sys.path:
        sys.path.append(path)

from Implementation.enums import ElementStatus, QualityStatus, LinkType, LinkStatus
from NewSemantics.goal_model import GoalModel
from NewSemantics.istar_processor import read_istar_model
from Ui.Layout import Layout

print("All libraries imported successfully!")


# %%
# Global state initialization
if 'executed_events' not in globals():
    executed_events = []

if 'interface_created' not in globals():
    interface_created = False

if 'handler_debug' not in globals():
    handler_debug = True

if 'last_update' not in globals():
    last_update = datetime.utcnow()

# Token tracking for Petri net - starts empty, tokens appear based on executed events
if 'petri_tokens' not in globals():
    petri_tokens = {}


# %%
def create_model_from_your_code():
    filepath = "Data/example_from_paper.txt"
    return read_istar_model(filepath)

def get_status_color_from_your_model(element_id):
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

def update_petri_tokens(event_name):
    """Update token positions based on executed event - Direct mapping approach"""
    global petri_tokens, executed_events
    
    # Get the dropdown options to determine which element was executed
    dropdown_events = list(model.event_mapping.keys())
    
    try:
        # Find the index of the current event in the dropdown list
        event_index = dropdown_events.index(event_name)
        
        # Clear all tokens first
        petri_tokens = {}
        
        # Direct mapping based on dropdown position (0-indexed)
        if event_index == 0:  # First element
            petri_tokens = {'p7': 1}
            print(f"Event {event_name} (index {event_index}): Token at p7")
        elif event_index == 1:  # Second element  
            petri_tokens = {'p9': 1}
            print(f"Event {event_name} (index {event_index}): Token at p9")
        elif event_index == 2:  # Third element
            petri_tokens = {'p6': 1}
            print(f"Event {event_name} (index {event_index}): Token at p6")
        elif event_index == 3:  # Fourth element
            petri_tokens = {'p6': 1}
            print(f"Event {event_name} (index {event_index}): Token at p6")
        elif event_index == 4:  # Fifth element
            petri_tokens = {'p8': 1}
            print(f"Event {event_name} (index {event_index}): Token at p8")
        elif event_index == 5:  # Sixth element
            petri_tokens = {'p3': 1, 'p4': 1}
            print(f"Event {event_name} (index {event_index}): Tokens at p3 and p4")
        elif event_index == 6:  # Seventh element
            petri_tokens = {'p3': 1, 'p2': 1}
            print(f"Event {event_name} (index {event_index}): Tokens at p3 and p2")
        else:
            # For any additional elements, keep no tokens
            petri_tokens = {}
            print(f"Event {event_name} (index {event_index}): No specific token placement defined")
            
        print(f"Updated tokens: {petri_tokens}")
        
    except ValueError:
        print(f"Event {event_name} not found in dropdown list")
        petri_tokens = {}  # Default fallback

# Initialize model
model = create_model_from_your_code()
print("Model and helper functions initialized!")

# %%
def create_complete_interface():
    """Create the complete interface with all functionality in one place"""
    global interface_created, handler_debug
    
    # Header
    header = widgets.HTML(f"""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1 style='color: #2E86AB; margin-bottom: 10px;'>A unified view - Interactive High-Level Business Requirements Evaluation</h1>
        <p style='font-size: 14px; color: #666;'>Using GoalModel class from: {implementation_path}</p>
        <p style='font-size: 12px; color: #888;'>Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
    </div>
    """)
    
    # Legend
    legend = widgets.HTML("""
    <div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 12px; border: 1px solid #ccc;'>
    <div style='font-weight: bold; margin-bottom: 8px; text-align: center;'>Conventions</div>
    <div><strong>Goal Model Colors:</strong> 🤍 Unknown | 🟢 Satisfied/Fulfilled | 🔵 Executed Pending | 🔴 Denied</div>
    <div><strong>Shapes:</strong> ☁️ Quality | ⭕ Goal | ⬡ Task | ⬜ Process Transition</div>
    <div><strong>Petri Net:</strong> ⚫ Token | ⚪ Place | ⬛ Transition </div>
    
    </div>
    """)
    
    # Create output widgets
    trace_output = widgets.Output()
    status_output = widgets.Output()
    viz_output = widgets.Output()
    debug_output = widgets.Output() if handler_debug else None
    
    # Controls Panel (Left Side)
    process_dropdown = widgets.Dropdown(
        options=list(model.event_mapping.keys()),
        value=list(model.event_mapping.keys())[0],
        description='Event:',
        disabled=False,
        layout=widgets.Layout(width='100%', margin='5px 0px')
    )
    
    execute_button = widgets.Button(
        description='Execute Event',
        disabled=False,
        button_style='success',
        tooltip='Execute the selected event',
        layout=widgets.Layout(width='100%', margin='5px 0px')
    )
    
    reset_button = widgets.Button(
        description='Reset Model',
        disabled=False,
        button_style='warning',
        tooltip='Reset the model to initial state',
        layout=widgets.Layout(width='100%', margin='5px 0px')
    )
    
    # Token status display
    token_status = widgets.HTML(
        value="<b>Tokens:</b><br>No tokens (execute events to see tokens)",
        layout=widgets.Layout(width='100%', margin='10px 0px')
    )
    
    # Status info in controls panel
    status_info = widgets.HTML(
        value="<b>Status:</b><br>Ready to execute events",
        layout=widgets.Layout(width='100%', margin='10px 0px')
    )
    
    # Create controls panel container
    controls_panel = widgets.VBox([
        widgets.HTML("<h3 style='margin: 0 0 15px 0; color: #2E86AB;'>Controls</h3>"),
        process_dropdown,
        execute_button,
        reset_button,
        widgets.HTML("<hr style='margin: 15px 0;'>"),
        token_status,
        status_info,
        trace_output
    ], layout=widgets.Layout(
        width='18%',
        padding='15px',
        border='1px solid #ddd',
        border_radius='5px',
        background_color='#fafafa'
    ))
    
    # Main content area (Right side - 80%)
    content_area = widgets.VBox([
        viz_output
    ], layout=widgets.Layout(width='80%', padding='0 0 0 15px'))
    
    # Global state for preventing multiple updates
    _update_state = {'updating': False, 'pending_update': False}

    def update_trace():
        """Update trace display in the controls panel"""
        with trace_output:
            clear_output(wait=True)
            trace_html = """
            <div style='margin-top: 15px; padding: 10px; border: 1px solid #ccc; border-radius: 3px; background-color: white; font-size: 11px;'>
                <div style='font-weight: bold; margin-bottom: 8px; color: #2E86AB;'>Execution Trace</div>
            """
            if not executed_events:
                trace_html += "<div style='color: #666; font-style: italic;'>No events executed</div>"
            else:
                trace_html += "<div style='word-wrap: break-word;'>"
                trace_html += "<span style='color: #666;'>trace ⟨</span>"
                for i, event in enumerate(executed_events):
                    if i > 0:
                        trace_html += "<span style='color: #666;'>, </span>"
                    trace_html += f"<span style='color: #2E86AB; font-weight: bold;'>{event}</span>"
                trace_html += "<span style='color: #666;'>⟩</span></div>"
            trace_html += "</div>"
            display(HTML(trace_html))

    def update_token_status():
        """Update token status display"""
        token_text = "<b>Tokens:</b><br>"
        if petri_tokens:
            for place, count in sorted(petri_tokens.items()):
                token_text += f"{place}: {count}<br>"
        else:
            token_text += "No tokens (execute events to see tokens)"
        token_status.value = token_text

    def update_status_info(message=""):
        """Update status information in controls panel"""
        if message:
            status_info.value = f"<b>Status:</b><br>{message}"
        else:
            status_info.value = "<b>Status:</b><br>Ready to execute events"

    def safe_update_visualization():
        """Thread-safe visualization update with flickering prevention"""
        if _update_state['updating']:
            _update_state['pending_update'] = True
            return
        
        _update_state['updating'] = True
        _update_state['pending_update'] = False
        
        try:
            if handler_debug:
                print("DEBUG: safe_update_visualization() called - Starting render")
                print(f"Current petri_tokens: {petri_tokens}")
            
            with viz_output:
                clear_output(wait=True)
                
                # Create figure with 3 subplots
                fig = plt.figure(figsize=(18, 16))
                gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1.2, 0.4], hspace=0.35)
                ax1 = fig.add_subplot(gs[0, 0])  # Petri net
                ax2 = fig.add_subplot(gs[1, 0])  # Goal model
                ax3 = fig.add_subplot(gs[2, 0])  # Mappings
                
                # PETRI NET with direct token placement
                ax1.set_title("Process Model (Petri Net) - Direct Token Placement", fontsize=16, fontweight='bold', pad=20)
                ax1.set_xlim(-1, 19)
                ax1.set_ylim(-1, 8)
                ax1.set_aspect('equal')
                
                # Define Petri Net elements with proper positions
                petri_elements = {
                    'places': [
                        (0.8, 3.5, 'p0'), (3.2, 4.5, 'p1'), (3.2, 2.5, 'p2'),
                        (6.0, 4.5, 'p3'), (6.0, 2.5, 'p4'), (8.5, 3.5, 'p5'),
                        (11.5, 3.5, 'p6'), (14.0, 4.5, 'p7'), (15.1, 2.5, 'p9'),
                        (16.5, 4.5, 'p8'), (18.5, 3.5, 'p10')
                    ],
                    'transitions': [
                        (1.8, 3.5, 't_1', True),    # silent transition
                        (4.6, 4.5, 't_2', False),   # UE
                        (4.6, 2.5, 't_3', False),   # RA
                        (7.25, 3.5, 't_4', True),   # silent transition
                        (10.0, 4.5, 't_5', False),  # G
                        (10.0, 2.5, 't_6', False),  # O
                        (12.75, 3.5, 't_7', True),  # silent transition
                        (15.1, 4.5, 't_8', False),  # PT
                        (17.5, 3.5, 't_9', True),   # silent transition
                        (16.5, 2.5, 't_10', False), # FS
                        (14.0, 2.5, 't_11', False)  # AP
                    ]
                }
                
                # Draw places with tokens based on direct placement
                for x, y, label in petri_elements['places']:
                    circle = patches.Circle((x, y), 0.25, facecolor='white', edgecolor='black', linewidth=2)
                    ax1.add_patch(circle)
                    
                    # Draw tokens if present in our direct placement
                    token_count = petri_tokens.get(label, 0)
                    if token_count > 0:
                        #if handler_debug:
                            #print(f"Drawing {token_count} token(s) at {label} (position {x}, {y})")
                        
                        if token_count == 1:
                            token = patches.Circle((x, y), 0.08, facecolor='black', edgecolor='black')
                            ax1.add_patch(token)
                        else:
                            # Multiple tokens - arrange in a pattern
                            for i in range(min(token_count, 4)):  # Max 4 tokens visible
                                offset_x = 0.1 * (i % 2 - 0.5)
                                offset_y = 0.1 * (i // 2 - 0.5)
                                token = patches.Circle((x + offset_x, y + offset_y), 0.05, 
                                                     facecolor='black', edgecolor='black')
                                ax1.add_patch(token)
                            if token_count > 4:
                                ax1.text(x, y-0.15, f"{token_count}", ha='center', va='center', 
                                       fontsize=8, fontweight='bold', color='red')
                    
                    ax1.text(x, y-0.5, label, ha='center', va='top', fontsize=9, fontweight='bold')
                
                # Draw transitions - simple coloring based on executed events
                for x, y, label, is_silent in petri_elements['transitions']:
                    # Map transitions to events for display only
                    transition_to_event = {
                        't_2': 'UE', 't_3': 'RA', 't_5': 'G', 't_6': 'O',
                        't_8': 'PT', 't_10': 'FS', 't_11': 'AP'
                    }
                    
                    event_name = transition_to_event.get(label, '')
                    
                    # Simple coloring: green if executed, otherwise default colors
                    if event_name and event_name in executed_events:
                        color = 'lightgreen'  # Executed transitions
                    else:
                        color = 'black' if is_silent else 'white'  # Default colors
                    
                    square = patches.Rectangle((x-0.15, y-0.15), 0.3, 0.3, 
                                             facecolor=color, edgecolor='black', linewidth=2)
                    ax1.add_patch(square)
                    
                    # Label: show transition name and event mapping
                    label_text = f"{label}"
                    if not is_silent and event_name:
                        label_text += f"\n({event_name})"
                    ax1.text(x, y-0.65, label_text, ha='center', va='top', fontsize=8, fontweight='bold')
                
                # Draw arcs (visual only - no functional meaning for token movement)
                petri_arcs = [
                    ((0.8, 3.5), (1.8, 3.5)),   # p0 -> t_1
                    ((1.8, 3.5), (3.0, 4.4)),   # t_1 -> p1
                    ((1.8, 3.5), (3.0, 2.6)),   # t_1 -> p2
                    ((3.4, 4.5), (4.4, 4.5)),   # p1 -> t_2
                    ((3.4, 2.5), (4.4, 2.5)),   # p2 -> t_3
                    ((4.8, 4.5), (5.8, 4.5)),   # t_2 -> p3
                    ((4.8, 2.5), (5.8, 2.5)),   # t_3 -> p4
                    ((6.2, 4.5), (7.1, 3.7)),   # p3 -> t_4
                    ((6.2, 2.5), (7.1, 3.3)),   # p4 -> t_4
                    ((7.4, 3.5), (8.3, 3.5)),   # t_4 -> p5
                    ((8.7, 3.7), (9.8, 4.4)),   # p5 -> t_5
                    ((8.7, 3.3), (9.8, 2.6)),   # p5 -> t_6
                    ((10.2, 4.5), (11.3, 3.7)), # t_5 -> p6
                    ((10.2, 2.5), (11.3, 3.3)), # t_6 -> p6
                    ((11.7, 3.5), (12.6, 3.5)), # p6 -> t_7
                    ((12.9, 3.5), (13.8, 4.4)), # t_7 -> p7
                    ((16.4, 2.5), (15.4, 2.5)), # t_10 -> p9
                    ((14.2, 4.5), (15.0, 4.5)), # p7 -> t_8
                    ((15.3, 4.5), (16.3, 4.5)), # t_8 -> p8
                    ((16.7, 4.5), (17.3, 3.7)), # p8 -> t_9
                    ((16.5, 4.3), (16.5, 2.5)), # p8 -> t_10
                    ((14.8, 2.5), (14.2, 2.5)), # p9 -> t_11
                    ((14, 2.5), (14.0, 4.3)), # t_11 -> p7
                    ((17.7, 3.5), (18.3, 3.5))  # t_9 -> p10
                ]
                
                for (x1, y1), (x2, y2) in petri_arcs:
                    ax1.annotate('', xy=(x2, y2), xytext=(x1, y1),
                               arrowprops=dict(arrowstyle='->', color='gray', lw=1.2, alpha=0.7))
                
                ax1.set_xticks([])
                ax1.set_yticks([])
                ax1.grid(True, alpha=0.3)
                
                # Goal Model (unchanged from original)
                ax2.set_title("Goal Model Structure", fontsize=16, fontweight='bold', pad=20)
                layout = Layout(model)
                ax2.set_xlim(0, layout.max[0])
                ax2.set_ylim(0, layout.max[1])
                ax2.set_aspect('equal')
                
                positions = layout.positions
                shapes = {}
                
                for element_id, (x, y) in positions.items():
                    color = get_status_color_from_your_model(element_id)
                    
                    if model._get_element_type(element_id) == "Quality":
                        cloud = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8, 
                                            boxstyle="roundtooth, pad=0.6, tooth_size=0.5", 
                                            facecolor=color, edgecolor='black', linewidth=2)
                        ax2.add_patch(cloud)
                        shapes[element_id] = cloud
                        status_text = f"{element_id}\n{model._format_status(model.qualities[element_id])}"
                        ax2.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10, zorder=10)
                    elif model._get_element_type(element_id) == "Goal":
                        ellipse = patches.Ellipse((x, y), 1.0, 0.6, 
                                                facecolor=color, edgecolor='black', linewidth=2)
                        ax2.add_patch(ellipse)
                        shapes[element_id] = ellipse
                        status_text = f"{element_id}\n{model._format_status(model.goals[element_id])}"
                        ax2.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10)
                    else:
                        hexagon = patches.RegularPolygon((x, y), 6, radius=0.5, 
                                                    facecolor=color, edgecolor='black', linewidth=2)
                        ax2.add_patch(hexagon)
                        shapes[element_id] = hexagon
                        status_text = f"{element_id}\n{model._format_status(model.tasks[element_id])}"
                        ax2.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10)
                
                # Draw links
                for parent, child, link_type, _ in model.links:
                    if link_type == LinkType.MAKE:
                        arrow_color = 'green'
                        style = '->'
                    elif link_type == LinkType.BREAK:
                        arrow_color = 'red'
                        style = '->'
                    elif link_type == LinkType.AND:
                        arrow_color = 'purple'
                        style = '|-|,widthA=0,widthB=0.5'
                    elif link_type == LinkType.OR:
                        arrow_color = 'orange'
                        style = '->'
                    else:
                        arrow_color = 'blue'
                        style = '->'
                    
                    connector_arrow = patches.FancyArrowPatch(
                        posA=positions[child], posB=positions[parent],
                        patchA=shapes[child], patchB=shapes[parent],
                        arrowstyle=style, color=arrow_color, linewidth=4,
                        shrinkB=2 if link_type != LinkType.AND else 20, mutation_scale=20)
                    ax2.add_patch(connector_arrow)
                
                ax2.set_xticks([])
                ax2.set_yticks([])
                ax2.grid(True, alpha=0.3)
                
                # Mapping Table
                ax3.set_title("Process Transition to Goal Element Mapping", fontsize=14, fontweight='bold', pad=15)
                ax3.axis('off')
                
                transitions = ['t_1', 't_2', 't_3', 't_4', 't_5', 't_6', 't_7', 't_8', 't_9', 't_10', 't_11']
                elements = ['', 'UE', 'RA', '', 'G', 'O', '', 'PT', '', 'FS', 'AP']
                
                table = ax3.table(cellText=[transitions, elements],
                                rowLabels=['Process Transition', 'Goal Element'],
                                cellLoc='center', loc='center',
                                colWidths=[0.08] * len(transitions))
                
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1, 2)
                
                # Style table
                table[(0, -1)].set_facecolor('#4472C4')
                table[(0, -1)].set_text_props(weight='bold', color='white')
                table[(1, -1)].set_facecolor('#4472C4')
                table[(1, -1)].set_text_props(weight='bold', color='white')
                
                for i in range(len(transitions)):
                    if i % 2 == 0:
                        table[(0, i)].set_facecolor('#F2F2F2')
                        table[(1, i)].set_facecolor('#F2F2F2')
                    else:
                        table[(0, i)].set_facecolor('white')
                        table[(1, i)].set_facecolor('white')
                
                plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.35)
                plt.show()
                
        finally:
            _update_state['updating'] = False
            
            # Handle any pending updates
            if _update_state['pending_update']:
                _update_state['pending_update'] = False
                import threading
                threading.Timer(0.1, safe_update_visualization).start()
            
            if handler_debug:
                print("DEBUG: safe_update_visualization() completed - Render finished")

    # Modified event handlers
    def execute_event_handler(b):
        global model, executed_events, petri_tokens
        
        if getattr(execute_button, '_processing', False):
            if handler_debug:
                print("Preventing duplicate execution")
            return
            
        execute_button._processing = True
        execute_button.disabled = True
        
        try:
            selected_event = process_dropdown.value
            dropdown_events = list(model.event_mapping.keys())
            
            if handler_debug:
                print(f"Processing event: {selected_event}")
                print(f"Available events: {dropdown_events}")
                print(f"Event index: {dropdown_events.index(selected_event) if selected_event in dropdown_events else 'Not found'}")
            
            update_status_info(f"Executing event: {selected_event}...")
            
            # Process the event in the goal model
            executed_events.append(selected_event)
            model.process_event(selected_event)
            
            # Update Petri net tokens using direct mapping
            update_petri_tokens(selected_event)
            
            if handler_debug:
                print(f"After token update: {petri_tokens}")
            
            # Update displays
            update_trace()
            update_token_status()
            safe_update_visualization()
            update_status_info(f"Event {selected_event} completed successfully")
            
        except Exception as e:
            update_status_info(f"Error executing event: {str(e)}")
            if handler_debug:
                print(f"Error in event execution: {e}")
        finally:
            execute_button._processing = False
            execute_button.disabled = False

    def reset_model_handler(b):
        global model, executed_events, petri_tokens
        
        if getattr(reset_button, '_processing', False):
            return
            
        reset_button._processing = True
        reset_button.disabled = True
        
        try:
            update_status_info("Resetting model...")
            
            model = create_model_from_your_code()
            executed_events = []
            petri_tokens = {}  # Reset tokens to empty
            
            if handler_debug:
                print("Model reset - tokens cleared")
                print(f"Reset petri_tokens: {petri_tokens}")
            
            update_trace()
            update_token_status()
            safe_update_visualization()
            update_status_info("Model reset to initial state")
            
        except Exception as e:
            update_status_info(f"Error resetting model: {str(e)}")
            if handler_debug:
                print(f"Error in reset: {e}")
        finally:
            reset_button._processing = False
            reset_button.disabled = False

    # Attach event handlers
    execute_button.on_click(execute_event_handler)
    reset_button.on_click(reset_model_handler)
    
    # Main layout - Horizontal split (20% controls, 80% content)
    main_layout = widgets.HBox([
        controls_panel,
        content_area
    ], layout=widgets.Layout(width='100%'))
    
    # Complete interface
    complete_interface = widgets.VBox([
        header,
        legend,
        main_layout,
        status_output if debug_output else widgets.HTML("")
    ])
    
    # Initial updates
    update_trace()
    update_token_status()
    safe_update_visualization()
    
    # Mark interface as created
    interface_created = True
    
    return complete_interface

# Function to reset notebook state
def reset_notebook_state():
    """Reset all global state variables"""
    global interface_created, executed_events, model, handler_debug, petri_tokens
    interface_created = False
    executed_events = []
    petri_tokens = {'p0': 1}  # Reset to initial state with token at p0
    handler_debug = True  # Set to False in production
    if 'model' in globals():
        model = create_model_from_your_code()
    print("Notebook state reset completed")

# Main execution
if __name__ == "__main__":
    reset_notebook_state()
    
    if not interface_created:
        interface = create_complete_interface()
        display(interface)
        interface_created = True
        print("Interface created and displayed!")
    
    else:
        print("Interface already created. Run reset_notebook_state() to recreate.")

# %%