"""
Main file to run the application.

This script initializes the application, sets up the user interface, and determines
which functionality to execute based on the selected tab and the options in the sidebar.

The application includes various tabs for different functionalities, such as:
    - `One agent` (for 2D/3D agent creation and visualisation)
    - `Crowd` (for 2D/3D crowd creation, visualisation, and generation of .xml config files)
    - `Anthropometry` (for data visualisation and analysis)
    - `About` (for displaying general information about the project)

Examples
--------
To run the application, execute these commands from the root directory of the project:

>>> pip install uv
>>> uv sync
>>> uv run streamlit run src/streamlit_app/app/app.py
"""

# Copyright  2025  Institute of Light and Matter, CNRS UMR 5306, University Claude Bernard Lyon 1
# Contributors: Oscar DUFOUR, Maxime STAPELLE, Alexandre NICOLAS

# This software is a computer program designed to generate a realistic crowd from anthropometric data and
# simulate the mechanical interactions that occur within it and with obstacles.

# This software is governed by the CeCILL-B license under French law and abiding by the rules of distribution
# of free software.  You can  use, modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL "http://www.cecill.info".

# As a counterpart to the access to the source code and  rights to copy, modify and redistribute granted by
# the license, users are provided only with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited liability.

# In this respect, the user's attention is drawn to the risks associated with loading,  using,  modifying
# and/or developing or reproducing the software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also therefore means  that it is reserved
# for developers  and  experienced professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their requirements in conditions enabling
# the security of their systems and/or data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.

# The fact that you are presently reading this means that you have had knowledge of the CeCILL-B license and that
# you accept its terms.

import streamlit_app.utils.constants as cst_app
from configuration.data import datafactory
from streamlit_app.app import documentation, ui
from streamlit_app.tabs.anthropometry_tab import run_tab_anthropometry
from streamlit_app.tabs.crowd_creation_tab import run_tab_crowd
from streamlit_app.tabs.one_agent_tab import run_tab_one_agent
from streamlit_app.utils.logging import setup_logging

setup_logging()
if __name__ == "__main__":
    ui.setup_app()
    selected_tab = ui.menubar()
    ui.init_sidebar_looks()
    datafactory.prepare_data()

    if selected_tab == cst_app.FIRST_TAB_NAME:
        run_tab_one_agent()

    if selected_tab == cst_app.SECOND_TAB_NAME:
        run_tab_crowd()

    if selected_tab == cst_app.THIRD_TAB_NAME:
        run_tab_anthropometry()

    if selected_tab == cst_app.FOURTH_TAB_NAME:
        documentation.about()
