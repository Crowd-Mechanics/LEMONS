"""Contains functions to represent the crowd data in dictionary format."""

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

import itertools
from collections import defaultdict
from typing import Any, cast

import numpy as np
from shapely.geometry import Point, Polygon

import configuration.utils.constants as cst
import configuration.utils.functions as fun
from configuration.models.crowd import Crowd
from configuration.utils.typing_custom import (
    DynamicCrowdDataType,
    GeometryDataType,
    InteractionsDataType,
    IntrinsicMaterialDataType,
    MaterialsDataType,
    PairMaterialsDataType,
    ShapeType,
    StaticCrowdDataType,
)


def get_light_agents_params(current_crowd: Crowd) -> StaticCrowdDataType:
    """
    Retrieve the physical and geometric parameters of all agents in a structured format.

    Parameters
    ----------
    current_crowd : Crowd
        The current crowd object containing agent data.

    Returns
    -------
    StaticCrowdDataType
        A dictionary containing agent data for all agents in the crowd.
    """
    crowd_dict: StaticCrowdDataType = {
        "Agents": {
            f"Agent{id_agent}": {
                "Type": f"{agent.agent_type.name}",
                "Id": id_agent,
                "Mass": agent.measures.measures[cst.CommonMeasures.weight.name],  # in kg
                **(
                    {"Height": agent.measures.measures[cst.PedestrianParts.height.name] * cst.CM_TO_M}  # in m
                    if agent.agent_type.name == cst.AgentTypes.pedestrian.name
                    else {}
                ),
                "MomentOfInertia": float(np.round(agent.measures.measures[cst.CommonMeasures.moment_of_inertia.name], 2)),  # in kg*m^2
                "FloorDamping": float(np.round(cst.DEFAULT_FLOOR_DAMPING, 2)),
                "AngularDamping": float(np.round(cst.DEFAULT_ANGULAR_DAMPING, 2)),
                "Shapes": agent.shapes2D.get_additional_parameters(),
            }
            for id_agent, agent in enumerate(current_crowd.agents)
        }
    }

    return crowd_dict


def get_static_params(current_crowd: Crowd) -> StaticCrowdDataType:
    """
    Retrieve the physical and geometric parameters of all agents in a structured format.

    Parameters
    ----------
    current_crowd : Crowd
        The current crowd object containing agent data.

    Returns
    -------
    StaticCrowdDataType
        Static parameters of all agents in the crowd.
    """
    crowd_dict: StaticCrowdDataType = {"Agents": defaultdict(dict)}

    # Raise an error if all the agents are not pedestrians
    if not all(agent.agent_type.name == cst.AgentTypes.pedestrian.name for agent in current_crowd.agents):
        raise ValueError("All agents must be pedestrians to retrieve static parameters.")

    for agent_id, agent in enumerate(current_crowd.agents):
        # Initialize shapes dictionary for the current agent
        shapes_dict: dict[str, int | ShapeType | float | tuple[float, float]] = defaultdict(dict)
        all_shape_params = agent.shapes2D.get_additional_parameters()
        delta_g_to_gi: dict[str, tuple[float, float]] = agent.get_delta_GtoGi()
        theta: float = agent.get_agent_orientation()
        delta_g_to_gi_rotated = fun.rotate_vectors(delta_g_to_gi, -theta)

        # Extract all shape parameters for the current agent
        for shape_name, shape_params in all_shape_params.items():
            delta_g_to_gi_shape = delta_g_to_gi_rotated[shape_name]

            # Add shape information to shapes_dict
            shapes_dict[f"{shape_name}"] = {
                "Type": shape_params["type"],
                "Radius": float(np.round(shape_params["radius"], 3)),
                "MaterialId": getattr(cst.MaterialNames, shape_params["material"]).name,
                "Position": (
                    float(np.round(delta_g_to_gi_shape[0] * cst.CM_TO_M, 3)),
                    float(np.round(delta_g_to_gi_shape[1] * cst.CM_TO_M, 3)),
                ),
            }

        # Add agent data to crowd_dict
        crowd_dict["Agents"][f"Agent{agent_id}"] = {
            "Type": agent.agent_type.name,
            "Id": agent_id,
            "Mass": float(np.round(agent.measures.measures[cst.CommonMeasures.weight.name], 2)),  # in kg
            "Height": float(np.round(agent.measures.measures[cst.PedestrianParts.height.name] * cst.CM_TO_M, 2)),  # in m
            "MomentOfInertia": float(np.round(agent.measures.measures[cst.CommonMeasures.moment_of_inertia.name], 2)),  # in kg*m^2
            "FloorDamping": float(np.round(cst.DEFAULT_FLOOR_DAMPING, 2)),
            "AngularDamping": float(np.round(cst.DEFAULT_ANGULAR_DAMPING, 2)),
            "Shapes": shapes_dict,
        }

    return crowd_dict


def get_dynamic_params(current_crowd: Crowd) -> DynamicCrowdDataType:
    """
    Retrieve the physical and geometric parameters of all agents in a structured format.

    Parameters
    ----------
    current_crowd : Crowd
        The current crowd object containing agent data.

    Returns
    -------
    DynamicCrowdDataType
        Dynamical parameters for all agents in the crowd.
    """
    dynamical_parameters_crowd: DynamicCrowdDataType = {
        "Agents": {
            f"Agent{id_agent}": {
                "Id": id_agent,
                "Kinematics": {
                    "Position": (
                        float(np.round(agent.get_position().x * cst.CM_TO_M, 3)),
                        float(np.round(agent.get_position().y * cst.CM_TO_M, 3)),
                    ),
                    "Velocity": (
                        float(np.round(cst.INITIAL_TRANSLATIONAL_VELOCITY_X, 2)),
                        float(np.round(cst.INITIAL_TRANSLATIONAL_VELOCITY_Y, 2)),
                    ),
                    "Theta": float(np.round(np.radians(agent.get_agent_orientation()), 2)),
                    "Omega": float(np.round(cst.INITIAL_ROTATIONAL_VELOCITY, 2)),
                },
                "Dynamics": {
                    "Fp": (
                        float(np.round(cst.DECISIONAL_TRANSLATIONAL_FORCE_X, 2)),
                        float(np.round(cst.DECISIONAL_TRANSLATIONAL_FORCE_Y, 2)),
                    ),
                    "Mp": float(np.round(cst.DECISIONAL_TORQUE, 2)),
                },
            }
            for id_agent, agent in enumerate(current_crowd.agents)
        }
    }

    return dynamical_parameters_crowd


def get_geometry_params(current_crowd: Crowd) -> GeometryDataType:
    """
    Retrieve the parameters of the boundaries.

    Parameters
    ----------
    current_crowd : Crowd
        The current crowd object containing agent data.

    Returns
    -------
    GeometryDataType
        A dictionary containing the geometric parameters of the boundaries, including dimensions (Lx and Ly) and wall corner data.
    """
    # Ensure current_crowd.boundaries is a Polygon
    if not isinstance(current_crowd.boundaries, Polygon):
        raise ValueError("current_crowd.boundaries must be a shapely Polygon object.")
    current_boundaries = current_crowd.boundaries
    if current_boundaries.is_empty:
        # create a boundaries with a large square
        current_boundaries = Polygon(
            [
                Point(0.0, 0.0),
                Point(0.0, cst.INFINITE),
                Point(cst.INFINITE, cst.INFINITE),
                Point(cst.INFINITE, 0.0),
            ]
        )
    # Extract coordinates from the polygon's exterior
    coords = list(current_boundaries.exterior.coords)

    # Calculate Lx and Ly as maximum distances between x and y coordinates
    x_coords = [point[0] for point in coords]
    y_coords = [point[1] for point in coords]
    Lx = max(x_coords) - min(x_coords)
    Ly = max(y_coords) - min(y_coords)

    # Construct boundaries dictionary
    boundaries_dict: GeometryDataType = {
        "Geometry": {
            "Dimensions": {
                "Lx": float(np.round(Lx * cst.CM_TO_M, 3)),
                "Ly": float(np.round(Ly * cst.CM_TO_M, 3)),
            },
            "Wall": {
                "Wall0": {
                    "Id": 0,
                    "MaterialId": cst.MaterialNames.concrete.name,
                    "Corners": {
                        f"Corner{id_corner}": {
                            "Coordinates": (
                                float(np.round(coords[id_corner][0] * cst.CM_TO_M, 3)),
                                float(np.round(coords[id_corner][1] * cst.CM_TO_M, 3)),
                            ),
                        }
                        for id_corner in range(len(coords))
                    },
                }
            },
        }
    }

    return boundaries_dict


def get_interactions_params(current_crowd: Crowd) -> InteractionsDataType:
    """
    Retrieve the parameters for agent interactions.

    Parameters
    ----------
    current_crowd : Crowd
        The current crowd object containing agent data.

    Returns
    -------
    InteractionsDataType
        A dictionary containing the parameters for agent interactions.
    """
    interactions_dict: InteractionsDataType = {"Interactions": defaultdict(dict)}

    # Loop through all agents
    for id_agent1, agent1 in enumerate(current_crowd.agents):
        agent1_data: dict[str, Any] = {
            "Id": id_agent1,
            "NeighbouringAgents": defaultdict(dict),  # Initialize as an empty dictionary
        }
        shapes_agent1 = agent1.shapes2D.get_geometric_shapes()

        for id_agent2, agent2 in enumerate(current_crowd.agents):
            if id_agent1 == id_agent2:
                continue  # Skip self-interactions

            shapes_agent2 = agent2.shapes2D.get_geometric_shapes()
            interactions: dict[str, dict[str, int | tuple[float, float]]] = {
                f"Interaction_{p_id}_{c_id}": {
                    "ParentShape": p_id,
                    "ChildShape": c_id,
                    "TangentialRelativeDisplacement": (
                        cst.INITIAL_TANGENTIAL_RELATIVE_DISPLACEMENT_X,
                        cst.INITIAL_TANGENTIAL_RELATIVE_DISPLACEMENT_Y,
                    ),
                    "Fn": (cst.INITIAL_NORMAL_FORCE_X, cst.INITIAL_NORMAL_FORCE_Y),
                    "Ft": (cst.INITIAL_TANGENTIAL_FORCE_X, cst.INITIAL_TANGENTIAL_FORCE_Y),
                }
                for p_id, shape1 in enumerate(shapes_agent1)
                for c_id, shape2 in enumerate(shapes_agent2)
                if p_id <= c_id and shape1.intersects(shape2)
            }

            if interactions:  # Only add if there are interactions
                agent1_data["NeighbouringAgents"][f"Agent{id_agent2}"] = {
                    "Id": id_agent2,
                    "Interactions": interactions,
                }

        interactions_dict["Interactions"][f"Agent{id_agent1}"] = agent1_data

    return interactions_dict


def get_materials_params() -> MaterialsDataType:
    """
    Retrieve the parameters of the materials.

    Returns
    -------
    MaterialsDataType
        A dictionary containing the parameters of the materials.
    """
    # Use the Enum directly so mypy knows the type of each member.
    materials_enum = list(cst.MaterialNames)  # list[MaterialNames]
    material_names = [m.name for m in materials_enum]  # list[str]

    # Intrinsic material properties
    intrinsic_materials: IntrinsicMaterialDataType = {}
    for id_material, material in enumerate(material_names):
        young_name = f"YOUNG_MODULUS_{material.upper()}"
        shear_name = f"SHEAR_MODULUS_{material.upper()}"

        # getattr() is dynamic -> cast to keep mypy happy
        young = cast(float, getattr(cst, young_name))
        shear = cast(float, getattr(cst, shear_name))

        intrinsic_materials[f"Material{id_material}"] = {
            "Id": material,
            "YoungModulus": float(np.round(young, 2)),
            "ShearModulus": float(np.round(shear, 2)),
        }

    # Binary material properties (pairwise interactions)
    human_naked = cst.MaterialNames.human_naked.name
    concrete = cst.MaterialNames.concrete.name

    binary_materials: PairMaterialsDataType = {}
    for id_contact, (id1, id2) in enumerate(itertools.combinations_with_replacement(material_names, 2)):
        # Defaults (typed locals help mypy)
        gamma_n: float = cst.GAMMA_NORMAL
        gamma_t: float = cst.GAMMA_TANGENTIAL
        mu_k: float = cst.KINETIC_FRICTION

        # Overrides
        if id1 == human_naked and id2 == human_naked:
            gamma_n = cst.GAMMA_NORMAL_HUMANNAKED_HUMANNAKED
            gamma_t = cst.GAMMA_TANGENTIAL_HUMANNAKED_HUMANNAKED
            mu_k = cst.KINETIC_FRICTION_HUMANNAKED_HUMANNAKED
        elif (id1 == concrete and id2 == human_naked) or (id1 == human_naked and id2 == concrete):
            gamma_n = cst.GAMMA_NORMAL_CONCRETE_HUMANNAKED
            gamma_t = cst.GAMMA_TANGENTIAL_CONCRETE_HUMANNAKED

        binary_materials[f"Contact{id_contact}"] = {
            "Id1": id1,
            "Id2": id2,
            "GammaNormal": float(np.round(gamma_n, 2)),
            "GammaTangential": float(np.round(gamma_t, 2)),
            "KineticFriction": float(np.round(mu_k, 2)),
        }

    return {
        "Materials": {
            "Intrinsic": intrinsic_materials,
            "Binary": binary_materials,
        }
    }
