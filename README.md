## High-Level Requirements-Driven Business Process Compliance

## Abstract

Regulatory compliance often prioritizes adherence to explicit rules, overlooking the qualitative aspects of rule implementation. Existing goal-driven compliance approaches often focus on mapping tasks and events to enable process discovery and model repair without evaluating the qualitative factors influencing compliance goals. This study introduces a goal-driven framework that integrates requirements engineering techniques to ensure compliance at design time. It merges process and goal dimensions to validate the fulfillment of high-level compliance requirements, such as reliability, efficiency, and appropriateness. The framework involves modeling legal and business requirements as a process model, capturing compliance requirements in a goal model, and synchronizing the models to determine if the intended high-level requirements are satisfied. The framework was validated through an initial implementation, demonstrating how organizations can systematically integrate and verify both procedural and high-level compliance.

#Initial Implementation

A [Prototype]  was developed in Python3, taking as input a set of business process models (BPMN file), the goal model (JSON File), and the mapping (CSV File). It provides two evaluation options: the first assesses if the process model complies with the goal model by analyzing the composed Labeled Transition System, while the second simulates execution traces to determine which satisfies the high-level compliance requirements. The system includes an interactive Jupyter notebook for manual inspection and analysis of process execution.

## Use Case: Fintech Company "FT"

We initially implemented our algorithm using a fictitious Fintech company called "FT" that acts as the data controller and must manage customer data in full compliance with GDPR Articles 12–22. In this use case, 10 BPMN process models were extended and adapted to the fintech context (based on [case studies](https://link.springer.com/chapter/10.1007/978-3-030-21297-1_2)) to satisfy both the operational requirements specified in the relevant GDPR articles and the specific business requirements. 

For the qualitative aspects, the relevant GDPR articles were analyzed to extract the associated qualitative attributes. The operationalization of these qualitative elements was performed using the proposed method in [reference](https://doi.org/10.1145/2884781.2884788), which assigns business-related fill-in variables to formalize the requirements. Subsequently, the mapping of process activities to these qualitative elements was validated by synchronizing the operational process models with a goal model that encapsulated the qualitative compliance requirements.

## Features

- **Compliance Assessment**: Analyze the composed Labeled Transition System to check process model compliance with the goal model.
- **Simulation of Execution Traces**: Determine which execution traces satisfy high-level compliance requirements.
- **Interactive Jupyter Notebook**: Manual inspection and analysis of process execution.

## Requirements

- Python 3
- Jupyter Notebook

## Installation

1. Clone the repository:
   ```bash
   git clone [https://anonymous.4open.science/r/High-Level-Requirements-Driven-Business-Process.Compliance](https://anonymous.4open.science/r/HLRDBPC)
   cd Traces-driven-goals-analysis
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```


## Non-interactive usage
1. Model the goal model using PiStart download the .txt and change the extension to .json
2. Model the process model using SAP signavio, camunda or your process model editor and download the file you can use .bpmn  or .pnl
3. Save a CSV file with two colums Event (Process Transition or DCR events) and Intentional Element to indicate the mapping.
4. Save the models in C:\Users\<youruser>\Documents\GitHub\Kogi-Python\Data
5. Go to C:\Users\<youruser>\Documents\GitHub\Kogi-Python\App

You can run three mains modules:
1. main.py
2. trace_analyzer.py
3. whatif-analyzer.py

For instance, if you run python whatif-analyzer.py, you will have the following options 

============================================================
GOAL MODEL EVALUATION SYSTEM
============================================================
Choose evaluation mode:
1. Interactive evaluation (enter events manually)
2. Predefined traces evaluation
============================================================
Enter your choice (1 or 2):

If you want to test the test the tool without upload your own models you can choose the option 2 to see the evaluation of some traces against predefined models that you can find in the Data directory.


============================================================
EVALUATING TRACE 1: e6 -> e2 -> e3 -> e4 -> e5 -> e7 -> e8
============================================================

Processing event: e6
Task T6: (?, ?) -> (⊤, ⊥)

Processing event: e2
Task T2: (?, ?) -> (⊤, ⊥)
Goal G1: (?, ?) -> (⊤, ⊥)
Quality Q1: (?) -> (⊤)

Processing event: e3
Task T3: (?, ?) -> (⊤, ⊥)

Processing event: e4
Task T4: (?, ?) -> (⊤, ⊥)

Processing event: e5
Task T5: (?, ?) -> (⊤, ⊥)
Goal G2: (?, ?) -> (⊤, ⊥)
Quality Q1: (⊤) -> (⊥)
Goal G1: (⊤, ⊥) -> (⊤, ⊤) (executed pending)
Task T6: (⊤, ⊥) -> (⊤, ⊤) (executed pending)
Task T2: (⊤, ⊥) -> (⊤, ⊤) (executed pending)

Processing event: e7
Task T7: (?, ?) -> (⊤, ⊥)

Processing event: e8
Task T8: (?, ?) -> (⊤, ⊥)

Trace 1 Quality Status:
  Q1: (⊥)

==================================================

Example of statistics

================================================================================
GOAL MODEL EVALUATION STATISTICS
================================================================================

Element      Type     Satisfied %  Exec.Pend %  Unsatisfied %  Satisfied Traces
------------------------------------------------------------------------------------------
G1           Goal           50.0%       50.0%          0.0% 2, 3
G2           Goal           50.0%       50.0%          0.0% 1, 4
G3           Goal            0.0%        0.0%        100.0% None
Q1           Quality        50.0%        0.0%         50.0% 2, 3
T1           Task            0.0%        0.0%        100.0% None
T2           Task            0.0%      100.0%          0.0% None
T3           Task           50.0%       50.0%          0.0% 1, 4
T4           Task           50.0%       50.0%          0.0% 1, 4
T5           Task           50.0%       50.0%          0.0% 1, 4
T6           Task            0.0%      100.0%          0.0% None
T7           Task          100.0%        0.0%          0.0% 1, 2, 3, 4
T8           Task           50.0%        0.0%         50.0% 1, 4

================================================================================
QUALITY ANALYSIS
================================================================================

Quality Q1:
  Fulfilled in 2/4 traces (50.0%)
  Traces where fulfilled: 2, 3

================================================================================
TRACE PATTERN ANALYSIS
================================================================================
Successful traces: 2 (50.0%)
  Trace 2: e6 -> e2 -> e3 -> e4 -> e5 -> e7 -> e1
  Trace 3: e6 -> e3 -> e2 -> e4 -> e5 -> e7 -> e1

Unsuccessful traces: 2 (50.0%)
  Trace 1: e6 -> e2 -> e3 -> e4 -> e5 -> e7 -> e8
  Trace 4: e6 -> e3 -> e2 -> e4 -> e5 -> e7 -> e8
================================================================================

On the other hand, if you choose option 1 you will have the opportunity to analyze the impact of the execution of an specific event on the satisfaction of the goal model elements.

Example:

============================================================
INTERACTIVE GOAL MODEL EVALUATION
============================================================
Available events: e1, e2, e3, e4, e5, e6, e7, e8
Event mappings:
  e1 -> G1
  e2 -> T2
  e3 -> T3, G1
  e4 -> T4
  e5 -> T5
  e6 -> T6
  e7 -> T7
  e8 -> T8

Type events one by one (or 'stop' to finish, 'status' to see current state):
============================================================

Enter event: e1

Processing event: e1
Goal G1: (?, ?) -> (⊤, ⊥)
Quality Q1: (?) -> (⊤)

Current Quality Status:
  Q1: (⊤)

## Interactive Usage

1. Place the BPMN files, JSON goal model file, and CSV mapping file in the `input` directory.
2. Run the Jupyter notebook:
   ```bash
   jupyter notebook
   ```
3. Open the notebook and follow the instructions to perform the compliance assessment or simulate execution traces.




## References


 
- High-Level Requirements-Driven Business Process Compliance
