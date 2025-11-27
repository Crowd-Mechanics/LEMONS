"""Streamlit tab for visualizing a single agent in 2D or 3D."""

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

import streamlit as st

from streamlit_app.tabs.one_agent_2D import run_tab_agent2D
from streamlit_app.tabs.one_pedestrian_3D import run_tab_pedestrian3D


def run_tab_one_agent() -> None:
    """Run the 2D agent visualization or the 3D pedestrian visualisation depending on the selected option."""
    st.subheader("Choose dimension")
    dimension_options = {
        "2D": "2D",
        "3D": "3D",
    }
    selected_dimension_options = st.pills(" ", list(dimension_options.values()), label_visibility="collapsed", default="2D")

    if selected_dimension_options == dimension_options["2D"]:
        run_tab_agent2D()
    elif selected_dimension_options == dimension_options["3D"]:
        run_tab_pedestrian3D()
