"""3D pedestrian visualization tab."""

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

import pickle
from datetime import datetime
from io import BytesIO
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from matplotlib.figure import Figure

import configuration.utils.constants as cst
import streamlit_app.utils.constants as cst_app
from configuration.models.agents import Agent
from configuration.models.initial_agents import InitialPedestrian
from configuration.models.measures import AgentMeasures
from configuration.utils import functions as fun
from streamlit_app.plot import plot


def initialize_session_state() -> None:
    """Initialize the session state variables."""
    if "current_pedestrian" not in st.session_state:
        initial_pedestrian = InitialPedestrian(cst_app.DEFAULT_SEX)
        # Create a new pedestrian object
        pedestrian_measures = AgentMeasures(
            agent_type=cst.AgentTypes.pedestrian,
            measures={
                "sex": cst_app.DEFAULT_SEX,
                "bideltoid_breadth": initial_pedestrian.measures[cst.PedestrianParts.bideltoid_breadth.name],
                "chest_depth": initial_pedestrian.measures[cst.PedestrianParts.chest_depth.name],
                "height": initial_pedestrian.measures[cst.PedestrianParts.height.name],
                "weight": initial_pedestrian.measures[cst.CommonMeasures.weight.name],
            },
        )
        st.session_state.current_pedestrian = Agent(agent_type=cst.AgentTypes.pedestrian, measures=pedestrian_measures)


def sliders_for_agent_parameters() -> AgentMeasures:
    """
    Create sliders in the sidebar for adjusting pedestrian parameters.

    Attributes
    ----------
    Sidebar:
        - Radio button for selecting sex (male or female).
        - Sliders for anthropometric parameters:
            - Bideltoid breadth (cm).
            - Chest depth (cm).
            - Height (cm).

    Returns
    -------
    AgentMeasures
        An object containing the updated measures for the pedestrian agent.
    """
    # Sex Selection
    st.sidebar.radio(
        "Sex of the pedestrian",
        options=["male", "female"],
        index=0,  # Default to "male"
        key="sex",  # Automatically syncs with st.session_state.sex
    )
    initial_pedestrian = InitialPedestrian(st.session_state.sex)

    # Sliders for anthropometric parameters
    bideltoid_breadth: float = st.sidebar.slider(
        "Bideltoid breadth (cm)",
        min_value=cst.CrowdStat["male_bideltoid_breadth_min"],
        max_value=cst.CrowdStat["male_bideltoid_breadth_max"],
        value=float(initial_pedestrian.get_bideltoid_breadth()),
        step=1.0,
    )
    chest_depth: float = st.sidebar.slider(
        "Chest depth (cm)",
        min_value=cst.CrowdStat["male_chest_depth_min"],
        max_value=cst.CrowdStat["male_chest_depth_max"],
        value=float(initial_pedestrian.get_chest_depth()),
        step=1.0,
    )
    height: float = st.sidebar.slider(
        "Height (cm)",
        min_value=float(cst_app.DEFAULT_HEIGHT_MIN),
        max_value=float(cst_app.DEFAULT_HEIGHT_MAX),
        value=float(initial_pedestrian.get_height()),
        step=1.0,
    )

    # Create the AgentMeasures object with the updated values
    pedestrian_measures = AgentMeasures(
        agent_type=cst.AgentTypes.pedestrian,
        measures={
            "sex": st.session_state.sex,
            "bideltoid_breadth": bideltoid_breadth,
            "chest_depth": chest_depth,
            "height": height,
            "weight": initial_pedestrian.measures[cst.CommonMeasures.weight.name],
        },
    )
    return pedestrian_measures


def sliders_for_agent_position() -> tuple[float, float, float]:
    """
    Create sliders in the sidebar for adjusting an agent's position and rotation.

    Returns
    -------
    tuple[float, float, float]
        A tuple containing:

        - `x_translation`: The translation along the X-axis (cm).
        - `y_translation`: The translation along the Y-axis (cm).
        - `rotation_angle`: The rotation angle around the Z-axis in degrees.
    """
    x_translation = st.sidebar.slider(
        "X-translation (cm)",
        min_value=-cst_app.MAX_TRANSLATION_X,
        max_value=cst_app.MAX_TRANSLATION_X,
        value=0.0,
        step=1.0,
    )
    y_translation = st.sidebar.slider(
        "Y-translation (cm)",
        min_value=-cst_app.MAX_TRANSLATION_Y,
        max_value=cst_app.MAX_TRANSLATION_Y,
        value=0.0,
        step=1.0,
    )
    rotation_angle = st.sidebar.slider(
        "Rotation angle around z-axis (degrees)",
        min_value=-180.0,
        max_value=180.0,
        value=90.0,
        step=1.0,
    )
    return x_translation, y_translation, rotation_angle


def download_data(current_pedestrian: Agent) -> None:
    """
    Display two download buttons in the sidebar to export 3D shape data of the current agent as pickle files.

    The first button allows the user to download the current pedestrian's 3D shape polygons.
    The second button enables downloading the reference 3D body model with standard parameters and high precision.

    Parameters
    ----------
    current_pedestrian : Agent
        The agent object representing the current pedestrian.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"agent3D_{current_pedestrian.agent_type}_{current_pedestrian.measures.measures['sex']}_{timestamp}.pkl"
    data_to_download = pickle.dumps(current_pedestrian.shapes3D.shapes)
    st.sidebar.download_button(
        label="Download data as PKL",
        data=data_to_download,
        file_name=filename,
        mime="application/octet-stream",
        width="stretch",
        help="Contains the polygons used to display the pedestrian.",
    )

    dir_path = Path(__file__).parent.parent.parent.parent.absolute() / "data" / "pkl"
    data_to_download = pickle.dumps(fun.load_pickle(str(dir_path / f"{current_pedestrian.measures.measures['sex']}_3dBody.pkl")))
    filename = f"agent3D_{current_pedestrian.agent_type}_{current_pedestrian.measures.measures['sex']}.pkl"
    st.sidebar.download_button(
        label="Download precise data as PKL",
        data=data_to_download,
        file_name=filename,
        mime="application/octet-stream",
        help="Contains the polygons used to build the 3D representation of the pedestrian"
        " with standard parameters,"
        " with a precision up to 0.1 mm in the altitude-direction.",
        width="stretch",
    )


def orthogonal_projection_option(current_pedestrian: Agent) -> None:
    """
    Display the orthogonal projection of the pedestrian agent in 3D.

    Parameters
    ----------
    current_pedestrian : Agent
        The agent object representing the current pedestrian.

    Notes
    -----
    - The function creates a progress bar and status text to indicate the progress of the computation.
    - The orthogonal projection is computed and displayed using the `plot.display_body3D_orthogonal_projection` function.
    - The resulting figure is saved to a `BytesIO` object in PDF format.
    - A download button is provided to allow users to download the orthogonal projection as a PDF file.
    """
    title_progress_bar = st.text("Progress bar")
    my_progress_bar = st.progress(0)
    status_text = st.empty()

    # Compute the orthogonal projection
    fig: Figure = plot.display_body3D_orthogonal_projection(current_pedestrian, extra_info=(my_progress_bar, status_text))
    # Display the figure
    st.pyplot(fig)

    status_text.text("Operation complete! ⌛")
    my_progress_bar.empty()
    title_progress_bar.empty()
    status_text.empty()

    # Save the figure to a BytesIO object in PDF format
    body3D_orthogonal_projection = BytesIO()
    fig.savefig(body3D_orthogonal_projection, format="pdf")
    body3D_orthogonal_projection.seek(0)

    # Streamlit button in the sidebar to download the graph in PDF format
    st.sidebar.header("Download")
    st.sidebar.download_button(
        label="Download plot as PDF",
        data=body3D_orthogonal_projection,
        file_name="body3D_orthogonal_projection.pdf",
        mime="application/pdf",
        width="stretch",
    )


def slices_option(current_pedestrian: Agent) -> None:
    """
    Display the slices of the pedestrian agent in 3D.

    Parameters
    ----------
    current_pedestrian : Agent
        The agent object representing the current pedestrian.

    Notes
    -----
    - The function creates a progress bar and status text to indicate the progress of the computation.
    - The slices are computed and displayed using the `plot.display_body3D_polygons` function.
    - The resulting figure is saved to a `BytesIO` object in PDF format.
    - A download button is provided to allow users to download the slices as a PDF file.
    """
    title_progress_bar = st.text("Progress Bar")
    my_progress_bar = st.progress(0)
    status_text = st.empty()

    # Compute the 3D body with slices
    fig_plotly: go.Figure = plot.display_body3D_polygons(current_pedestrian, extra_info=(my_progress_bar, status_text))
    # Display the figure
    st.plotly_chart(fig_plotly)

    status_text.text("Operation complete! ⌛")
    my_progress_bar.empty()
    title_progress_bar.empty()
    status_text.empty()

    # # Streamlit button in the sidebar to download the graph in PNG format # Requites kaleido package that causes issues on some OS
    # st.sidebar.header("Download")
    # st.sidebar.download_button(
    #     label="Download plot as PNG",
    #     data=fig_plotly.to_image(format="png", width=1600, height=1200),
    #     file_name="body3D_slices.png",
    #     width="stretch",
    # )


def mesh_option(current_pedestrian: Agent) -> None:
    """
    Display the mesh of the pedestrian agent in 3D.

    Parameters
    ----------
    current_pedestrian : Agent
        The agent object representing the current pedestrian.

    Notes
    -----
    - The function creates a progress bar and status text to indicate the progress of the computation.
    - The mesh is computed and displayed using the `plot.display_body3D_mesh` function.
    - The resulting figure is saved to a `BytesIO` object in PDF format.
    - A download button is provided to allow users to download the mesh as a PDF file.
    """
    title_progress_bar = st.text("Progress Bar")
    my_progress_bar = st.progress(0)
    status_text = st.empty()

    # Compute the 3D body with a mesh
    fig_plotly_mesh: go.Figure = plot.display_body3D_mesh(
        current_pedestrian, precision=len(current_pedestrian.shapes3D.shapes.keys()), extra_info=(my_progress_bar, status_text)
    )

    # Display the figure
    st.plotly_chart(fig_plotly_mesh)

    status_text.text("Operation complete! ⌛")
    my_progress_bar.empty()
    title_progress_bar.empty()
    status_text.empty()

    # # Streamlit button in the sidebar to download the graph in PDF format # Requites kaleido package that causes issues on some OS
    # st.sidebar.header("Download")
    # st.sidebar.download_button(
    #     label="Download plot as PNG",
    #     data=fig_plotly_mesh.to_image(format="png", width=1600, height=1200),
    #     file_name="body3D_mesh.png",
    #     width="stretch",
    # )


def run_tab_pedestrian3D() -> None:
    """
    Provide an interactive interface for visualizing and interacting with a 3D representation of a pedestrian agent.

    Users can adjust anthropometric parameters, manipulate position and rotation, and choose from different visualization
    modes. Download options for figures and data are also provided.

    Main Page:
        - Visualization of the selected 3D representation mode:
            - Orthogonal projection (matplotlib figure).
            - 3D body as slices (Plotly figure).
            - 3D body with a mesh (Plotly figure).
        - Progress bars and status messages during computations.
    """
    initialize_session_state()
    current_pedestrian = st.session_state.current_pedestrian

    # Sidebar Sliders for Anthropometric Parameters
    st.sidebar.header("Adjust parameters")
    pedestrian_measures = sliders_for_agent_parameters()
    current_pedestrian.measures = pedestrian_measures

    # Main Page Content

    # Define the URL of the database website
    database_url = "https://datadiscovery.nlm.nih.gov/Images/Visible-Human-Project/ux2j-9i9a/about_data"
    st.markdown(f"Visit the [database website]({database_url}) for the original photos of human body slices.")

    st.subheader("Visualisation")

    # Sidebar menu for selecting visualization type
    menu_option = st.selectbox(
        "Choose an option",
        [
            "Orthogonal projection",
            "Body in 3D as a superposition of slices",
            "Body in 3D with a mesh",
        ],
        label_visibility="collapsed",
    )

    if menu_option != "Orthogonal projection":
        if cst_app.SHOW_DEV:
            x_translation, y_translation, rotation_angle = sliders_for_agent_position()
            current_pedestrian.translate_body3D(x_translation, y_translation, dz=0.0)
            current_pedestrian.rotate_body3D(rotation_angle)

    col1, _ = st.columns([2.0, 1])
    with col1:
        # Display content based on the selected menu option
        if menu_option == "Orthogonal projection":
            current_pedestrian.rotate_body3D(90.0)
            orthogonal_projection_option(current_pedestrian)

        elif menu_option == "Body in 3D as a superposition of slices":
            slices_option(current_pedestrian)

        elif menu_option == "Body in 3D with a mesh":
            mesh_option(current_pedestrian)

    # Download data button
    download_data(current_pedestrian)
