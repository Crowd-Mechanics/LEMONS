"""Class to store body shapes dynamically based on agent type."""

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

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import dual_annealing
from shapely.affinity import scale
from shapely.geometry import MultiPoint, MultiPolygon

import configuration.utils.constants as cst
import configuration.utils.functions as fun
from configuration.models.initial_agents import InitialPedestrian
from configuration.models.measures import AgentMeasures
from configuration.utils.typing_custom import ShapeDataType


@dataclass
class Shapes3D:
    """Store and manage 3D body shapes for different agent types."""

    agent_type: cst.AgentTypes
    shapes: ShapeDataType = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Validate dataclass attributes after initialization.

        Raises
        ------
        ValueError
            If any of the following validation checks fail:
                - Agent type is not a member of `AgentTypes`
                - Shapes container is not a dictionary
                - Shape values are not Shapely MultiPolygon objects
                - Height keys cannot be converted to float values
        """
        # Validate the provided agent type
        if not isinstance(self.agent_type, cst.AgentTypes):
            raise ValueError(f"Agent type should be one of: {[member.name for member in cst.AgentTypes]}.")

        # Validate the provided shapes
        if not isinstance(self.shapes, dict):
            raise ValueError("shapes should be a dictionary.")

        # Validate that the provided shapes are valid Shapely objects
        for height, multipolygon in self.shapes.items():
            if not isinstance(multipolygon, MultiPolygon):
                raise ValueError(f"Invalid shape type for '{height}': {type(multipolygon)}")
            try:
                float(height)
            except ValueError:
                raise ValueError(f"Invalid height type for '{height}': {type(height)}") from None

    def create_pedestrian3D(self, measurements: AgentMeasures) -> None:
        """
        Create a 3D representation of a pedestrian based on provided measurements.

        Parameters
        ----------
        measurements : AgentMeasures
            An object containing the target measurements of the pedestrian, including sex, bideltoid breadth, chest depth, and height.

        Raises
        ------
        ValueError
            If the provided sex in "measurements" is not "male" or "female".

        Notes
        -----
        - The method uses an initial pedestrian representation based on the provided sex.
        - Scaling factors are calculated for each dimension (x, y, z) based on
          the ratio of target measurements to initial measurements.
        """
        # Extract sex from measurements and create initial pedestrian object
        sex_name = measurements.measures[cst.PedestrianParts.sex.name]
        if isinstance(sex_name, str) and sex_name in ["male", "female"]:
            initial_pedestrian = InitialPedestrian(sex_name)
        else:
            raise ValueError(f"Invalid sex name: {sex_name}. Expected 'male' or 'female'.")

        # Calculate scaling factors for each dimension
        scale_factor_x = float(measurements.measures[cst.PedestrianParts.bideltoid_breadth.name]) / float(
            initial_pedestrian.measures[cst.PedestrianParts.bideltoid_breadth.name]
        )
        scale_factor_y = float(measurements.measures[cst.PedestrianParts.chest_depth.name]) / float(
            initial_pedestrian.measures[cst.PedestrianParts.chest_depth.name]
        )
        scale_factor_z = float(measurements.measures[cst.PedestrianParts.height.name]) / float(
            initial_pedestrian.measures[cst.PedestrianParts.height.name]
        )
        reference_multipolygon = initial_pedestrian.get_reference_multipolygon()
        wanted_chest_depth = float(measurements.measures[cst.PedestrianParts.chest_depth.name])
        wanted_bideltoid_breadth = float(measurements.measures[cst.PedestrianParts.bideltoid_breadth.name])

        def objectif_fun(scaling_factor: NDArray[np.float64]) -> float:
            """
            Objective function to minimize the difference between the scaled bideltoid breadth and the target value.

            Parameters
            ----------
            scaling_factor : NDArray[np.float64]
                The scaling factor for the x, y, and z dimensions.

            Returns
            -------
            float
                The absolute difference between the scaled bideltoid breadth and the target value.
            """
            # Extract scaling factors for x, y, and z dimensions
            scale_factor_x = scaling_factor[0]
            scale_factor_y = scaling_factor[1]
            homothety_center = reference_multipolygon.centroid
            scaled_multipolygon = scale(
                reference_multipolygon,
                xfact=scale_factor_x,
                yfact=scale_factor_y,
                origin=homothety_center,
            )
            # Compute the scaled bideltoid breadth
            scaled_bideltoid_breadth = fun.compute_bideltoid_breadth_from_multipolygon(scaled_multipolygon)
            scaled_chest_depth = fun.compute_chest_depth_from_multipolygon(scaled_multipolygon)
            penalty_chest: float = (scaled_chest_depth - wanted_chest_depth) ** 2
            penalty_bideltoid: float = (scaled_bideltoid_breadth - wanted_bideltoid_breadth) ** 2
            return float(penalty_chest + penalty_bideltoid)

        # Optimize the scaling factors to minimize the penalty
        bounds = np.array([[1e-5, 3.0], [1e-5, 3.0]])
        guess_parameters = np.array([scale_factor_x, scale_factor_y])
        optimized_scaling = dual_annealing(objectif_fun, bounds=bounds, x0=guess_parameters, maxfun=cst.NB_FUNCTION_EVALS)
        optimized_scale_factor_x, optimized_scale_factor_y = optimized_scaling.x

        # Initialize dictionary to store scaled 3D shapes
        current_body3D: ShapeDataType = {}

        # Calculate the center point for scaling (centroid of all initial shapes)
        homothety_center = MultiPoint([multipolygon.centroid for multipolygon in initial_pedestrian.shapes3D.values()]).centroid

        # Scale each component of the initial 3D representation
        for height, multipolygon in initial_pedestrian.shapes3D.items():
            scaled_multipolygon = scale(
                multipolygon,
                xfact=fun.rectangular_function(height, optimized_scale_factor_x, sex_name),
                yfact=fun.rectangular_function(height, optimized_scale_factor_y, sex_name),
                origin=homothety_center,
            )
            scaled_height = height * scale_factor_z
            current_body3D[scaled_height] = MultiPolygon(scaled_multipolygon)

        # Update the shapes attribute with the new 3D representation
        self.shapes = current_body3D

    def get_height(self) -> float:
        """
        Compute the height of the agent in meters.

        Returns
        -------
        float
            The height of the agent in meters.
        """
        if self.agent_type != cst.AgentTypes.pedestrian:
            raise ValueError("get_height() can only be used for pedestrian agents.")
        shapes3D_dict = self.shapes
        lowest_height = min(float(height) for height in shapes3D_dict.keys())
        highest_height = max(float(height) for height in shapes3D_dict.keys())
        return highest_height - lowest_height

    def get_reference_multipolygon(self) -> MultiPolygon:
        """
        Get the reference multipolygon of the agent i.e. the one at torso height.

        Returns
        -------
        MultiPolygon
            The reference multipolygon of the agent.
        """
        smallest_height = min(self.shapes.keys())
        largest_height = max(self.shapes.keys()) - smallest_height
        theoretical_torso_height = largest_height * cst.HEIGHT_OF_BIDELTOID_OVER_HEIGHT + smallest_height
        closest_height = min(self.shapes.keys(), key=lambda x: abs(float(x) - theoretical_torso_height))
        multip = self.shapes[closest_height]
        return multip

    def get_bideltoid_breadth(self) -> float:
        """
        Compute the bideltoid breadth of the agent (that has an orientation of 90°) in cm.

        Returns
        -------
        float
            The bideltoid breadth of the agent in cm.
        """
        if self.agent_type != cst.AgentTypes.pedestrian:
            raise ValueError("get_bideltoid_breadth() can only be used for pedestrian agents.")
        reference_multipolygon = self.get_reference_multipolygon()
        return float(fun.compute_bideltoid_breadth_from_multipolygon(reference_multipolygon))

    def get_chest_depth(self) -> float:
        """
        Compute the chest depth of the agent (that has an orientation of 90°) in cm.

        Returns
        -------
        float
            The chest depth of the agent in cm.
        """
        if self.agent_type != cst.AgentTypes.pedestrian:
            raise ValueError("get_chest_depth() can only be used for pedestrian agents.")
        reference_multipolygon = self.get_reference_multipolygon()
        return float(fun.compute_chest_depth_from_multipolygon(reference_multipolygon))
