"""Module containing the AgentMeasures and CrowdMeasures dataclass to store body measures and crowd desired measures."""

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
from pathlib import Path

import numpy as np

import configuration.utils.constants as cst
from configuration.utils import functions as fun
from configuration.utils.typing_custom import Sex


@dataclass
class AgentMeasures:
    """Class to store body characteristics based on agent type."""

    agent_type: cst.AgentTypes
    measures: dict[str, float | Sex] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Validate the measures based on the agent type after object initialization.

        Raises
        ------
        ValueError
            If the agent type is not one of the allowed values.
        ValueError
            If measures is not a dictionary.
        ValueError
            If required measures for the agent type are missing.
        ValueError
            If extra measures are provided for non-custom agent types.
        ValueError
            If the sex for a pedestrian agent is invalid.
        """
        # Check if the agent type is valid
        if not isinstance(self.agent_type, cst.AgentTypes):
            raise ValueError(f"Agent type should be one of: {[member.name for member in cst.AgentTypes]}.")

        # Check if measures is a dictionary
        if not isinstance(self.measures, dict):
            raise ValueError("measures should be a dictionary.")

        # Determine required parts based on the agent type
        if self.agent_type == cst.AgentTypes.pedestrian:
            required_parts = {part.name for part in cst.PedestrianParts}
        elif self.agent_type == cst.AgentTypes.bike:
            required_parts = {part.name for part in cst.BikeParts}
        elif self.agent_type == cst.AgentTypes.custom:
            required_parts = set()  # Custom agents have no predefined required parts
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")
        required_parts.add(cst.CommonMeasures.weight.name)
        # we do not add the moment of inertia because it will computed a posteriori and added to the measures later

        # Validate that all required measures are present
        missing_parts = required_parts - self.measures.keys()
        if missing_parts:
            raise ValueError(f"Missing measures for {self.agent_type}: {', '.join(missing_parts)}")

        # Validate that no extra measures are provided
        extra_parts = self.measures.keys() - required_parts
        # Do not care about the moment of inertia measure if it exists as it will be computed a posteriori
        extra_parts.discard(cst.CommonMeasures.moment_of_inertia.name)
        if extra_parts and self.agent_type != cst.AgentTypes.custom:
            raise ValueError(f"Extra measures provided for {self.agent_type}: {', '.join(extra_parts)}")

        # if pedestrian, check if the sex is valid (str and either male or female)
        if self.agent_type == cst.AgentTypes.pedestrian.name:
            sex_name = self.measures[cst.PedestrianParts.sex]
            if not isinstance(sex_name, str) or sex_name.lower() not in ["male", "female"]:
                raise ValueError(f"Invalid sex name: {sex_name}. Expected 'male' or 'female'.")

    def number_of_measures(self) -> int:
        """
        Return the number of measures stored.

        Returns
        -------
        int
            The number of measures stored in the "measures" attribute.
        """
        return len(self.measures)


@dataclass
class CrowdMeasures:
    """Collection of dictionaries (databases and statistics) representing the characteristics of the crowd, used to create agents."""

    default_database: dict[int, dict[str, float]] = field(default_factory=dict)
    agent_statistics: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Validate the crowd measures after the dataclass initialization and loads the ANSURII dataset into the `default_database`.

        Raises
        ------
        ValueError
            If `default_database`, or `agent_statistics` are not dictionaries.
        ValueError
            If any required statistics are missing in `agent_statistics`.
        """
        # Check if the provided databases are dictionaries
        if not isinstance(self.default_database, dict):
            raise ValueError("default_database should be a dictionary.")
        if not isinstance(self.agent_statistics, dict):
            raise ValueError("agent_statistics should be a dictionary.")

        # Fill the default database with the ANSURII dataset
        dir_path = Path(__file__).parent.parent.parent.parent.absolute() / "data" / "pkl"
        self.default_database = (fun.load_pickle(str(dir_path / "ANSUREIIPublic.pkl"))).transpose().to_dict()

        # Check if the agent statistics are provided for all parts
        if self.agent_statistics:
            required_parts = cst.CrowdStat.keys()
            missing_parts = required_parts - self.agent_statistics.keys()
            if missing_parts:
                raise ValueError(f"Missing statistics for the crowd: {', '.join(missing_parts)}")


def draw_agent_measures(agent_type: cst.AgentTypes, crowd_measures: CrowdMeasures) -> AgentMeasures:
    """
    Draw randomly a set of agent measures based on the agent type.

    Parameters
    ----------
    agent_type : AgentTypes
        The type of agent for which to draw measures. Must be either AgentTypes.pedestrian or AgentTypes.bike.
    crowd_measures : CrowdMeasures
        An object containing statistical measures for the crowd, including both pedestrian and bike-specific measurements.

    Returns
    -------
    AgentMeasures
        An object containing the randomly drawn measures for the specified agent type.
    """
    if agent_type == cst.AgentTypes.pedestrian:
        return _draw_pedestrian_measures(crowd_measures)
    if agent_type == cst.AgentTypes.bike:
        return _draw_bike_measures(crowd_measures)
    raise ValueError(f"Invalid agent type '{agent_type}'. Please provide a valid agent type.")


def _draw_pedestrian_measures(crowd_measures: CrowdMeasures) -> AgentMeasures:
    """
    Draw pedestrian-specific measures from the crowd statistics.

    Parameters
    ----------
    crowd_measures : CrowdMeasures
        An object containing statistical measures for the crowd, including
        pedestrian-specific measurements.

    Returns
    -------
    AgentMeasures
        An object containing the randomly drawn measures for a pedestrian agent, including:
            - sex : Literal["male","female"]
                The randomly drawn sex of the pedestrian ("male" or "female").
            - bideltoid_breadth : float
                The shoulder width of the pedestrian.
            - chest_depth : float
                The chest depth of the pedestrian.
            - height : float
                The height of the pedestrian (set to a default value).
            - weight : float
                The weight of the pedestrian.
    """
    agent_sex = fun.draw_sex(crowd_measures.agent_statistics["male_proportion"])
    measures = {
        cst.PedestrianParts.sex.name: agent_sex,
        cst.PedestrianParts.bideltoid_breadth.name: _draw_measure(crowd_measures, agent_sex, cst.PedestrianParts.bideltoid_breadth),
        cst.PedestrianParts.chest_depth.name: _draw_measure(crowd_measures, agent_sex, cst.PedestrianParts.chest_depth),
        cst.PedestrianParts.height.name: _draw_measure(crowd_measures, agent_sex, cst.PedestrianParts.height),
        cst.CommonMeasures.weight.name: _draw_measure(crowd_measures, agent_sex, cst.CommonMeasures.weight),
    }
    return AgentMeasures(agent_type=cst.AgentTypes.pedestrian, measures=measures)


def _draw_bike_measures(crowd_measures: CrowdMeasures) -> AgentMeasures:
    """
    Draw bike-specific measures from the crowd statistics.

    Parameters
    ----------
    crowd_measures : CrowdMeasures
        An object containing statistical measures for the crowd, including bike-specific measurements.

    Returns
    -------
    AgentMeasures
        An object containing the randomly drawn measures for a bike agent, including:
            - wheel_width : float
            - total_length : float
            - handlebar_length : float
            - top_tube_length : float
            - weight : float
    """
    measures = {
        cst.BikeParts.wheel_width.name: _draw_measure(crowd_measures, None, cst.BikeParts.wheel_width),
        cst.BikeParts.total_length.name: _draw_measure(crowd_measures, None, cst.BikeParts.total_length),
        cst.BikeParts.handlebar_length.name: _draw_measure(crowd_measures, None, cst.BikeParts.handlebar_length),
        cst.BikeParts.top_tube_length.name: _draw_measure(crowd_measures, None, cst.BikeParts.top_tube_length),
        cst.CommonMeasures.weight.name: _draw_measure(crowd_measures, None, cst.CommonMeasures.weight),
    }

    return AgentMeasures(agent_type=cst.AgentTypes.bike, measures=dict(measures))


def _draw_measure(crowd_measures: CrowdMeasures, sex: Sex | None, part_enum: cst.PedestrianParts | cst.BikeParts) -> float:
    """
    Draw a measure for a specific body part or bike component, from a truncated normal distribution.

    Parameters
    ----------
    crowd_measures : CrowdMeasures
        An object containing statistical measures for the crowd.
    sex : Literal["male","female"] or None
        The sex of the agent ("male" or "female") for pedestrians, or None for bikes.
    part_enum : PedestrianParts or BikeParts
        The enum representing the body part or bike component to measure.

    Returns
    -------
    float
        A randomly drawn measure from the truncated normal distribution.
    """
    # Initialize prefix based on sex
    prefix = f"{sex}_" if sex else ""

    # Check if part_enum.name is "weight" and sex is truthy
    if str(part_enum.name) == "weight":
        # if sex:
        #     prefix = "pedestrian_"
        if not sex:
            prefix = "bike_"

    stats = crowd_measures.agent_statistics
    mean = stats[f"{prefix}{part_enum.name}_mean"]
    std_dev = stats[f"{prefix}{part_enum.name}_std_dev"]
    min_val = stats[f"{prefix}{part_enum.name}_min"]
    max_val = stats[f"{prefix}{part_enum.name}_max"]

    return float(fun.draw_from_trunc_normal(mean, std_dev, min_val, max_val))


def draw_agent_type(crowd_measures: CrowdMeasures) -> cst.AgentTypes:
    """
    Draw a random agent type using tower sampling algorithm.

    Parameters
    ----------
    crowd_measures : CrowdMeasures
        An instance of CrowdMeasures containing the statistics of different agent types in the crowd.

    Returns
    -------
    AgentTypes
        The randomly selected agent type (pedestrian or bike) based on the given proportions.

    Raises
    ------
    ValueError
        If the sum of pedestrian and bike proportions is not equal to 1.
    """
    # Get the proportions of pedestrian and bike agents
    pedestrian_proportion = crowd_measures.agent_statistics["pedestrian_proportion"]
    bike_proportion = crowd_measures.agent_statistics["bike_proportion"]

    # Check if the proportions sum to 1
    if pedestrian_proportion + bike_proportion != 1.0:
        raise ValueError("The proportions of pedestrian and bike agents should sum to 1.")

    # Draw a random agent type based on the proportions
    cumulative_proportion = 0.0
    random_value = np.random.uniform(0, 1)

    # Loop through the agent types and return the one that corresponds to the random value
    for agent_type in cst.AgentTypes:
        proportion = 0.0
        if agent_type == cst.AgentTypes.pedestrian:
            proportion = pedestrian_proportion
        elif agent_type == cst.AgentTypes.bike:
            proportion = bike_proportion

        cumulative_proportion += proportion

        if random_value <= cumulative_proportion:
            return agent_type

    # If the random value is greater than the sum of proportions, return pedestrian by default
    return cst.AgentTypes.pedestrian


def create_pedestrian_measures(agent_data: dict[str, float]) -> AgentMeasures:
    """
    Create pedestrian-specific AgentMeasures object.

    Parameters
    ----------
    agent_data : dict[str, float]
        A dictionary containing pedestrian measurements. Expected keys are:
            - "sex": The sex of the pedestrian (either "male" or "female").
            - "bideltoid breadth [cm]": Shoulder width in centimeters.
            - "chest depth [cm]": Depth of the chest in centimeters.
            - "height [cm]": Height of the pedestrian in centimeters.
            - "weight [kg]": Weight of the pedestrian in kilograms.

    Returns
    -------
    AgentMeasures
        An AgentMeasures object.
    """
    return AgentMeasures(
        agent_type=cst.AgentTypes.pedestrian,
        measures={
            cst.PedestrianParts.sex.name: agent_data["sex"],
            cst.PedestrianParts.bideltoid_breadth.name: agent_data["bideltoid breadth [cm]"],
            cst.PedestrianParts.chest_depth.name: agent_data["chest depth [cm]"],
            cst.PedestrianParts.height.name: agent_data["height [cm]"],
            cst.CommonMeasures.weight.name: agent_data["weight [kg]"],
        },
    )


def create_bike_measures(agent_data: dict[str, float]) -> AgentMeasures:
    """
    Create bike-specific AgentMeasures object.

    Parameters
    ----------
    agent_data : dict[str, float]
        A dictionary containing bike measurements. Expected keys are:
            - "wheel width [cm]": Width of the bike's wheel in centimeters.
            - "total length [cm]": Total length of the bike in centimeters.
            - "handlebar length [cm]": Length of the bike's handlebar in centimeters.
            - "top tube length [cm]": Length of the bike's top tube in centimeters.

    Returns
    -------
    AgentMeasures
        An AgentMeasures object with the following attributes:
            - agent_type: Set to AgentTypes.bike
            - measures: A dictionary mapping bike parts to their measurements
    """
    return AgentMeasures(
        agent_type=cst.AgentTypes.bike,
        measures={
            cst.BikeParts.wheel_width.name: agent_data["wheel width [cm]"],
            cst.BikeParts.total_length.name: agent_data["total length [cm]"],
            cst.BikeParts.handlebar_length.name: agent_data["handlebar length [cm]"],
            cst.BikeParts.top_tube_length.name: agent_data["top tube length [cm]"],
        },
    )
