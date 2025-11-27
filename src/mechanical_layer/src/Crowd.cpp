/*
    Copyright  2025  Institute of Light and Matter, CNRS UMR 5306, University Claude Bernard Lyon 1
    Contributors: Oscar DUFOUR, Maxime STAPELLE, Alexandre NICOLAS

    This software is a computer program designed to generate a realistic crowd from anthropometric data and
    simulate the mechanical interactions that occur within it and with obstacles.

    This software is governed by the CeCILL-B license under French law and abiding by the rules of distribution
    of free software.  You can  use, modify and/ or redistribute the software under the terms of the CeCILL-B
    license as circulated by CEA, CNRS and INRIA at the following URL "http://www.cecill.info".

    As a counterpart to the access to the source code and  rights to copy, modify and redistribute granted by
    the license, users are provided only with a limited warranty  and the software's author,  the holder of the
    economic rights,  and the successive licensors  have only  limited liability.

    In this respect, the user's attention is drawn to the risks associated with loading,  using,  modifying
    and/or developing or reproducing the software by the user in light of its specific status of free software,
    that may mean  that it is complicated to manipulate,  and  that  also therefore means  that it is reserved
    for developers  and  experienced professionals having in-depth computer knowledge. Users are therefore
    encouraged to load and test the software's suitability as regards their requirements in conditions enabling
    the security of their systems and/or data to be ensured and,  more generally, to use and operate it in the
    same conditions as regards security.

    The fact that you are presently reading this means that you have had knowledge of the CeCILL-B license and that
    you accept its terms.
*/

#include "Crowd.h"

#include <algorithm>
#include <fstream>
#include <vector>

#include "../3rdparty/tinyxml/tinyxml2.h"
#include "MechanicalLayer.h"

using std::string, std::vector, std::list, std::cerr, std::cout, std::endl, std::ranges::find, std::ofstream;

//  Global variable: Mechanically active agents
list<Agent*> mech_active_agents;

/**
 * @brief The function creates all agents from the data stored by InputStatic.cpp.
 *        It also creates the kinematics and dynamics of the agents by calling updateSetting().
 *
 * @param dynamicsFile The input file containing the current state and driving forces for all agents
 * @param nb_shapes_allagents The number of shapes by agent (size: number of agents)
 * @param shapeIDagent A correspondence between the shape ids (index) and the agent (value) (size: number of shapes)
 * @param edges The indices of the first shape for each agent (size:  number of agents + 1)
 * @param radius_allshapes The radii of all shapes (size: number of shapes)
 * @param masses The masses of the agents
 * @param mois The moment of inertia of the agents
 * @param delta_gtos The relative positions of the shapes with respect to the center of mass of each agent
 *
 * @return EXIT_SUCCESS if no issue with the Dynamics file
 *         EXIT_FAILURE otherwise
 *         (the return code comes from updateSetting())
 */
int initialiseSetting(const std::string& dynamicsFile, std::vector<unsigned>& nb_shapes_allagents, std::vector<unsigned>& shapeIDagent,
                      std::vector<int>& edges, std::vector<double>& radius_allshapes, std::vector<double>& masses,
                      std::vector<double>& mois, std::vector<double2>& delta_gtos)
{
    /*  Allocate agents */
    agents = new Agent*[nAgents];

    /*  Create ids of shapes for agents */
    vector<unsigned> Id_shapes(shapeIDagent.size());
    for (size_t i = 0; i < shapeIDagent.size(); i++)
    {
        Id_shapes[i] = i;
    }

    /*  Create the agents  */
    for (uint32_t a = 0; a < nAgents; a++)
    {
        vector<double2> delta_gtos_curr(&delta_gtos[edges[a]], &delta_gtos[edges[a + 1]]);
        double2 shoulders_direction(delta_gtos[edges[a + 1] - 1] - delta_gtos[edges[a]]);    // from left to right
        double2 orientation_vec({-shoulders_direction.second, shoulders_direction.first});   // normal to the shoulders direction
        double theta_body_init(0.);
        if (!(orientation_vec.first == 0. && orientation_vec.second == 0.))
            theta_body_init = atan2(orientation_vec.second, orientation_vec.first);

        vector<double> radius_shapes(&radius_allshapes[edges[a]], &radius_allshapes[edges[a + 1]]);
        const vector<unsigned> Ids_shapes_agent(&Id_shapes[edges[a]], &Id_shapes[edges[a + 1]]);
        const double mass_curr(masses[a]), moi_curr(mois[a]);

        //  Actual creation of the Agent object
        agents[a] = new Agent(a, Ids_shapes_agent, nb_shapes_allagents[a], delta_gtos_curr, radius_shapes, theta_body_init, mass_curr,
                              moi_curr);
    }

    /*  Update the agents with the Dynamics file  */
    return updateSetting(dynamicsFile);
}
/**
 * @brief The function updates all agents with the agentDynamics (dynamic data) XML files.
 *        It initiates the list of neighbours by calling determine_agents_neighbours().
 *
 * @param dynamicsFile The input file containing the current state and driving forces for all agents
 *
 * @return EXIT_SUCCESS if no issue with the Dynamics file
 *         EXIT_FAILURE otherwise
 */
int updateSetting(const string& dynamicsFile)
{
    /*  Create agents: read the dynamics file first  */
    tinyxml2::XMLDocument document;
    document.LoadFile(dynamicsFile.data());
    if (document.ErrorID() != 0)
    {
        cerr << "Error: Could not load or parse XML file " << dynamicsFile << endl;
        return EXIT_FAILURE;
    }
    //  Read the Agents block
    tinyxml2::XMLElement* agentsElement = document.FirstChildElement("Agents");
    if (!agentsElement)
    {
        cerr << "Error: agents must be embedded in \"Agents\" tag!" << endl;
        return EXIT_FAILURE;
    }
    const tinyxml2::XMLElement* agentElement = agentsElement->FirstChildElement("Agent");
    if (!agentElement)
    {
        cerr << "Error: no Agent tag present in " << dynamicsFile << endl;
        return EXIT_FAILURE;
    }
    uint32_t agentCounter = 0;
    while (agentElement != nullptr)
    {
        const char* agentId = nullptr;
        uint32_t a;
        if (agentElement->QueryStringAttribute("Id", &agentId) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: agent tag with no id in dynamics file" << endl;
            return EXIT_FAILURE;
        }
        if (!agentMap.contains(agentId))
        {
            cerr << "Error: unknown agent " << agentId << " in dynamics file" << endl;
            return EXIT_FAILURE;
        }
        else
        {
            a = agentMap[agentId];
        }
        //  Kinematics and Dynamics
        const tinyxml2::XMLElement* kinematicsElement = agentElement->FirstChildElement("Kinematics");
        if (!kinematicsElement)
        {
            cerr << "Error: no Kinematics tag present for agent " << agentId << endl;
            return EXIT_FAILURE;
        }
        const char* buffer = nullptr;
        if (kinematicsElement->QueryStringAttribute("Position", &buffer) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: Could not parse agent position from XML file " << dynamicsFile << endl;
            return EXIT_FAILURE;
        }
        auto [rcPosition, position] = parse2DComponents(buffer);
        if (rcPosition != EXIT_SUCCESS)
        {
            cerr << "Error: Could not parse position coordinates from XML file " << dynamicsFile << endl;
            return EXIT_FAILURE;
        }

        if (kinematicsElement->QueryStringAttribute("Velocity", &buffer) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: Could not parse agent velocity from XML file " << dynamicsFile << endl;
            return EXIT_FAILURE;
        }
        auto [rcVelocity, velocity] = parse2DComponents(buffer);
        if (rcVelocity != EXIT_SUCCESS)
        {
            cerr << "Error: Could not parse velocity coordinates from XML file " << dynamicsFile << endl;
            return EXIT_FAILURE;
        }
        double theta, omega;
        if (kinematicsElement->QueryDoubleAttribute("Theta", &theta) != tinyxml2::XML_SUCCESS)
            cerr << "Error: could not get orientation of agent " << agentId << endl;
        if (kinematicsElement->QueryDoubleAttribute("Omega", &omega) != tinyxml2::XML_SUCCESS)
            cerr << "Error: could not get angular velocity of agent " << agentId << endl;

        const tinyxml2::XMLElement* dynamicsElement = agentElement->FirstChildElement("Dynamics");
        if (!dynamicsElement)
        {
            cerr << "Error: no Dynamics tag present for agent " << agentId << endl;
            return EXIT_FAILURE;
        }
        if (dynamicsElement->QueryStringAttribute("Fp", &buffer) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: could not get driving force of agent " << agentId << endl;
            return EXIT_FAILURE;
        }
        auto [rcFp, Fp] = parse2DComponents(buffer);
        if (rcFp != EXIT_SUCCESS)
        {
            cerr << "Error: Could not parse driving force coordinates from XML file " << dynamicsFile << endl;
            return EXIT_FAILURE;
        }
        double Mp;
        if (dynamicsElement->QueryDoubleAttribute("Mp", &Mp) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: could not get driving torque of agent " << agentId << endl;
            return EXIT_FAILURE;
        }
        //  Update agent with the kinematics and dynamics
        agents[a]->_x = position.first;
        agents[a]->_y = position.second;
        agents[a]->_theta = theta;
        agents[a]->_vx = velocity.first;
        agents[a]->_vy = velocity.second;
        agents[a]->_w = omega;
        agents[a]->_Fp = (1 / agents[a]->_mass) * Fp;
        const double inverseTauMechTranslation = agentProperties[a].first;
        const double inverseTauMechRotation = agentProperties[a].second;
        agents[a]->_vx_des = agents[a]->_Fp.first / inverseTauMechTranslation;   //  vx_des := Fpx/m * tau_mech
        agents[a]->_vy_des = agents[a]->_Fp.second / inverseTauMechTranslation;
        agents[a]->_w_des = Mp / inverseTauMechRotation / agents[a]->_moi;   //  w_des  := Mp/I  * tau_mech
        if (!(agents[a]->_vx_des == 0. && agents[a]->_vy_des == 0.))
            agents[a]->_theta_des = atan2(agents[a]->_vy_des, agents[a]->_vx_des);
        else
            agents[a]->_theta_des = 0.;
        agents[a]->_neighbours.clear();

        agentElement = agentElement->NextSiblingElement("Agent");
        agentCounter++;
    }
    if (agentCounter < nAgents)
    {
        cerr << "Agents are missing in the dynamics file!" << endl;
        return EXIT_FAILURE;
    }

    /*  Update neighbours before calling the mechanical layer   */
    determine_agents_neighbours();

    return EXIT_SUCCESS;
}

/**
 * @brief Updates the list of neighbors for each agent in the crowd.
 *
 * This function creates the lists based on the proximity of each agent to other agents and to walls.
 * We will consider all agents within a certain distance from one another, ie the maximum distance
 * that can be traveled by an agent within dt seconds at max speed vMaxAgent. We multiply it by 2 in the "extreme"
 * case of two pedestrians walking (running) fast towards each other. All this ensures that all agents who can
 * potentially collide within dt are taken into account.
 */
void determine_agents_neighbours()
{
    const double criticalDistanceWall = dt * vMaxAgent;
    const double criticalDistance = 2 * criticalDistanceWall;

    for (uint32_t a1 = 0; a1 < nAgents; a1++)
    {
        Agent* agent1 = agents[a1];
        //  First, check walls
        for (uint32_t iobs = 0; iobs < listObstacles.size(); iobs++)
        {
            for (uint32_t iwall = 0; iwall < listObstacles[iobs].size() - 1; iwall++)
            {
                auto [distance, closest_point] = get_distance_to_wall_and_closest_point(
                    listObstacles[iobs][iwall], listObstacles[iobs][iwall + 1], agent1->get_r());
                if (distance < criticalDistanceWall + agent1->_radius)
                    agent1->_neighbours_walls.emplace_back(iobs, iwall);
            }
        }
        //  Then, other agents
        for (uint32_t a2 = a1 + 1; a2 < nAgents; a2++)
        {
            Agent* agent2 = agents[a2];

            const double2 r1 = agent1->get_r();
            const double2 r2 = agent2->get_r();
            if (const double r = get_distance(r1, r2); r < criticalDistance + agent1->_radius + agent2->_radius)
            {
                agent1->_neighbours.push_back(agent2->_id);
                agent2->_neighbours.push_back(agent1->_id);
            }
        }
    }
}

/**
 * @brief Executes the mechanical layer.
 *
 * This function is responsible for updating the state of each agent in the Crowd.
 * It performs the following steps:
 * 1. Handles mechanically active agents using the mechanical layer.
 * 2. Handles non-mechanically active agents (simple positional update)
 * 3. Generates an output file with the new position and velocity, plus their angular counterparts.
 *
 * @param dynamicsFile The input dynamics file will be overwritten with the output of the mechanical layer.
 */
void handleMechanicalLayer(const std::string& dynamicsFile)
{
    /*  Handle mechanically active agents: mechanical layer */
    if (get_future_collision())
    {
        try
        {
            const MechanicalLayer* crowdMech = new MechanicalLayer(mech_active_agents);
            delete crowdMech;
        }
        catch (const std::exception& e)
        {
            exit(EXIT_FAILURE);
        }
    }

    /*  Handle non mechanically active agents: simple positional update */
    for (uint32_t a = 0; a < nAgents; a++)
    {
        Agent* agent = agents[a];
        if (is_mechanically_active(agent))
            continue;
        /// The dynamics follow a simple relaxation equation, ie
        /// dv/dt = (v_des - v) / tau_mech  ==> v(t)= v_des (1 - e^-t/tau_mech) + v(t=0) e^-t/tau_mech
        const double inverseTauMechTranslation = agentProperties[agent->_id].first;
        const double inverseTauMechRotation = agentProperties[agent->_id].second;
        agent->_vx = (1.0 - exp(-dt * inverseTauMechTranslation)) * agent->_vx_des + exp(-dt * inverseTauMechTranslation) * agent->_vx;
        agent->_vy = (1.0 - exp(-dt * inverseTauMechTranslation)) * agent->_vy_des + exp(-dt * inverseTauMechTranslation) * agent->_vy;
        agent->_w = (1.0 - exp(-dt * inverseTauMechRotation)) * agent->_w_des + exp(-dt * inverseTauMechRotation) * agent->_w;
        agent->move();
    }

    /*  Save output of mechanical layer to file */
    generateDynamicsOutputFile(dynamicsFile);
}

/**
 * @brief Checks if the given agent is mechanically active in the crowd.
 * An agent is considered mechanically active if it is present in the mech_active_agents container.
 *
 * @param agent The agent to check.
 * @return True if the agent is mechanically active, false otherwise.
 */
bool is_mechanically_active(const Agent* agent) { return (find(mech_active_agents, agent) != mech_active_agents.end()); }

/**
 * @brief Checks if there will be any future collisions between agents in the crowd.
 *
 * @return true if there will be future collisions, false otherwise.
 */
bool get_future_collision()
{
    //  Test new positions
    for (uint32_t a = 0; a < nAgents; a++)
    {
        Agent* agent = agents[a];

        agent->_x += agent->_vx_des * dt;
        agent->_y += agent->_vy_des * dt;
        agent->_theta += agent->_w_des * dt;
    }

    //  Check if overlaps
    mech_active_agents.clear();
    for (uint32_t a = 0; a < nAgents; a++)
    {
        Agent* agent1 = agents[a];
        //  Loop over current agent's wall neighbours
        for (const auto& [iobs, iwall] : agent1->_neighbours_walls)
        {
            double2 middlePointWall = 0.5 * (listObstacles[iobs][iwall] + listObstacles[iobs][iwall + 1]);
            if ((!(agent1->get_r() - middlePointWall)) < agent1->_radius + 1e-1)
                if (!is_mechanically_active(agent1))
                    mech_active_agents.push_back(agent1);
        }
        //  Loop over current agent's neighbours
        for (const unsigned agent2_id : agent1->_neighbours)
        {
            if (Agent* agent2 = agents[agent2_id];
                (!(agent1->get_r() - agent2->get_r())) < fabs(agent1->_radius + agent2->_radius) + 1e-1)
            {
                if (!is_mechanically_active(agent1))
                    mech_active_agents.push_back(agent1);
                if (!is_mechanically_active(agent2))
                    mech_active_agents.push_back(agent2);
            }
        }
    }

    //  Revert to former positions
    for (uint32_t a = 0; a < nAgents; a++)
    {
        Agent* agent = agents[a];

        agent->_x -= agent->_vx_des * dt;
        agent->_y -= agent->_vy_des * dt;
        agent->_theta -= agent->_w_des * dt;
    }

    //  Add agents with significant velocity changes
    for (uint32_t a = 0; a < nAgents; a++)
    {
        if (Agent* agent = agents[a];
            pow(agent->_vx - agent->_vx_des, 2) + pow(agent->_vy - agent->_vy_des, 2) + pow(agent->_w - agent->_w_des, 2) > 1e-4 &&
            !is_mechanically_active(agent))
            mech_active_agents.push_back(agent);
    }

    //  Add neighbours of active agents
    for (const Agent* agent : mech_active_agents)
    {
        for (const unsigned neighbour : agent->_neighbours)
        {
            if (!is_mechanically_active(agents[neighbour]))
                mech_active_agents.push_back(agents[neighbour]);
        }
    }
    return (!mech_active_agents.empty());
}

/**
 * @brief The function generates the final state of the agents by overwriting the input dynamics file.
 *
 * @param dynamicsFile The name of the file.
 */
void generateDynamicsOutputFile(const std::string& dynamicsFile)
{
    //  We'll  build the output from the input (the structure and fields are exactly the same)
    tinyxml2::XMLDocument inputDoc;
    inputDoc.LoadFile((dynamicsFile).data());
    ofstream outputDoc;
    outputDoc.open(dynamicsFile);

    outputDoc << R"(<?xml version="1.0" encoding="utf-8"?>)" << endl;
    //  Read the Agents block
    tinyxml2::XMLElement* InAgentsElement = inputDoc.FirstChildElement("Agents");
    outputDoc << "<Agents>" << endl;

    const tinyxml2::XMLElement* InAgentElement = InAgentsElement->FirstChildElement("Agent");
    while (InAgentElement != nullptr)
    {
        //  First, get our internal id
        const char* agentId = nullptr;
        InAgentElement->QueryStringAttribute("Id", &agentId);
        const uint32_t a = agentMap[agentId];
        struct Agent* agent = agents[a];
        outputDoc << "    <Agent Id=\"" << agentId << "\">" << endl;
        //  Kinematics
        outputDoc << "        <Kinematics Position=\"" << agent->_x << "," << agent->_y << "\" ";
        outputDoc << "Velocity=\"" << agent->_vx << "," << agent->_vy << "\" ";
        outputDoc << "Theta=\"" << agent->_theta << "\" Omega=\"" << agent->_w << "\"/>" << endl;

        InAgentElement = InAgentElement->NextSiblingElement("Agent");
        outputDoc << "    </Agent>" << endl;
    }
    outputDoc << "</Agents>";

    outputDoc.close();
}
