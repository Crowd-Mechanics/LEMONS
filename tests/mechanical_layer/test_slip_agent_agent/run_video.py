"""Script for building the video of the crowd dynamics simulation in slip agent agent scenario."""

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

import argparse
import os
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt

import configuration.backup.dict_to_xml_and_reverse as fun_xml  # For converting XML to dictionary and vice versa
from configuration.models.crowd import create_agents_from_dynamic_static_geometry_parameters  # For creating agents based on XML data
from streamlit_app.plot import plot  # For plotting crowd data

# === Command Line Argument Parsing ===
parser = argparse.ArgumentParser(description="Export movie with configurable ffmpeg path.")
parser.add_argument("--ffmpeg", type=str, required=True, help="Path to the ffmpeg executable")
args = parser.parse_args()

# === Simulation Parameters ===
dt = 0.1  # Time step for the decisional layer (matches "TimeStep" in Parameters.xml)
Ndt = 50  # How many dt will be performed in total

# === Prepare the folders ===
# Define the paths to the folders you'll use
CWD = Path(__file__).parent  # Current working directory
inputPath = CWD / "inputXML"
staticPath = CWD / "static"
plotsPath = CWD / "plots"
plotsPath.mkdir(parents=True, exist_ok=True)  # Create plots directory if it doesn't exist

# Remove any old '.png' files in the plots directory
for file in plotsPath.glob("*.png"):
    os.remove(file)

# === Load static XML files ===
# Read the Agents.xml file as a string and convert it to a dictionary
with open(staticPath / "Agents.xml", encoding="utf-8") as f:
    crowd_xml = f.read()
static_dict = fun_xml.static_xml_to_dict(crowd_xml)

# Read the Geometry.xml file as a string and convert it to a dictionary
with open(staticPath / "Geometry.xml", encoding="utf-8") as f:
    geometry_xml = f.read()
geometry_dict = fun_xml.geometry_xml_to_dict(geometry_xml)

# === Loop over time steps ===
for t in range(Ndt):
    current_time = t * dt

    # Check if the dynamics file exists; if not, skip to the next time step
    dynamics_file = inputPath / f"AgentDynamics input t={current_time:.1f}.xml"
    if not dynamics_file.exists():
        print(f"Warning: {dynamics_file} not found, skipping.")
        continue

    # === Read and process the dynamics XML file ===
    # Read the current dynamics XML file as a string and convert it to a dictionary
    with open(dynamics_file, encoding="utf-8") as f:
        dynamic_xml = f.read()
    dynamic_dict = fun_xml.dynamic_xml_to_dict(dynamic_xml)

    # Create a crowd object using the configuration files data
    crowd = create_agents_from_dynamic_static_geometry_parameters(
        static_dict=static_dict,
        dynamic_dict=dynamic_dict,
        geometry_dict=geometry_dict,
    )

    # Plot and save the crowd as a PNG file
    plot.display_crowd2D(crowd)[0]
    plt.savefig(plotsPath / rf"crowd2D_t={t:d}.png", dpi=300, format="png")
    plt.close()


# === Export to a movie with FFMPEG ===
ffmpeg = args.ffmpeg  # Get the ffmpeg path from command line arguments
movie_name = "test_slip_agent_agent"
plotsPath = CWD / "plots"
moviesPath = CWD / "movies"
moviesPath.mkdir(parents=True, exist_ok=True)
framerate = int(1.0 / dt)

for file in moviesPath.glob("*.mov"):
    os.remove(file)

# 1. Create an MP4 movie from PNG images in the plots folder
cmd1 = f"{ffmpeg} -framerate {framerate} -i {plotsPath}/crowd2D_t=%d.png {moviesPath}/{movie_name}.mp4"
subprocess.Popen(cmd1.split(), stdout=subprocess.PIPE).communicate()

# 2. Convert the MP4 to MOV for compatibility
cmd2 = f"{ffmpeg} -i {moviesPath}/{movie_name}.mp4 -pix_fmt yuv420p {moviesPath}/{movie_name}.mov"
subprocess.Popen(cmd2.split(), stdout=subprocess.PIPE).communicate()

# 3. Remove the intermediate MP4 file
cmd3 = f"rm {moviesPath}/{movie_name}.mp4"
subprocess.Popen(cmd3.split(), stdout=subprocess.PIPE).communicate()
