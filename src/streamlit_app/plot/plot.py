"""Contains functions to plot the geometric shapes of the pedestrian, the crowd and the anthropometric data."""

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

import logging
from typing import Optional

import cmcrameri as cram
import matplotlib.axes as maxes
import matplotlib.colors as mcolors
import matplotlib.figure as mfig
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pyvista as pv
from matplotlib.colors import Normalize, to_rgba
from matplotlib.typing import ColorType
from mpl_toolkits.axes_grid1 import make_axes_locatable
from numpy.typing import NDArray
from shapely.geometry import MultiPolygon, Polygon
from streamlit.delta_generator import DeltaGenerator

import configuration.utils.constants as cst
import streamlit_app.utils.functions as fun
from configuration.models.agents import Agent
from configuration.models.crowd import Crowd

plt.rcParams.update(
    {
        "font.size": 25,
        "figure.dpi": 300,
    }
)


def display_shape2D(agents: list[Agent]) -> go.Figure:
    """
    Generate a Plotly figure visualizing the 2D shapes of the given agents.

    Parameters
    ----------
    agents : list[Agent]
        List of Agent objects to visualize.

    Returns
    -------
    go.Figure
        Plotly figure displaying the agents' 2D shapes.

    Notes
    -----
    - If an agent's shape is a `Polygon`, it is directly plotted with its exterior boundary.
    - If an agent's shape is a `MultiPolygon`, each individual polygon in the collection is plotted separately.
    - The centroid of each shape (or collection of shapes) is computed and annotated with the corresponding agent's ID.
    """
    # Initialize a Plotly figure
    fig = go.Figure()

    # Add each agent's shape to the plot
    for id_agent, agent in enumerate(agents):
        id_agent += 1
        geometric_agent = agent.shapes2D.get_geometric_shape()
        if isinstance(geometric_agent, Polygon):
            x, y = geometric_agent.exterior.xy
            fig.add_trace(
                go.Scatter(
                    x=np.array(x),
                    y=np.array(y),
                    fill="toself",
                    mode="lines",
                    line={"color": "black", "width": 1},
                    fillcolor="rgba(255, 255, 0, 0.5)",
                    name=f"agent {id_agent}",
                )
            )

            # Add pedestrian ID as annotation
            centroid_x = np.mean(x)
            centroid_y = np.mean(y)
            fig.add_annotation(
                x=centroid_x,
                y=centroid_y,
                text=f"agent {id_agent}",
                showarrow=False,
                font={"size": 16},
                align="center",
            )

        # If the agent's shape is a MultiPolygon, plot each polygon separately
        elif isinstance(geometric_agent, MultiPolygon):
            for polygon in geometric_agent.geoms:
                x, y = polygon.exterior.xy
                fig.add_trace(
                    go.Scatter(
                        x=np.array(x),
                        y=np.array(y),
                        fill="toself",
                        mode="lines",
                        line={"color": "black", "width": 1},
                        fillcolor="rgba(255, 255, 0, 0.5)",
                    )
                )

            # Add pedestrian ID as annotation
            centroid_x = np.mean([np.mean(polygon.exterior.xy[0]) for polygon in geometric_agent.geoms])
            centroid_y = np.mean([np.mean(polygon.exterior.xy[1]) for polygon in geometric_agent.geoms])
            fig.add_annotation(
                x=centroid_x,
                y=centroid_y,
                text=f"agent {id_agent}",
                showarrow=False,
                font={"size": 16},
                align="center",
            )

    # Set layout properties
    x_max = max(agent.shapes2D.get_geometric_shape().bounds[2] for agent in agents)
    y_max = max(agent.shapes2D.get_geometric_shape().bounds[3] for agent in agents)
    x_min = min(agent.shapes2D.get_geometric_shape().bounds[0] for agent in agents)
    y_min = min(agent.shapes2D.get_geometric_shape().bounds[1] for agent in agents)

    fig.update_layout(
        xaxis={
            "scaleanchor": "y",
            "showgrid": False,
            "title_standoff": 15,
            "title": "X [cm]",
            "title_font": {"size": 20},
            "tickfont": {"size": 16},
            "range": [x_min, x_max],
        },
        yaxis={
            "showgrid": False,
            "title_standoff": 15,
            "title": "Y [cm]",
            "title_font": {"size": 20},
            "tickfont": {"size": 16},
            "range": [y_min, y_max],
        },
        showlegend=False,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        width=550,
        height=550,
    )

    return fig


def display_body3D_orthogonal_projection(
    agent: Agent, extra_info: Optional[tuple[DeltaGenerator, DeltaGenerator]] = None
) -> mfig.Figure:
    """
    Generate a matplotlib figure showing the orthogonal projection of a pedestrian's 3D body.

    Parameters
    ----------
    agent : Agent
        An Agent object with 3D shapes accessible via `agent.shapes3D.shapes`,
        where keys are heights as float and values are MultiPolygon.
    extra_info : tuple[DeltaGenerator, DeltaGenerator], optional
        A tuple containing:
            - DeltaGenerator: Streamlit object for updating the progress bar.
            - DeltaGenerator: Streamlit object for displaying status messages.

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure showing the orthogonal projection of the pedestrian's 3D body.

    Raises
    ------
    ValueError
        If `agent.shapes3D` or `agent.shapes3D.shapes` is `None`.
        If any shape in `agent.shapes3D.shapes` is not a `MultiPolygon`.
    """
    # Check if the agent's 3D shapes are available
    if agent.shapes3D is None or agent.shapes3D.shapes is None:
        raise ValueError("agent.shapes3D or agent.shapes3D.shapes is None")

    # Create a ScalarMappable object for color mapping
    sm = plt.cm.ScalarMappable(
        cmap="coolwarm",
        norm=Normalize(vmin=0, vmax=max(agent.shapes3D.shapes.keys(), key=float)),
    )

    # Initialize a Matplotlib figure
    fig, ax = plt.subplots(figsize=(11, 11))

    # Normalize heights for color mapping
    min_height = min(agent.shapes3D.shapes.keys(), key=float)
    max_height = max(agent.shapes3D.shapes.keys(), key=float)

    # Plot each polygon at different heights
    for height in sorted(agent.shapes3D.shapes.keys(), key=float):
        multi_polygon = agent.shapes3D.shapes[height]
        if not isinstance(multi_polygon, MultiPolygon):
            raise ValueError("multi_polygon is not a MultiPolygon")
        proportion_completed = (height - min_height) / (max_height - min_height)
        if extra_info is not None:
            fun.update_progress_bar(extra_info[0], extra_info[1], proportion_completed)
        for polygon in multi_polygon.geoms:
            x, y = polygon.exterior.xy
            ax.plot(x, y, color=sm.to_rgba(np.array([height])), alpha=0.6, linewidth=2)

    # Add a colorbar with inverted orientation (red at top)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.2)

    # Set colorbar properties
    plt.colorbar(sm, cax=cax, label="Altitude [cm]")

    # Set plot properties
    ax.set_title(f"Orthogonal projection of a {agent.measures.measures['sex']}")
    ax.margins(0)
    ax.set_aspect("equal")
    ax.set_xlabel("X [cm]")
    ax.set_ylabel("Y [cm]")
    plt.tight_layout()

    return fig


def display_body3D_polygons(agent: Agent, extra_info: Optional[tuple[DeltaGenerator, DeltaGenerator]] = None) -> go.Figure:
    """
    Generate a Plotly figure object of a 3D representation of an agent body from the polygons that constitute it.

    Parameters
    ----------
    agent : Agent
        The agent object containing 3D shapes (agent.shapes3D) and associated measurements.
    extra_info : tuple[DeltaGenerator, DeltaGenerator], optional
        A tuple containing:
            - DeltaGenerator: Streamlit object for updating the progress bar.
            - DeltaGenerator: Streamlit object for displaying status messages.

    Returns
    -------
    go.Figure
        A Plotly figure object representing the 3D body made of polygons.

    Raises
    ------
    ValueError
        If agent.shapes3D or agent.shapes3D.shapes is None, or if any shape
        in agent.shapes3D.shapes is not a MultiPolygon.
    """
    # Check if the agent's 3D shapes are available
    if agent.shapes3D is None or agent.shapes3D.shapes is None:
        raise ValueError("agent.shapes3D or agent.shapes3D.shapes is None")

    # Initialize a Plotly figure
    fig = go.Figure()

    # Normalize heights for color mapping
    min_height = min(agent.shapes3D.shapes.keys(), key=float)
    max_height = max(agent.shapes3D.shapes.keys(), key=float)

    # Add each polygon to the 3D plot
    for height in sorted(agent.shapes3D.shapes.keys(), key=float):
        multi_polygon = agent.shapes3D.shapes[height]

        # Check if multi_polygon is a MultiPolygon object
        if not isinstance(multi_polygon, MultiPolygon):
            raise ValueError("multi_polygon is not a MultiPolygon")

        # Normalize height for color scale
        normalized_height = (height - min_height) / (max_height - min_height)  # Normalize height for color scale

        # Update progress bar
        if extra_info is not None:
            fun.update_progress_bar(extra_info[0], extra_info[1], normalized_height)

        # Assign color based on normalized height
        if agent.measures.measures["sex"] == "female":
            # Gradient from green to red
            color = f"rgba(255, {int(205 * (normalized_height))}, {int(205 * (1 - normalized_height))}, 0.8)"
        else:
            # Gradient from blue to red
            color = f"rgba({int(205 * (1 - normalized_height))}, {int(205 * (normalized_height))}, 255, 0.8)"

        # Plot each polygon
        for polygon in multi_polygon.geoms:
            x, y = polygon.exterior.xy
            fig.add_trace(
                go.Scatter3d(
                    x=np.array(x),
                    y=np.array(y),
                    z=np.full_like(x, height),
                    mode="lines",
                    line={"width": 2, "color": color},
                )
            )

    # Determine the maximum range for equal scaling
    x_range = fun.compute_range(agent, axis="x")
    y_range = fun.compute_range(agent, axis="y")
    z_range = max_height - min_height
    max_range = max(x_range, y_range, z_range)

    # Set layout properties
    fig.update_layout(
        scene={
            "xaxis": {"title": "X [cm]", "title_font": {"size": 16}, "tickfont": {"size": 14}},
            "yaxis": {"title": "Y [cm]", "title_font": {"size": 16}, "tickfont": {"size": 14}},
            "zaxis": {"title": "Altitude [cm]", "title_font": {"size": 16}, "tickfont": {"size": 14}},
            "aspectmode": "manual",
            "aspectratio": {
                "x": x_range / max_range,
                "y": y_range / max_range,
                "z": z_range / max_range,
            },
        },
        showlegend=False,
        width=500,
        height=900,
        scene_camera={"eye": {"x": 1.5, "y": 0.4, "z": 0.5}},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )

    return fig


def display_body3D_mesh(
    agent: Agent, precision: int = 40, extra_info: Optional[tuple[DeltaGenerator, DeltaGenerator]] = None
) -> go.Figure:
    """
    Generate a Plotly figure object of a continuous 3D mesh connecting contours at different heights.

    This function generates a smooth 3D mesh visualization of an agent by connecting shape contours
    at various heights using Plotly's Mesh3d. It fills missing triangles and smooths the mesh surface.

    Parameters
    ----------
    agent : Agent
        An instance of the Agent class containing 3D shape data.
    precision : int, optional
        The number of layers to be displayed in the mesh.
    extra_info : tuple[DeltaGenerator, DeltaGenerator], optional
        A tuple containing:
            - DeltaGenerator: Streamlit object for updating the progress bar.
            - DeltaGenerator: Streamlit object for displaying status messages.

    Returns
    -------
    go.Figure
        A Plotly Figure object displaying the generated 3D mesh.

    Raises
    ------
    ValueError
        If agent.shapes3D or agent.shapes3D.shapes is None.
    """
    # Check if the agent's 3D shapes are available
    if agent.shapes3D is None or agent.shapes3D.shapes is None:
        raise ValueError("agent.shapes3D or agent.shapes3D.shapes is None")

    # Extract every nth height to reduce the number of vertices
    skip_every = len(agent.shapes3D.shapes.keys()) // precision
    new_body: dict[float, MultiPolygon] = {
        height: multi_polygon for idx, (height, multi_polygon) in enumerate(agent.shapes3D.shapes.items()) if idx % skip_every == 0
    }
    logging.info("Number of layers: %d", len(new_body))

    # Sort the heights in descending order
    sorted_heights = np.array(sorted(new_body.keys(), reverse=True, key=float))

    # Initialize arrays to store vertices and triangles
    all_points: NDArray[np.float64] = np.empty((0, 3), dtype=float)
    all_triangles: NDArray[np.int64] = np.empty((0, 3), dtype=int)

    # Loop through consecutive heights and connect contours with triangular meshes
    for h_idx in range(len(sorted_heights) - 1):
        # Update progress bar
        percent_completed = (sorted_heights[h_idx] - sorted_heights[0]) / (sorted_heights[-1] - sorted_heights[0])
        if extra_info is not None:
            fun.update_progress_bar(extra_info[0], extra_info[1], percent_completed)

        # Extract high and low contours for the current height pair
        height_high, height_low = sorted_heights[h_idx], sorted_heights[h_idx + 1]
        high_contours: MultiPolygon = new_body[height_high]
        low_contours: MultiPolygon = new_body[height_low]

        # Loop through high contours and connect them with low contours
        for polygon_high in high_contours.geoms:
            # Extract coordinates for high and low contours
            x_high, y_high = polygon_high.exterior.xy
            x_high, y_high = np.array(x_high), np.array(y_high)
            z_high = np.full_like(x_high, height_high)

            x_low, y_low = fun.extract_coordinates(low_contours)
            z_low = np.full_like(x_low, height_low)

            # Append high and low contours to the vertices array
            start_idx_high = all_points.shape[0]
            points_high: NDArray[np.float64] = np.column_stack((x_high, y_high, z_high))
            all_points = np.vstack((all_points, points_high))

            start_idx_low = all_points.shape[0]
            points_low = np.column_stack((x_low, y_low, z_low))
            all_points = np.vstack((all_points, points_low))

            # Connect high and low contours with triangular meshes
            for idx in range(len(x_high) - 1):
                # Find the nearest vertex in the low contour
                nearest_idx = np.argmin((x_low - x_high[idx]) ** 2 + (y_low - y_high[idx]) ** 2)
                # Triangle 1: two vertices from high contour and one from low contour
                triangle1 = np.column_stack(
                    (
                        start_idx_high + idx,
                        start_idx_high + idx + 1,
                        start_idx_low + nearest_idx,
                    )
                )
                all_triangles = np.vstack((all_triangles, triangle1))
                # Triangle 2: one vertex from high contour and two from low contour
                triangle2 = np.column_stack(
                    (
                        start_idx_high + idx + 1,
                        start_idx_low + nearest_idx,
                        start_idx_low + (nearest_idx + 1) % len(x_low),
                    )
                )
                all_triangles = np.vstack((all_triangles, triangle2))

    # Fill holes in the mesh and remove triangles associated with the last layer of vertices
    faces = np.column_stack((np.full(len(all_triangles), 3), all_triangles)).flatten()
    mesh_pv = pv.PolyData(all_points, faces)
    try:
        filled_mesh_pv = mesh_pv.fill_holes(5.0)
        points_filled = filled_mesh_pv.points
        faces_filled = filled_mesh_pv.faces.reshape(-1, 4)[:, 1:]
        all_triangles_filled = faces_filled
    except (ValueError, RuntimeError) as e:
        logging.info("Error filling holes: %s", e)
        all_triangles_filled = all_triangles

    # Filter the mesh by removing vertices and triangles below a certain threshold
    min_height = min(agent.shapes3D.shapes.keys())
    points_filled, all_triangles_filled = fun.filter_mesh_by_z_threshold(
        points_filled, all_triangles_filled, z_threshold=min_height + 0.1
    )

    # Normalize the height values for color mapping
    color_scale_name = "viridis" if agent.measures.measures["sex"] == "male" else "inferno"
    norm = Normalize(vmin=np.min(points_filled[:, 2]), vmax=np.max(points_filled[:, 2]))
    colorscale_values = norm(points_filled[:, 2])
    colorscale_values = plt.cm.get_cmap(color_scale_name)(colorscale_values)[:, :3]
    vertex_colors = [f"rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})" for r, g, b in colorscale_values]

    logging.info("Plotting...")

    # Create a Plotly figure with the filled mesh
    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=points_filled[:, 0],
                y=points_filled[:, 1],
                z=points_filled[:, 2],
                i=all_triangles_filled[:, 0],
                j=all_triangles_filled[:, 1],
                k=all_triangles_filled[:, 2],
                facecolor=vertex_colors,
                opacity=1.0,
                colorscale=color_scale_name,
                intensity=points_filled[:, 2],
                showscale=False,
            )
        ]
    )

    # Determine the maximum range for equal scaling
    x_range = np.ptp(points_filled[:, 0])
    y_range = np.ptp(points_filled[:, 1])
    z_range = np.ptp(points_filled[:, 2])
    max_range = max(x_range, y_range, z_range)

    # Set layout properties
    fig.update_layout(
        scene={
            "aspectmode": "manual",
            "aspectratio": {
                "x": x_range / max_range,
                "y": y_range / max_range,
                "z": z_range / max_range,
            },
            "xaxis": {"title": "X [cm]", "title_font": {"size": 16}, "tickfont": {"size": 14}},
            "yaxis": {"title": "Y [cm]", "title_font": {"size": 16}, "tickfont": {"size": 14}},
            "zaxis": {"title": "Altitutde [cm]", "title_font": {"size": 16}, "tickfont": {"size": 14}},
        },
        width=500,
        height=900,
        scene_camera={"eye": {"x": 1.5, "y": 0.4, "z": 0.5}},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
    )

    return fig


def display_crowd2D(crowd: Crowd) -> tuple[mfig.Figure, maxes.Axes]:
    """
    Generate a matplotlib figure object of a crowd of agents in 2D.

    Parameters
    ----------
    crowd : Crowd
        The crowd object containing agents with 2D geometric shapes.

    Returns
    -------
    tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]
        A tuple containing a matplotlib figure object and axes displaying the 2D plot of the crowd.

    Raises
    ------
    AttributeError
        If any agent in the crowd lacks the required 2D shape attributes.
    TypeError
        If an agent's geometric shape is neither a Polygon nor a MultiPolygon.
    """
    # Create a Normalize object to scale values between the minimum and maximum areas of 2D shapes of all agents in the crowd
    norm = Normalize(
        vmin=min(agent.shapes2D.get_area() for agent in crowd.agents),
        vmax=max(agent.shapes2D.get_area() for agent in crowd.agents),
    )
    # Set text size based on the area of the crowd boundaries or the number of agents
    if not crowd.boundaries.is_empty:
        txt_size = max(int(8 * 10**5 / crowd.boundaries.area), 10)
    else:
        txt_size = max(int(80 / crowd.get_number_agents()), 10)

    # Initialize a Matplotlib figure
    fig, ax = plt.subplots(figsize=(9, 9))
    # Plot each agent's shape
    for id_agent, agent in enumerate(crowd.agents):
        agent_geometric = agent.shapes2D.get_geometric_shape()
        agent_area = agent.shapes2D.get_area()
        color = cram.cm.hawaii(norm(agent_area))  # pylint: disable=no-member

        # Check if agent_geomtetric is of type Polygon
        if isinstance(agent_geometric, Polygon):
            x, y = agent_geometric.exterior.xy
            ax.fill(x, y, alpha=0.8, color=color)
            ax.plot(x, y, color="black", linewidth=0.5)

            # Add pedestrian ID as annotation
            centroid_x = np.mean(x)
            centroid_y = np.mean(y)
            ax.annotate(
                f"{id_agent}",
                xy=(centroid_x, centroid_y),
                xytext=(centroid_x, centroid_y),
                fontsize=txt_size,
                color="black",
                ha="center",  # horizontal alignment
                va="center",  # vertical alignment
            )

        # If the agent's shape is a MultiPolygon, plot each polygon separately
        elif isinstance(agent_geometric, MultiPolygon):
            agent_area = agent.shapes2D.get_area()
            for polygon in agent_geometric.geoms:
                x, y = polygon.exterior.xy
                ax.fill(x, y, alpha=0.8, color=color)
                ax.plot(x, y, color="black", linewidth=0.5)

            # Add pedestrian ID as annotation
            centroid_x = np.mean([np.mean(polygon.exterior.xy[0]) for polygon in agent_geometric.geoms])
            centroid_y = np.mean([np.mean(polygon.exterior.xy[1]) for polygon in agent_geometric.geoms])
            ax.annotate(
                f"{id_agent}",
                xy=(centroid_x, centroid_y),
                xytext=(centroid_x, centroid_y),
                fontsize=txt_size,
                color="black",
                ha="center",  # horizontal alignment
                va="center",  # vertical alignment
            )

    bounds = np.array([agent.shapes2D.get_geometric_shape().bounds for agent in crowd.agents])
    x_min, y_min = bounds[:, [0, 1]].min(axis=0)
    x_max, y_max = bounds[:, [2, 3]].max(axis=0)

    # If boundaries exist, include them in the limits
    if not crowd.boundaries.is_empty:
        bx, by = crowd.boundaries.exterior.xy
        ax.plot(bx, by, color="grey", linewidth=1, linestyle="dashed")
        # Update limits to include boundaries if they are not too large
        if not np.isclose(np.max(by), cst.INFINITE) and not np.isclose(np.max(bx), cst.INFINITE):
            x_min = min(x_min, np.min(bx))
            y_min = min(y_min, np.min(by))
            x_max = max(x_max, np.max(bx))
            y_max = max(y_max, np.max(by))

    # Set plot properties
    ax.set(xlim=(x_min, x_max), ylim=(y_min, y_max), aspect="equal", xlabel="x [cm]", ylabel="y [cm]")
    ax.set_aspect("equal", "box")
    fig.tight_layout()

    return fig, ax


def display_crowd3D_slices_by_slices(crowd: Crowd) -> go.Figure:
    """
    Generate an animated Plotly figure of a 3D crowd made of layers of 2D polygons at different altitude.

    For a given set of altitutdes, this function plots all polygons at that altitude. If there is not a
    polygon for a given agent at that specific altitude, then the polygon with the nearest altitude is shown.
    No interpolation is performed. The result is an animated Plotly figure, where each animation frame
    corresponds to a different altitude.

    Parameters
    ----------
    crowd : Crowd
        The crowd object containing agents.

    Returns
    -------
    go.Figure
        An animated Plotly figure with a slider to select the altitude. Each frame displays all polygons of
        all agents at a given altitude. Polygon color encodes agent area. Agent indices are labeled at their centroid.
    """
    # Normalize color by 2D area
    norm = Normalize(
        vmin=min(agent.shapes2D.get_area() for agent in crowd.agents),
        vmax=max(agent.shapes2D.get_area() for agent in crowd.agents),
    )

    # Set text size based on the area of the crowd boundaries or the number of agents
    txt_size = (
        max(int(8 * 10**5 / crowd.boundaries.area), 10)
        if not crowd.boundaries.is_empty
        else max(int(80 / crowd.get_number_agents()), 10)
    )

    # Initialize variables
    highest_agent_height = 0
    agent_heights = []
    current_polygons = []
    all_altitudes = []
    for agent in crowd.agents:
        # Round heights to int and update agent.shapes3D.shapes
        new_shapes = {}
        for height, multipolygon in agent.shapes3D.shapes.items():
            rounded_height = int(height)
            if rounded_height not in new_shapes:
                new_shapes[rounded_height] = multipolygon
                all_altitudes.append(rounded_height)
        agent.shapes3D.shapes = new_shapes

        # Track the highest agent height
        agent_height = agent.shapes3D.get_height()
        highest_agent_height = max(highest_agent_height, agent_height)

        # Collect agent heights and initialize polygons
        agent_heights.append(agent_height)
        current_polygons.append(MultiPolygon([]))

    all_unique_altitudes: NDArray[np.int64] = np.unique(all_altitudes)
    height_agent_traces = []
    total_covered_area_per_altitude = {}

    # Loop through each height and create traces for each agent
    for height in all_unique_altitudes:
        traces = []
        sum_area = 0
        for idx, (agent, max_height) in enumerate(zip(crowd.agents, agent_heights, strict=False)):
            if height > max_height:
                continue

            # Get the multipolygon for this height, or use the last one
            multi_polygon = agent.shapes3D.shapes.get(height, current_polygons[idx])
            current_polygons[idx] = multi_polygon
            sum_area += multi_polygon.area

            # Check if multi_polygon is a MultiPolygon object
            if not isinstance(multi_polygon, MultiPolygon) or multi_polygon.is_empty:
                continue

            # Add each polygon as a separate trace
            for polygon in multi_polygon.geoms:
                if polygon.is_empty:
                    continue
                x, y = polygon.exterior.xy
                r, g, b = [int(255 * x) for x in cram.cm.hawaii(norm(agent.shapes2D.get_area()))[:3]]  # pylint: disable=no-member
                traces.append(
                    go.Scatter(
                        x=np.array(x),
                        y=np.array(y),
                        fill="toself",
                        mode="lines",
                        line={"color": "black", "width": 1},
                        fillcolor=f"rgba({r},{g},{b},0.8)",
                        visible=False,
                        name=f"agent {idx}",
                    )
                )

            # Add centroid label
            centroid = multi_polygon.centroid
            traces.append(
                go.Scatter(
                    x=[centroid.x],
                    y=[centroid.y],
                    text=[f"{idx}"],
                    mode="text",
                    showlegend=False,
                    textfont={"size": txt_size, "family": "Arial"},
                    visible=False,
                    hoverinfo="skip",
                )
            )
        height_agent_traces.append(traces)
        total_covered_area_per_altitude[height] = sum_area

    # Create a Plotly figure with all traces and update the hover template
    fig = go.Figure()
    [fig.add_trace(trace) for traces in height_agent_traces for trace in traces]
    fig.update_traces(hovertemplate="<b>centroid</b><br>" + "x: %{x:.2f} cm<br>" + "y: %{y:.2f} cm<extra></extra>")

    # Get the number of traces for each altitude
    n_traces_per_height = [len(traces) for traces in height_agent_traces]
    cum_traces = np.cumsum([0] + n_traces_per_height)
    total_traces = cum_traces[-1]

    # Create steps for the slider
    steps = []
    for i, height in enumerate(all_unique_altitudes):
        visible = [cum_traces[i] <= j < cum_traces[i + 1] for j in range(total_traces)]
        area = int(total_covered_area_per_altitude.get(height, 0))
        step = {
            "method": "update",
            "args": [{"visible": visible}, {"title.text": f"Horizontal slices | Covered area: {area} cm² | Altitude: {height} cm"}],
            "label": f"{height} cm",
        }
        steps.append(step)

    # Create a slider for altitude selection
    mid_min_agent_height = int(np.min(agent_heights) * cst.HEIGHT_OF_BIDELTOID_OVER_HEIGHT)
    slider_start_index = np.abs(all_unique_altitudes - mid_min_agent_height).argmin()
    sliders = [
        {
            "active": slider_start_index,
            "currentvalue": {"prefix": "Altitude: "},  # Appears only here, no covered area
            "pad": {"t": 50},
            "steps": steps,
        }
    ]

    # Calculate bounds
    bounds = np.array([multipolygon.bounds for agent in crowd.agents for multipolygon in agent.shapes3D.shapes.values()])
    x_min, y_min = bounds[:, [0, 1]].min(axis=0)
    x_max, y_max = bounds[:, [2, 3]].max(axis=0)

    # Include boundaries if present
    if hasattr(crowd, "boundaries") and not crowd.boundaries.is_empty:
        bx, by = crowd.boundaries.exterior.xy
        # Update limits to include boundaries if they are not too large
        if not np.isclose(np.max(by), cst.INFINITE) and not np.isclose(np.max(bx), cst.INFINITE):
            x_min = min(x_min, np.min(bx))
            y_min = min(y_min, np.min(by))
            x_max = max(x_max, np.max(bx))
            y_max = max(y_max, np.max(by))

    # Update layout with slider
    fig.update_layout(
        sliders=sliders,
        xaxis={
            "scaleanchor": "y",
            "showgrid": False,
            "range": [x_min, x_max],
            "title": "X [cm]",
            "title_font": {"size": 20},
            "tickfont": {"size": 16},
        },
        yaxis={
            "scaleanchor": "x",
            "showgrid": False,
            "range": [y_min, y_max],
            "title": "Y [cm]",
            "title_font": {"size": 20},
            "tickfont": {"size": 16},
        },
        showlegend=False,
        title="Horizontal slices",
        margin={"l": 0, "r": 0, "t": 25, "b": 0},
        width=550,
        height=550,
    )

    # Make only traces for the first height visible
    for i in range(total_traces):
        fig.data[i].visible = cum_traces[slider_start_index] <= i < cum_traces[slider_start_index + 1]

    return fig


def display_crowd3D_whole_3Dscene(crowd: Crowd) -> go.Figure:
    """
    Generate a 3D Plotly figure of a 3D crowd.

    Parameters
    ----------
    crowd : Crowd
        The crowd object containing agents.

    Returns
    -------
    plotly.graph_objects.Figure
        A Plotly figure object representing the 3D crowd.
    """
    norm = Normalize(
        vmin=min(agent.shapes2D.get_area() for agent in crowd.agents),
        vmax=max(agent.shapes2D.get_area() for agent in crowd.agents),
    )

    # Initialize a Plotly figure
    fig = go.Figure()

    # Add each agent's 3D mesh to the plot
    for id_agent, agent in enumerate(crowd.agents):
        rgba_color = cram.cm.hawaii(norm(agent.shapes2D.get_area()))  # pylint: disable=no-member

        # Add each polygon to the 3D plot
        for _, height in enumerate(sorted(agent.shapes3D.shapes.keys(), key=int)):
            # Get the multipolygon for this height
            multi_polygon = agent.shapes3D.shapes[height]

            # Check if multi_polygon is a MultiPolygon object
            if not isinstance(multi_polygon, MultiPolygon):
                raise ValueError("multi_polygon is not a MultiPolygon")

            # Plot each polygon
            for polygon in multi_polygon.geoms:
                x, y = polygon.exterior.xy
                fig.add_trace(
                    go.Scatter3d(
                        x=np.array(x),
                        y=np.array(y),
                        z=np.full_like(x, height),
                        mode="lines",
                        line={
                            "width": 2,
                            "color": mcolors.to_hex(rgba_color),
                        },
                        showlegend=False,
                        hovertemplate=f"<b>agent {id_agent}</b><br>"
                        + "x: %{x:.2f} cm<br>"
                        + "y: %{y:.2f} cm<br>"
                        + "z: %{z:.2f} cm<br>"
                        + "<extra></extra>",
                    )
                )

    # Calculate bounds from agents' 2D shapes
    bounds = np.array([multipolygon.bounds for agent in crowd.agents for multipolygon in agent.shapes3D.shapes.values()])
    x_min, y_min = bounds[:, [0, 1]].min(axis=0)
    x_max, y_max = bounds[:, [2, 3]].max(axis=0)

    # If boundaries exist, include them in the limits and plot as a dashed line
    if not crowd.boundaries.is_empty:
        bx, by = crowd.boundaries.exterior.xy
        # Update limits to include boundaries if they are not too large
        if not np.isclose(np.max(by), cst.INFINITE) and not np.isclose(np.max(bx), cst.INFINITE):
            x_min = min(x_min, np.min(bx))
            y_min = min(y_min, np.min(by))
            x_max = max(x_max, np.max(bx))
            y_max = max(y_max, np.max(by))

    x_range = x_max - x_min
    y_range = y_max - y_min
    z_range = max(agent.shapes3D.get_height() for agent in crowd.agents)
    max_range = max(x_range, y_range, z_range)

    # Set layout properties
    fig.update_layout(
        title="In 3D",
        scene={
            "xaxis": {"title": "X [cm]", "range": [x_min, x_max], "title_font": {"size": 20}, "tickfont": {"size": 16}},
            "yaxis": {"title": "Y [cm]", "range": [y_min, y_max], "title_font": {"size": 20}, "tickfont": {"size": 16}},
            "zaxis": {"title": "Altitude [cm]", "title_font": {"size": 20}, "tickfont": {"size": 16}},
            "aspectmode": "manual",
            "aspectratio": {
                "x": x_range / max_range,
                "y": y_range / max_range,
                "z": z_range / max_range,
            },
        },
        scene_camera={"eye": {"x": 0.05, "y": -2.3, "z": 0.8}},
        margin={"l": 0, "r": 0, "t": 25, "b": 0},
        showlegend=False,
        height=900,
    )

    return fig


def display_distribution(df: pd.DataFrame, column: str) -> go.Figure:
    """
    Generate a Plotly figure of the distribution of a specified DataFrame column as overlaid histograms for each sex.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data. Must include a 'sex' column.
    column : str
        Name of the column to plot.

    Returns
    -------
    go.Figure
        Plotly Figure object with overlaid histograms for males and females.

    Raises
    ------
    ValueError
        If the specified column or the 'sex' column is not found in the DataFrame.
    """
    # Convert the column name to lowercase for case-insensitive matching
    column = column.lower()

    # Check if the specified column is present in the DataFrame
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in the DataFrame.")
    if "sex" not in df.columns:
        raise ValueError("Column 'sex' not found in the DataFrame, required for hue.")

    # Initialize a Plotly figure
    fig = go.Figure()

    # Select values associated with the sex male or female
    values_male = df[df["sex"] == "male"][column]
    values_female = df[df["sex"] == "female"][column]

    # Set number of bins for weight [kg]
    nbins_male = {"chest depth [cm]": 45, "bideltoid breadth [cm]": 50, "height [cm]": 40, "weight [kg]": 40, "sex": None}
    nbins_female = {"chest depth [cm]": 45, "bideltoid breadth [cm]": 55, "height [cm]": 30, "weight [kg]": 40, "sex": None}

    # Add histograms
    fig.add_trace(
        go.Histogram(
            x=values_male,
            name="male",
            marker_color="blue",
            nbinsx=nbins_male[column],
        )
    )
    # Overlay the histograms
    fig.add_trace(
        go.Histogram(
            x=values_female,
            name="female",
            marker_color="red",
            nbinsx=nbins_female[column],
        )
    )

    # Set opacity for overlapping histograms
    fig.update_traces(opacity=0.5)

    # Add custom hover text using hovertemplate
    if column not in ["sex", "weight [kg]"]:
        fig.update_traces(hovertemplate=f"<b>{column[:-5]}</b>" + " = %{x} cm<br><b>count = </b>%{y}</b>")
    elif column == "weight [kg]":
        fig.update_traces(hovertemplate=f"<b>{column[:-5]}</b>" + " = %{x} kg<br><b>count = </b>%{y}</b>")
    elif column == "sex":
        fig.update_traces(hovertemplate=f"<b>{column}</b>" + " = %{x}<br><b>count = </b>%{y}</b><extra></extra>")

    # Set layout properties
    fig.update_layout(
        barmode="overlay",
        xaxis_title=column,
        yaxis_title="count",
        legend_title_text="",
        font={"size": 18, "color": "black"},  # General font size
        xaxis={"title_font": {"size": 20}, "tickfont": {"size": 16}},
        yaxis={"title_font": {"size": 20}, "tickfont": {"size": 16}},
        legend={"font": {"size": 16}},
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        width=600,
        height=500,
    )

    return fig


def darken(color: ColorType, factor: float = 0.8) -> tuple[float, float, float, float]:
    """
    Return a darker shade of `color` without changing its hue.

    Parameters
    ----------
    color : ColorType
        Any Matplotlib-acceptable color specification.
    factor : float, optional
        Multiplier for RGB channels; < 1 darkens, > 1 lightens.

    Returns
    -------
    RGBA
        Darkened color as (r, g, b, a) with components in [0.0, 1.0].
    """
    r, g, b, a = to_rgba(color)
    return (r * factor, g * factor, b * factor, a)
