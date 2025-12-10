"""2D agent visualization tab."""

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

import configuration.utils.constants as cst
import streamlit_app.utils.constants as cst_app
from configuration.models.agents import Agent
from configuration.models.measures import AgentMeasures
from streamlit_app.plot import plot


def init_session_state() -> AgentMeasures:
    """
    Initialize session state variables for different agent types (pedestrian or bike).

    Returns
    -------
    AgentMeasures
        An object containing the initialized measures for the selected agent type.

    Notes
    -----
    - For pedestrians, default measures include the attributes sex, bideltoid breadth, chest depth, height, and weight.
    - For bikes, default measures include the attributes wheel width, total length, handlebar length, top tube length, and weight.
    """
    agent_type: str = st.sidebar.radio(
        "Agent type",
        [cst.AgentTypes.pedestrian.name, cst.AgentTypes.bike.name],
        label_visibility="collapsed",
    )

    if str(agent_type) not in st.session_state:
        if agent_type == cst.AgentTypes.pedestrian.name:
            # Create a new pedestrian object
            agent_measures = AgentMeasures(
                agent_type=cst.AgentTypes.pedestrian,
                measures={
                    "sex": cst_app.DEFAULT_SEX,
                    "bideltoid_breadth": cst.CrowdStat["male_bideltoid_breadth_mean"],
                    "chest_depth": cst.CrowdStat["male_chest_depth_mean"],
                    "height": cst.CrowdStat["male_height_mean"],
                    "weight": cst.CrowdStat["male_weight_mean"],
                },
            )
            st.session_state.agent_type_measures = cst.AgentTypes.pedestrian
            st.session_state.current_agent = Agent(agent_type=cst.AgentTypes.pedestrian, measures=agent_measures)

        elif agent_type == cst.AgentTypes.bike.name:
            # Create a new bike object
            agent_measures = AgentMeasures(
                agent_type=cst.AgentTypes.bike,
                measures={
                    "wheel_width": cst.CrowdStat["wheel_width_mean"],
                    "total_length": cst.CrowdStat["total_length_mean"],
                    "handlebar_length": cst.CrowdStat["handlebar_length_mean"],
                    "top_tube_length": cst.CrowdStat["top_tube_length_mean"],
                    "weight": cst.CrowdStat["bike_weight_mean"],
                },
            )
            st.session_state.agent_type_measures = cst.AgentTypes.bike
            st.session_state.current_agent = Agent(agent_type=cst.AgentTypes.bike, measures=agent_measures)

        else:  # default case
            agent_measures = AgentMeasures(
                agent_type=cst.AgentTypes.pedestrian,
                measures={
                    "sex": cst_app.DEFAULT_SEX,
                    "bideltoid_breadth": cst.CrowdStat["male_bideltoid_breadth_mean"],
                    "chest_depth": cst.CrowdStat["male_chest_depth_mean"],
                    "height": cst.CrowdStat["male_height_mean"],
                    "weight": cst.CrowdStat["male_weight_mean"],
                },
            )
            st.session_state.agent_type_measures = cst.AgentTypes.pedestrian
            st.session_state.current_agent = Agent(agent_type=cst.AgentTypes.pedestrian, measures=agent_measures)
        st.session_state.agent_type = agent_type

    return agent_measures


def sliders_for_agent_measures(agent_measures: AgentMeasures) -> None:
    """
    Create sliders in the sidebar to adjust agent measures.

    Parameters
    ----------
    agent_measures : AgentMeasures
        The current `AgentMeasures` object that holds the measures for the selected agent type.

    Attributes
    ----------
    - `st.session_state.current_agent`: The updated `Agent` object with modified measures.

    Notes
    -----
    - For pedestrians:

        - Sliders are created for `bideltoid_breadth` and `chest_depth`.
        - Other measures (e.g., height, weight, and sex) are set to default values.
    - For bikes:

        - Sliders are created for `wheel_width`, `total_length`, `handlebar_length`, and `top_tube_length`.
        - Other measures (e.g., weight) are set to default values.
    """
    current_agent = st.session_state.current_agent
    if st.session_state.agent_type == cst.AgentTypes.pedestrian.name:
        bideltoid_breadth = st.sidebar.slider(
            "Bideltoid breadth (cm)",
            min_value=cst.CrowdStat["male_bideltoid_breadth_min"],
            max_value=cst.CrowdStat["male_bideltoid_breadth_max"],
            value=cst.CrowdStat["male_bideltoid_breadth_mean"],
            step=1.0,
        )
        chest_depth = st.sidebar.slider(
            "Chest depth (cm)",
            min_value=cst.CrowdStat["male_chest_depth_min"],
            max_value=cst.CrowdStat["male_chest_depth_max"],
            value=cst.CrowdStat["male_chest_depth_mean"],
            step=1.0,
        )
        agent_measures = AgentMeasures(
            agent_type=cst.AgentTypes.pedestrian,
            measures={
                "sex": cst_app.DEFAULT_SEX,
                "bideltoid_breadth": bideltoid_breadth,
                "chest_depth": chest_depth,
                "height": cst.CrowdStat["male_height_mean"],
                "weight": cst.CrowdStat["male_weight_mean"],
            },
        )
    elif st.session_state.agent_type == cst.AgentTypes.bike.name:
        total_length = st.sidebar.slider(
            "Total length (cm)",
            min_value=cst.CrowdStat["total_length_min"],
            max_value=cst.CrowdStat["total_length_max"],
            value=cst.CrowdStat["total_length_mean"],
            step=1.0,
        )
        handlebar_length = st.sidebar.slider(
            "Handlebar length (cm)",
            min_value=cst.CrowdStat["handlebar_length_min"],
            max_value=cst.CrowdStat["handlebar_length_max"],
            value=cst.CrowdStat["handlebar_length_mean"],
            step=1.0,
        )
        top_tube_length = st.sidebar.slider(
            "Top tube length (cm)",
            min_value=cst.CrowdStat["top_tube_length_min"],
            max_value=cst.CrowdStat["top_tube_length_max"],
            value=cst.CrowdStat["top_tube_length_mean"],
            step=1.0,
        )
        wheel_width = st.sidebar.slider(
            "Wheel width (cm)",
            min_value=cst.CrowdStat["wheel_width_min"],
            max_value=cst.CrowdStat["wheel_width_max"],
            value=cst.CrowdStat["wheel_width_mean"],
            step=0.5,
        )
        agent_measures = AgentMeasures(
            agent_type=cst.AgentTypes.bike,
            measures={
                "wheel_width": wheel_width,
                "total_length": total_length,
                "handlebar_length": handlebar_length,
                "top_tube_length": top_tube_length,
                "weight": cst.DEFAULT_BIKE_WEIGHT,
            },
        )

    current_agent.measures = agent_measures


def sliders_for_position() -> tuple[float, float, float]:
    """
    Create sliders in the sidebar for position and rotation adjustments.

    Returns
    -------
    tuple[float, float, float]
        A tuple containing:

        - `x_translation` (float): The translation along the X-axis (cm).
        - `y_translation` (float): The translation along the Y-axis (cm).
        - `rotation_angle` (float): The rotation angle in degrees.
    """
    x_translation = st.sidebar.slider(
        "X-translation (cm)", min_value=-cst_app.MAX_TRANSLATION_X, max_value=cst_app.MAX_TRANSLATION_X, value=0.0, step=1.0
    )
    y_translation = st.sidebar.slider(
        "Y-translation (cm)", min_value=-cst_app.MAX_TRANSLATION_Y, max_value=cst_app.MAX_TRANSLATION_Y, value=0.0, step=1.0
    )
    rotation_angle = st.sidebar.slider(
        "Rotation angle (degrees)",
        min_value=-180.0,
        max_value=180.0,
        value=90.0,
        step=1.0,
    )
    return x_translation, y_translation, rotation_angle


def run_tab_agent2D() -> None:
    """
    Provide an interactive interface for visualizing 2D representations of agents (e.g. pedestrians or bikes).

    Attributes
    ----------
    Sidebar:
        - Agent type selection.
        - Sliders for anthropometric parameters.
    Main Page:
        - Visualization of the 2D agent shape.
        - Displays an image illustrating the definitions of the current agent's measurements.
    """
    st.sidebar.header("Select agent type")

    # Initialize session state variables
    agent_measures = init_session_state()

    # Access the stored object
    current_agent = st.session_state.current_agent

    # Input fields for Anthropometric parameters
    st.sidebar.header("Adjust agent parameters")
    sliders_for_agent_measures(agent_measures)

    # Input fields for translation and rotation
    if cst_app.SHOW_DEV:
        st.sidebar.header("Adjust position")
        x_translation, y_translation, rotation_angle = sliders_for_position()
        current_agent.translate(x_translation, y_translation)
        current_agent.rotate(rotation_angle)

    # Main page content
    if st.session_state.agent_type_measures == cst.AgentTypes.pedestrian:
        col1, col2 = st.columns([1.0, 1])  # Adjust proportions as needed
    else:
        col1, col2 = st.columns([1.5, 1])
    with col1:
        st.subheader("Visualisation")
        fig = plot.display_shape2D([current_agent])
        st.plotly_chart(fig)
    with col2:
        # display the current agent measures
        st.subheader("Current agent measures")
        if st.session_state.agent_type_measures == cst.AgentTypes.pedestrian:
            path_file = Path(__file__).parent.parent.parent.parent / "data" / "images"
            st.image(str(path_file / "measures_pedestrian.png"), width="stretch")
        elif st.session_state.agent_type_measures == cst.AgentTypes.bike:
            path_file = Path(__file__).parent.parent.parent.parent / "data" / "images"
            st.text(" ")
            st.text(" ")
            st.text(" ")
            st.text(" ")
            st.image(str(path_file / "measures_bike.png"), width="stretch")

    # st.sidebar.header("Download") # Requites kaleido package that causes issues on some OS
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # st.sidebar.download_button(
    #     label="Download plot as PNG",
    #     data=fig.to_image(format="png", width=1600, height=1200),
    #     file_name=f"body2D_orthogonal_projection_{timestamp}.png",
    #     mime="image/png",
    #     width="stretch",
    # )
