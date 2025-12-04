"""
Tests the Coulomb friction interaction between two agents as one slides over the other.

Tests cover:
    - Time and position continuity for each agent
    - Near-zero angular velocity (omega) and near constant orientation (theta) for all agents
    - Agents 0 and 1 should remain static translationally: translational velocity ~ 0, x and y coordinates ~ constants
    - Velocity of Agent 2 should be positive along the x-axis during the slip
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

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from configuration.backup import xml_to_Chaos

#: Tolerance for the constancy of the decisional time step used throughout the simulation (s).
TIME_TOL = 1e-4
#: Maximum allowed spatial jump (m) between consecutive time steps for each agent.
MAX_SPATIAL_JUMP = 1
#: Minimum velocity allowed for agent 2 along x during slip phase (m/s).
VX_TOL = 1e-2
#: Tolerance for near-zero velocities of agent 0 and 1 along x during the whole simulation (m/s).
VX_CONTACT_TOL = 0.5
#: Tolerance for near-zero velocities of agent 0 and 1 along y during the whole simulation (m/s).
VY_CONTACT_TOL = 0.5
#: Tolerance for near-zero angular velocities of all agents during the whole simulation (rad/s).
OMEGA_CONTACT_TOL = 0.5
#: Maximum allowed range for orientation (theta) of all agents during the whole simulation (radians).
DELTA_THETA_CONTACT_TOL = 0.5
#: Maximum allowed range for x of agents 0 and 1 during the whole simulation (m).
DELTA_X_CONTACT_TOL = 0.5
#: Maximum allowed range for y of agents 0 and 1 during the whole simulation (m).
DELTA_Y_CONTACT_TOL = 0.5


@pytest.fixture(scope="session")
def df() -> pd.DataFrame:
    """
    Export to CSV the XML files and load the time series once per test session.

    Returns
    -------
    pd.DataFrame
        DataFrame containing all time series.
    """
    subprocess.run(
        ["uv", "run", "python", "run_simulation.py"],
        check=True,
    )
    filenameCSV = "all_trajectories.csv"  # Name of the final CSV file we’ll generate
    PathXML = Path("inputXML")  # Folder path where the XML files are located
    PathCSV = Path("inputCSV")  # Folder path where CSV files will be saved
    PathCSV.mkdir(parents=True, exist_ok=True)  # Create directories if it doesn't exist
    xml_to_Chaos.export_XML_to_CSV(PathCSV, PathXML)
    return pd.read_csv(PathCSV / filenameCSV)


def test_time_and_position_continuity(df: pd.DataFrame) -> None:
    """
    Test time and position continuity for each agent.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all time series.
    """
    required_cols = {"ID", "t", "x", "y"}
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing expected columns: {missing}"

    # agent IDs with irregular time steps
    violations_missing_time: list[int] = []
    # (agent_id, list of jump distances > MAX_SPATIAL_JUMP)
    violations_big_jump: list[tuple[int, list[float]]] = []

    for agent_id, g in df.sort_values("t").groupby("ID"):
        t = g["t"].to_numpy()
        dt = np.diff(t)
        ddt = np.diff(dt)
        if not np.all(np.abs(ddt) < TIME_TOL):
            violations_missing_time.append(int(agent_id))

        x = g["x"].to_numpy()
        y = g["y"].to_numpy()
        dist = np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2)
        bad_jump_idx = np.where(dist > MAX_SPATIAL_JUMP)[0]
        if bad_jump_idx.size > 0:
            violations_big_jump.append((int(agent_id), dist[bad_jump_idx].tolist()))

    assert not violations_missing_time, f"Irregular time steps: {violations_missing_time}"
    assert not violations_big_jump, f"Large spatial jumps: {violations_big_jump}"


def test_omega_near_zero_and_theta_near_constant(df: pd.DataFrame) -> None:
    """
    Test near-zero angular velocity (omega) and near constant orientation (theta) for all agents over the whole simulation.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all time series.
    """
    required_cols = {"ID", "omega", "theta"}
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing expected columns: {missing}"

    violations_omega: list[tuple[int, float]] = []
    violations_theta: list[tuple[int, float]] = []

    for agent_id, g in df.groupby("ID"):
        max_abs_omega = float(g["omega"].abs().max())
        if max_abs_omega > OMEGA_CONTACT_TOL:
            violations_omega.append((agent_id, max_abs_omega))
        theta_range = np.abs(g["theta"].max() - g["theta"].min())
        if theta_range > DELTA_THETA_CONTACT_TOL:
            violations_theta.append((agent_id, theta_range))

    assert not violations_omega, f"omega not ~0 for some agents: {violations_omega}"
    assert not violations_theta, f"theta not constant for some agents: {violations_theta}"


def test_agents_0_and_1_static(df: pd.DataFrame) -> None:
    """
    Test that agents 0 and 1 remain static translationally: translational velocity ~ 0, x and y coordinates ~ constants.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all time series.
    """
    required_cols = {"ID", "vx", "vy", "x", "y"}
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing expected columns: {missing}"

    violations: list[tuple[int, dict[str, float]]] = []

    for static_id in (0, 1):
        g = df[df["ID"] == static_id]
        assert not g.empty, f"No data for agent {static_id}"

        max_vx = float(g["vx"].abs().max())
        max_vy = float(g["vy"].abs().max())

        if (max_vx > VX_CONTACT_TOL) or (max_vy > VY_CONTACT_TOL):
            violations.append((static_id, {"max_vx": max_vx, "max_vy": max_vy}))

        x_range = np.abs(g["x"].max() - g["x"].min())
        y_range = np.abs(g["y"].max() - g["y"].min())
        if x_range > DELTA_X_CONTACT_TOL or y_range > DELTA_Y_CONTACT_TOL:
            violations.append((static_id, {"x_range": x_range, "y_range": y_range}))

    assert not violations, f"Agents 0 and/or 1 are not static: {violations}"


def test_agent_2_positive_vx_during_slip(df: pd.DataFrame) -> None:
    """
    Test that the velocity of Agent 2 is positive along the x-axis during the slip phase (x < 2.8 meters).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all time series.
    """
    required_cols = {"ID", "t", "vx", "x"}
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing expected columns: {missing}"

    g = df[df["ID"] == 2].sort_values("t")
    assert not g.empty, "No data for agent 2"

    # slip phase is for x smaller than 2.8 meters
    slip_phase = g[g["x"] < 2.8]

    moving = slip_phase[slip_phase["vx"].abs() > VX_TOL]
    assert not moving.empty, "Agent 2 never moves significantly"
