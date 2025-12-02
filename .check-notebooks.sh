#!/bin/bash

# prepare the environment for notebook testing => copy configuration files needed for the evacuation tutorial
cp ./data/xml/evacuation_tutorial_initial_config_files/AgentDynamics.xml ./tutorials/mechanical_layer/dynamic/
cp ./data/xml/evacuation_tutorial_initial_config_files/Agents.xml ./tutorials/mechanical_layer/static/
cp ./data/xml/evacuation_tutorial_initial_config_files/Geometry.xml ./tutorials/mechanical_layer/static/
cp ./data/xml/evacuation_tutorial_initial_config_files/Materials.xml ./tutorials/mechanical_layer/static/
cp ./data/xml/evacuation_tutorial_initial_config_files/Parameters.xml ./tutorials/mechanical_layer/

# run nbmake tests on the notebooks in the tutorials folder
uv run pytest --nbmake ./tutorials/configuration