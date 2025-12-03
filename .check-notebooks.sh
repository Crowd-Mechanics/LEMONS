#!/bin/bash

# Prepare the environment for notebook testing => copy configuration files needed for the evacuation tutorial
cp ./data/xml/evacuation_tutorial_initial_config_files/AgentDynamics.xml ./tutorials/mechanical_layer/dynamic/
cp ./data/xml/evacuation_tutorial_initial_config_files/Agents.xml ./tutorials/mechanical_layer/static/
cp ./data/xml/evacuation_tutorial_initial_config_files/Geometry.xml ./tutorials/mechanical_layer/static/
cp ./data/xml/evacuation_tutorial_initial_config_files/Materials.xml ./tutorials/mechanical_layer/static/
cp ./data/xml/evacuation_tutorial_initial_config_files/Parameters.xml ./tutorials/mechanical_layer/

# Run nbmake tests on the notebooks in the tutorials folder
uv run pytest --nbmake ./tutorials/configuration

# Additionally, you can run nbmake tests on the mechanical-layer notebook on your local machine, provided you set the correct ffmpeg path in the notebook and use the appropriate extension for ../../src/mechanical_layer/build/libCrowdMechanics (.so on Ubuntu, .dylib on macOS).
# uv run pytest --nbmake ./tutorials/mechanical_layer