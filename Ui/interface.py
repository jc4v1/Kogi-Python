import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from datetime import datetime
from Ui.Layout import Layout
from Semantics.enums import LinkType
from Semantics.transition_system import combine_goal_model_and_petri_net
from Semantics.transition_system import CombinedTransitionSystem
from Semantics.petri_net import PetriNet
from typing import Any
import re

def get_status_color_from_model(model, element_id):
    from Semantics.enums import ElementStatus, QualityStatus
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

def whitespace_to_newlines(s: str) -> str:
    if s is None:
        return s
    if '@' in s:
        return s.replace('@ ', '\n')
    return re.sub(r'\s+', '\n', s)

class InterfaceBuilder:
    def __init__(self, model, petri_net: PetriNet | None = None, event_mapping = None, whatif=False, debug=False):
        self.model = model
        if event_mapping is not None:
            self.model.event_mapping = event_mapping
        self.petri_net = petri_net
        self.debug = debug
        self.whatif = whatif
        if self.petri_net is None and not self.whatif:
            raise Exception("Petri net must be provided if whatif is False")
        if self.whatif and self.petri_net is None:
            self.petri_net = self.model.generate_all_events_petri_net()
        self.executed_events = []
        self.petri_tokens = {self.petri_net.initial_place(): 1}
        self._update_state = {'updating': False, 'pending_update': False}

        # Widgets
        self.header = widgets.HTML(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h1 style='color: #2E86AB; margin-bottom: 10px;'>A unified view - Interactive High-Level Business Requirements Evaluation</h1>
            <p style='font-size: 14px; color: #666;'>Using GoalModel class from: Semantics</p>
            <p style='font-size: 12px; color: #888;'>Last Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        """)

        self.legend = widgets.HTML("""
        <div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 12px; border: 1px solid #ccc;'>
        <div style='font-weight: bold; margin-bottom: 8px; text-align: center;'>Conventions</div>
        <div><strong>Goal Model Colors:</strong> 🤍 Unknown | 🟢 Satisfied/Fulfilled | 🔵 Executed Pending | 🔴 Denied</div>
        <div><strong>Shapes:</strong> ☁️ Quality | ⭕ Goal | ⬡ Task | ⬜ Process Transition</div>
        <div><strong>Petri Net:</strong> ⚫ Token | ⚪ Place | ⬛ Transition </div>
        </div>
        """)

        self.trace_output = widgets.Output()
        self.status_output = widgets.Output()
        self.viz_output = widgets.Output()
        self.debug_output = widgets.Output() if debug else None

        options = self.petri_net.transition_names()
        self.process_dropdown = widgets.Dropdown(
            options=options,
            value=options[0],
            description='Event:',
            disabled=False,
            layout=widgets.Layout(width='100%', margin='5px 0px')
        )

        self.execute_button = widgets.Button(
            description='Execute Event',
            disabled=False,
            button_style='success',
            tooltip='Execute the selected event',
            layout=widgets.Layout(width='100%', margin='5px 0px')
        )

        self.reset_button = widgets.Button(
            description='Reset Model',
            disabled=False,
            button_style='warning',
            tooltip='Reset the model to initial state',
            layout=widgets.Layout(width='100%', margin='5px 0px')
        )

        # Add new buttons for stability and weak compliance
        self.check_stability_button = widgets.Button(
            description='Check Stability',
            disabled=False,
            button_style='info',
            tooltip='Check stability for the goal model qualities',
            layout=widgets.Layout(width='100%', margin='5px 0px')
        )

        self.check_weak_compliance_button = widgets.Button(
            description='Check Weak Compliance',
            disabled=False,
            button_style='info',
            tooltip='Check weak compliance for the goal model qualities',
            layout=widgets.Layout(width='100%', margin='5px 0px')
        )

        # Attach handlers
        self.check_stability_button.on_click(self.check_stability_handler)
        self.check_weak_compliance_button.on_click(self.check_weak_compliance_handler)

        self.token_status = widgets.HTML(
            value="<b>Tokens:</b><br>No tokens (execute events to see tokens)",
            layout=widgets.Layout(width='100%', margin='10px 0px')
        )

        self.status_info = widgets.HTML(
            value="<b>Status:</b><br>Ready to execute events",
            layout=widgets.Layout(width='100%', margin='10px 0px')
        )

        # Dropdown for failed markings (initially hidden)
        self.failed_markings_dropdown = widgets.Dropdown(
            options=[],
            description='Failed marking:',
            disabled=True,
            layout=widgets.Layout(width='100%', margin='5px 0px')
        )
        self.failed_markings_dropdown.observe(self.on_failed_marking_selected, names='value')

        self._last_failed_markings: list[Any] = []

        self.controls_panel = widgets.VBox([
            widgets.HTML("<h3 style='margin: 0 0 15px 0; color: #2E86AB;'>Controls</h3>"),
            self.process_dropdown,
            self.execute_button,
            self.check_stability_button,
            self.check_weak_compliance_button,
            self.reset_button,
            widgets.HTML("<hr style='margin: 15px 0;'>"),
            self.token_status,
            self.status_info,
            self.failed_markings_dropdown,
            self.trace_output
        ], layout=widgets.Layout(
            width='18%',
            padding='15px',
            border='1px solid #ddd',
            border_radius='5px',
            background_color='#fafafa'
        ))

        self.content_area = widgets.VBox([
            self.viz_output
        ], layout=widgets.Layout(width='80%', padding='0 0 0 15px'))

        self.main_layout = widgets.HBox([
            self.controls_panel,
            self.content_area
        ], layout=widgets.Layout(width='100%'))

        self.complete_interface = widgets.VBox([
            self.header,
            self.legend,
            self.main_layout,
            self.status_output if self.debug_output else widgets.HTML("")
        ])

        # Attach event handlers
        self.execute_button.on_click(self.execute_event_handler)
        self.reset_button.on_click(self.reset_model_handler)

        # Initial updates
        self.update_trace()
        self.update_token_status()
        self.safe_update_visualization()

    def update_trace(self):
        with self.trace_output:
            clear_output(wait=True)
            trace_html = """
            <div style='margin-top: 15px; padding: 10px; border: 1px solid #ccc; border-radius: 3px; background-color: white; font-size: 11px;'>
                <div style='font-weight: bold; margin-bottom: 8px; color: #2E86AB;'>Execution Trace</div>
            """
            if not self.executed_events:
                trace_html += "<div style='color: #666; font-style: italic;'>No events executed</div>"
            else:
                trace_html += "<div style='word-wrap: break-word;'>"
                trace_html += "<span style='color: #666;'>trace ⟨</span>"
                for i, event in enumerate(self.executed_events):
                    if i > 0:
                        trace_html += "<span style='color: #666;'>, </span>"
                    trace_html += f"<span style='color: #2E86AB; font-weight: bold;'>{event}</span>"
                trace_html += "<span style='color: #666;'>⟩</span></div>"
            trace_html += "</div>"
            display(HTML(trace_html))

    def update_token_status(self):
        token_text = "<b>Tokens:</b><br>"
        if self.petri_tokens:
            for place, count in sorted(self.petri_tokens.items()):
                token_text += f"{place}: {count}<br>"
        else:
            token_text += "No tokens (execute events to see tokens)"
        self.token_status.value = token_text

    def update_status_info(self, message=""):
        if message:
            self.status_info.value = f"<b>Status:</b><br>{message}"
        else:
            self.status_info.value = "<b>Status:</b><br>Ready to execute events"

    def safe_update_visualization(self):
        if self._update_state['updating']:
            self._update_state['pending_update'] = True
            return
    
        self._update_state['updating'] = True
        self._update_state['pending_update'] = False
    
        try:
            if self.debug:
                print("DEBUG: safe_update_visualization() called - Starting render")
                print(f"Current petri_tokens: {self.petri_tokens}")
    
            with self.viz_output:
                clear_output(wait=True)
                fig = plt.figure(figsize=(18, 16))
                if not self.whatif:
                    gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 1.2, 0.4], hspace=0.35)
                else: 
                    gs = fig.add_gridspec(1, 1, height_ratios=[1], hspace=0.35)   
                ax1 = fig.add_subplot(gs[0, 0]) if not self.whatif else None # Petri net
                ax2 = fig.add_subplot(gs[1, 0]) if not self.whatif else fig.add_subplot(gs[0,0]) # Goal model
                ax3 = fig.add_subplot(gs[2, 0]) if not self.whatif else None # Mappings
    
                self._draw_petri_net(ax1) if not self.whatif else None
                self._draw_goal_model(ax2)
                self._draw_mapping_table(ax3) if not self.whatif else None
    
                plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.35)
                plt.show()
        finally:
            self._update_state['updating'] = False
            if self._update_state['pending_update']:
                self._update_state['pending_update'] = False
                import threading
                threading.Timer(0.1, self.safe_update_visualization).start()
            if self.debug:
                print("DEBUG: safe_update_visualization() completed - Render finished")
    
    def _draw_petri_net(self, ax1):
        min_, max_ = self.petri_net.min_max()
        ax1.set_title("Process Model (Petri Net) - Direct Token Placement", fontsize=16, fontweight='bold', pad=20)
        ax1.set_xlim(min_[0]-1, max_[0]+1)
        ax1.set_ylim(min_[1]-1, max_[1]+1)
        ax1.set_aspect('equal')
    
        from builtins import max as fmax
        font_scale = 17/fmax(max_[0] - min_[0], max_[1] - min_[1])
        font_size = 9*font_scale
    
        petri_elements = self.petri_net.positions
        nodes = {}
        shapes = {}
    
        # Draw places with tokens
        for x, y, label in petri_elements['places']:
            nodes[label] = (x, y)
            edgecolor = 'red' if label in self.petri_tokens else 'black'
            circle = patches.Circle((x, y), 0.25, facecolor='white', edgecolor=edgecolor, linewidth=2)
            shapes[label] = circle
            ax1.add_patch(circle)
            token_count = self.petri_tokens.get(label, 0)
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
            color = 'lightgreen' if self.executed_events and label == self.executed_events[-1] else ('black' if is_silent else 'white')
            square = patches.Rectangle((x-0.15, y-0.15), 0.3, 0.3, facecolor=color, edgecolor='black', linewidth=2)
            shapes[label] = square
            ax1.add_patch(square)
            label_text = f"{label}"
            if not is_silent and event_name:
                label_text += f"\n({whitespace_to_newlines(event_name)})"
            ax1.text(x, y-0.35, label_text, ha='center', va='top', fontsize=8*font_scale, fontweight='bold')
    
        for arc in self.petri_net.net.arcs:
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
    
    def _draw_goal_model(self, ax2):
        from matplotlib.patches import FancyBboxPatch
        import math
    
        ax2.set_title("Goal Model Structure", fontsize=16, fontweight='bold', pad=20)
        layout = Layout(self.model)
        ax2.set_xlim(0, layout.max[0])
        ax2.set_ylim(0, layout.max[1])
        ax2.set_aspect('equal')
        from builtins import max as fmax
        font_scale = 10/fmax(layout.max[0], layout.max[1])
        font_scale = font_scale if not self.whatif else font_scale*3
        positions = layout.positions
        shapes = {}
    
        for element_id, (x, y) in positions.items():
            color = get_status_color_from_model(self.model, element_id)
            if self.model._get_element_type(element_id) == "Quality":
                cloud = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8,
                                      boxstyle="roundtooth, pad=0.6, tooth_size=0.5",
                                      facecolor=color, edgecolor='black', linewidth=2)
                ax2.add_patch(cloud)
                shapes[element_id] = cloud
                status_text = f"{whitespace_to_newlines(element_id)}\n{self.model._format_status(self.model.qualities[element_id])}"
                ax2.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10*font_scale, zorder=10)
            elif self.model._get_element_type(element_id) == "Goal":
                ellipse = patches.Ellipse((x, y), 1.0, 0.6,
                                          facecolor=color, edgecolor='black', linewidth=2)
                ax2.add_patch(ellipse)
                shapes[element_id] = ellipse
                status_text = f"{whitespace_to_newlines(element_id)}\n{self.model._format_status(self.model.goals[element_id])}"
                ax2.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10*font_scale)
            else:
                hexagon = patches.RegularPolygon((x, y), 6, radius=0.5,
                                                 facecolor=color, edgecolor='black', linewidth=2)
                ax2.add_patch(hexagon)
                shapes[element_id] = hexagon
                status_text = f"{whitespace_to_newlines(element_id)}\n{self.model._format_status(self.model.tasks[element_id])}"
                ax2.text(x, y, status_text, ha='center', va='center', fontweight='bold', fontsize=10*font_scale)
    
        # Draw links (with AND as perpendicular bar)
        for parent, child, link_type, _ in self.model.links:
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
    
    def _draw_mapping_table(self, ax3):
        ax3.set_title("Process Transition to Goal Element Mapping", fontsize=14, fontweight='bold', pad=15)
        ax3.axis('off')
        mapping = self.model.event_mapping
        transitions = sorted(list(mapping.keys()))
        elements = ['' if not mapping[k] else whitespace_to_newlines(mapping[k][0][0]) for k in transitions]
        table = ax3.table(cellText=[transitions, elements],
                          rowLabels=['Process Transition', 'Goal Element'],
                          cellLoc='center', loc='center',
                          colWidths=[0.08] * len(transitions))
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)

    def update_petri_tokens(self, event_name):
        transitions = self.petri_net.transitions()
        actions = transitions[event_name]
        if not all(p in self.petri_tokens for p in actions[0]):
            raise Exception(f"One of {actions[0]} is missing a token")
        for p in actions[0]:
            self.petri_tokens.pop(p, None)
        for p in actions[1]:
            self.petri_tokens[p] = 1

    def execute_event_handler(self, b):
        selected_event = self.process_dropdown.value
        try:
            self.update_status_info(f"Executing event: {selected_event}...")
            self.update_petri_tokens(selected_event)
            self.model.process_event(selected_event)
            self.executed_events.append(selected_event)
            self.update_trace()
            self.update_token_status()
            self.safe_update_visualization()
            self.update_status_info(f"Event {selected_event} completed successfully")
        except Exception as e:
            self.update_status_info(f"Error executing event: {str(e)}")
            if self.debug:
                print(f"Error in event execution: {e}")

    def reset_model_handler(self, b):
        self.executed_events.clear()
        self.petri_tokens.clear()
        self.petri_tokens.update({self.petri_net.initial_place(): 1})
        self.model.reset()
        self.update_trace()
        self.update_token_status()
        self.safe_update_visualization()
        self.update_status_info("Model reset to initial state")
        self.failed_markings_dropdown.options = []
        self.failed_markings_dropdown.disabled = True
        self._last_failed_markings = []
        
    def check_stability_handler(self, b):
        try:
            self.update_status_info("Checking stability...")
            self.executed_events.clear()
            self.model.reset()
            self.petri_tokens = {self.petri_net.initial_place(): 1}
            lts = combine_goal_model_and_petri_net(self.model, self.petri_net,self.model.event_mapping)
            result = lts.check_stability(list(self.model.qualities.keys()))
            if result.is_ok():
                self.update_status_info("Stability check: TRUE")
                self.failed_markings_dropdown.options = []
                self.failed_markings_dropdown.disabled = True
                self._last_failed_markings = []
            else:
                failed = sorted(result.failing_states)
                self.update_status_info(f"Stability check: FALSE ({len(failed)} failed states)")
                self.failed_markings_dropdown.options = [
                    (str(failed[i]), i) for i in range(len(failed))
                ]
                self.failed_markings_dropdown.disabled = False
                self._last_failed_markings = sorted(failed)
        except Exception as e:
            self.update_status_info(f"Error checking stability: {str(e)}")
            self.failed_markings_dropdown.options = []
            self.failed_markings_dropdown.disabled = True
            self._last_failed_markings = []
        finally:
            self.update_trace()
            self.update_token_status()
            self.safe_update_visualization()


    def check_weak_compliance_handler(self, b):
        try:
            self.update_status_info("Checking weak compliance...")
            self.executed_events.clear()
            self.model.reset()
            self.petri_tokens = {self.petri_net.initial_place(): 1}
            lts = combine_goal_model_and_petri_net(self.model, self.petri_net,self.model.event_mapping)
            result = lts.check_weak_compliance(list(self.model.qualities.keys()))
            if result.is_ok():
                self.update_status_info("Weak compliance: TRUE")
                self.failed_markings_dropdown.options = []
                self.failed_markings_dropdown.disabled = True
                self._last_failed_markings = []
            else:
                failed = sorted(result.failing_states)
                self.update_status_info(f"Weak compliance: FALSE ({len(failed)} failed states)")
                self.failed_markings_dropdown.options = [
                    (str(failed[i]), i) for i in range(len(failed))
                ]
                self.failed_markings_dropdown.disabled = False
                self._last_failed_markings = failed
        except Exception as e:
            self.update_status_info(f"Error checking weak compliance: {str(e)}")
            self.failed_markings_dropdown.options = []
            self.failed_markings_dropdown.disabled = True
            self._last_failed_markings = []
        finally:
            self.update_trace()
            self.update_token_status()
            self.safe_update_visualization()

    def on_failed_marking_selected(self, change):
        if change['type'] == 'change' and change['name'] == 'value':
            idx = change['new']
            if idx is None or not self._last_failed_markings:
                return
            marking = self._last_failed_markings[idx]
            # Expect marking to be a tuple: (goal_model_status_dict, petri_tokens_dict)
            goal_status, petri_tokens = marking.gm_marking, marking.pn_marking
            # Set goal model status
            self.model.set_markings(goal_status.markings())
            # Set petri tokens
            self.petri_tokens.clear()
            self.petri_tokens.update({ p:v for p,v in petri_tokens.markings().items() if v > 0 })
            self.update_trace()
            self.update_token_status()
            self.safe_update_visualization()
            self.update_status_info("Set to selected failed marking.")

    def create_interface(self):
        return self.complete_interface
    
class WhatIfInterfaceBuilder(InterfaceBuilder):
    def __init__(self, model, debug=False):
        super().__init__(model, None, event_mapping=None,whatif=True, debug=debug)

# For non-interactive analysis
def analyse_models(goal_model, process_model, event_mapping):
    lts_gm = goal_model.as_transition_system()
    print(f"Goal Model LTS reachable states and transitions: {lts_gm.size()}")

    lts_pn = process_model.as_transition_system()
    print(f"Process Model LTS reachable states and transitions: {lts_pn.size()}")   
    lts_combined = CombinedTransitionSystem(lts_gm, lts_pn, event_mapping)  
    print(f"Combined LTS reachable states and transitions: {lts_combined.size()}")
    print()
    
    print(f"Goal Model Goals and Tasks: {goal_model.goals_and_tasks()}")
    print(f"Goal Model Qualities: {set(goal_model.qualities.keys())}")
    print()
    print(f"Combined LTS Actions: {lts_combined.actions()}")
    print()
    print(f"Event Mapping {event_mapping}")
    print()
    
    stability = lts_combined.check_stability(goal_model.qualities)
    print(f"Stability: {stability}")

    weak_compliance = lts_combined.check_weak_compliance(goal_model.qualities)
    print(f"Weak Compliance: {weak_compliance}")


def _create_upload_widgets():
    ug = widgets.FileUpload(accept='.json,.istar,.txt', multiple=False, description='Goal Model')
    up = widgets.FileUpload(accept='.pnml', multiple=False, description='Petri Net')
    um = widgets.FileUpload(accept='.csv', multiple=False, description='Event Mapping (optional)')
    lb = widgets.Button(description='Load Models', button_style='primary')
    st = widgets.HTML("<b>Awaiting files...</b>")
    box = widgets.VBox([
        widgets.HTML('Load models from files'),
        ug,
        up,
        um,
        lb,
        st
    ], layout=widgets.Layout(width='30%', padding='10px', border='1px solid #ddd', background_color='#fafafa'))
    return ug, up, um, lb, st, box


def create_interface_with_file_upload(debug: bool = False):
    """
    Return a widget that asks the user to upload three files: goal model (JSON/iStar),
    Petri net (.pnml) and optional mapping (.csv). After loading the files the
    function will instantiate `InterfaceBuilder` and display the interactive UI.
    """
    import tempfile
    import os

    upload_goal, upload_pn, upload_map, load_button, status, uploader_box = _create_upload_widgets()
    widgets_state = {
        'upload_goal': upload_goal,
        'upload_pn': upload_pn,
        'upload_map': upload_map,
        'load_button': load_button,
        'status': status,
        'uploader_box': uploader_box
    }
    placeholder = widgets.Output()
    debug_area = widgets.Output()

    def _save_upload_to_temp(uploader: widgets.FileUpload, required: bool = False):
        if not uploader.value:
            if required:
                raise Exception('Required file not uploaded')
            return None
        if isinstance(uploader.value, dict):
            key = next(iter(uploader.value))
            entry = uploader.value[key]
            content = entry.get('content')
            filename = key
        else:
            entry = uploader.value[0]
            content = entry.get('content') if isinstance(entry, dict) else entry
            filename = entry.get('name', 'upload') if isinstance(entry, dict) else 'upload'
        suffix = os.path.splitext(filename)[1] or ''
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        if content is None:
            raise Exception('Uploaded file has no content')
        if isinstance(content, str):
            content = content.encode('utf-8')
        tf.write(content)
        tf.flush()
        tf.close()
        return tf.name

    def on_load(b):
        widgets_state['status'].value = "<b>Loading...</b>"
        try:
            goal_path = _save_upload_to_temp(widgets_state['upload_goal'], required=True)
            pn_path = _save_upload_to_temp(widgets_state['upload_pn'], required=True)
            map_path = _save_upload_to_temp(widgets_state['upload_map'], required=False)

            from Semantics.istar_processor import read_istar_model
            from Semantics.petri_net_processor import read_petri_net
            from Semantics.event_mapping_from_csv import read_event_mapping_csv

            goal_model = read_istar_model(goal_path)
            petri_net = read_petri_net(pn_path)

            if map_path:
                mapping = read_event_mapping_csv(map_path)
            else:
                mapping = petri_net.get_default_event_mapping()

            # Debug output: show map file path and resolved mapping
            with debug_area:
                clear_output(wait=True)
                try:
                    from pprint import pformat
                    map_file_display = map_path if map_path else '(inferred from PN)'
                    print(f"Mapping file: {map_file_display}")
                    print("upload_map.value:")
                    print(pformat(widgets_state['upload_map'].value))
                    print("Resolved mapping (transition -> intentional elements):")
                    print(pformat(mapping))
                except Exception as de:
                    print(f"Error displaying mapping debug info: {de}")

            builder = InterfaceBuilder(goal_model, petri_net=petri_net, event_mapping=mapping, debug=debug)

            placeholder.clear_output()
            with placeholder:
                display(builder.complete_interface)

            # Recreate upload widgets so subsequent uses don't reuse previous files/mappings
            new_ug, new_up, new_um, new_lb, new_st, new_box = _create_upload_widgets()
            # update the existing visible box children and the widgets_state
            widgets_state['uploader_box'].children = new_box.children
            widgets_state.update({
                'upload_goal': new_ug,
                'upload_pn': new_up,
                'upload_map': new_um,
                'load_button': new_lb,
                'status': new_st,
                'uploader_box': widgets_state['uploader_box']
            })
            # bind handler to new button
            widgets_state['load_button'].on_click(on_load)

            widgets_state['status'].value = "<b style='color:green'>Loaded successfully.</b>"
        except Exception as e:
            widgets_state['status'].value = f"<b style='color:red'>Error: {str(e)}</b>"

    widgets_state['load_button'].on_click(on_load)

    # Return uploader + debug area + display placeholder
    right_column = widgets.VBox([placeholder, debug_area], layout=widgets.Layout(width='70%'))
    return widgets.HBox([uploader_box, right_column], layout=widgets.Layout(width='100%'))