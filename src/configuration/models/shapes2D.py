"""Class to store body shapes based on agent type."""

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
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import dual_annealing
from shapely.affinity import scale
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union

import configuration.utils.constants as cst
import configuration.utils.functions as fun
from configuration.models.initial_agents import InitialBike, InitialPedestrian
from configuration.models.measures import AgentMeasures
from configuration.utils.typing_custom import MaterialType, ShapeDataType, ShapeType


@dataclass
class Shapes2D:
    """
    Class to store body shapes based on agent type.

    This class allows you to manage shapes in two ways:

    1. Provide a dictionary of pre-defined Shapely shapes as input
    2. Specify the type of shape and its characteristics to create it
    """

    agent_type: cst.AgentTypes
    shapes: ShapeDataType = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Validate the provided shapes and agent type after initialization.

        Raises
        ------
        ValueError
            If the agent type is not one of the allowed values defined in `AgentType`.
        ValueError
            If the `shapes` attribute is not a dictionary.
        ValueError
            If any shape in the `shapes` dictionary is not a valid Shapely object (Point or Polygon).
        ValueError
            If the reference direction is not within the range (-180.0, 180.0].
        """
        # Validate the provided agent type
        if not isinstance(self.agent_type, cst.AgentTypes):
            raise ValueError(f"Agent type should be one of: {[member.name for member in cst.AgentTypes]}.")

        # Validate the provided shapes
        if not isinstance(self.shapes, dict):
            raise ValueError("shapes should be a dictionary.")

        # Validate that the provided shapes are valid Shapely objects
        for shape_name, shape in self.shapes.items():
            if not isinstance(shape.get("object"), (Point, Polygon)):
                raise ValueError(f"Invalid shape type for '{shape_name}': {type(shape.get('object'))}")

    def add_shape(self, name: str, shape_type: ShapeType, material: MaterialType, **kwargs: Any) -> None:
        r"""
        Create a shape and add it to the shapes dictionary.

        Parameters
        ----------
        name : str
            The name of the shape.
        shape_type : ShapeType
            The type of the shape. Must be one of the following: {'disk', 'rectangle', 'polygon'}.
        material : MaterialType
            The material of the shape.
        \*\*kwargs : Any
            Additional keyword arguments specific to the shape type:

            - **Disk**:

                - `x` (float): The x-coordinate of the disk's center.
                - `y` (float): The y-coordinate of the disk's center.
                - `radius` (float): The radius of the disk.
                - `material` (str): The material of the disk.

            - **Rectangle**:

                - `min_x` (float): The minimum x-coordinate of the rectangle.
                - `min_y` (float): The minimum y-coordinate of the rectangle.
                - `max_x` (float): The maximum x-coordinate of the rectangle.
                - `max_y` (float): The maximum y-coordinate of the rectangle.
                - `material` (str): The material of the rectangle.

            - **Polygon**:

                - `points` (list of tuple[float, float]): A list of `(x, y)` coordinates representing
                    the vertices of the polygon. Must contain at least 3 points, and the first and last
                    points must match to close the polygon.
                - `material` (str): The material of the polygon.

        Raises
        ------
        ValueError
            If the shape type is unsupported or if required keyword arguments are missing or invalid.

        Notes
        -----
        This method validates that all required parameters are provided and ensures that
        shapes are correctly formatted before adding them to the dictionary.
        """
        fun.validate_material(material)

        if shape_type == cst.ShapeTypes.disk.name:
            center = (kwargs.get("x"), kwargs.get("y"))
            radius = kwargs.get("radius")
            if not isinstance(center, tuple) or not isinstance(radius, (int, float)):
                raise ValueError("For a disk, 'center' must be a tuple and 'radius' must be a number.")
            if not isinstance(material, str):
                raise ValueError("'material' must be a string.")
            self.shapes[name] = {
                "type": cst.ShapeTypes.disk.name,
                "material": material,
                "object": Point(center).buffer(radius, quad_segs=cst.DISK_QUAD_SEGS),
            }

        elif shape_type == cst.ShapeTypes.rectangle.name:
            min_x = kwargs.get("min_x")
            min_y = kwargs.get("min_y")
            max_x = kwargs.get("max_x")
            max_y = kwargs.get("max_y")
            if not all(isinstance(coord, (int, float)) for coord in [min_x, min_y, max_x, max_y]):
                raise ValueError("For a rectangle, 'min_x', 'min_y', 'max_x', and 'max_y' must be numbers.")
            self.shapes[name] = {
                "type": cst.ShapeTypes.rectangle.name,
                "material": material,
                "object": Polygon([(min_x, min_y), (min_x, max_y), (max_x, max_y), (max_x, min_y)]),
            }

        elif shape_type == cst.ShapeTypes.polygon.name:
            points = kwargs.get("points")
            if not isinstance(points, list) or not all(isinstance(point, tuple) for point in points):
                raise ValueError("For a polygon, 'points' must be a list of tuples.")

            if len(points) < 3 or points[0] != points[-1]:
                raise ValueError("A polygon must have at least 3 points and the first/last points must match.")

            self.shapes[name] = {
                "type": cst.ShapeTypes.polygon.name,
                "material": material,
                "object": Polygon(points),
            }
        else:
            raise ValueError(f"Unsupported shape type: {shape_type}. Must be one of {cst.ShapeTypes.__members__}.")

    def get_additional_parameters(self) -> ShapeDataType:
        """
        Retrieve the parameters for each stored shape.

        Returns
        -------
        ShapeDataType
            A dictionary where each key is the name of a shape, and the corresponding value is a dictionary
            containing the parameters for that shape. The structure of the parameter dictionary depends on
            the type of shape:

            - **Disk**:

                - `type` (str): The type of the shape (always `'disk'`).
                - `radius` (float): The radius of the disk.
                - `material` (str): The material of the disk's interior.
                - `x` (float): The x-coordinate of the disk's center.
                - `y` (float): The y-coordinate of the disk's center.

            - **Rectangle**:

                - `type` (str): The type of the shape (always `'rectangle'`).
                - `material` (str): The material of the rectangle's interior.
                - `min_x` (float): The x-coordinate of the rectangle's minimum bound.
                - `min_y` (float): The y-coordinate of the rectangle's minimum bound.
                - `max_x` (float): The x-coordinate of the rectangle's maximum bound.
                - `max_y` (float): The y-coordinate of the rectangle's maximum bound.

            - **Polygon**:

                - `type` (str): The type of the shape (always `'polygon'`).
                - `material` (str): The material of the polygon's interior.
                - `points` (list of tuple[float, float]): A list of `(x, y)` coordinates representing
                    the vertices of the polygon.

        Notes
        -----
        This method assumes that all shapes are stored with their respective parameters in a consistent format.
        """
        # Create a dictionary to store the parameters of each shape
        params: ShapeDataType = {}
        for name, shape in self.shapes.items():
            material = shape.get("material")
            # Retrieve the parameters of each shape according to its type
            if shape["type"] == cst.ShapeTypes.disk.name:
                disk: Polygon = shape["object"]
                disk_center = disk.centroid
                disk_radius = disk.exterior.distance(disk.centroid)
                params[name] = {
                    "type": cst.ShapeTypes.disk.name,
                    "radius": float(np.round(disk_radius * cst.CM_TO_M, 3)),
                    "material": material,
                    "x": float(np.round(disk_center.x * cst.CM_TO_M, 3)),
                    "y": float(np.round(disk_center.y * cst.CM_TO_M, 3)),
                }
            elif shape["type"] == cst.ShapeTypes.rectangle.name:
                rect: Polygon = shape["object"]
                min_x, min_y, max_x, max_y = rect.bounds
                params[name] = {
                    "type": cst.ShapeTypes.rectangle.name,
                    "material": material,
                    "min_x": float(np.round(min_x * cst.CM_TO_M, 3)),
                    "min_y": float(np.round(min_y * cst.CM_TO_M, 3)),
                    "max_x": float(np.round(max_x * cst.CM_TO_M, 3)),
                    "max_y": float(np.round(max_y * cst.CM_TO_M, 3)),
                }
            elif shape["type"] == cst.ShapeTypes.polygon.name:
                poly: Polygon = shape["object"]
                poly_points = list(poly.exterior.coords)
                poly_points = [
                    (float(np.round(point[0] * cst.CM_TO_M, 3)), float(np.round(point[1] * cst.CM_TO_M, 3))) for point in poly_points
                ]
                params[name] = {
                    "type": cst.ShapeTypes.polygon.name,
                    "material": material,
                    "points": poly_points,
                }

        return params

    def number_of_shapes(self) -> int:
        """
        Return the total number of stored shapes.

        Returns
        -------
        int
            The total number of shapes stored in the `shapes` attribute.
        """
        return len(self.shapes)

    def create_pedestrian_shapes(self, measurements: AgentMeasures) -> None:
        """
        Create the shapes of a pedestrian based on the provided measures.

        This method generates the shapes of a pedestrian agent by scaling initial disk centers and radii
        according to the provided measurements. To find the correct scalings, it uses an optimization algorithm
        to minimize the difference between the desired and actual chest depth and bideltoid breadth.

        Parameters
        ----------
        measurements : AgentMeasures
            An object containing the measurements of the pedestrian agent.

        Raises
        ------
        ValueError
            If the agent type is not 'pedestrian'.
        """
        # Validate the agent type
        if self.agent_type != cst.AgentTypes.pedestrian:
            raise ValueError("create_pedestrian_shapes() can only create pedestrian agents.")

        # Scale the initial pedestrian shapes to match the provided measurements
        sex_name = measurements.measures[cst.PedestrianParts.sex.name]
        homothety_center = Point(0.0, 0.0)
        if isinstance(sex_name, str) and sex_name in ["male", "female"]:
            initial_pedestrian = InitialPedestrian(sex_name)
            homothety_center = initial_pedestrian.get_position()

        def objectif_fun(scaling_factor: NDArray[np.float64]) -> float:
            """
            Objective function to minimize the difference between the desired and actual pedestrian dimensions.

            Parameters
            ----------
            scaling_factor : NDArray[np.float64]
                A 1D numpy array of length 2 containing scaling factors:

                - scaling_factor[0]: x-axis scaling factor
                - scaling_factor[1]: y-axis scaling factor

            Returns
            -------
            float
                The penalty value representing the sum of squared differences between the desired and actual dimensions.
            """
            # Retrieve the wanted measurements from the provided measures
            wanted_chest_depth = measurements.measures[cst.PedestrianParts.chest_depth.name]
            wanted_bideltoid_breadth = measurements.measures[cst.PedestrianParts.bideltoid_breadth.name]

            # Compute the new measurements based on the scaling factors
            scale_factor_x, scale_factor_y = scaling_factor
            adjusted_centers = [
                scale(disk_center, xfact=scale_factor_x, origin=homothety_center)
                for disk_center in initial_pedestrian.get_disk_centers()
            ]
            adjusted_radii = [disk_radius * scale_factor_y for disk_radius in initial_pedestrian.get_disk_radii()]
            current_chest_depth = 2.0 * adjusted_radii[2]
            current_bideltoid_breadth = 2.0 * adjusted_centers[4].x + 2.0 * adjusted_radii[4]

            # Compute the penalty based on the difference between the new and old measurements
            penalty_chest = (current_chest_depth - wanted_chest_depth) ** 2
            penalty_shoulder_breadth = (current_bideltoid_breadth - wanted_bideltoid_breadth) ** 2

            return float(penalty_chest + penalty_shoulder_breadth)

        # Optimize the scaling factors to minimize the penalty
        bounds = np.array([[1e-5, 3.0], [1e-5, 3.0]])
        guess_parameters = np.array([0.9, 0.9])
        optimized_scaling = dual_annealing(
            objectif_fun,
            bounds=bounds,
            maxfun=cst.NB_FUNCTION_EVALS,
            x0=guess_parameters,
        )
        optimized_scale_factor_x, optimized_scale_factor_y = optimized_scaling.x

        # Adjust the initial pedestrian shapes based on the optimized scaling factors
        adjusted_centers = [
            scale(disk_center, xfact=optimized_scale_factor_x, origin=homothety_center)
            for disk_center in initial_pedestrian.get_disk_centers()
        ]
        adjusted_radii = [disk_radius * optimized_scale_factor_y for disk_radius in initial_pedestrian.get_disk_radii()]

        # Create the adjusted shapes for the pedestrian
        disks = [{"center": center, "radius": radius} for center, radius in zip(adjusted_centers, adjusted_radii, strict=False)]
        adjusted_shapes = {
            f"disk{i}": {
                "type": cst.ShapeTypes.disk.name,
                "material": cst.MaterialNames.human_naked.name,
                "object": Point(disk["center"]).buffer(disk["radius"], quad_segs=cst.DISK_QUAD_SEGS),
            }
            for i, disk in enumerate(disks)
        }

        self.shapes = adjusted_shapes

    def create_bike_shapes(self, measurements: AgentMeasures) -> None:
        """
        Create and scale 2D shapes for a bike and its rider based on provided measurements.

        This method uses an optimization process to generate bike and rider shapes that
        best match the provided measurements. It scales initial shapes to minimize the
        difference between desired and actual dimensions.

        Parameters
        ----------
        measurements : AgentMeasures
            An object containing the target measurements for various bike parts and rider dimensions.

        Raises
        ------
        ValueError
            If the agent type is not 'bike'.
        """
        # Validate the agent type
        if self.agent_type != cst.AgentTypes.bike:
            raise ValueError("create_bike_shapes() can only create bike agents.")

        # Scale the initial bike shapes to match the provided measurements
        init_bike = InitialBike()

        def objective_fun(scaling_factor: NDArray[np.float64]) -> float:
            """
            Objective function to minimize the difference between the desired and actual bike/rider dimensions.

            Parameters
            ----------
            scaling_factor : NDArray[np.float64]
                An array containing the scaling factors for the bike and rider dimensions in the order
                [scale_bike_factor_x,
                scale_bike_factor_y,
                scale_rider_factor_x,
                scale_rider_factor_y].

            Returns
            -------
            float
                The penalty value representing the sum of squared differences between the desired and actual dimensions.
            """
            # Unpack the scaling factors
            (
                scale_bike_factor_x,
                scale_bike_factor_y,
                scale_rider_factor_x,
                scale_rider_factor_y,
            ) = scaling_factor

            # Retrieve the wanted measurements from the provided measures
            wanted_rider_width = measurements.measures[cst.BikeParts.handlebar_length.name]
            wanted_rider_length = measurements.measures[cst.BikeParts.top_tube_length.name]
            wanted_bike_width = measurements.measures[cst.BikeParts.wheel_width.name]
            wanted_bike_length = measurements.measures[cst.BikeParts.total_length.name]

            # Compute the new measurements based on the scaling factors
            new_shapes = {
                "bike": {
                    "type": cst.ShapeTypes.rectangle.name,
                    "material": cst.MaterialNames.concrete.name,
                    "min_x": init_bike.shapes2D["bike"]["min_x"] * scale_bike_factor_x,
                    "min_y": init_bike.shapes2D["bike"]["min_y"] * scale_bike_factor_y,
                    "max_x": init_bike.shapes2D["bike"]["max_x"] * scale_bike_factor_x,
                    "max_y": init_bike.shapes2D["bike"]["max_y"] * scale_bike_factor_y,
                },
                "rider": {
                    "type": cst.ShapeTypes.rectangle.name,
                    "material": cst.MaterialNames.human_clothes.name,
                    "min_x": init_bike.shapes2D["rider"]["min_x"] * scale_rider_factor_x,
                    "min_y": init_bike.shapes2D["rider"]["min_y"] * scale_rider_factor_y,
                    "max_x": init_bike.shapes2D["rider"]["max_x"] * scale_rider_factor_x,
                    "max_y": init_bike.shapes2D["rider"]["max_y"] * scale_rider_factor_y,
                },
            }
            current_bike_length = abs(new_shapes["bike"]["max_y"] - new_shapes["bike"]["min_y"])
            current_rider_width = abs(new_shapes["rider"]["max_x"] - new_shapes["rider"]["min_x"])
            current_rider_length = abs(new_shapes["rider"]["max_y"] - new_shapes["rider"]["min_y"])
            current_bike_width = abs(new_shapes["bike"]["max_x"] - new_shapes["bike"]["min_x"])

            # Compute the penalty based on the difference between the current and wanted measurements
            penalty_rider_width = (wanted_rider_width - current_rider_width) ** 2
            penalty_rider_length = (wanted_rider_length - current_rider_length) ** 2
            penalty_bike_width = (wanted_bike_width - current_bike_width) ** 2
            penalty_bike_length = (wanted_bike_length - current_bike_length) ** 2

            return float(penalty_rider_length + penalty_bike_width + penalty_bike_length + penalty_rider_width)

        # Optimize the scaling factors to minimize the penalty
        bounds = np.array([[1e-5, 3.0], [1e-5, 3.0], [1e-5, 3.0], [1e-5, 3.0]])
        guess_parameters = np.array([0.99, 0.99, 0.99, 0.99])
        optimised_scaling = dual_annealing(
            objective_fun,
            bounds=bounds,
            maxfun=cst.NB_FUNCTION_EVALS,
            x0=guess_parameters,
        )
        opt_bike_sfx, opt_bike_sfy, opt_rider_sfx, opt_rider_sfy = optimised_scaling.x  # optimised scaling factors

        # Adjust the initial bike shapes based on the optimized scaling factors
        adjusted_shapes = {
            "bike": {
                "type": cst.ShapeTypes.rectangle.name,
                "material": cst.MaterialNames.concrete.name,
                "object": Polygon(
                    [
                        (
                            init_bike.shapes2D["bike"]["min_x"] * opt_bike_sfx,
                            init_bike.shapes2D["bike"]["min_y"] * opt_bike_sfy,
                        ),
                        (
                            init_bike.shapes2D["bike"]["min_x"] * opt_bike_sfx,
                            init_bike.shapes2D["bike"]["max_y"] * opt_bike_sfy,
                        ),
                        (
                            init_bike.shapes2D["bike"]["max_x"] * opt_bike_sfx,
                            init_bike.shapes2D["bike"]["max_y"] * opt_bike_sfy,
                        ),
                        (
                            init_bike.shapes2D["bike"]["max_x"] * opt_bike_sfx,
                            init_bike.shapes2D["bike"]["min_y"] * opt_bike_sfy,
                        ),
                    ]
                ),
            },
            "rider": {
                "type": cst.ShapeTypes.rectangle.name,
                "material": cst.MaterialNames.human_clothes.name,
                "object": Polygon(
                    [
                        (
                            init_bike.shapes2D["rider"]["min_x"] * opt_rider_sfx,
                            init_bike.shapes2D["rider"]["min_y"] * opt_rider_sfy,
                        ),
                        (
                            init_bike.shapes2D["rider"]["min_x"] * opt_rider_sfx,
                            init_bike.shapes2D["rider"]["max_y"] * opt_rider_sfy,
                        ),
                        (
                            init_bike.shapes2D["rider"]["max_x"] * opt_rider_sfx,
                            init_bike.shapes2D["rider"]["max_y"] * opt_rider_sfy,
                        ),
                        (
                            init_bike.shapes2D["rider"]["max_x"] * opt_rider_sfx,
                            init_bike.shapes2D["rider"]["min_y"] * opt_rider_sfy,
                        ),
                    ]
                ),
            },
        }
        self.shapes = adjusted_shapes

    def get_geometric_shapes(self) -> list[Polygon]:
        """
        Return the geometric shapes that constitute a pedestrian physical shape.

        Returns
        -------
        list[Polygon]
            A list of Polygon objects representing the individual shapes.
        """
        return [shape["object"] for shape in self.shapes.values()]

    def get_geometric_shape(self) -> Polygon | MultiPolygon:
        """
        Return the geometric union of all shapes that constitute a pedestrian physical shape.

        Returns
        -------
        Polygon
            The union of all stored shapes as a single Polygon object.
        """
        return unary_union(self.get_geometric_shapes())

    def get_area(self) -> float:
        """
        Compute the area of the agent 2D representation.

        Returns
        -------
        float
            The area of the agent 2D representation (cm²).
        """
        return float(self.get_geometric_shape().area)

    def get_chest_depth(self) -> float:
        """
        Compute the chest depth (anterior-posterior diameter) of a pedestrian agent in centimeters.

        The chest depth is defined as twice the radius of 'disk2', converted from meters to centimeters.

        Returns
        -------
        float
            The chest depth of the agent in centimeters.

        Raises
        ------
        ValueError
            If the agent is not a pedestrian or required parameters are missing.
        """
        if self.agent_type != cst.AgentTypes.pedestrian:
            raise ValueError("get_chest_depth() can only be used for pedestrian agents.")

        parameters_shapes = self.get_additional_parameters()

        # Ensure 'disk2' and 'radius' are present
        if "disk2" not in parameters_shapes:
            raise ValueError("Missing required parameter: 'disk2' in agent shape parameters.")
        if "radius" not in parameters_shapes["disk2"]:
            raise ValueError("Missing 'radius' in 'disk2' parameters.")

        radius_m = parameters_shapes["disk2"]["radius"]
        chest_depth_cm = 2.0 * radius_m * cst.M_TO_CM

        return float(chest_depth_cm)

    def get_bideltoid_breadth(self) -> float:
        """
        Compute the bideltoid breadth (shoulder width) of a pedestrian agent in centimeters.

        Returns
        -------
        float
            The bideltoid breadth of the agent in centimeters.

        Raises
        ------
        ValueError
            If the agent is not a pedestrian or required parameters are missing.
        """
        if self.agent_type != cst.AgentTypes.pedestrian:
            raise ValueError("get_bideltoid_breadth() can only be used for pedestrian agents.")

        parameters_shapes = self.get_additional_parameters()

        # Ensure required disks are present
        for disk in ("disk0", "disk4"):
            if disk not in parameters_shapes:
                raise ValueError(f"Missing required parameter: '{disk}' in agent shape parameters.")

        disk0 = parameters_shapes["disk0"]
        disk4 = parameters_shapes["disk4"]

        # Ensure required keys are present in each disk
        for key in ("x", "y", "radius"):
            if key not in disk0 or key not in disk4:
                raise ValueError(f"Missing '{key}' in disk parameters.")

        # Calculate the center-to-center distance between disk0 and disk4
        dx = disk4["x"] - disk0["x"]
        dy = disk4["y"] - disk0["y"]
        center_distance = np.hypot(dx, dy)

        # Total breadth is the sum of both radii and the center distance, converted to cm
        total_breadth_m = disk0["radius"] + center_distance + disk4["radius"]
        bideltoid_breadth_cm = total_breadth_m * cst.M_TO_CM

        return float(bideltoid_breadth_cm)
