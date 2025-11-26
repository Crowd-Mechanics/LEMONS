"""Utility functions for plotting."""

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

from typing import Literal

import numpy as np
from numpy.typing import NDArray
from shapely.geometry import MultiPolygon
from streamlit.delta_generator import DeltaGenerator

from configuration.models.agents import Agent


def extract_coordinates(multi_polygon: MultiPolygon) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Extract x and y coordinates from a MultiPolygon object.

    Parameters
    ----------
    multi_polygon : MultiPolygon
        A MultiPolygon object containing one or more polygons.

    Returns
    -------
    tuple[NDArray[np.float64], NDArray[np.float64]]
        A tuple of two numpy arrays:
            - The first array contains the x-coordinates.
            - The second array contains the y-coordinates.
    """
    all_x, all_y = [], []

    # Iterate through each polygon in the MultiPolygon
    for polygon in multi_polygon.geoms:
        x, y = polygon.exterior.xy  # Extract exterior boundary coordinates
        all_x.extend(x)
        all_y.extend(y)

    # Convert lists to NumPy arrays
    return np.array(all_x), np.array(all_y)


def filter_mesh_by_z_threshold(
    all_points: NDArray[np.float64], all_triangles: NDArray[np.float64], z_threshold: float = 0.3
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Filter a 3D mesh by removing vertices and triangles below a given z-coordinate threshold.

    Parameters
    ----------
    all_points : NDArray[np.float64]
        An array representing the coordinates of the vertices in the mesh.
    all_triangles : NDArray[np.float64]
        An array representing the indices of the vertices forming the triangles in the mesh.
    z_threshold : float
        The z-coordinate threshold below which vertices and associated triangles are removed.
        Default is 0.3.

    Returns
    -------
    filtered_points : NDArray[np.float64]
        An array representing the coordinates of the filtered vertices.
    filtered_triangles : NDArray[np.float64]
        An array representing the indices of the vertices forming the filtered triangles.

    Notes
    -----
    - `N` is the number of vertices in the original mesh.
    - `M` is the number of triangles in the original mesh.
    - `P` and `Q` are the numbers of vertices and triangles remaining after filtering, respectively.
    """
    # Step 1: Identify valid vertices (z > threshold)
    valid_vertices_mask = all_points[:, 2] > z_threshold
    valid_indices = np.where(valid_vertices_mask)[0]

    # Step 2: Create a mapping from old vertex indices to new ones
    old_to_new_index = np.full(all_points.shape[0], -1)  # Initialize with -1 for invalid indices
    old_to_new_index[valid_indices] = np.arange(len(valid_indices))  # Map valid indices to new positions

    # Step 3: Filter triangles where all three vertices are valid
    valid_triangles_mask = np.all(np.isin(all_triangles, valid_indices), axis=1)
    filtered_triangles = all_triangles[valid_triangles_mask]

    # Step 4: Update triangle indices to reflect the new vertex indexing
    filtered_triangles = old_to_new_index[filtered_triangles]

    # Step 5: Filter the vertices based on the valid mask
    filtered_points = all_points[valid_vertices_mask]

    return filtered_points, filtered_triangles


def update_progress_bar(progress_bar: DeltaGenerator, status_text: DeltaGenerator, frac: float) -> None:
    """
    Update a progress bar and status text based on the given completion fraction.

    Parameters
    ----------
    progress_bar : DeltaGenerator
        The Streamlit progress bar object to be updated. Typically created using `st.progress()`.
    status_text : DeltaGenerator
        The Streamlit text object to display the status message. Typically created using `st.text()`.
    frac : float
        A value between 0 and 1 representing the completion fraction of the task. For example, `frac=0.5` indicates 50% completion.

    Raises
    ------
    ValueError
        If `frac` is not in [0,1].
    """
    if not 0 <= frac <= 1:
        raise ValueError("The completion fraction 'frac' must be in [0,1].")

    # Update progress bar
    percent_complete = int(frac * 100.0)
    progress_bar.progress(percent_complete)

    # Update status text
    progress_text = "Operation in progress. Please wait. ⏳"
    status_text.text(f"{progress_text} {percent_complete}%")


def compute_range(agent: Agent, axis: Literal["x", "y"]) -> float:
    """
    Compute the range (maximum - minimum) of coordinates along a given axis for an agent's 3D shapes.

    Parameters
    ----------
    agent : Agent
        The agent object containing 3D shape information.
    axis : Literal["x", "y"]
        The axis along which to compute the range.

    Returns
    -------
    float
        The range (maximum - minimum) of coordinates along the specified axis.

    Raises
    ------
    ValueError
        If the axis is not 'x' or 'y', if agent.shapes3D or agent.shapes3D.shapes is None,
        or if any shape in agent.shapes3D.shapes is not a MultiPolygon.
    """
    # Check if axis is either "x" or "y"
    if axis not in ("x", "y"):
        raise ValueError("Axis must be 'x' or 'y'")

    # Check if the agent's 3D shapes are available
    if agent.shapes3D is None or agent.shapes3D.shapes is None:
        raise ValueError("agent.shapes3D or agent.shapes3D.shapes is None")

    # Put the coordinates in a list
    coord_index = 0 if axis == "x" else 1
    coordinates: list[float] = []
    for multi_polygon in agent.shapes3D.shapes.values():
        # Check if multi_polygon is of type MultiPolygon
        if not isinstance(multi_polygon, MultiPolygon):
            raise ValueError("multi_polygon is not a MultiPolygon")

        # Extract coordinates for the given axis from all polygons
        coordinates.extend(coord[coord_index] for polygon in multi_polygon.geoms for coord in polygon.exterior.coords)

    # Compute the range of values (maximum-minimum)
    xy_range: float = np.ptp(coordinates)
    return xy_range
