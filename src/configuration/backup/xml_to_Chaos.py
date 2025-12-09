"""Export agent trajectories from XML files to CHAOS format."""

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

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

regex_nb = r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?"
trajectories_csv_filename = "all_trajectories.csv"


def get_list_of_agents_and_times_from_XML(
    folder_path: Path,
) -> tuple[list[str], list[float], dict[int, str]]:
    """
    Extract a sorted list of unique agent IDs, sorted list of times, and a dictionary of filenames from XML files in a folder.

    Parameters
    ----------
    folder_path : Path
        Path to the folder containing XML files.

    Returns
    -------
    list[str]
        Sorted list of unique agent IDs found in the XML files.
    list[float]
        Sorted list of times extracted from the filenames.
    dict[int, str]
        Dictionary mapping time (as int, scaled by 1000) to the corresponding filename.

    Notes
    -----
    Assumes XML files are named with the pattern 'AgentDyn...input t=<time>.xml'.
    """
    folder_path.mkdir(parents=True, exist_ok=True)

    ID_agents: set[str] = set()
    times: list[float] = []
    filenames: dict[int, str] = {}

    for fichier in folder_path.iterdir():
        if fichier.is_file() and fichier.name.startswith("AgentDyn") and fichier.name.endswith("xml"):
            print(f"Processing file: {fichier}")
            pattern = re.compile(rf".*(input|output) t=({regex_nb})\.xml")
            m = pattern.fullmatch(str(fichier))
            if not m:
                continue
            time_loc = float(m.group(2))
            times.append(time_loc)
            filenames[int(1000 * time_loc)] = str(fichier)

            agents_tree = ET.parse(fichier).getroot()
            for agent in agents_tree:
                agent_id = agent.get("Id")
                if agent_id is not None:
                    ID_agents.add(agent_id)
            del agents_tree

    return sorted(ID_agents), sorted(times), filenames


def create_dict_of_agent_trajectories(
    folder_path: Path,
) -> tuple[list[float], dict[str, dict[float, dict[str, float]]]]:
    """
    Create a dictionary of agent trajectories from XML files in a folder.

    For each agent, stores their position and velocity at each time point.

    Parameters
    ----------
    folder_path : Path
        Path to the folder containing XML files.

    Returns
    -------
    list[float]
        Sorted list of all time points extracted from the XML filenames.
    dict[str, dict[float, dict[str, float]]]
        Nested dictionary such that:
        agents[agent_id][time] = {
            'x': pos_x,
            'y': pos_y,
            'vx': vel_x,
            'vy': vel_y
        }.

    Notes
    -----
    Assumes XML files are named and structured as expected by `get_list_of_agents_and_times_from_XML`.
    """
    ID_agents, times, filenames = get_list_of_agents_and_times_from_XML(folder_path)

    agents: dict[str, dict[float, dict[str, float]]] = {ID: {} for ID in ID_agents}

    for time_loc in times:
        file_path = filenames[int(1000 * time_loc)]
        agents_tree = ET.parse(file_path).getroot()

        for agent in agents_tree:
            ID_agent = agent.get("Id")
            if ID_agent is None:
                continue

            kinematics = next(agent.iterfind("Kinematics"), None)
            if kinematics is None:
                continue

            pos = kinematics.get("Position")
            vel = kinematics.get("Velocity")
            omega = kinematics.get("Omega")
            theta = kinematics.get("Theta")
            if pos is None or vel is None or omega is None or theta is None:
                continue

            pos_match = re.fullmatch(rf"({regex_nb}),({regex_nb})", pos)
            vel_match = re.fullmatch(rf"({regex_nb}),({regex_nb})", vel)
            omega_match = float(omega)
            theta_match = float(theta)

            if not pos_match or not vel_match:
                continue

            agents[ID_agent][time_loc] = {
                "x": float(pos_match.group(1)),
                "y": float(pos_match.group(2)),
                "vx": float(vel_match.group(1)),
                "vy": float(vel_match.group(2)),
                "theta": theta_match,
                "omega": omega_match,
            }

        del agents_tree

    return times, agents


def export_XML_to_CSV(PathCSV: Path, PathXML: Path) -> None:
    """
    Export agent trajectories to a CSV file with header: t,ID,x,y,vx,vy.

    Each row of the CSV contains the time, agent ID, position (x, y), and velocity (vx, vy) for each agent at each time point.

    Parameters
    ----------
    PathCSV : Path
        Path to the folder where the CSV file will be saved.
    PathXML : Path
        Path to the folder containing the XML files.
    """
    times, agents = create_dict_of_agent_trajectories(PathXML)
    ID_agents = sorted(agents.keys())
    csv_path = PathCSV / trajectories_csv_filename

    with open(csv_path, "w", encoding="utf-8") as monfichier:
        monfichier.write("t,ID,x,y,vx,vy,theta,omega")
        for time_loc in times:
            for ID_agent in ID_agents:
                posvel = agents[ID_agent].get(time_loc)
                if posvel is not None:
                    monfichier.write(
                        f"\n{time_loc:.4f},{ID_agent},{posvel['x']:.6f},{posvel['y']:.6f},{posvel['vx']:.6f},{posvel['vy']:.6f},"
                        f"{posvel['theta']:.6f},{posvel['omega']:.6f}",
                    )


def export_CSV_to_CHAOS(PathCSV: Path, dt: float) -> None:
    """
    Read agent trajectories from a CSV file and exports them into multiple text files in the format required by the ChAOS software.

    For each unique agent ID, creates a file containing interpolated positions at regular time steps.

    Parameters
    ----------
    PathCSV : Path
        Path to the folder containing the CSV file containing columns: t, ID, x, y, vx, vy.
    dt : float
        Timestep to use for interpolation in the CHAOS output.

    Notes
    -----
    Each output file is named 'trajXXX.csv' where XXX is the zero-padded agent index.
    Each line in the output file contains: t, x, y, 0.0
    """
    PathCSV.mkdir(parents=True, exist_ok=True)
    PathCHAOS = PathCSV / "ForCHAOS"
    PathCHAOS.mkdir(parents=True, exist_ok=True)
    for file in PathCHAOS.glob("traj*.csv"):
        os.remove(file)  # clean old files

    path_to_CSV_main_file = PathCSV / trajectories_csv_filename
    lignes = pd.read_csv(path_to_CSV_main_file, sep=",", header=0, index_col=False)
    lignes["t"] = lignes["t"].astype(float)
    lignes.sort_values(by=["ID", "t"], inplace=True)

    t_min = lignes["t"].min()
    t_max = lignes["t"].max()
    t_vec = np.arange(t_min, t_max, dt)

    for cpt_agent, ID in enumerate(sorted(lignes["ID"].unique())):
        lignes_loc = lignes[lignes["ID"] == ID].reset_index(drop=True)
        times = lignes_loc["t"].values
        xs = lignes_loc["x"].values
        ys = lignes_loc["y"].values

        out_path = PathCHAOS / f"traj{cpt_agent:03d}.csv"
        with open(out_path, "w", encoding="utf-8") as monfichier:
            for t in t_vec:
                # Find indices before and after t
                idx_after = np.searchsorted(times, t, side="right")
                if idx_after == 0 or idx_after == len(times):
                    # If t is outside the trajectory time range, skip
                    continue
                idx_before = idx_after - 1

                t_before = times[idx_before]
                t_after = times[idx_after]
                x_before = xs[idx_before]
                x_after = xs[idx_after]
                y_before = ys[idx_before]
                y_after = ys[idx_after]

                # Linear interpolation
                coef = (t - t_before) / (t_after - t_before)
                x_interp = (1.0 - coef) * x_before + coef * x_after
                y_interp = (1.0 - coef) * y_before + coef * y_after

                monfichier.write(f"{t:.3f},{x_interp:.3f},{y_interp:.3f},0.0\n")

    print("\n* Trajectories have been converted to Chaos-compatible files")
