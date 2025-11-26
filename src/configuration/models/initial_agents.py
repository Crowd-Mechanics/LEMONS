"""Module defining the InitialPedestrian and InitialBike classes."""

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

from pathlib import Path

from shapely.geometry import MultiPolygon, Point, box
from shapely.ops import unary_union

import configuration.utils.constants as cst
from configuration.utils import functions as fun
from configuration.utils.typing_custom import Sex, ShapeDataType, ShapeType


class InitialPedestrian:
    """
    Class representing the initial pedestrian state including its 2D shape data and basic measurements.

    Parameters
    ----------
    sex : Sex
        Biological sex of the pedestrian, must be either "male" or "female".
    """

    def __init__(self, sex: Sex) -> None:
        """
        Initialize a pedestrian agent with biomechanical properties.

        Parameters
        ----------
        sex : Sex
            Biological sex of the pedestrian, must be either "male" or "female".

        Attributes
        ----------
        _agent_type : AgentTypes
            Agent type set to pedestrian
        _shapes2D : ShapeDataType
            2D shape object
        _shapes3D : dict[float, MultiPolygon]
            3D body layers mapped to z-height coordinates
        _measures : dict[str, float | Sex | None]
            Biomechanical measurements including:
                - sex: Biological sex (Literal["male","female"])
                - bideltoid_breadth: Shoulder width derived from disk4
                - chest_depth: Torso depth from disk2
                - height: Vertical span of 3D body
                - weight: Default weight from constants file
                - moment_of_inertia: Initially uncalculated (None)

        Notes
        -----
        - 2D and 3D coordinates are in centimeters
        - The moment_of_inertia will computed later when the agent will be created
        """
        if isinstance(sex, str) and sex not in ["male", "female"]:
            raise ValueError("The sex should be either 'male' or 'female'.")

        self._agent_type: cst.AgentTypes = cst.AgentTypes.pedestrian
        self._shapes2D: ShapeDataType = self._initialize_shapes()
        dir_path = Path(__file__).parent.parent.parent.parent.absolute() / "data" / "pkl"
        self._shapes3D: dict[float, MultiPolygon] = fun.load_pickle(str(dir_path / f"{sex}_3dBody_light.pkl"))

        # Initialize measures
        bideltoid_breadth: float = 0.0
        if (
            isinstance(self._shapes2D["disk4"]["x"], float)
            and isinstance(self._shapes2D["disk4"]["y"], float)
            and isinstance(self._shapes2D["disk4"]["radius"], float)
        ):
            bideltoid_breadth = 2.0 * self._shapes2D["disk4"]["x"] + 2.0 * self._shapes2D["disk4"]["radius"]
        chest_depth: float = 0.0
        if isinstance(self._shapes2D["disk2"]["radius"], float):
            chest_depth = 2.0 * self._shapes2D["disk2"]["radius"]

        self._measures: dict[str, float | Sex | None] = {
            cst.PedestrianParts.sex.name: sex,
            cst.PedestrianParts.bideltoid_breadth.name: bideltoid_breadth,
            cst.PedestrianParts.chest_depth.name: chest_depth,
            cst.PedestrianParts.height.name: abs(max(self._shapes3D.keys()) - min(self._shapes3D.keys())),
            cst.CommonMeasures.weight.name: cst.DEFAULT_PEDESTRIAN_WEIGHT,
            cst.CommonMeasures.moment_of_inertia.name: None,
        }

        # Center the initial shapes around (0, 0)
        self._center_initial_shapes2D()

    def _initialize_shapes(self) -> dict[str, dict[str, ShapeType | float | tuple[float, float]]]:
        """
        Initialize shape data.

        Creates and configures five circular disks representing key body features:
            - Disk0: Left arm
            - Disk1: Left pectoral muscle
            - Disk2: Central belly
            - Disk3: Right pectoral muscle
            - Disk4: Right arm

        Returns
        -------
        dict[str, dict[str, ShapeType | float | tuple[float, float]]]
            Nested dictionary containing circular shape data with:
                - Outer keys: Component IDs (e.g., "disk0" to "disk4")
                - Inner dictionaries containing:
                    * type: "disk" (str from ShapeTypes enum name)
                    * radius: Disk radius (cm)
                    * material: Material name (str from MaterialNames enum)
                    * x: x-coordinate (cm)
                    * y: y-coordinate (cm)

        Notes
        -----
        - Initial coordinates are defined in image pixels before conversion
        - Defaults to (0.0, 0.0) center and 0.0 radius if invalid data types found
        - Disk positions correspond to anatomical features:
            - Disk2 represents central belly
            - Disks 1/3 represent left/right pectoral muscle
            - Disks 0/4 represent left/right arms
        """
        # Define disk parameters (center coordinates and radii)
        disks: list[dict[str, tuple[float, float] | float]] = [
            {"center": (-552.7920, 0.00000), "radius": 282.41232},
            {"center": (-242.5697, 71.73901), "radius": 388.36243},
            {"center": (0.0000, 86.11438), "radius": 405.97552},
            {"center": (242.5697, 71.73901), "radius": 388.36243},
            {"center": (552.7920, 0.00000), "radius": 282.41232},
        ]

        # Convert disk data into a structured dictionary
        return {
            f"disk{i}": {
                "type": cst.ShapeTypes.disk.name,
                "radius": disk["radius"] * cst.PIXEL_TO_CM_PEDESTRIAN if isinstance(disk["radius"], float) else 0.0,
                "material": cst.MaterialNames.human_naked.name,
                "x": disk["center"][0] * cst.PIXEL_TO_CM_PEDESTRIAN if isinstance(disk["center"], tuple) else 0.0,
                "y": disk["center"][1] * cst.PIXEL_TO_CM_PEDESTRIAN if isinstance(disk["center"], tuple) else 0.0,
            }
            for i, disk in enumerate(disks)
        }

    @property
    def sex(self) -> Sex:
        """
        Get the biological sex of the pedestrian.

        Returns
        -------
        Sex
            The biological sex of the pedestrian as either "male" or "female".

        Raises
        ------
        ValueError
            If provided value is not "male" or "female"
        TypeError
            If non-string value is provided
        """
        sex_name = self._measures[cst.PedestrianParts.sex.name]
        if isinstance(sex_name, str) and sex_name in ["male", "female"]:
            return sex_name
        raise TypeError(f"Expected type 'str' with value 'male' or 'female', but got {type(sex_name).__name__}")

    @property
    def agent_type(self) -> cst.AgentTypes:
        """
        Get the type of the agent.

        Returns
        -------
        AgentTypes
            Enum member representing the agent's type classification (either "pedestrian", "bike" or "custom").
        """
        return self._agent_type

    @property
    def shapes2D(self) -> ShapeDataType:
        """
        Get the 2D geometric representation of the pedestrian's body components.

        Returns
        -------
        ShapeDataType
            Dictionary containing circular disk representations of body parts with:
                - Keys: Format "disk{N}" where N ranges 0-4 (e.g., "disk0", "disk1")
                - Values: Dictionaries with properties:
                    * type: "disk" (str from ShapeTypes enum name)
                    * radius: Disk radius (cm)
                    * material: Material name (str from MaterialNames enum)
                    * x: x-coordinate (cm)
                    * y: y-coordinate (cm)
        """
        return self._shapes2D

    @property
    def measures(self) -> dict[str, float | Sex | None]:
        """
        Get the measures of the pedestrian.

        Returns
        -------
        dict[str, float | Sex | None]
            A dictionary containing the pedestrian's measures. The keys are measure name.
        """
        return self._measures

    @property
    def shapes3D(self) -> dict[float, MultiPolygon]:
        """
        Get the 3D body representation of the pedestrian.

        Returns
        -------
        dict[float, MultiPolygon]
            A dictionary where:
                - Keys are float representing the height of each pedestrian slice.
                - Values are "MultiPolygon" objects representing the 2D geometry of each layer or slice.
        """
        return self._shapes3D

    def _center_initial_shapes2D(self) -> None:
        """Center the initial 2D shapes of the pedestrian to center them around (0, 0)."""
        center_of_mass = self.get_position()
        for shape in self.shapes2D.values():
            shape["x"] -= center_of_mass.x
            shape["y"] -= center_of_mass.y

    def get_position(self) -> Point:
        """
        Get the centroid position of the pedestrian based on their 2D shapes.

        Returns
        -------
        Point
            A Point object representing the centroid of the pedestrian's geometry.
        """
        # Create buffered shapes from the 2D shape definitions
        buffered_shapes = [
            Point(shape["x"], shape["y"]).buffer(shape["radius"], quad_segs=cst.DISK_QUAD_SEGS) for shape in self.shapes2D.values()
        ]

        if not buffered_shapes:
            raise ValueError("No shapes defined for the pedestrian.")

        # Compute the union of all shapes
        combined_shape = unary_union(buffered_shapes)

        # Return the centroid as a Point
        return combined_shape.centroid

    def get_disk_centers(self) -> list[Point]:
        """
        Retrieve the center coordinates of all disks of the agent physical shape.

        Returns
        -------
        list[Point]
            A list of Point objects representing the center coordinates of each disk (cm).
            The points are returned in the order of disk indices (disk0, disk1, ..., diskN-1).
        """
        return [Point(self.shapes2D[f"disk{i}"]["x"], self.shapes2D[f"disk{i}"]["y"]) for i in range(cst.DISK_NUMBER)]

    def get_disk_radii(self) -> list[float]:
        """
        Retrieve the radii of all disks of the agent physical shape.

        Returns
        -------
        list[float]
            A list containing the radii of the disks in the order they are stored.
        """
        list_of_radii: list[float] = []
        for i in range(cst.DISK_NUMBER):
            radius = self.shapes2D[f"disk{i}"]["radius"]
            if isinstance(radius, float):
                list_of_radii.append(radius)
        return list_of_radii

    def get_reference_multipolygon(self) -> MultiPolygon:
        """
        Get the reference multipolygon of the agent i.e. the one at torso height.

        Returns
        -------
        MultiPolygon
            The reference multipolygon of the agent.
        """
        smallest_height = min(self.shapes3D.keys())
        largest_height = max(self.shapes3D.keys()) - smallest_height
        theoretical_torso_height = largest_height * cst.HEIGHT_OF_BIDELTOID_OVER_HEIGHT + smallest_height
        closest_height = min(self.shapes3D.keys(), key=lambda x: abs(float(x) - theoretical_torso_height))
        multip = self.shapes3D[closest_height]
        return multip

    def get_bideltoid_breadth(self) -> float:
        """
        Compute the bideltoid breadth of the agent (that has not rotated) in cm.

        Returns
        -------
        float
            The bideltoid breadth of the agent (cm).
        """
        if self.agent_type != cst.AgentTypes.pedestrian:
            raise ValueError("get_bideltoid_breadth() can only be used for pedestrian agents.")
        reference_multipolygon = self.get_reference_multipolygon()
        return float(fun.compute_bideltoid_breadth_from_multipolygon(reference_multipolygon))

    def get_chest_depth(self) -> float:
        """
        Compute the chest depth of the agent (that has not rotated) in cm.

        Returns
        -------
        float
            The chest depth of the agent (cm).
        """
        if self.agent_type != cst.AgentTypes.pedestrian:
            raise ValueError("get_chest_depth() can only be used for pedestrian agents.")
        reference_multipolygon = self.get_reference_multipolygon()
        return float(fun.compute_chest_depth_from_multipolygon(reference_multipolygon))

    def get_height(self) -> float:
        """
        Compute the height of the agent (cm).

        Returns
        -------
        float
            The height of the agent (cm).
        """
        if self.agent_type != cst.AgentTypes.pedestrian:
            raise ValueError("get_height() can only be used for pedestrian agents.")
        shapes3D_dict = self.shapes3D
        lowest_height = min(float(height) for height in shapes3D_dict.keys())
        highest_height = max(float(height) for height in shapes3D_dict.keys())
        return highest_height - lowest_height


class InitialBike:
    """Class representing the initial state of a bike, including its 2D shape data and derived measurements."""

    def __init__(self) -> None:
        """
        Initialize an instance of the InitialBike class.

        Attributes
        ----------
        _agent_type : AgentTypes
            The type of agent, initialized to 'bike'.
        _shapes2D : ShapeDataType
            The 2D shape data initialized by the "_initialize_shapes" method.
        _measures : dict[str, float | None]
            A dictionary containing measurements derived from the shape data.
            Keys are defined in BikeParts and CommonMeasures enums:
                - 'wheel_width': The width of the bike's wheel.
                - 'total_length': The total length of the bike.
                - 'handlebar_length': The length of the rider's handlebar.
                - 'top_tube_length': The length of the rider's top tube.
                - 'weight': The default weight of the bike (set to DEFAULT_BIKE_WEIGHT).
                - 'moment_of_inertia': The moment of inertia (initially set to None).

        Notes
        -----
        - All measurements are calculated in centimeters.
        - The moment of inertia is initially set to None and should be calculated separately.
        """
        self._agent_type: cst.AgentTypes = cst.AgentTypes.bike
        self._shapes2D: ShapeDataType = self._initialize_shapes()

        # Initialize measures
        wheel_width: float = 0.0
        if isinstance(self._shapes2D["bike"]["max_x"], float) and isinstance(self._shapes2D["bike"]["min_x"], float):
            wheel_width = self._shapes2D["bike"]["max_x"] - self._shapes2D["bike"]["min_x"]
        total_length: float = 0.0
        if isinstance(self._shapes2D["bike"]["max_y"], float) and isinstance(self._shapes2D["bike"]["min_y"], float):
            total_length = self._shapes2D["bike"]["max_y"] - self._shapes2D["bike"]["min_y"]
        handlebar_length: float = 0.0
        if isinstance(self._shapes2D["rider"]["max_x"], float) and isinstance(self._shapes2D["rider"]["min_x"], float):
            handlebar_length = self._shapes2D["rider"]["max_x"] - self._shapes2D["rider"]["min_x"]
        top_tube_length: float = 0.0
        if isinstance(self._shapes2D["rider"]["max_y"], float) and isinstance(self._shapes2D["rider"]["min_y"], float):
            top_tube_length = self._shapes2D["rider"]["max_y"] - self._shapes2D["rider"]["min_y"]

        self._measures: dict[str, float | None] = {
            cst.BikeParts.wheel_width.name: wheel_width,
            cst.BikeParts.total_length.name: total_length,
            cst.BikeParts.handlebar_length.name: handlebar_length,
            cst.BikeParts.top_tube_length.name: top_tube_length,
            cst.CommonMeasures.weight.name: cst.DEFAULT_BIKE_WEIGHT,
            cst.CommonMeasures.moment_of_inertia.name: None,
        }

        # Center the initial shapes around (0, 0)
        self._center_initial_shapes2D()

    def _initialize_shapes(self) -> dict[str, dict[str, ShapeType | float]]:
        """
        Initialize 2D shape data for the bicycle and rider.

        Creates rectangular shapes for both bicycle and rider, then:
        1. Calculates their original center of mass
        2. Adjusts coordinates to set center of mass at (0,0)
        3. Converts coordinates from pixels to centimeters using PIXEL_TO_CM_BIKE

        Returns
        -------
        dict[str, dict[str, ShapeType | float]]
            Nested dictionary containing shape data with two keys:
                - "bike": Dictionary of bicycle shape properties
                - "rider": Dictionary of rider shape properties
            Each shape dictionary contains:
                - type: ShapeTypes.rectangle.name (str)
                - material: MaterialNames.iron.name (str)
                - min_x: Minimum x-coordinate (cm)
                - min_y: Minimum y-coordinate (cm)
                - max_x: Maximum x-coordinate (cm)
                - max_y: Maximum y-coordinate (cm)
        """
        # define the bike as a rectangle
        rider = {
            "min_x": 62.0,
            "min_y": 96.0,
            "max_x": 62.0 + 86.0,
            "max_y": 96.0 + 99.0,
        }
        # define the rider as a rectangle orthogonal to the bike
        bike = {
            "min_x": 96.0,
            "min_y": 46.0,
            "max_x": 96.0 + 16.0,
            "max_y": 46.0 + 204.0,
        }
        # put the CM to (0,0) and convert to cm
        center_of_mass_bike = Point((bike["min_x"] + bike["max_x"]) / 2.0, (bike["min_y"] + bike["max_y"]) / 2.0)
        center_of_mass_rider = Point(
            (rider["min_x"] + rider["max_x"]) / 2.0,
            (rider["min_y"] + rider["max_y"]) / 2.0,
        )
        bike["min_x"] = bike["min_x"] - center_of_mass_bike.x
        bike["min_y"] = bike["min_y"] - center_of_mass_bike.y
        bike["max_x"] = bike["max_x"] - center_of_mass_bike.x
        bike["max_y"] = bike["max_y"] - center_of_mass_bike.y
        rider["min_x"] = rider["min_x"] - center_of_mass_rider.x
        rider["min_y"] = rider["min_y"] - center_of_mass_rider.y
        rider["max_x"] = rider["max_x"] - center_of_mass_rider.x
        rider["max_y"] = rider["max_y"] - center_of_mass_rider.y

        for key in bike:
            bike[key] = bike[key] * cst.PIXEL_TO_CM_BIKE
        for key in rider:
            rider[key] = rider[key] * cst.PIXEL_TO_CM_BIKE

        return {
            "bike": {
                "type": cst.ShapeTypes.rectangle.name,
                "material": cst.MaterialNames.concrete.name,
                "min_x": bike["min_x"],
                "min_y": bike["min_y"],
                "max_x": bike["max_x"],
                "max_y": bike["max_y"],
            },
            "rider": {
                "type": cst.ShapeTypes.rectangle.name,
                "material": cst.MaterialNames.human_clothes.name,
                "min_x": rider["min_x"],
                "min_y": rider["min_y"],
                "max_x": rider["max_x"],
                "max_y": rider["max_y"],
            },
        }

    @property
    def agent_type(self) -> cst.AgentTypes:
        """
        Get the type of the agent.

        Returns
        -------
        AgentTypes
            Enum member representing the agent's type classification (either "pedestrian", "bike" or "custom").
        """
        # return error if the agent type is not bike
        if self._agent_type != cst.AgentTypes.bike:
            raise ValueError("The agent type is not bike.")
        return self._agent_type

    @property
    def shapes2D(self) -> ShapeDataType:
        """
        Get the 2D shapes of the agent.

        Returns
        -------
        ShapeDataType
            An object containing the 2D shapes of the agent.
        """
        return self._shapes2D

    @property
    def measures(self) -> dict[str, float | None]:
        """
        Get the measures of the agent.

        Returns
        -------
        dict[str, float | None]
            A dictionary containing the measures of the agent.
            Keys are measure names and values are measure values.
        """
        return self._measures

    def get_position(self) -> Point:
        """
        Compute the centroid position of the agent based on all 2D shapes.

        Returns
        -------
        Point
            A Point object representing the centroid of the agent's geometry.

        Raises
        ------
        ValueError
            If no valid shapes are found in self.shapes2D.
        """
        polygons = []
        for shape_name, shape in self.shapes2D.items():
            try:
                min_x = shape["min_x"]
                min_y = shape["min_y"]
                max_x = shape["max_x"]
                max_y = shape["max_y"]
                polygons.append(box(min_x, min_y, max_x, max_y))
            except KeyError as e:
                raise ValueError(f"Missing key {e} in shape '{shape_name}'") from e

        if not polygons:
            raise ValueError("No valid shapes found to compute centroid.")

        combined_shape = unary_union(polygons)
        return combined_shape.centroid

    def _center_initial_shapes2D(self) -> None:
        """Center the initial 2D shapes of the bike to center them around (0, 0)."""
        center_of_mass = self.get_position()
        for shape in self.shapes2D.values():
            shape["min_x"] -= center_of_mass.x
            shape["min_y"] -= center_of_mass.y
            shape["max_x"] -= center_of_mass.x
            shape["max_y"] -= center_of_mass.y
