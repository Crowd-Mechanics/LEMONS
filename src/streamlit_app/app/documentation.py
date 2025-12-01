"""About tab of the app."""

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

from pathlib import Path

import streamlit as st

from streamlit_app.utils import constants as cst_app


def about() -> None:
    """Write about text."""
    current_file_path = Path(__file__)
    ROOT_DIR = current_file_path.parent.parent.parent.parent.absolute()
    st.markdown(f"## Overview of the {cst_app.PROJECT_NAME} project")
    st.markdown("""
        The software release dubbed LEMONS consists of:

        1. **This online platform**
        [https://lemons.streamlit.app/](https://lemons.streamlit.app/) to generate and visualise individual pedestrians
        (whose shapes are compatible with anthropometric data) or crowds.

        2. **A C++ library**
        to compute mechanical contact forces in two dimensions and then evolve the crowd according to Newton's equation of motion.

        3. **A Python wrapper**
        to manage and automate crowd simulations through simple calls to the C++ library, with visualisation
        enabled by exporting results to [ChAOS](https://project.inria.fr/crowdscience/project/ocsr/chaos/) input format.
        """)

    visible_human_proj_url = "https://www.nlm.nih.gov/research/visible/visible_human.html"
    ANSURII_url = "https://ph.health.mil/topics/workplacehealth/ergo/Pages/Anthropometric-Database.aspx"
    granular_material_url = "https://doi.org/10.1016/j.cpc.2025.109524"
    col1, col2 = st.columns([1, 1])  # Adjust proportions as needed
    with col1:
        st.markdown(f"""
        ### I - Pedestrian shape elaboration

        To determine a pedestrian shape, we chose to rely on medical data from the [Visible Human Project]({visible_human_proj_url}),
        consisting of slices of frozen bodies. We take the slice associated with the torso and cover it with disks:
        two for the shoulders, two for the pectoral muscles and one for the belly.
        """)
        st.image(str(ROOT_DIR / "data" / "images" / "coverage.png"), width="stretch")
        st.markdown(f"""
        Then, to extend that shape to other individuals in a population, we used anthropometric measurements
        from [Gordon and collaborators]({ANSURII_url}). In particular, we matched the measure of the **chest depth** using a uniform
        scaling factor for the disk radii, and the measure of the **bideltoid breadth** using an homothety on the disk centers.""")
        st.image(str(ROOT_DIR / "data" / "images" / "measure_ped.png"), width="stretch")
        st.markdown("""
        We use disks instead of one single ellipse or a single polygon because the physical contact is easier
        to define mathematically, and the use of composite shapes allows for **relative motion** between the different
        composents allowing for body torsion (currently unimplemented).""")

    with col2:
        st.markdown(f"""
        ### II - Mechanical layer

        Drawing inspiration from the [granular material literature]({granular_material_url}), all the complexity of a 3D mechanical
        contact is reduced to 2D and modelled with **damped springs** that are normal and tangential to the surface contact.
        Stick and slip mechanism is rendered using **Coulomb law**.
        """)
        st.image(str(ROOT_DIR / "data" / "images" / "contact_mecha_spring.png"), width="stretch")

    st.markdown(
        """
        ### III - Coupling Mechanical - Decisional layers
        """
    )

    st.markdown(
        r"The user can impose decisions for each agent via $F_{\text{decision}}$ and $\tau_{\text{decision}}$. "
        "The motion of each agent is subjected to the following equations coupling the decision layer (:blue[blue]) with "
        "the mechanical layer (:green[green] and :orange[orange])."
    )
    st.image(str(ROOT_DIR / "data" / "images" / "coupling.png"), width="stretch")
    st.markdown("The :green[green] part represents the floor contact and all other sources of mechanical dissipation.")
