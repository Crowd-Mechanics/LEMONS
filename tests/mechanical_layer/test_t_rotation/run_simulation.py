"""Test script for running the mechanical layer engine in a simple rotation scenario."""

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

import ctypes
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from shutil import copyfile

# === Simulation Parameters ===
dt = 0.1  # Time step for the decisional layer (matches "TimeStep" in Parameters.xml)
Ndt = 40  # How many dt will be performed in total

# === Paths Setup ===
outputPath = Path("outputXML/")  # Directory to store output XML files
inputPath = Path("inputXML/")  # Directory to store input XML files
outputPath.mkdir(parents=True, exist_ok=True)  # Create directories if they don't exist
Path("dynamic/").mkdir(parents=True, exist_ok=True)
inputPath.mkdir(parents=True, exist_ok=True)
# Clean the input and output directory before starting
for file in list(inputPath.glob("*.xml")) + list(outputPath.glob("*.xml")) + list(Path("dynamic/").glob("*.xml")):
    os.remove(file)

# Copy the initial agent dynamics file to the dynamic folder
copyfile("../initial_agent_dynamics_files/AgentDynamics_test_t_rotation.xml", "dynamic/AgentDynamics.xml")

# === Loading the External Mechanics Library ===
# Adjust filename for OS (.so for Linux, .dylib for macOS)
Clibrary = ctypes.CDLL("../../../src/mechanical_layer/build/libCrowdMechanics.dylib")

agentDynamicsFilename = "AgentDynamics.xml"

# Prepare the list of XML files that will be passed to the DLL/shared library
files = [
    b"Parameters.xml",
    b"Materials.xml",
    b"Geometry.xml",
    b"Agents.xml",
    agentDynamicsFilename.encode("ascii"),  # Convert filename to bytes (required by ctypes)
]
nFiles = len(files)  # Number of configuration files to be passed
FilesArray = ctypes.c_char_p * nFiles  # Create a ctypes array of string pointers
filesInput = FilesArray(*files)  # Populate array with the XML file names

# === Main Simulation Loop ===
for t in range(Ndt):
    print("Looping the Crowd mechanics engine - t=%.1fs..." % (t * dt))

    # 1. Save the current AgentDynamics file as input for this step (can be used for analysis later)
    copyfile("dynamic/" + agentDynamicsFilename, str(inputPath) + rf"/AgentDynamics input t={t * dt:.1f}.xml")

    # 2. Call the external mechanics engine, passing in the list of required XML files
    Clibrary.CrowdMechanics(filesInput)

    # 3. Save the updated AgentDynamics output to results folder (can be used for analysis later)
    copyfile("dynamic/" + agentDynamicsFilename, str(outputPath) + rf"/AgentDynamics output t={(t + 1) * dt:.1f}.xml")

    # 4. If the simulation produced an AgentInteractions.xml file, save that as well (optional output)
    try:
        copyfile("dynamic/AgentInteractions.xml", str(outputPath) + rf"/AgentInteractions t={(t + 1) * dt:.1f}.xml")
    except FileNotFoundError:
        # If the AgentInteractions file does not exist, skip copying
        pass

    # === Decision/Controller Layer for Next Step ===
    # Read the output AgentDynamics XML as input for the next run.
    # This is where you (or another program) can set new forces/moments for each agent for the next simulation step.
    XMLtree = ET.parse("dynamic/" + agentDynamicsFilename)
    agentsTree = XMLtree.getroot()

    # -- Assign random forces/moments to each agent --
    for agent in agentsTree.findall("Agent"):
        # Create new <Dynamics> tag for the agent (as the output file doesn't have it)
        dyn_elem = agent.find("Dynamics")
        # If the Dynamics element does not exist, create it
        if dyn_elem is None:
            dyn_elem = ET.SubElement(agent, "Dynamics")

        dyn_elem.set("Fp", "0.0,0.0")
        dyn_elem.set("Mp", "0.0")

    # Write the modified XML back, to be used in the next iteration
    XMLtree.write("dynamic/" + agentDynamicsFilename)
    # ================================================

# After all simulation steps are complete, print a final message.
print(f"Loop terminated at t={Ndt * dt:.1f}s!")
