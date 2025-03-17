# Traces-driven Goals Analysis

[Prototype](https://aab.dk/) upload code was developed in Python3, taking as input a set of business process models (BPMN file), the goal model (JSON File), and the mapping (CSV File). It provides two evaluation options: the first assesses if the process model is compliant with the goal model by analyzing the composed Labeled Transition System, while the second simulates execution traces to determine which satisfies the high-level compliance requirements. The system includes an interactive Jupyter notebook for manual inspection and analysis of process execution.

## Use Case: Fintech Company "FT"

We made an initial implementation of our algorithm using a fictitious Fintech company called "FT" acting as the data controller that must manage customer data in full compliance with GDPR Articles 12–22. In this use case, 10 BPMN process models were extended and adapted to the fintech context (based on [case studies](#)) to satisfy both the operational requirements specified in the relevant GDPR articles and the specific business requirements. 

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
   git clone https://github.com/JUANITACABALLEROV/Traces-driven-goals-analysis.git
   cd Traces-driven-goals-analysis
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Place the BPMN files, JSON goal model file, and CSV mapping file in the `input` directory.
2. Run the Jupyter notebook:
   ```bash
   jupyter notebook
   ```
3. Open the notebook and follow the instructions to perform the compliance assessment or simulate execution traces.

## References

- High-Level Requirements-Driven Business Process Compliance
