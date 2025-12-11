#!/bin/bash

# Prepare the environment for notebook testing

# => Copy configuration files needed for the pushing scenario (mechanical layer tutorial)
cp ./data/tutorial_mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/AgentDynamics.xml ./tutorials/mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/dynamic/
cp ./data/tutorial_mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/Agents.xml ./tutorials/mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/static/
cp ./data/tutorial_mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/Geometry.xml ./tutorials/mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/static/
cp ./data/tutorial_mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/Materials.xml ./tutorials/mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/static/
cp ./data/tutorial_mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/Parameters.xml ./tutorials/mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/
if [ -f ./tutorials/mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/dynamic/AgentInteractions.xml ]; then
    rm ./tutorials/mechanical_layer/push_Feldmann/Tue_15_m_noW_row2_15_w_s_b_p_n_d/dynamic/AgentInteractions.xml
fi

# => Copy configuration files needed for the pushing scenario (mechanical layer tutorial)
cp ./data/tutorial_mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/AgentDynamics.xml ./tutorials/mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/dynamic/
cp ./data/tutorial_mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/Agents.xml ./tutorials/mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/static/
cp ./data/tutorial_mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/Geometry.xml ./tutorials/mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/static/
cp ./data/tutorial_mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/Materials.xml ./tutorials/mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/static/
cp ./data/tutorial_mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/Parameters.xml ./tutorials/mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/
if [ -f ./tutorials/mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/dynamic/AgentInteractions.xml ]; then
    rm ./tutorials/mechanical_layer/push_Feldmann/Wed_03_m_wiW_row4_14_w_s_b_p_n_u/dynamic/AgentInteractions.xml
fi

# => Copy configuration files needed for the evacuation scenario (mechanical layer tutorial)
cp ./data/tutorial_mechanical_layer/evacuation/AgentDynamics.xml ./tutorials/mechanical_layer/evacuation/dynamic/
cp ./data/tutorial_mechanical_layer/evacuation/Agents.xml ./tutorials/mechanical_layer/evacuation/static/
cp ./data/tutorial_mechanical_layer/evacuation/Geometry.xml ./tutorials/mechanical_layer/evacuation/static/
cp ./data/tutorial_mechanical_layer/evacuation/Materials.xml ./tutorials/mechanical_layer/evacuation/static/
cp ./data/tutorial_mechanical_layer/evacuation/Parameters.xml ./tutorials/mechanical_layer/evacuation/
if [ -f ./tutorials/mechanical_layer/evacuation/dynamic/AgentInteractions.xml ]; then
    rm ./tutorials/mechanical_layer/evacuation/dynamic/AgentInteractions.xml
fi

# Run nbmake tests on the notebooks in the tutorials folder
uv run pytest-xdist --nbmake ./tutorials/configuration

# Additionally, you can run nbmake tests on the mechanical-layer notebook on your local machine, provided you set the correct ffmpeg path in the notebook and use the appropriate extension for ../../src/mechanical_layer/build/libCrowdMechanics (.so on Ubuntu, .dylib on macOS).
# uv run pytest --nbmake ./tutorials/mechanical_layer