"""Export agent trajectories from XML files to TrajectoryData and WalkableArea formats used in PedPy."""

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
from pathlib import Path

import numpy as np
import pandas as pd
from pedpy import TrajectoryData, WalkableArea

from configuration.backup.dict_to_xml_and_reverse import geometry_xml_to_dict
from configuration.backup.xml_to_Chaos import export_XML_to_CSV
from configuration.utils.typing_custom import GeometryDataType


def _corners_to_ring(corners: dict[str, dict[str, tuple[float, float]]]) -> list[tuple[float, float]]:
    """
    Convert a dictionary of corners (from XML) to a list of (x, y) tuples representing a closed ring.

    Parameters
    ----------
    corners : dict[str, dict[str, tuple[float, float]]]
        A dictionary where each key is a corner identifier and the value is another dictionary containing "Coordinates"
        as a tuple of (x, y) coordinates.

    Returns
    -------
    list[tuple[float, float]]
        A list of (x, y) tuples representing the corners of a polygon, ensuring that the first and last points are the
        same to form a closed ring.
    """
    pts = []
    for _, v in corners.items():
        if "Coordinates" not in v:
            raise KeyError("Corner entry missing 'Coordinates'.")
        x, y = v["Coordinates"]
        pts.append((float(x), float(y)))

    if len(pts) < 3:
        raise ValueError("Need at least 3 points to define a polygon.")

    # Ensure closed ring: last point equals first point.
    if pts[0] != pts[-1]:
        pts.append(pts[0])

    return pts


def GeometryDict_to_PedPyWalkableArea(geometry_dict: GeometryDataType) -> WalkableArea:
    """
    Convert a geometry dictionary (from XML) to a PedPy WalkableArea object.

    Parameters
    ----------
    geometry_dict : GeometryDataType
        Dictionary containing geometry information, expected to have a structure with "Geometry" -> "Wall" -> "Wall0" with "Corners"
            for the main walkable area, and optionally other wallsrepresenting obstacles.

    Returns
    -------
    WalkableArea
        A PedPy WalkableArea object with the main polygon defined by "Wall0" and any additional walls as obstacles.
    """
    walls = geometry_dict.get("Geometry", {}).get("Wall", {})
    if not walls:
        raise ValueError("No 'Wall' found in Geometry XML.")

    wall0 = walls.get("Wall0")
    if not wall0 or "Corners" not in wall0:
        raise ValueError("No 'Wall0'/'Corners' found; cannot determine walkable area.")

    polygon = _corners_to_ring(wall0["Corners"])

    obstacles: list[list[tuple[float, float]]] = []
    for wall_key, wall_value in walls.items():
        if wall_key == "Wall0":
            continue
        corners = wall_value.get("Corners", {})
        if not corners:
            continue
        obstacles.append(_corners_to_ring(corners))
    return WalkableArea(polygon=polygon, obstacles=obstacles or None)


def export_XML_to_PedPy(
    PathAgentDynamicsXML: Path, PathGeometryXMLfile: Path, PathCSVfile: Path | None = None
) -> tuple[TrajectoryData, WalkableArea]:
    """
    Export trajectories from the AgentDynamics XML files to a TrajectoryData and WalkableArea objects used in PedPy Python library.

    Parameters
    ----------
    PathAgentDynamicsXML : Path
        Path to the XML directory containing the AgentDynamics XML files.
    PathGeometryXMLfile : Path
        Path to the XML file containing geometry information.
    PathCSVfile : Path | None
        Optional path for the intermediate CSV. If None, uses xml_path.with_suffix(".csv").

    Returns
    -------
    tuple[TrajectoryData, WalkableArea]
        PedPy trajectory data with columns ["id", "frame", "x", "y"] and frame_rate = 1/dt.

    Notes
    -----
    Assumes XML files are named with the pattern 'AgentDyn...input t=<time>.xml'.
    The AgentDynamics XML files are first converted into a single CSV file and then converted into a TrajectoryData object.
    Expected CSV columns: t, ID, x, y.
    """
    if not PathAgentDynamicsXML.is_dir():
        raise NotADirectoryError(f"AgentDynamics XML path is not a directory: {PathAgentDynamicsXML}")

    if not PathGeometryXMLfile.exists():
        raise FileNotFoundError(f"Geometry XML file not found: {PathGeometryXMLfile}")

    if PathGeometryXMLfile.suffix.lower() != ".xml":
        raise ValueError("Both PathAgentDynamicsXML and PathGeometryXML must be XML files with .xml extension.")

    if PathCSVfile is not None and PathCSVfile.suffix.lower() != ".csv":
        raise ValueError("PathCSV must have a .csv extension if provided.")

    if PathCSVfile is None:
        PathCSVfile = PathAgentDynamicsXML.with_suffix(".csv")
        logging.info(f"No CSV path provided; using {PathCSVfile} as intermediate file.")
        export_XML_to_CSV(PathCSVfile, PathAgentDynamicsXML)

    df = pd.read_csv(PathCSVfile, usecols=["t", "ID", "x", "y"]).dropna()
    if df.empty:
        raise ValueError(f"No usable rows found in CSV: {PathCSVfile}")

    # Normalize types + ordering
    df["ID"] = df["ID"].astype(int, errors="ignore")
    df["t"] = pd.to_numeric(df["t"], errors="raise")
    df["x"] = pd.to_numeric(df["x"], errors="raise")
    df["y"] = pd.to_numeric(df["y"], errors="raise")
    df = df.dropna(subset=["t", "ID", "x", "y"]).sort_values(["ID", "t"])

    t0 = float(df["t"].min())
    t1 = float(df["t"].max())
    duration = t1 - t0
    if duration < 0:
        raise ValueError("Invalid time range (tmax < tmin).")

    dt = df.groupby("ID")["t"].diff().min().min()
    if dt <= 0:
        raise ValueError("Non-positive time differences found; cannot determine frame rate.")
    if dt < 1e-4:
        logging.warning(f"Very small time step detected ({dt:.2e}s); capping at 0.1s to avoid excessive frame rates.")
        dt = 0.1

    n_frames = int(np.floor(duration / dt)) + 1
    grid = pd.to_timedelta(np.arange(n_frames) * dt, unit="s")  # TimedeltaIndex starting at 0

    per_ped_dfs: list[pd.DataFrame] = []
    for ped_id, g in df.groupby("ID", sort=False):
        g = g.sort_values("t")
        if len(g) < 2:
            continue

        # Make a time index relative to the global start so everyone shares frame=0
        td = pd.to_timedelta(g["t"].to_numpy(dtype=float) - t0, unit="s")

        # Create a DataFrame with x,y indexed by the relative time
        ts = g[["x", "y"]].copy()
        ts.index = td

        # If duplicate timestamps exist, keep last sample
        if ts.index.duplicated().any():
            logging.warning(f"Duplicate timestamps for ped {ped_id}; keeping last.")
            ts = ts[~ts.index.duplicated(keep="last")]

        # Align to global grid and interpolate in time; then fill ends
        ts = ts.reindex(grid).interpolate(method="time").ffill().bfill()

        per_ped_dfs.append(
            pd.DataFrame(
                {
                    "id": np.full(len(grid), ped_id),
                    "frame": np.arange(len(grid), dtype=int),
                    "x": ts["x"].to_numpy(),
                    "y": ts["y"].to_numpy(),
                }
            )
        )

    if not per_ped_dfs:
        raise ValueError("No usable pedestrian trajectories found (all too short/empty).")

    data = pd.concat(per_ped_dfs, ignore_index=True)
    frame_rate = 1.0 / dt

    traj = TrajectoryData(data=data, frame_rate=frame_rate)

    with open(PathGeometryXMLfile, encoding="utf-8") as f:
        geometry_xml = f.read()
    geometry_dict = geometry_xml_to_dict(geometry_xml)

    walkable_area = GeometryDict_to_PedPyWalkableArea(geometry_dict)

    return traj, walkable_area
