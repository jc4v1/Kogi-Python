## Aligning Processes with High-Level Requirements: Goal-Model-Based Compliance Checking

## Abstract

Regulatory compliance often prioritizes adherence to explicit rules, overlooking the qualitative aspects of rule implementation. Existing goal-driven compliance approaches often focus on mapping tasks and events to enable process discovery and model repair without evaluating the qualitative factors influencing compliance goals. This study introduces a goal-driven framework that integrates requirements engineering techniques to ensure compliance at design time. It merges process and goal dimensions to validate the fulfillment of high-level compliance requirements, such as reliability, efficiency, and appropriateness. The framework involves modeling legal and business requirements as a process model, capturing compliance requirements in a goal model, and synchronizing the models to determine if the intended high-level requirements are satisfied. The framework was validated through an initial implementation, demonstrating how organizations can systematically integrate and verify both procedural and high-level compliance.

# Initial Implementation

A Prototype was developed in Python3, taking as input a Petri Net model (PNML File) and the goal model (JSON File). The event mapping is either derived directly from the Petri Net model, or provided as a CSV fie. 

The provides three options:
- a non-interactive option. checking for stability and weak-compliance and returning either true or fals with counter examples
- an interactive option, which allows for the animation of the combined model by executing transitions
in the process model and see the effect on the goal model. It also allows to run the algorithms for checking stability and weak-compliance and if they are not stable or not compliant, then select those states, where the validation fails.
- a second interactive option, where it is possible to animate how the goal model reacts to certain events.


## Installation

1. Clone the repository: ``git clone https://github.com/jc4v1/Kogi-Python.git``
2. Install the required packages: ``pip install -r requirements.txt``
3. You can then start Jupyter notebook with ``jupyter notebook`` and then open the file README.ipynb to see this document as a Jupyter notebook and run the demo code.


## Required imports

```bash
from Semantics.istar_processor import read_istar_model
from Semantics.petri_net_processor import read_petri_net
from Semantics.event_mapping_from_csv import read_event_mapping_csv
from Ui.interface import InterfaceBuilder
from Semantics.transition_system import combine_goal_model_and_petri_net
from Semantics.transition_system import CombinedTransitionSystem
```

## Non-interactive usage
1. Model the goal model using PiStar (https://www.cin.ufpe.br/~jhcp/pistar/tool/#) and download the goalModel.txt file
2. Model the process model as a Petri Net using, e.g., the "I love Petri Nets" editor (https://www.fernuni-hagen.de/ilovepetrinets/fapra/wise23/rot/index.html)
3. For the event mapping create a spreadsheet with a column for events and another for Intentional elements and save it as a CSV file.

| Event | Intentional Element |
| --- | --- |
| t1 |   |
| t2  | e2   |

The empty cell of the intentional element indicates that that specific transition is not mapped to an intentional element.
4. Alternatively, extract the event mapping from the Petri Net file. In the case for "I love Petri Nets", the transitions will be mapped to the actions defined in the editor and interpreted as intentional elements. The following Petri Net would correspond to the event mapping from before
![petri net](Data/pn-event-mapping.png)



The following steps follows the method outlined in the paper. Based on the provided process model, goal model and event mapping
1. in the first step, the models are translated to their respective labelled transition systems
2. then the combined transition system is constructed from the process model, the goal model, and the event mapping
3. then the combined system is checked for stability
4. and weak compliance. 

The results are true or false, depending on the result of the checks and if the property does not hold, a list of states are returned in which the property does not hold.



The following example is based on the security example from the paper, which is not stable, because we can always break the quality, but it is weak compliant, as we can always reach a state where the quality is true.

```bash
goal_model = read_istar_model("Data/security/goal_model.txt")
petri_net = read_petri_net("Data/security/petri_net.pnml")
# Map generated from the Petri Net.
event_mapping = petri_net.get_default_event_mapping()
# Alternatively the event mapping can be read from a CSV file.
# event_mapping = read_event_mapping_csv("Data/security/map.csv")

lts_gm = goal_model.as_transition_system()
print(f"Goal Model LTS reachable states and transitions: {lts_gm.size()}")

lts_pn = petri_net.as_transition_system()
print(f"Petri Net LTS reachable states and transitions: {lts_pn.size()}")

lts_combined = CombinedTransitionSystem(lts_gm, lts_pn, event_mapping)
print(f"Combined LTS reachable states and transitions: {lts_combined.size()}")

result = lts_combined.check_stability(goal_model.qualities)
print(f"Stability: {result}")

result = lts_combined.check_weak_compliance(goal_model.qualities)
print(f"Weak Compliance: {result}")

```

Note that the number of states for the goal model, the process model, and the combined labeled transition system are shown. Note that there is no state explosion happening for the combined labeled transition system. The reason is the strong synchronization of the process model and the goal model. Each action in the process model will lead either to an intentional event in the goal model or nothing. But it is not possible for the goal model to make independent transitions from that of the process model.


## Interactive Usage

The following shows the interactive usage of the Kogi tool. 

The following options are available in the interactive version
- One can select a transition form the Petri Net and then press on the button "execute the event" to see the effect of that transition on the goal model
- Run the stabiity check and jump to a failing state to then select a transition to see, why this state is not stable
- Run the weak compliance check and again check through animation, why weak compliance fails.

The following is the screenshot of the interactive version. In the Jupyter notebook, you can try the interactive version for yourself.
![screenshot](Data/kogi_interactive.jpg)


For comparision, we choose again the security example from the paper.

```bash
goal_model = read_istar_model("Data/security/goal_model.txt")
petri_net = read_petri_net("Data/security/petri_net.pnml")
# Map generated from the Petri Net.
event_mapping = petri_net.get_default_event_mapping()
# Alternatively the event mapping can be read from a CSV file.
# event_mapping = read_event_mapping_csv("Data/security/map.csv")

interface = InterfaceBuilder(goal_model,petri_net=petri_net,event_mapping=event_mapping).create_interface()
display(interface)
```

## What if scenario


The what-if scenario only looks at the behaviour of the goal model, and how the goal model reacts to 
when tasks or goals are activated. In this animation, goals and tasks that don't have a
refinement, can be selected in any order. 

This allows to experiment with possible scenarios on how to achieve the goals of the 
goal model or to make or break its qualities.


The first step is to create a goal model with [PiStar](https://www.cin.ufpe.br/~jhcp/pistar/tool/#), move the file goal_model.txt in the Download folder to the right place and the right
name, and then read the file.

And then create the interface with the InterfaceBuilder class, and diplay the created interface.

```python
goal_model = read_istar_model("Data/what_if_gm.txt")
petri_net = goal_model.generate_all_events_petri_net()

combine_goal_model_and_petri_net(goal_model, petri_net, event_mapping = None)

```

```python
gm = read_istar_model("Data/what_if_gm.txt")

interface = InterfaceBuilder(gm, whatif=True).create_interface()
display(interface)
```

What happens is, that in the background a Petri net is created. That Petri net 
has one place and a transition from and to that place for each task and goal that
does not have a refinement. This allows to select and execute those tasks and goals in any order.

Here is an example of the Petri net for two events e1 and e2.

![petri net](Data/all-events-pn.png)


```python
goal_model = read_istar_model("Data/test/simple.txt")
petri_net = goal_model.generate_all_events_petri_net()

combine_goal_model_and_petri_net(goal_model, petri_net, event_mapping = None)

```

```python
gm = read_istar_model("Data/test/simple.txt")

interface = InterfaceBuilder(gm, whatif=True).create_interface()
display(interface)
```

```python
goal_model = read_istar_model("Data/test/simple2.txt")
petri_net = goal_model.generate_all_events_petri_net()

combine_goal_model_and_petri_net(goal_model, petri_net, event_mapping = None)

```

```python
gm = read_istar_model("Data/test/simple2.txt")

interface = InterfaceBuilder(gm, whatif=True).create_interface()
display(interface)
```

```python
goal_model = read_istar_model("Data/test/simple.txt")
petri_net = read_petri_net("Data/test/pn.pnml")

petri_net.set_event_mapping(goal_model)

combine_goal_model_and_petri_net(goal_model, petri_net, event_mapping = goal_model.event_mapping)

```

## Your own example




Choose your process model and goal model. You can use the following tools
- For Petri Nets https://www.fernuni-hagen.de/ilovepetrinets/fapra/wise23/rot/index.html
  - If you add actions to transitions in the petri net editor; they will be automatically mapped to intentional elements in the goal model using 
  - ``petri_net.set_event_mapping(goal_model)``
- For Goal models https://www.cin.ufpe.br/~jhcp/pistar/tool/#


```python

# goal_model = read_istar_model("your_goal_model.txt")
# petri_net = read_petri_net("your_petri_net.pnml")

# petri_net.set_event_mapping(goal_model)

# interface = InterfaceBuilder(goal_model, petri_net, debug=True).create_interface()
# display(interface)

```

## Your own example




Choose your process model and goal model. You can use the following tools
- For Petri Nets https://www.fernuni-hagen.de/ilovepetrinets/fapra/wise23/rot/index.html
  - If you add actions to transitions in the petri net editor; they will be automatically mapped to intentional elements in the goal model using 
  - ``petri_net.set_event_mapping(goal_model)``
- For Goal models https://www.cin.ufpe.br/~jhcp/pistar/tool/#
- For DCR Graphs https://https://hugoalopez-dtu.github.io/dcr-js/ (download as DCR Solutions XML)
  - Note that the basic notation for DCR's is supported by Kogi

```python

# goal_model = read_istar_model("your_goal_model.txt")
# petri_net = read_petri_net("your_petri_net.pnml")

# petri_net.set_event_mapping(goal_model)

# interface = InterfaceBuilder(goal_model, petri_net, debug=True).create_interface()
# display(interface)

```



## References



- Aligning Processes with High-Level Requirements: Goal-Model-Based Compliance Checking
- High-Level Requirements-Driven Business Process Compliance

