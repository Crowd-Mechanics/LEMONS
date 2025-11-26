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

#include "Agent.h"

#include <vector>

using std::vector;

#if !defined(DOXYGEN_SHOULD_SKIP_THIS)
/**
 * @brief Calculates the size of the body of the agent.
 * The size is defined as the radius of the smallest circle containing all the shapes.
 *
 * @param delta_gtos The vector of delta_gtos', ie the shapes' positions relative to the agent's center of mass
 * @param radius_shapes The vector of radius_shapes, ie the radii of the agent's shapes.
 *
 * @return The size of the body of the agent.
 */
static double size_body(const vector<double2>& delta_gtos, const vector<double>& radius_shapes)
{
    double max_delta_gtos = 0.0;
    size_t cpt_max = 0;
    for (size_t i = 0; i < delta_gtos.size(); ++i)
    {
        if (const double magnitude = !delta_gtos[i]; magnitude > max_delta_gtos)
        {
            max_delta_gtos = magnitude;
            cpt_max = i;
        }
    }
    double radius(radius_shapes[cpt_max]);
    if (radius_shapes[cpt_max] < 0.0)
    {
        radius = -radius_shapes[cpt_max];
    }
    return radius + max_delta_gtos;
}
#endif   // DOXYGEN_SHOULD_SKIP_THIS

/**
 * @brief Constructor for the Agent class.
 *
 * @param ID The ID of the agent.
 * @param Ids_shapes The Ids of the shapes
 * @param nb_shapes The number of shapes.
 * @param delta_gtos Vector the shapes' positions relative to the agent's center of mass.
 * @param radius_shapes Vector of shape radii.
 * @param theta_body_init The initial orientation of the agent's body.
 * @param mass The mass of the agent.
 * @param moi The moment of inertia of the agent.
 */
Agent::Agent(unsigned ID, std::vector<unsigned> Ids_shapes, unsigned nb_shapes, const std::vector<double2>& delta_gtos,
             const std::vector<double>& radius_shapes, double theta_body_init, double mass, double moi)
    : _id(ID),
      _mass(mass),
      _moi(moi),
      _ids_shapes(std::move(Ids_shapes)),
      _radius(size_body(delta_gtos, radius_shapes)),
      _nb_shapes(nb_shapes),
      _delta_gtos(delta_gtos),
      _radius_shapes(radius_shapes),
      _theta_init(theta_body_init)
{
}

/**
 * @brief Destructor for the Agent class.
 *
 * This destructor is responsible for cleaning up any resources allocated by an Agent object.
 * It is automatically called when an Agent object goes out of scope or is explicitly deleted.
 */
Agent::~Agent() = default;

/**
 * @brief Moves the agent based on its velocity and angular velocity.
 *
 * This function updates the position and orientation of the agent based on its current velocity (_vx, _vy)
 * and angular velocity (_w). The movement is performed over a small time interval (dt).
 */
void Agent::move()
{
    _x += _vx * dt;
    _y += _vy * dt;
    _theta += _w * dt;
}

/**
 * @brief Calculates the current relative positions of the shapes
 *
 * Based on the current orientation of the agent wrt the x-axis, this function gives
 * the relative positions of the agent's shapes.
 *
 * @return The updated relative positions of the shapes
 */
vector<double2> Agent::get_delta_gtos()
{
    vector<double2> delta_gtos_abs;
    for (auto [x, y] : _delta_gtos)
    {
        const double rotation_angle = _theta - _theta_init;
        delta_gtos_abs.emplace_back(x * cos(rotation_angle) - y * sin(rotation_angle),
                                    x * sin(rotation_angle) + y * cos(rotation_angle));
    }
    return delta_gtos_abs;
}
