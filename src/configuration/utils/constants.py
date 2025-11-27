"""Constants used in the project."""

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

from enum import Enum, auto
from types import MappingProxyType

import numpy as np

# Fix the seed
np.random.seed(0)

# Conversion factors
PIXEL_TO_CM_PEDESTRIAN: float = 30.0 / (2.0 * 405.97552)
PIXEL_TO_CM_BIKE: float = 142.0 / 204.0
MM_TO_CM: float = 0.1
INCH_TO_CM: float = 2.54
LB_TO_KG: float = 0.453592
CM_TO_M: float = 0.01
M_TO_CM: float = 100.0

# Initial agents / measures
DISK_QUAD_SEGS: int = 10  # Number of segments in a quarter circle
POLYGON_TOLERANCE: float = 0.04  # Size of minimum distance between two points
DISTANCE_BTW_TARGET_KEYS_ALTITUDES: float = 2.0  # Minimum distance between two target keys
NB_FUNCTION_EVALS: int = 80  # Number of function evaluations
DISK_NUMBER: int = 5

DEFAULT_FLOOR_DAMPING: float = 2.0  # Damping coefficient for the floor
DEFAULT_ANGULAR_DAMPING: float = 2.0  # Damping coefficient for the angular velocity
EPSILON_SMOOTHING_KNEES: float = 8.0  # Small value for smoothing
EPSILON_SMOOTHING_NECK: float = 2.0  # Small value for smoothing
NECK_HEIGHT_MALE: float = 160.0  # Height of the neck in cm
NECK_HEIGHT_FEMALE: float = 150.0  # Height of the neck in cm
KNEES_HEIGHT_MALE: float = 59.0  # Height of the knees in cm
KNEES_HEIGHT_FEMALE: float = 50.0  # Height of the knees in cm

HEIGHT_OF_BIDELTOID_OVER_HEIGHT: float = 151.6 / 187.0  # Ratio of the height of the bideltoid to the agent height (male = female)

# Material properties
YOUNG_MODULUS_CONCRETE: float = 1.7e10  # N/m
YOUNG_MODULUS_HUMAN_NAKED: float = 2.6e6  # N/m
YOUNG_MODULUS_HUMAN_CLOTHES: float = 3.05e6  # N/m

SHEAR_MODULUS_CONCRETE: float = 7.10e9  # N/m
SHEAR_MODULUS_HUMAN_NAKED: float = 7.5e5  # N/m, incompressibility hypothesis, nu = 0.5
SHEAR_MODULUS_HUMAN_CLOTHES: float = 1.02e6  # N/m, incompressibility hypothesis, nu = 0.5

GAMMA_NORMAL: float = 1.3 * 10**4  # Damping coefficient for normal contact (N/(m/s))
GAMMA_TANGENTIAL: float = 1.3 * 10**4  # Damping coefficient for tangential contact (N/(m/s))
KINETIC_FRICTION: float = 0.5  # Coefficient of kinetic friction (dimensionless)

# Crowd class
DEFAULT_AGENT_NUMBER: int = 4  # Default number of agents
MAX_NB_ITERATIONS: int = 130  # Maximum number of iterations for the parking algorithm
DEFAULT_REPULSION_LENGTH: float = 5.0  # cm
DEFAULT_DESIRED_DIRECTION: float = 0.0  # degrees
DEFAULT_VARIABLE_ORIENTATION: bool = False
INFINITE: float = 1.0e10  # Infinite value for the simulation
INTENSITY_ROTATIONAL_FORCE: float = 10.0  # degrees
INTENSITY_TRANSLATIONAL_FORCE: float = 5.0  # arbitrary units
GRID_SIZE_X: float = 31.0  # cm
GRID_SIZE_Y: float = 60.0  # cm
GRID_SIZE_X_BIKE: float = 200.0  # cm
GRID_SIZE_Y_BIKE: float = 200.0  # cm
INITIAL_TEMPERATURE: float = 1.0  # Initial temperature for the packing algorithm
ADDITIVE_COOLING: float = 0.1  # Cooling rate for the simulated annealing algorithm T<- max(T, T - COOLING_RATE)

# Crowd Statistics
DEFAULT_PEDESTRIAN_HEIGHT: float = 170.0  # cm
DEFAULT_BIKE_WEIGHT: float = 30.0  # kg
DEFAULT_PEDESTRIAN_WEIGHT: float = 70.0  # kg

# Decisional force and torque
DECISIONAL_TRANSLATIONAL_FORCE_X: float = 10.0**2  # N
DECISIONAL_TRANSLATIONAL_FORCE_Y: float = 10.0**2  # N
DECISIONAL_TORQUE: float = 0.0  # N.m

# Initial velocity
INITIAL_TRANSLATIONAL_VELOCITY_X: float = 0.0  # m/s
INITIAL_TRANSLATIONAL_VELOCITY_Y: float = 0.0  # m/s
INITIAL_ROTATIONAL_VELOCITY: float = 0.0  # rad/s

# Agent Interactions
INITIAL_TANGENTIAL_FORCE_X: float = 0.0  # N
INITIAL_TANGENTIAL_FORCE_Y: float = 0.0  # N
INITIAL_NORMAL_FORCE_X: float = 0.0  # N
INITIAL_NORMAL_FORCE_Y: float = 0.0  # N
INITIAL_TANGENTIAL_RELATIVE_DISPLACEMENT_X: float = 0.0  # m
INITIAL_TANGENTIAL_RELATIVE_DISPLACEMENT_Y: float = 0.0  # m


class BackupDataTypes(Enum):
    """Enum for backup data types."""

    zip = auto()
    pickle = auto()
    xml = auto()


class AgentTypes(Enum):
    """Enum for agent types."""

    pedestrian = auto()
    bike = auto()
    custom = auto()


class ShapeTypes(Enum):
    """Enum for shape types."""

    disk = auto()
    rectangle = auto()
    polygon = auto()


class PedestrianParts(Enum):
    """Enum for pedestrian parts."""

    sex = auto()
    bideltoid_breadth = auto()
    chest_depth = auto()
    height = auto()


class Sex(Enum):
    """Enum for pedestrian sex."""

    male = auto()
    female = auto()


class BikeParts(Enum):
    """Bike is an enumeration that defines different parts of a bike."""

    wheel_width = auto()
    total_length = auto()
    handlebar_length = auto()
    top_tube_length = auto()


class CommonMeasures(Enum):
    """CommonMeasures is an enumeration that defines different common measures."""

    weight = auto()
    moment_of_inertia = auto()


class StatType(Enum):
    """StatType is an enumeration that defines different types of statistics."""

    mean = auto()
    std_dev = auto()
    min = auto()
    max = auto()


CrowdStat = MappingProxyType(
    {
        "male_proportion": 0.5,
        "pedestrian_proportion": 1.0,
        "bike_proportion": 0.0,
        # Male measurements
        "male_bideltoid_breadth_min": 30.0,  # cm
        "male_bideltoid_breadth_max": 65.0,  # cm
        "male_bideltoid_breadth_mean": 51.0,  # cm
        "male_bideltoid_breadth_std_dev": 2.0,  # cm
        "male_chest_depth_min": 15.0,  # cm
        "male_chest_depth_max": 45.0,  # cm
        "male_chest_depth_mean": 26.0,  # cm
        "male_chest_depth_std_dev": 2.0,  # cm
        "male_height_min": 140.0,  # cm
        "male_height_max": 240.0,  # cm
        "male_height_mean": 178.0,  # cm
        "male_height_std_dev": 8.0,  # cm
        "male_weight_min": 30.0,  # kg
        "male_weight_max": 160.0,  # kg
        "male_weight_mean": 85.0,  # kg
        "male_weight_std_dev": 15.0,  # kg
        # Female measurements
        "female_bideltoid_breadth_min": 30.0,  # cm
        "female_bideltoid_breadth_max": 60.0,  # cm
        "female_bideltoid_breadth_mean": 45.0,  # cm
        "female_bideltoid_breadth_std_dev": 1.5,  # cm
        "female_chest_depth_min": 15.0,  # cm
        "female_chest_depth_max": 45.0,  # cm
        "female_chest_depth_mean": 24.0,  # cm
        "female_chest_depth_std_dev": 1.5,  # cm
        "female_height_min": 140.0,  # cm
        "female_height_max": 210.0,  # cm
        "female_height_mean": 164.0,  # cm
        "female_height_std_dev": 7.0,  # cm
        "female_weight_min": 30.0,  # kg
        "female_weight_max": 130.0,  # kg
        "female_weight_mean": 67.0,  # kg
        "female_weight_std_dev": 11.0,  # kg
        # Wheel dimensions
        "wheel_width_min": 2.0,  # cm
        "wheel_width_max": 20.0,  # cm
        "wheel_width_mean": 6.0,  # cm
        "wheel_width_std_dev": 0.50,  # cm
        # Total length
        "total_length_min": 100.0,  # cm
        "total_length_max": 200.0,  # cm
        "total_length_mean": 142.0,  # cm
        "total_length_std_dev": 5.0,  # cm
        # Handlebar dimensions
        "handlebar_length_min": 30.0,  # cm
        "handlebar_length_max": 90.0,  # cm
        "handlebar_length_mean": 45.0,  # cm
        "handlebar_length_std_dev": 5.0,  # cm
        # Top tube dimensions
        "top_tube_length_min": 40.0,  # cm
        "top_tube_length_max": 90.0,  # cm
        "top_tube_length_mean": 61.0,  # cm
        "top_tube_length_std_dev": 5.0,  # cm
        # Bike weights
        "bike_weight_min": 10.0,  # kg
        "bike_weight_max": 100.0,  # kg
        "bike_weight_mean": 30.0,  # kg
        "bike_weight_std_dev": 5.0,  # kg
    }
)


class MaterialNames(Enum):
    """Enum for material names."""

    concrete = auto()
    human_clothes = auto()
    human_naked = auto()


class MaterialProperties(Enum):
    """Enum for material properties."""

    young_modulus = auto()
    shear_modulus = auto()


class MaterialsContactProperties(Enum):
    """Enum for the properties of the contact between two materials."""

    gamma_normal = auto()
    gamma_tangential = auto()
    kinetic_friction = auto()
