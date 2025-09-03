

# %%
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def render_corrected_petri_net(executed_events=None, figsize=(20, 8)):
    """
    Render the corrected Petri Net with proper arc connections
    
    Parameters:
    - executed_events: list of executed events to highlight transitions
    - figsize: tuple for figure size (width, height)
    """
    if executed_events is None:
        executed_events = []
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Petri Net setup
    ax.set_title("Corrected Process Model (Petri Net)", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(-1, 19)
    ax.set_ylim(-1, 8)
    ax.set_aspect('equal')
    
    # Define Petri Net elements with corrected positions
    petri_elements = {
        'places': [
            (0.8, 3.5, 'p0'), (3.2, 4.5, 'p1'), (3.2, 2.5, 'p2'),
            (6.0, 4.5, 'p3'), (6.0, 2.5, 'p4'), (8.5, 3.5, 'p5'),
            (11.5, 3.5, 'p6'), (14.0, 4.5, 'p7'), (15.1, 2.5, 'p9'),
            (16.5, 4.5, 'p8'), (18.5, 3.5, 'p10')
        ],
        'transitions': [
            (1.8, 3.5, 't_1', True),    # silent transition (True = silent)
            (4.6, 4.5, 't_2', False),   # labeled transition
            (4.6, 2.5, 't_3', False),   # labeled transition
            (7.25, 3.5, 't_4', True),   # silent transition
            (10.0, 4.5, 't_5', False),  # labeled transition
            (10.0, 2.5, 't_6', False),  # labeled transition
            (12.75, 3.5, 't_7', True),  # silent transition
            (15.1, 4.5, 't_8', False),  # labeled transition
            (17.5, 3.5, 't_9', False),  # labeled transition
            (16.5, 2.5, 't_10', False), # labeled transition
            (14.0, 2.5, 't_11', False)  # labeled transition
        ]
    }
    
    # Draw places
    for x, y, label in petri_elements['places']:
        if label == 'p0':
            # Initial place with token
            circle = patches.Circle((x, y), 0.25, facecolor='white', edgecolor='black', linewidth=2)
            ax.add_patch(circle)
            token = patches.Circle((x, y), 0.08, facecolor='black', edgecolor='black')
            ax.add_patch(token)
        else:
            circle = patches.Circle((x, y), 0.25, facecolor='white', edgecolor='black', linewidth=2)
            ax.add_patch(circle)
        ax.text(x, y-0.5, label, ha='center', va='top', fontsize=9, fontweight='bold')
    
    # Draw transitions
    for x, y, label, is_silent in petri_elements['transitions']:
        event_name = label.replace('_', '')
        
        # Check if this transition has been executed
        if event_name in executed_events or f"e{label.split('_')[1]}" in executed_events:
            if is_silent:
                color = 'lightgreen'  # executed silent transition
            else:
                color = 'lightgreen'  # executed labeled transition
        else:
            if is_silent:
                color = 'black'       # silent transition (black square)
            else:
                color = 'white'       # labeled transition (white square)
        
        square = patches.Rectangle((x-0.15, y-0.15), 0.3, 0.3, 
                                 facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(square)
        
        # Label: show transition name for all transitions
        ax.text(x, y-0.55, label, ha='center', va='top', fontsize=9, fontweight='bold')
    
    # CORRECTED ARCS - Proper flow representation
    corrected_arcs = [
        # Start: p0 -> t_1
        ((0.8, 3.5), (1.8, 3.5)),
        
        # t_1 splits to parallel branches: t_1 -> p1, p2
        ((1.8, 3.5), (3.0, 4.4)),  # t_1 -> p1 (upper)
        ((1.8, 3.5), (3.0, 2.5)),  # t_1 -> p2 (lower)
        
        # Parallel processing: p1 -> t_2, p2 -> t_3
        ((3.4, 4.5), (4.5, 4.5)),  # p1 -> t_2
        ((3.4, 2.5), (4.5, 2.5)),  # p2 -> t_3
        
        # Results: t_2 -> p3, t_3 -> p4
        ((4.8, 4.5), (5.8, 4.5)),  # t_2 -> p3
        ((4.8, 2.5), (5.8, 2.5)),  # t_3 -> p4
        
        # Merge at t_4: p3 -> t_4, p4 -> t_4
        ((6.2, 4.5), (7.25, 3.5)), # p3 -> t_4
        ((6.2, 2.5), (7.25, 3.5)), # p4 -> t_4
        
        # Continue: t_4 -> p5
        ((7.25, 3.5), (8.3, 3.5)), # t_4 -> p5
        
        # Split again: p5 -> t_5, p5 -> t_6
        ((8.7, 3.7), (9.9, 4.5)), # p5 -> t_5
        ((8.7, 3.3), (9.9, 2.4)), # p5 -> t_6
        
        # Merge at p6: t_5 -> p6, t_6 -> p6
        ((10.15, 4.5), (11.35, 3.7)), # t_5 -> p6
        ((10.15, 2.5), (11.35, 3.3)), # t_6 -> p6
        
        # Continue: p6 -> t_7
        ((11.75, 3.5), (12.75, 3.5)), # p6 -> t_7
        
        # Final split: t_7 -> p7, t_7 -> p9
        ((12.75, 3.5), (13.8, 4.5)), # t_7 -> p7
        
        
        # Final processing: p7 -> t_8, p9 -> t_11
        ((14.2, 4.5), (15, 4.5)), # p7 -> t_8
        ((14.9, 2.5), (14.2, 2.5)), # p9 -> t_11
        ((14, 2.7), (14, 4.3)), # t11 -> p7

        # Results: t_8 -> p8, t_11 -> t_10
        ((15.25, 4.5), (16.3, 4.5)), # t_8 -> p8

        ((16.32, 2.5), (15.35, 2.5)), # t_10-> p9
        
        # Final merge at t_9: p8 -> t_9, t_10 -> t_9
        ((16.7, 4.5), (17.5, 3.65)), # p8 -> t_9
        ((16.5, 4.3), (16.5, 2.65)), # p8 -> t_10
       
        
        # End: t_9 -> p10
        ((17.65, 3.5), (18.25, 3.5))  # t_9 -> p10
    ]
    
    # Draw arcs
    for (x1, y1), (x2, y2) in corrected_arcs:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
    
    # Clean up axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
 

# Example usage:
# render_corrected_petri_net()  # Render basic net
# render_corrected_petri_net(['t2', 't3'])  # With some transitions executed
# %%
render_corrected_petri_net()

# %%
