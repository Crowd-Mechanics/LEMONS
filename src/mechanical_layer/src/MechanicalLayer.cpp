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

#include "MechanicalLayer.h"

#include <sys/stat.h>

#include <array>
#include <fstream>
#include <map>
#include <set>
#include <string>
#include <tuple>
#include <unordered_set>
#include <vector>

#include "../3rdparty/tinyxml/tinyxml2.h"

using std::list, std::map, std::set, std::vector, std::string, std::tuple, std::pair, std::cout, std::cerr, std::endl, std::ofstream,
    std::fmin, std::runtime_error;

/**
 * @brief Constructor for the MechanicalLayer class.
 *
 * It is the main function of the mechanical layer. It will "prepare" the mechanically active agents,
 * read the Interactions file to get possible already existing contacts, loop on dt_mech and produce
 * the output Interactions file.
 *
 * @param mech_active_agents Reference to a list of pointers to Agent objects representing the active agents in the crowd.
 */
MechanicalLayer::MechanicalLayer(list<Agent*>& mech_active_agents)
    : nb_active_agents(mech_active_agents.size()),
      nb_active_shapes(0),
      vgn(nb_active_agents),
      vgnp1(nb_active_agents),
      rgn(nb_active_agents),
      rgnp1(nb_active_agents),
      delta(0),
      thetn(nb_active_agents),
      thetnp1(nb_active_agents),
      wn(nb_active_agents),
      wnp1(nb_active_agents),
      wdesired(nb_active_agents),
      Fp(nb_active_agents),
      Forthon(nb_active_agents),
      Ftn(nb_active_agents),
      taun(nb_active_agents),
      neighbours(nb_active_agents),
      active_shapeIDagent(0),
      active_shapeIDshape_crowd(0),
      radius(0),
      size_agents(nb_active_agents),
      neighbours_shape(nb_active_agents),
      agentIDshape(nb_active_agents + 1, 0),
      masses(nb_active_agents),
      mois(nb_active_agents),
      damping(nb_active_agents)
{
    /*  Preliminary definitions and initialisation  */
    //  Sort mechanically active agents to have agent/shapes in ascending order
    mech_active_agents.sort([](auto const& a, auto const& b) { return (a->_id) < (b->_id); });
    unsigned cpt_agent = 0;
    for (Agent* agent : mech_active_agents)
    {
        for (unsigned cpt_shape(0); cpt_shape < agent->_nb_shapes; cpt_shape++)
        {
            active_shapeIDagent.push_back(cpt_agent);
            active_shapeIDshape_crowd.push_back(agent->_ids_shapes[cpt_shape]);
        }
        agentIds[agent->_id] = cpt_agent;
        agentActiveIds.push_back(agent->_id);
        vector<double2> delta_gtos_agent = agent->get_delta_gtos();
        delta.insert(delta.end(), (delta_gtos_agent).begin(), (delta_gtos_agent).end());
        radius.insert(radius.end(), (agent->_radius_shapes).begin(), (agent->_radius_shapes).end());
        size_agents[cpt_agent] = agent->_nb_shapes;
        nb_active_shapes += agent->_nb_shapes;
        rgn[cpt_agent] = double2(agent->_x, agent->_y);
        thetn[cpt_agent] = agent->_theta;
        vgn[cpt_agent] = double2(agent->_vx, agent->_vy);
        wn[cpt_agent] = agent->_w;
        masses[cpt_agent] = agent->_mass;
        mois[cpt_agent] = agent->_moi;
        damping[cpt_agent] = agentProperties[agent->_id];

        rgnp1[cpt_agent] = double2(agent->_x, agent->_y);
        thetnp1[cpt_agent] = agent->_theta;
        vgnp1[cpt_agent] = double2(agent->_vx, agent->_vy);
        wnp1[cpt_agent] = agent->_w;
        //  The "F" here have the dimension of an acceleration
        Fp[cpt_agent] = agent->_Fp;
        Forthon[cpt_agent] = double2(0., 0.);
        Ftn[cpt_agent] = double2(0., 0.);
        taun[cpt_agent] = 0.;
        wdesired[cpt_agent] = agent->_w_des;

        cpt_agent++;
    }

    //  Get the correspondence between agent and shapes  (ie the edges)
    unsigned length(0);
    for (size_t a = 0; a < nb_active_agents; ++a)
    {
        length += size_agents[a];
        agentIDshape[a + 1] = length;
    }

    //  Get neighbouring shapes id of each agent
    cpt_agent = 0;
    for (const Agent* agent : mech_active_agents)
    {
        unsigned cpt_agent2 = 0;
        for (const Agent* agent2 : mech_active_agents)
        {
            if (cpt_agent2 > cpt_agent)
            {
                //  Include as neighbour if within 5*(r1+r2) where r1 and r2 are the size of the body (the radius of the smallest
                //  circle containing all the shapes)
                if (const double distance = !(rgn[cpt_agent] - rgn[cpt_agent2]); distance < 5.0 * (agent->_radius + agent2->_radius))
                {
                    for (unsigned cpt_shape(agentIDshape[cpt_agent2]); cpt_shape < agentIDshape[cpt_agent2] + size_agents[cpt_agent2];
                         ++cpt_shape)
                        neighbours_shape[cpt_agent].push_back(cpt_shape);
                    for (unsigned cpt_shape(agentIDshape[cpt_agent]); cpt_shape < agentIDshape[cpt_agent] + size_agents[cpt_agent];
                         ++cpt_shape)
                        neighbours_shape[cpt_agent2].push_back(cpt_shape);
                }
            }
            cpt_agent2++;
        }
        cpt_agent++;
    }

    /*  Check if an Interactions File already exists    */
    const string interactionsFile = pathDynamic + "AgentInteractions.xml";
    struct stat buffer{};
    if (stat(interactionsFile.c_str(), &buffer) != -1)
        if (readInteractionsInputFile(interactionsFile) == EXIT_FAILURE)
            throw runtime_error("Issue while reading interactions file");

    /*  MECHANICAL Loop */
    for (unsigned t = 0; t < static_cast<unsigned>(dt / dt_mech); t++)
    {
        loop();
    }

    /*  Update the positions and velocities of mechanically active agents   */
    cpt_agent = 0;
    for (Agent* agent : mech_active_agents)
    {
        agent->_x = rgn[cpt_agent].first;
        agent->_y = rgn[cpt_agent].second;
        agent->_vx = vgn[cpt_agent].first;
        agent->_vy = vgn[cpt_agent].second;
        agent->_theta = thetn[cpt_agent];
        agent->_w = wn[cpt_agent];
        cpt_agent++;
    }

    /*  Output the interactions file */
    generateInteractionsOutputFile(interactionsFile, existsContacts());
}

/**
 * @brief Destructor for the CrowdMech class.
 *
 * This destructor transfers computed data to the agents.
 */
MechanicalLayer::~MechanicalLayer()   // destructor transfers computed data to the agents
    = default;

/**
 * @brief This function read the interactions file to store the possible already existing contacts.
 * 			slip and slip_wall are the ones who get filled
 *
 * @param interactionsFile the name of the file
 *
 * return EXIT_FAILURE in case of problem with the XML file
 *		  EXIT_SUCCESS otherwise
 */
int MechanicalLayer::readInteractionsInputFile(const std::string& interactionsFile)
{
    tinyxml2::XMLDocument document;
    document.LoadFile(interactionsFile.data());
    if (document.ErrorID() != 0)
    {
        cerr << "Error: Could not load or parse XML file " << interactionsFile << endl;
        return EXIT_FAILURE;
    }

    //  Read the Interactions block
    const tinyxml2::XMLElement* interactionsElement = document.FirstChildElement("Interactions");
    if (!interactionsElement)
    {
        cerr << "Error: interactions must be embedded in \"Interactions\" tag!" << endl;
        return EXIT_FAILURE;
    }

    const tinyxml2::XMLElement* agent1Element = interactionsElement->FirstChildElement("Agent");
    if (!agent1Element)
    {
        cerr << "Error: no Agent tag present in " << interactionsFile << endl;
        return EXIT_FAILURE;
    }
    while (agent1Element)
    {
        const char* agent1ExternId = nullptr;
        if (agent1Element->QueryStringAttribute("Id", &agent1ExternId) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: Agents must have an Id in file " << interactionsFile << endl;
            return EXIT_FAILURE;
        }
        //  Interactions with other agents
        const tinyxml2::XMLElement* agent2Element = agent1Element->FirstChildElement("Agent");
        while (agent2Element)
        {
            const char* agent2ExternId = nullptr;
            if (agent2Element->QueryStringAttribute("Id", &agent2ExternId) != tinyxml2::XML_SUCCESS)
            {
                cerr << "Error: Agents must have an Id in file " << interactionsFile << endl;
                return EXIT_FAILURE;
            }
            //  Read interactions
            const tinyxml2::XMLElement* interactionElement = agent2Element->FirstChildElement("Interaction");
            while (interactionElement)
            {
                int32_t shapeParent;
                int32_t shapeChild;
                if (interactionElement->QueryIntAttribute("ParentShape", &shapeParent) != tinyxml2::XML_SUCCESS)
                {
                    cerr << "Error: no shape identifier in interaction between agents in " << interactionsFile << endl;
                    return EXIT_FAILURE;
                }
                if (interactionElement->QueryIntAttribute("ChildShape", &shapeChild) != tinyxml2::XML_SUCCESS)
                {
                    cerr << "Error: no shape identifier in interaction between agents in " << interactionsFile << endl;
                    return EXIT_FAILURE;
                }
                const char* buffer = nullptr;
                if (interactionElement->QueryStringAttribute("TangentialRelativeDisplacement", &buffer) != tinyxml2::XML_SUCCESS)
                {
                    cerr << "Error: no tangential relative displacement in one of the interactions of " << interactionsFile << endl;
                    return EXIT_FAILURE;
                }
                auto [rcSlip, inputSlip] = parse2DComponents(buffer);
                if (rcSlip != EXIT_SUCCESS)
                {
                    cerr << "Error: Could not parse components of tangential relative displacement in " << interactionsFile << endl;
                    return EXIT_FAILURE;
                }
                uint32_t cpt_shape = agentIDshape[agentIds[agentMap[agent1ExternId]]] + shapeParent;
                uint32_t cpt_shape_neigh = agentIDshape[agentIds[agentMap[agent2ExternId]]] + shapeChild;

                slip[{cpt_shape, cpt_shape_neigh}] = inputSlip;
                slip[{cpt_shape_neigh, cpt_shape}] = -1 * inputSlip;

                interactionElement = interactionElement->NextSiblingElement("Interaction");
            }

            agent2Element = agent2Element->NextSiblingElement("Agent");
        }
        //  Interactions with walls
        const tinyxml2::XMLElement* wallElement = agent1Element->FirstChildElement("Wall");
        while (wallElement)
        {
            int32_t shape;
            if (wallElement->QueryIntAttribute("ShapeId", &shape) != tinyxml2::XML_SUCCESS)
            {
                cerr << "Error: no shape identifier in interaction between agent and wall in " << interactionsFile << endl;
                return EXIT_FAILURE;
            }
            int iobs, iwall;
            if (wallElement->QueryIntAttribute("WallId", &iobs) != tinyxml2::XML_SUCCESS)
            {
                cerr << "Error: no obstacle identifier in interaction between agent and wall in " << interactionsFile << endl;
                return EXIT_FAILURE;
            }
            if (wallElement->QueryIntAttribute("CornerId", &iwall) != tinyxml2::XML_SUCCESS)
            {
                cerr << "Error: no wall identifier in interaction between agent and wall in " << interactionsFile << endl;
                return EXIT_FAILURE;
            }
            const char* buffer = nullptr;
            if (wallElement->QueryStringAttribute("TangentialRelativeDisplacement", &buffer) != tinyxml2::XML_SUCCESS)
            {
                cerr << "Error: no tangential relative displacement in interaction between agent and wall in " << interactionsFile
                     << endl;
                return EXIT_FAILURE;
            }
            auto [rcSlipWall, inputSlipWall] = parse2DComponents(buffer);
            if (rcSlipWall != EXIT_SUCCESS)
            {
                cerr << "Error: Could not parse components of tangential relative displacement between agent and wall in "
                     << interactionsFile << endl;
                return EXIT_FAILURE;
            }
            uint32_t cpt_shape = agentIDshape[agentIds[agentMap[agent1ExternId]]] + shape;
            slip_wall[{cpt_shape, iobs, iwall}] = inputSlipWall;

            wallElement = wallElement->NextSiblingElement("Wall");
        }
        agent1Element = agent1Element->NextSiblingElement("Agent");
    }

    return EXIT_SUCCESS;
}

/**
 * @brief Calculates the interactions between a shape and all the other shapes.
 *
 * @param cpt_shape The index of the shape.
 * @param AtTimen Flag indicating whether to calculate the forces at time n or n+1.
 *
 * @return A tuple containing the tangential force, normal force, and torque.
 */
tuple<double2, double2, double> MechanicalLayer::get_interactions(unsigned cpt_shape, bool AtTimen)
{
    unsigned cpt_agent = active_shapeIDagent[cpt_shape];
    double UnmZetadt = 1.0 - dt_mech * damping[cpt_agent].first;
    double2 delta_GtoS = AtTimen ? delta[cpt_shape] : delta[cpt_shape] + ((thetnp1[cpt_agent] - thetn[cpt_agent]) ^ delta[cpt_shape]);
    double2 posagent = AtTimen ? rgn[cpt_agent] : rgnp1[cpt_agent];   //  Center of mass of the agent
    double2 posshape = posagent + delta_GtoS;                         //  Center of mass of the shape
    double angvel =   //  Angular velocity of the shape at time n and trial angular velocity for the time n+1
        AtTimen ? wn[cpt_agent] : wn[cpt_agent] + dt_mech * taun[cpt_agent];
    double2 velagent =   //  Velocity of the shape (v_shape(t+dt) = v_CM(t+dt))
        AtTimen ? vgn[cpt_agent] : UnmZetadt * vgn[cpt_agent] + dt_mech * (Fp[cpt_agent] + Forthon[cpt_agent] + Ftn[cpt_agent]);
    double2 velshape = velagent + (angvel ^ delta_GtoS);

    double torq = 0.;
    double2 fortho(0., 0.);
    double2 ft(0., 0.);

    /*  Interactions between agents */
    for (unsigned cpt_shape_neigh : neighbours_shape[cpt_agent])
    {
        unsigned cpt_neigh = active_shapeIDagent[cpt_shape_neigh];
        double2 delta_GtoS_neigh = AtTimen
                                       ? delta[cpt_shape_neigh]
                                       : delta[cpt_shape_neigh] + ((thetnp1[cpt_neigh] - thetn[cpt_neigh]) ^ delta[cpt_shape_neigh]);
        double2 posagent_neigh = AtTimen ? rgn[cpt_neigh] : rgnp1[cpt_neigh];
        double2 posshape_neigh = posagent_neigh + delta_GtoS_neigh;

        double2 r_ij = posshape - posshape_neigh;
        double distance(!r_ij);
        double h(radius[cpt_shape] + radius[cpt_shape_neigh] - distance);   //  Indentation

        //  If the two shapes are in contact:
        if (h > 0.)
        {
            double angvel_neigh = AtTimen ? wn[cpt_neigh] : wn[cpt_neigh] + dt_mech * taun[cpt_neigh];
            double2 velagent_neigh =   //  Velocity of the CM of the neighbouring pedestrian neighbour
                AtTimen ? vgn[cpt_neigh]
                        : UnmZetadt * vgn[cpt_neigh] + dt_mech * (Fp[cpt_neigh] + Forthon[cpt_neigh] + Ftn[cpt_neigh]);
            double2 velshape_neigh = velagent_neigh + (angvel_neigh ^ delta_GtoS_neigh);

            double2 n_ij;
            if (distance == 0.)
                n_ij = double2(0., 0.);
            else
                n_ij = (1. / distance) * r_ij;
            double2 dcGshape = -(radius[cpt_shape] - h / 2.) * n_ij;   //  From the center of mass G of the shape
            //  towards c (the contact point)
            double2 dcGshapeneigh = +(radius[cpt_shape_neigh] - h / 2.) * n_ij;
            double2 dcG = delta[cpt_shape] + dcGshape;   //  Vector distance from CM of the agent to
            //  c = vector distance from CM agent to CM shape +
            //      distance from CM shape to c

            double2 v_ci = velshape + (angvel ^ dcGshape);                    //  Velocity of i at the contact point
            double2 v_cj = velshape_neigh + (angvel_neigh ^ dcGshapeneigh);   //  Velocity of j at the contact point
            double2 vij = v_ci - v_cj;
            double2 vortho_ij = (vij % n_ij) * n_ij;
            double2 vt_ij = vij - vortho_ij;

            //  If the map does not contain this pair ie the slip is not initialized, we initialize it
            //  Otherwise: we increment it
            if (!slip.contains({cpt_shape, cpt_shape_neigh}))
                slip[{cpt_shape, cpt_shape_neigh}] = double2(0., 0.);
            else
            {
                double2 slip_prime = slip[{cpt_shape, cpt_shape_neigh}];
                //  Rotation of the slip to take into account the rotation of the contact reference frame
                //  from t to t+dt_mech (D.R. Vyas, J.M. Ottino, R.M. Lueptow et al. 2025)
                double2 slip_projected = slip_prime - (slip_prime % n_ij) * n_ij;
                double2 slip_new = slip_prime;
                if ((!slip_projected) > 0.)
                    slip_new = (!slip_prime / !slip_projected) * slip_projected;
                slip[{cpt_shape, cpt_shape_neigh}] = slip_new + dt_mech * vt_ij;
            }
            //  For the output Interactions file:
            //  We will only put the N(N-1)/2 pairs, ie cpt_shape_neigh>cpt_shape
            if (!interactionsOutput.contains({cpt_shape_neigh, cpt_shape}))
                interactionsOutput[{cpt_shape, cpt_shape_neigh}][SLIP] = slip[{cpt_shape, cpt_shape_neigh}];

            uint32_t shapeMaterialId = shapesMaterial[active_shapeIDshape_crowd[cpt_shape]];
            uint32_t shapeNeighbourMaterialId = shapesMaterial[active_shapeIDshape_crowd[cpt_shape_neigh]];
            /*  Normal interactions */
            double k_n = binaryProperties[STIFFNESS_NORMAL][shapeMaterialId][shapeNeighbourMaterialId];
            double Gamma_n = binaryProperties[DAMPING_NORMAL][shapeMaterialId][shapeNeighbourMaterialId];
            double2 fnij_elastic = k_n * h * n_ij;
            double2 fnij_viscous = -Gamma_n * vortho_ij;
            double2 fnij = fnij_elastic + fnij_viscous;
            fortho = fortho + fnij;
            if (!interactionsOutput.contains({cpt_shape_neigh, cpt_shape}))
                interactionsOutput[{cpt_shape, cpt_shape_neigh}][FORCE_ORTHO] = fnij;

            /*  Tangential interactions */
            double k_t = binaryProperties[STIFFNESS_TANGENTIAL][shapeMaterialId][shapeNeighbourMaterialId];
            double Gamma_t = binaryProperties[DAMPING_TANGENTIAL][shapeMaterialId][shapeNeighbourMaterialId];
            double2 ftij_static = -k_t * slip[{cpt_shape, cpt_shape_neigh}] - Gamma_t * vt_ij;
            double mu_dyn = binaryProperties[FRICTION_SLIDING][shapeMaterialId][shapeNeighbourMaterialId];
            double2 t_vij = double2(0., 0.);
            double2 ftij = double2(0., 0.);
            if ((!ftij_static) > mu_dyn * !fnij)
            {
                t_vij = (1. / !ftij_static) * ftij_static;
                ftij = mu_dyn * !fnij * t_vij;
                slip[{cpt_shape, cpt_shape_neigh}] = -(1. / k_t) * (mu_dyn * !fnij * t_vij + Gamma_t * vt_ij);
            }
            else
                ftij = ftij_static;
            ft = ft + ftij;
            if (!interactionsOutput.contains({cpt_shape_neigh, cpt_shape}))
                interactionsOutput[{cpt_shape, cpt_shape_neigh}][FORCE_TAN] = ftij;

            /*  Torque  */
            double torqnij = (1. ^ dcG) % fnij;
            double torqtij = (1. ^ dcG) % ftij;
            double torqij = torqnij + torqtij;
            torq = torq + torqij;
        }
        else
        {
            if (slip.contains({cpt_shape, cpt_shape_neigh}))
            {
                slip.erase({cpt_shape, cpt_shape_neigh});
                if (interactionsOutput.contains({cpt_shape, cpt_shape_neigh}))
                    interactionsOutput.erase({cpt_shape, cpt_shape_neigh});
                else if (interactionsOutput.contains({cpt_shape_neigh, cpt_shape}))
                    interactionsOutput.erase({cpt_shape_neigh, cpt_shape});
            }
        }
    }

    /*  Interactions with walls */
    int iobs = 0;
    for (vector<double2> const& wall_it : listObstacles)
    {
        int iwall = 0;
        for (auto it = wall_it.begin(); next(it) != wall_it.end(); ++it)
        {
            auto [distance, closestPoint] = get_distance_to_wall_and_closest_point(*it, *(next(it)), posshape);
            double h = radius[cpt_shape] - distance;

            //  If the shape is in contact with the wall:
            if (h > 0.)
            {
                double2 r_iw = posshape - closestPoint;   //  Vector starting on the wall and going towards the shape
                double2 n_iw;
                if (distance == 0.)
                    n_iw = double2(0., 0.);
                else
                    n_iw = (1. / distance) * r_iw;
                double2 dcGshape = -(radius[cpt_shape] - h / 2.) * n_iw;
                double2 dcG = delta[cpt_shape] + dcGshape;   //  Distance from the CM G to the contact point c

                double2 v_ci = velshape + (angvel ^ dcGshape);
                double2 viw = v_ci - double2(0., 0.);
                double2 vortho_iw = (viw % n_iw) * n_iw;
                double2 vt_iw = viw - vortho_iw;

                //  If the map does not contain this pair ie the slip is not initialized, we initialize it
                //  Otherwise: we increment it
                if (!slip_wall.contains({cpt_shape, iobs, iwall}))
                    slip_wall[{cpt_shape, iobs, iwall}] = double2(0., 0.);
                else
                {
                    double2 slip_wall_prime = slip_wall[{cpt_shape, iobs, iwall}];
                    //  Rotation of the slip to take into account the rotation of the contact reference frame
                    //  from t to t+dt_mech (D.R. Vyas, J.M. Ottino, R.M. Lueptow et al. 2025)
                    double2 slip_wall_projected = slip_wall_prime - (slip_wall_prime % n_iw) * n_iw;
                    double2 slip_wall_new = slip_wall_prime;
                    if ((!slip_wall_projected) > 0.0)
                    {
                        slip_wall_new = (!slip_wall_prime / !slip_wall_projected) * slip_wall_projected;
                    }
                    slip_wall[{cpt_shape, iobs, iwall}] = slip_wall[{cpt_shape, iobs, iwall}] + dt_mech * vt_iw;
                }
                //  For the Interactions output file:
                interactionsOutputWall[{cpt_shape, iobs, iwall}][SLIP] = slip_wall[{cpt_shape, iobs, iwall}];

                uint32_t shapeMaterialId = shapesMaterial[active_shapeIDshape_crowd[cpt_shape]];
                uint32_t obstacleMaterialId = obstaclesMaterial[iobs];

                /*  Normal interactions  */
                double k_n_wall = binaryProperties[STIFFNESS_NORMAL][shapeMaterialId][obstacleMaterialId];
                double Gamma_n_wall = binaryProperties[DAMPING_NORMAL][shapeMaterialId][obstacleMaterialId];
                double2 fniw_elastic = k_n_wall * h * n_iw;
                double2 fniw_viscous = -Gamma_n_wall * vortho_iw;
                double2 fniw = fniw_elastic + fniw_viscous;
                fortho = fortho + fniw;
                interactionsOutputWall[{cpt_shape, iobs, iwall}][FORCE_ORTHO] = fniw;

                /*  Tangential interactions  */
                double k_t_wall = binaryProperties[STIFFNESS_TANGENTIAL][shapeMaterialId][obstacleMaterialId];
                double Gamma_t_wall = binaryProperties[DAMPING_TANGENTIAL][shapeMaterialId][obstacleMaterialId];
                double2 ftiw_static = -k_t_wall * slip_wall[{cpt_shape, iobs, iwall}] - Gamma_t_wall * vt_iw;
                double2 t_viw = double2(0., 0.);
                double2 ftiw = double2(0., 0.);
                double mu_dyn_wall = binaryProperties[FRICTION_SLIDING][shapeMaterialId][obstacleMaterialId];
                if ((!ftiw_static) > mu_dyn_wall * !fniw)
                {
                    t_viw = (1.0 / !ftiw_static) * ftiw_static;
                    ftiw = mu_dyn_wall * !fniw * t_viw;
                    slip_wall[{cpt_shape, iobs, iwall}] = -(1.0 / k_t_wall) * (mu_dyn_wall * !fniw * t_viw + Gamma_t_wall * vt_iw);
                }
                else
                {
                    ftiw = ftiw_static;
                }
                ft = ft + ftiw;
                interactionsOutputWall[{cpt_shape, iobs, iwall}][FORCE_TAN] = ftiw;

                /*  Torque  */
                double torqniw = (1. ^ dcG) % fniw;
                double torqtiw = (1. ^ dcG) % ftiw;
                double torqiw = torqniw + torqtiw;
                torq = torq + torqiw;
            }
            else
            {
                if (slip_wall.contains({cpt_shape, iobs, iwall}))
                {
                    slip_wall.erase({cpt_shape, iobs, iwall});
                    interactionsOutputWall.erase({cpt_shape, iobs, iwall});
                }
            }
            iwall++;
        }
        iobs++;
    }
    return {fortho, ft, torq};
}

/**
 * @brief Executes the main loop of the CrowdMech class.
 *
 * This function updates the forces, positions, velocities, orientations, and angular velocities
 * of the agents in the crowd simulation.
 * It iterates over the active shapes to calculate the forces and momentum at time n, and updates the corresponding
 * agent variables.
 * Then, it iterates over the active agents to update their positions using the velocity Verlet algorithm.
 * Next, it calculates the forces and momentum at time N+1 for each shape, and updates
 * the corresponding agent variables.
 * Finally, it updates the velocities of the agents and their angular velocities, and updates
 * the relative positions of the shapes.
 *
 */
void MechanicalLayer::loop()
{
    //  Reset the forces and torques
    for (unsigned cpt_agent = 0; cpt_agent < nb_active_agents; cpt_agent++)
    {
        Forthon[cpt_agent] = double2(0., 0.);
        Ftn[cpt_agent] = double2(0., 0.);
        taun[cpt_agent] = 0.;
    }

    //  Loop over shapes for forces and momentum
    //  Calculation is done at time n
    for (unsigned cpt_shape = 0; cpt_shape < nb_active_shapes; cpt_shape++)
    {
        auto Motion = get_interactions(cpt_shape, true);
        const unsigned cpt_agent(active_shapeIDagent[cpt_shape]);
        Forthon[cpt_agent] =   //  Resultant of normal forces (applied on the contact point)
            Forthon[cpt_agent] + (1. / masses[cpt_agent]) * get<0>(Motion);
        Ftn[cpt_agent] =   //  Resultant of tangential forces (applied on the contact point)
            Ftn[cpt_agent] + (1.0 / masses[cpt_agent]) * get<1>(Motion);
        taun[cpt_agent] = taun[cpt_agent] + (1.0 / mois[cpt_agent]) * get<2>(Motion);   //  Resultant of torques
    }

    //  Loop over agents for positions
    for (unsigned cpt_agent = 0; cpt_agent < nb_active_agents; cpt_agent++)
    {
        double UnmZetadt2 = 1.0 - 0.5 * dt_mech * damping[cpt_agent].first;
        taun[cpt_agent] = taun[cpt_agent] + (wdesired[cpt_agent] - wn[cpt_agent]) * damping[cpt_agent].second;
        //  Update positions with velocity Verlet algorithm
        rgnp1[cpt_agent] = rgn[cpt_agent] + UnmZetadt2 * dt_mech * vgn[cpt_agent] +
                           0.5 * dt_mech * dt_mech * (Fp[cpt_agent] + Forthon[cpt_agent] + Ftn[cpt_agent]);
        thetnp1[cpt_agent] = thetn[cpt_agent] + dt_mech * wn[cpt_agent] + 0.5 * dt_mech * dt_mech * taun[cpt_agent];
    }

    //  Loop over shapes for velocities
    //  Calculation is done at time n+1
    vector<double2> forthonp1(nb_active_agents, double2(0, 0));
    vector<double2> ftnp1(nb_active_agents, double2(0, 0));
    vector<double> taunp1(nb_active_agents, 0.);

    for (unsigned cpt_shape = 0; cpt_shape < nb_active_shapes; cpt_shape++)
    {
        auto Motion = get_interactions(cpt_shape, false);
        const unsigned cpt_agent(active_shapeIDagent[cpt_shape]);
        forthonp1[cpt_agent] = forthonp1[cpt_agent] + get<0>(Motion);
        ftnp1[cpt_agent] = ftnp1[cpt_agent] + get<1>(Motion);
        taunp1[cpt_agent] = taunp1[cpt_agent] + get<2>(Motion);
    }

    //  Loop over agents for velocities
    for (unsigned cpt_agent = 0; cpt_agent < nb_active_agents; cpt_agent++)
    {
        double UnmZetadt2 = 1.0 - 0.5 * dt_mech * damping[cpt_agent].first;
        double UnpZetadt2 = 1.0 + 0.5 * dt_mech * damping[cpt_agent].first;
        double wn_trial = wn[cpt_agent] + dt_mech * taun[cpt_agent];
        taunp1[cpt_agent] = taunp1[cpt_agent] + (wdesired[cpt_agent] - wn_trial) * damping[cpt_agent].second;
        //  Update velocities
        vgnp1[cpt_agent] =
            1.0 / UnpZetadt2 *
            (UnmZetadt2 * vgn[cpt_agent] +
             0.5 * dt_mech * (2. * Fp[cpt_agent] + Forthon[cpt_agent] + Ftn[cpt_agent] + forthonp1[cpt_agent] + ftnp1[cpt_agent]));
        wnp1[cpt_agent] = wn[cpt_agent] + 0.5 * dt_mech * (taun[cpt_agent] + taunp1[cpt_agent]);
    }

    //  Update relative positions of the shapes
    for (unsigned cpt_shape = 0; cpt_shape < nb_active_shapes; cpt_shape++)
    {
        const unsigned cpt_agent(active_shapeIDagent[cpt_shape]);
        const double delta_theta = thetnp1[cpt_agent] - thetn[cpt_agent];
        delta[cpt_shape].first = delta[cpt_shape].first * cos(delta_theta) - delta[cpt_shape].second * sin(delta_theta);
        delta[cpt_shape].second = delta[cpt_shape].first * sin(delta_theta) + delta[cpt_shape].second * cos(delta_theta);
    }

    //  Update position, velocity, orientation, angular velocity of each agent
    for (unsigned cpt_agent = 0; cpt_agent < nb_active_agents; cpt_agent++)
    {
        {
            rgn[cpt_agent] = rgnp1[cpt_agent];
            vgn[cpt_agent] = vgnp1[cpt_agent];
            thetn[cpt_agent] = thetnp1[cpt_agent];
            wn[cpt_agent] = wnp1[cpt_agent];
        }
    }
}

/**
 * @brief For output: do contacts exist?
 *
 * @return true if so (with agents/with walls)
 */
pair<bool, bool> MechanicalLayer::existsContacts()
{
    bool agentContact = false;
    bool wallContact = false;

    for (auto const& [key, value] : slip)
    {
        if (value != double2(0., 0.))
        {
            agentContact = true;
            break;
        }
    }
    for (auto const& [key, value] : slip_wall)
    {
        if (value != double2(0., 0.))
        {
            wallContact = true;
            break;
        }
    }
    return {agentContact, wallContact};
}

/**
 * @brief Outputs interactions between shapes.
 *
 * @param interactionsFile The name of the file to be written.
 * @param exists A boolean saying if there exists agent-agent or agent-wall contacts
 *
 */
void MechanicalLayer::generateInteractionsOutputFile(const string& interactionsFile, const pair<bool, bool>& exists)
{
    if (!exists.first && !exists.second)
    {
        return;
    }

    ofstream outputDoc;
    outputDoc.open(interactionsFile);

    outputDoc << R"(<?xml version="1.0" encoding="utf-8"?>)" << endl;
    outputDoc << "<Interactions>" << endl;

    /*  Loop over active agents */
    set<unsigned> parent;                        //  Variable to remember if we have opening tags for parents
    set<pair<unsigned, unsigned>> parentChild;   //  Variable to remember if we have an opening child tag
    for (uint32_t a = 0; a < nb_active_agents; a++)
    {
        //  First, collisions with agents
        if (exists.first && !interactionsOutput.empty())
        {
            for (auto iterator = interactionsOutput.begin(); iterator != interactionsOutput.end();)
            {
                auto shape = iterator->first.first;
                const uint32_t agent = active_shapeIDagent[shape];
                if (agent > a)
                    break;
                //  If we're here, agent = a
                auto output = iterator->second;
                if (output[SLIP] == double2(0., 0.) && output[FORCE_ORTHO] == double2(0., 0.) && output[FORCE_TAN] == double2(0., 0.))
                    continue;
                if (!parent.contains(a))
                {
                    if (!parent.empty())
                        outputDoc << "    </Agent>" << endl;
                    outputDoc << "    <Agent Id=\"" << agentMapInverse[agentActiveIds[agent]] << "\">" << endl;
                    parent.insert(a);
                }
                auto shapeNeighbour = iterator->first.second;
                const uint32_t neighbour = active_shapeIDagent[shapeNeighbour];
                if (!parentChild.contains({agent, neighbour}))
                {
                    if (!parentChild.empty() && parentChild.rbegin()->first == agent)
                        //  We have switched to another child within the same agent -> insert child closing tag
                        outputDoc << "        </Agent>" << endl;
                    outputDoc << "        <Agent Id=\"" << agentMapInverse[agentActiveIds[neighbour]] << "\">" << endl;
                    parentChild.insert({agent, neighbour});
                }
                outputDoc << "            <Interaction ParentShape=\"" << (shape - agentIDshape[agentActiveIds[agent]]) << "\" "
                          << "ChildShape=\"" << (shapeNeighbour - agentIDshape[agentActiveIds[neighbour]]) << "\" ";
                if (output[SLIP] != double2(0., 0.))
                    outputDoc << "TangentialRelativeDisplacement=\"" << output[SLIP].first << "," << output[SLIP].second << "\" ";
                if (output[FORCE_ORTHO] != double2(0., 0.))
                    outputDoc << "Fn=\"" << output[FORCE_ORTHO].first << "," << output[FORCE_ORTHO].second << "\" ";
                if (output[FORCE_TAN] != double2(0., 0.))
                    outputDoc << "Ft=\"" << output[FORCE_TAN].first << "," << output[FORCE_TAN].second << "\" ";
                outputDoc << "/>" << endl;
                interactionsOutput.erase(iterator++);
            }
            if (!parentChild.empty() && parentChild.rbegin()->first == a)
                //  If there were entries for the current agent, we need to close the last Agent child
                outputDoc << "        </Agent>" << endl;
        }
        //  Second, collision with walls
        if (exists.second && !interactionsOutputWall.empty())
        {
            for (auto iterator = interactionsOutputWall.begin(); iterator != interactionsOutputWall.end();)
            {
                auto key = iterator->first;
                const uint32_t shape = get<0>(key);
                const uint32_t agent = active_shapeIDagent[shape];
                //  If the current element of interactionsOutputWall is not the same as the last parent, end
                if (agent > a)
                    break;
                auto output = iterator->second;
                if (output[0] == double2(0., 0.) && output[1] == double2(0., 0.) && output[2] == double2(0., 0.))
                    continue;
                if (!parent.contains(a))
                {
                    if (!parent.empty())
                        outputDoc << "    </Agent>" << endl;
                    outputDoc << "    <Agent Id=\"" << agentMapInverse[agentActiveIds[agent]] << "\">" << endl;
                    parent.insert(a);
                }
                outputDoc << "        <Wall ShapeId=\"" << (shape - agentIDshape[agentActiveIds[agent]]) << "\" "
                          << "WallId=\"" << get<1>(key) << "\" CornerId=\"" << get<2>(key) << "\" ";
                outputDoc << "TangentialRelativeDisplacement=\"" << output[SLIP].first << "," << output[SLIP].second << "\" ";
                if (output[FORCE_ORTHO] != double2(0., 0.))
                    outputDoc << "Fn=\"" << output[FORCE_ORTHO].first << "," << output[FORCE_ORTHO].second << "\" ";
                if (output[FORCE_TAN] != double2(0., 0.))
                    outputDoc << "Ft=\"" << output[FORCE_TAN].first << "," << output[FORCE_TAN].second << "\" ";
                outputDoc << "/>" << endl;
                //  Erase the entry in slip_wall to make the next sequential search "easier"
                interactionsOutputWall.erase(iterator++);
            }
        }
    }
    outputDoc << "    </Agent>" << endl;
    outputDoc << "</Interactions>";

    outputDoc.close();
}
