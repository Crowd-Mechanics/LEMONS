"""
Tests for the slip agent wall scenario.

Tests cover:
    - Time and position continuity
    - Near-zero angular velocity (omega), constant orientation (theta)
    - Velocity along the x-axis should be positive during the core of the simulation
    - Velocity along the y-axis should be either near zero or negative during the core of the simulation
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

TIME_TOL = 1e-4  # seconds
MAX_SPATIAL_JUMP = 1  # meters
VX_TOL = 1e-2  # meters/second
VY_TOL = 1e-2  # meters/second
OMEGA_CONTACT_TOL = 0.5  # radians/second
DELTA_THETA_CONTACT_TOL = 0.5  # radians


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
    xml_to_Chaos.export_dict_to_CSV(PathCSV, PathXML)
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
    Near-zero angular velocity and near constant orientation for all agents.

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

        theta = g["theta"].to_numpy()
        theta_range = float(theta.max() - theta.min())
        if theta_range > DELTA_THETA_CONTACT_TOL:
            violations_theta.append((agent_id, theta_range))

    assert not violations_omega, f"omega not ~0 for some agents: {violations_omega}"
    assert not violations_theta, f"theta not constant for some agents: {violations_theta}"


def test_velocity_signs_during_core(df: pd.DataFrame) -> None:
    """
    During the core of the simulation: vx > 0 and vy ~ 0 or negative.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing all time series.
    """
    required_cols = {"ID", "t", "vx", "vy"}
    missing = required_cols - set(df.columns)
    assert not missing, f"Missing expected columns: {missing}"

    g = df[df["ID"] == 0].sort_values("t")
    assert not g.empty, "No data for slip agent (ID 0)"

    t = g["t"].to_numpy()
    t_min, t_max = float(t.min()), float(t.max())
    # Define "core" as the central 80% of the simulation time
    core = g[(g["t"] >= t_min + 0.1 * (t_max - t_min)) & (g["t"] <= t_min + 0.9 * (t_max - t_min))]
    assert not core.empty, "Core simulation window is empty"

    bad_vx = core[core["vx"] <= -VX_TOL]
    if not bad_vx.empty:
        raise AssertionError(f"Non-positive vx during core:\n{bad_vx[['t', 'vx']]}")

    bad_vy = core[core["vy"] > VY_TOL]
    if not bad_vy.empty:
        raise AssertionError(f"Positive vy above tolerance during core:\n{bad_vy[['t', 'vy']]}")
