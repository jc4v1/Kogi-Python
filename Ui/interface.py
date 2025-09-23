import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from datetime import datetime

from Ui.Layout import Layout  # Adjust if your Layout is elsewhere

def get_status_color_from_model(model, element_id):
    from NewSemantics.enums import ElementStatus, QualityStatus
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

def create_interface(model, petri_net, debug=False):
    """
    Creates the complete airline process interface as a widget.
    All graphical and interactive logic is encapsulated here.
    """
    executed_events = []
    petri_tokens = {petri_net.initial_place(): 1}
    # Header
    header = widgets.HTML(f"""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h1 style='color: #2E86AB; margin-bottom: 10px;'>A unified view - Interactive High-Level Business Requirements Evaluation</h1>
        <p style='font-size: 14px; color: #666;'>Using GoalModel class from: NewSemantics</p>
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

    # Output widgets
    trace_output = widgets.Output()
    status_output = widgets.Output()
    viz_output = widgets.Output()
    debug_output = widgets.Output() if debug else None

    # Controls Panel
    options = petri_net.transition_names()
    process_dropdown = widgets.Dropdown(
        options=options,
        value=options[0],
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

    token_status = widgets.HTML(
        value="<b>Tokens:</b><br>No tokens (execute events to see tokens)",
        layout=widgets.Layout(width='100%', margin='10px 0px')
    )

    status_info = widgets.HTML(
        value="<b>Status:</b><br>Ready to execute events",
        layout=widgets.Layout(width='100%', margin='10px 0px')
    )

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

    content_area = widgets.VBox([
        viz_output
    ], layout=widgets.Layout(width='80%', padding='0 0 0 15px'))

    _update_state = {'updating': False, 'pending_update': False}

    def update_trace():
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
        token_text = "<b>Tokens:</b><br>"
        if petri_tokens:
            for place, count in sorted(petri_tokens.items()):
                token_text += f"{place}: {count}<br>"
        else:
            token_text += "No tokens (execute events to see tokens)"
        token_status.value = token_text

    def update_status_info(message=""):
        if message:
            status_info.value = f"<b>Status:</b><br>{message}"
        else:
            status_info.value = "<b>Status:</b><br>Ready to execute events"

    def safe_update_visualization():
        if _update_state['updating']:
            _update_state['pending_update'] = True
            return

        _update_state['updating'] = True
        _update_state['pending_update'] = False

        try:
            if debug:
                print("DEBUG: safe_update_visualization() called - Starting render")
                print(f"Current petri_tokens: {petri_tokens}")

            with viz_output:
                clear_output(wait=True)
                fig = plt.figure(figsize=(18, 16))
                gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1.2, 0.4], hspace=0.35)
                ax1 = fig.add_subplot(gs[0, 0])  # Petri net
                ax2 = fig.add_subplot(gs[1, 0])  # Goal model
                ax3 = fig.add_subplot(gs[2, 0])  # Mappings

                # PETRI NET visualization
                ax1.set_title("Process Model (Petri Net) - Direct Token Placement", fontsize=16, fontweight='bold', pad=20)
                min_, max_ = petri_net.min_max()
                ax1.set_xlim(min_[0]-1, max_[0]+1)
                ax1.set_ylim(min_[1]-1, max_[1]+1)
                ax1.set_aspect('equal')

                from builtins import max as fmax
                font_scale = 17/fmax(max_[0] - min_[0], max_[1] - min_[1])
                font_size = 9*font_scale

                petri_elements = petri_net.positions
                nodes = {}
                shapes = {}

                # Draw places with tokens
                for x, y, label in petri_elements['places']:
                    nodes[label] = (x, y)
                    edgecolor = 'red' if label in petri_tokens else 'black'
                    circle = patches.Circle((x, y), 0.25, facecolor='white', edgecolor=edgecolor, linewidth=2)
                    shapes[label] = circle
                    ax1.add_patch(circle)
                    token_count = petri_tokens.get(label, 0)
                    if token_count > 0:
                        if token_count == 1:
                            token = patches.Circle((x, y), 0.08, facecolor='red', edgecolor='red')
                            ax1.add_patch(token)
                        else:
                            for i in range(min(token_count, 4)):
                                offset_x = 0.1 * (i % 2 - 0.5)
                                offset_y = 0.1 * (i // 2 - 0.5)
                                token = patches.Circle((x + offset_x, y + offset_y), 0.05, facecolor='red', edgecolor='red')
                                ax1.add_patch(token)
                            if token_count > 4:
                                ax1.text(x, y-0.15, f"{token_count}", ha='center', va='center', fontsize=8, fontweight='bold', color='red')
                    ax1.text(x, y-0.4, label, ha='center', va='top', fontsize=font_size, fontweight='bold')

                # Draw transitions
                for x, y, label, event_name in petri_elements['transitions']:
                    is_silent = event_name is None
                    nodes[label] = (x, y)
                    color = 'lightgreen' if executed_events and label == executed_events[-1] else ('black' if is_silent else 'white')
                    square = patches.Rectangle((x-0.15, y-0.15), 0.3, 0.3, facecolor=color, edgecolor='black', linewidth=2)
                    shapes[label] = square
                    ax1.add_patch(square)
                    label_text = f"{label}"
                    if not is_silent and event_name:
                        label_text += f"\n({event_name})"
                    ax1.text(x, y-0.35, label_text, ha='center', va='top', fontsize=8*font_scale, fontweight='bold')

                for arc in petri_net.net.arcs:
                    x1, y1 = nodes[arc.source.name]
                    x2, y2 = nodes[arc.target.name]
                    connector_arrow = patches.FancyArrowPatch(
                        posA=(x1, y1), posB=(x2, y2),
                        patchA=shapes[arc.source.name], patchB=shapes[arc.target.name],
                        arrowstyle='->', color='gray', linewidth=1.2, alpha=0.7,
                        shrinkB=0, mutation_scale=10)
                    ax1.add_patch(connector_arrow)

                ax1.set_xticks([])
                ax1.set_yticks([])
                ax1.grid(True, alpha=0.3)

                # Goal Model visualization
                ax2.set_title("Goal Model Structure", fontsize=16, fontweight='bold', pad=20)
                layout = Layout(model)
                ax2.set_xlim(0, layout.max[0])
                ax2.set_ylim(0, layout.max[1])
                ax2.set_aspect('equal')
                font_scale = 10/fmax(layout.max[0], layout.max[1])
                positions = layout.positions
                shapes = {}

                for element_id, (x, y) in positions.items():
                    color = get_status_color_from_model(model, element_id)
                    if model._get_element_type(element_id) == "Quality":
                        cloud = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8,
                                              boxstyle="roundtooth, pad=0.6, tooth_size=0.5",
                                              facecolor=color, edgecolor='black', linewidth=2)
                        ax2.add_patch(cloud)
                        shapes[element_id] = cloud
                        status_text = f"{element_id}\n{model._format_status(model.qualities[element_id])}"
                        ax2.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10*font_scale, zorder=10)
                    elif model._get_element_type(element_id) == "Goal":
                        ellipse = patches.Ellipse((x, y), 1.0, 0.6,
                                                  facecolor=color, edgecolor='black', linewidth=2)
                        ax2.add_patch(ellipse)
                        shapes[element_id] = ellipse
                        status_text = f"{element_id}\n{model._format_status(model.goals[element_id])}"
                        ax2.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10*font_scale)
                    else:
                        hexagon = patches.RegularPolygon((x, y), 6, radius=0.5,
                                                         facecolor=color, edgecolor='black', linewidth=2)
                        ax2.add_patch(hexagon)
                        shapes[element_id] = hexagon
                        status_text = f"{element_id}\n{model._format_status(model.tasks[element_id])}"
                        ax2.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10*font_scale)

                # for parent, child, link_type, _ in model.links:
                #     arrow_color = {
                #         "MAKE": 'green',
                #         "BREAK": 'red',
                #         "AND": 'purple',
                #         "OR": 'orange'
                #     }.get(link_type.name if hasattr(link_type, 'name') else link_type, 'blue')
                #     style = '->'
                #     connector_arrow = patches.FancyArrowPatch(
                #         posA=positions[child], posB=positions[parent],
                #         patchA=shapes[child], patchB=shapes[parent],
                #         arrowstyle=style, color=arrow_color, linewidth=4,
                #         shrinkB=2 if link_type != "AND" else 20, mutation_scale=20)
                #     ax2.add_patch(connector_arrow)

                for parent, child, link_type, _ in model.links:
                    if link_type.name == "MAKE":
                        arrow_color = 'green'
                        style = '->'
                    elif link_type.name == "BREAK":
                        arrow_color = 'red'
                        style = '->'
                    elif link_type.name == "AND":
                        arrow_color = 'purple'
                        style = '|-|,widthA=0,widthB=0.5'
                    elif link_type.name == "OR":
                        arrow_color = 'orange'
                        style = '->'
                    else:
                        arrow_color = 'blue'
                        style = '->'
                    
                    connector_arrow = patches.FancyArrowPatch(
                        posA=positions[child], posB=positions[parent],
                        patchA=shapes[child], patchB=shapes[parent],
                        arrowstyle=style, color=arrow_color, linewidth=4,
                        shrinkB=2 if link_type.name != "AND" else 20, mutation_scale=20)
                    ax2.add_patch(connector_arrow)

                ax2.set_xticks([])
                ax2.set_yticks([])
                ax2.grid(True, alpha=0.3)

                # Mapping Table
                ax3.set_title("Process Transition to Goal Element Mapping", fontsize=14, fontweight='bold', pad=15)
                ax3.axis('off')
                mapping = model.event_mapping
                transitions = sorted(list(mapping.keys()))
                elements = ['' if not mapping[k] else mapping[k][0][0] for k in transitions]
                table = ax3.table(cellText=[transitions, elements],
                                  rowLabels=['Process Transition', 'Goal Element'],
                                  cellLoc='center', loc='center',
                                  colWidths=[0.08] * len(transitions))
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1, 2)
                plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.35)
                plt.show()
        finally:
            _update_state['updating'] = False
            if _update_state['pending_update']:
                _update_state['pending_update'] = False
                import threading
                threading.Timer(0.1, safe_update_visualization).start()
            if debug:
                print("DEBUG: safe_update_visualization() completed - Render finished")

    def update_petri_tokens(event_name):
        transitions = petri_net.transitions()
        actions = transitions[event_name]
        if not all(p in petri_tokens for p in actions[0]):
            raise Exception(f"One of {actions[0]} is missing a token")
        for p in actions[0]:
            petri_tokens.pop(p, None)
        for p in actions[1]:
            petri_tokens[p] = 1

    def execute_event_handler(b):
        selected_event = process_dropdown.value
        try:
            update_status_info(f"Executing event: {selected_event}...")
            executed_events.append(selected_event)
            model.process_event(selected_event)
            update_petri_tokens(selected_event)
            update_trace()
            update_token_status()
            safe_update_visualization()
            update_status_info(f"Event {selected_event} completed successfully")
        except Exception as e:
            update_status_info(f"Error executing event: {str(e)}")
            if debug:
                print(f"Error in event execution: {e}")

    def reset_model_handler(b):
        executed_events.clear()
        petri_tokens.clear()
        petri_tokens.update({petri_net.initial_place(): 1})
        model.reset()
        update_trace()
        update_token_status()
        safe_update_visualization()
        update_status_info("Model reset to initial state")

    execute_button.on_click(execute_event_handler)
    reset_button.on_click(reset_model_handler)

    main_layout = widgets.HBox([
        controls_panel,
        content_area
    ], layout=widgets.Layout(width='100%'))

    complete_interface = widgets.VBox([
        header,
        legend,
        main_layout,
        status_output if debug_output else widgets.HTML("")
    ])

    update_trace()
    update_token_status()
    safe_update_visualization()

    return complete_interface

def reset_notebook_state(model, petri_net):
    """
    Resets any global or notebook state if needed.
    """
    # Implement your reset logic here if required
    pass