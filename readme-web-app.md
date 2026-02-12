# Kogi Web App
The [KogiApp](/KogiApp.ipynb) notebook can run as a Web application on a Linux server by using the [``voila``](https://voila.readthedocs.io/en/stable/) library. 

Installation instructions. 

- Requirements: Python 3.11
- Clone ``https://github.com/jc4v1/Kogi-Python.git``
- Change directory to Kogi-Python
- ``pip -r requirements.txt`` (includes Voila)
- ``voila KogiApp.ipynb --no-browser --Voila.ip=0.0.0.0 &``
