"""
Tests the behaviour as an agent undergoes a translation and gradually relaxes to a stationary state (no motion) due to friction.

Tests cover:
    - Time and position continuity
    - Constant x and y position during the whole simulation
    - Translational velocity (vx, vy) near zero during the whole simulation
    - Positive or near zero angular velocity (omega)
    - Stationary phase (with near constant x, y, theta and near zero vx, vy, omega)
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
#: Maximum allowed spatial jump (m) between consecutive time steps for the agent.
MAX_SPATIAL_JUMP = 1
#: Tolerance for near-zero velocities along x during the whole simulation (m/s).
VX_TOL = 1e-2
# : Tolerance for near-zero velocities along y during the whole simulation (m/s).
VY_TOL = 1e-2
#: Tolerance for the positivity of angular velocity during the whole simulation (rad/s).
OMEGA_TOL = 1e-2
#: Tolerance for constancy of orientation during the stationary phase (radians).
DELTA_THETA_TOL = 1e-2
#: Tolerance for constancy of x position during the stationary phase (m).
DELTA_X_TOL = 1e-2  # meters
#: Tolerance for constancy of y position during the stationary phase (m).
DELTA_Y_TOL = 1e-2  # meters


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


def test_constant_position_and_near_zero_velocity(df: pd.DataFrame) -> None:
    """
    Position x, y should be constant and translational speed vx, vy ~ 0 for all agents during the whole simulation.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all time series.
    """
    required_cols = {"ID", "x", "y", "vx", "vy"}
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing expected columns: {missing}"

    violations_pos: list[tuple[int, float, float]] = []
    violations_vel: list[tuple[int, float, float]] = []

    for agent_id, g in df.groupby("ID"):
        x = g["x"].to_numpy()
        y = g["y"].to_numpy()
        vx = g["vx"].to_numpy()
        vy = g["vy"].to_numpy()

        x_range = float(x.max() - x.min())
        y_range = float(y.max() - y.min())
        if x_range > DELTA_X_TOL or y_range > DELTA_Y_TOL:
            violations_pos.append((agent_id, x_range, y_range))

        max_vx = float(np.abs(vx).max())
        max_vy = float(np.abs(vy).max())
        if max_vx > VX_TOL or max_vy > VY_TOL:
            violations_vel.append((agent_id, max_vx, max_vy))

    assert not violations_pos, f"x or y not constant: {violations_pos}"
    assert not violations_vel, f"vx or vy not ~0: {violations_vel}"


def test_omega_positive_or_near_zero(df: pd.DataFrame) -> None:
    """
    Angular velocity should be positive or near zero for all agents.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all time series.
    """
    required_cols = {"ID", "omega"}
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing expected columns: {missing}"

    violations: list[tuple[int, float]] = []

    for agent_id, g in df.groupby("ID"):
        omega = g["omega"].to_numpy()

        if np.any(omega < -OMEGA_TOL):
            min_omega = float(omega.min())
            violations.append((agent_id, min_omega))

    assert not violations, f"omega has significantly negative values: {violations}"


def test_stationary_phase(df: pd.DataFrame) -> None:
    """
    Last 5% of the simulation is fully stationary: x, y, theta constant; vx, vy, omega ~ 0.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all time series.
    """
    required_cols = {"ID", "t", "x", "y", "theta", "vx", "vy", "omega"}
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing expected columns: {missing}"

    violations_pos: list[tuple[int, float, float]] = []
    violations_theta: list[tuple[int, float]] = []
    violations_vel: list[tuple[int, float, float]] = []
    violations_omega: list[tuple[int, float]] = []

    for agent_id, g in df.groupby("ID"):
        t_max = g["t"].max()
        stationary = g[g["t"] >= t_max * 0.95]

        x = stationary["x"].to_numpy()
        y = stationary["y"].to_numpy()
        theta = stationary["theta"].to_numpy()
        vx = stationary["vx"].to_numpy()
        vy = stationary["vy"].to_numpy()
        omega = stationary["omega"].to_numpy()

        x_range = float(x.max() - x.min())
        y_range = float(y.max() - y.min())
        if x_range > DELTA_X_TOL or y_range > DELTA_Y_TOL:
            violations_pos.append((agent_id, x_range, y_range))

        theta_range = float(theta.max() - theta.min())
        if theta_range > DELTA_THETA_TOL:
            violations_theta.append((agent_id, theta_range))

        max_vx = float(np.abs(vx).max())
        max_vy = float(np.abs(vy).max())
        if max_vx > VX_TOL or max_vy > VY_TOL:
            violations_vel.append((agent_id, max_vx, max_vy))

        max_abs_omega = float(np.abs(omega).max())
        if max_abs_omega > OMEGA_TOL:
            violations_omega.append((agent_id, max_abs_omega))

    assert not violations_pos, f"x or y not constant in stationary phase: {violations_pos}"
    assert not violations_theta, f"theta not constant in stationary phase: {violations_theta}"
    assert not violations_vel, f"vx or vy not ~0 in stationary phase: {violations_vel}"
    assert not violations_omega, f"omega not ~0 in stationary phase: {violations_omega}"
