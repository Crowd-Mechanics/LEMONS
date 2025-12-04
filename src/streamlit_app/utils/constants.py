"""Constants used in the application."""

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

from configuration.utils.typing_custom import Sex

# User Interface
#: Name fo the first tab within the Streamlit application
FIRST_TAB_NAME: str = "One agent"
#: Name fo the second tab within the Streamlit application
SECOND_TAB_NAME: str = "Crowd"
#: Name fo the third tab within the Streamlit application
THIRD_TAB_NAME: str = "Anthropometry"
#: Name fo the fourth tab within the Streamlit application
FOURTH_TAB_NAME: str = "About"

#: Project name
PROJECT_NAME: str = "LEMONS"

# 2D / 3D shapes tab
#: Minimum pedestrian height (cm)
DEFAULT_HEIGHT_MIN: float = 100.0
#: Maximum pedestrian height (cm)
DEFAULT_HEIGHT_MAX: float = 230.0

#: Maximum translation along X axis allowed (cm)
MAX_TRANSLATION_X: float = 200.0  # cm
#: Maximum translation along Y axis allowed (cm)
MAX_TRANSLATION_Y: float = 200.0  # cm

#: Default sex of the pedestrian
DEFAULT_SEX: Sex = "male"

# Crowd tab
#: Default boundary length along X axis (cm)
DEFAULT_BOUNDARY_X: float = 200.0
#: Minimum boundary length along X axis (cm)
DEFAULT_BOUNDARY_X_MIN: float = 50.0
#: Maximum boundary length along X axis (cm)
DEFAULT_BOUNDARY_X_MAX: float = 2000.0
#: Default boundary length along Y axis (cm)
DEFAULT_BOUNDARY_Y: float = 200.0
#: Minimum boundary length along Y axis (cm)
DEFAULT_BOUNDARY_Y_MIN: float = 50.0
#: Maximum boundary length along Y axis (cm)
DEFAULT_BOUNDARY_Y_MAX: float = 2000.0
#:  Default number of agents in the crowd
DEFAULT_AGENT_NUMBER: int = 4
#: Minimum number of agents in the crowd
DEFAULT_AGENT_NUMBER_MIN: int = 1
#: Maximum number of agents in the crowd
DEFAULT_AGENT_NUMBER_MAX: int = 300

#: Minimum repulsion strength between agents during crowd generation
DEFAULT_REPULSION_LENGTH_MIN: float = 1.0
#: Maximum repulsion strength between agents during crowd generation
DEFAULT_REPULSION_LENGTH_MAX: float = 70.0

#: Presence or not of wall interactions during the simulation
DEFAULT_WALL_INTERACTION: bool = False

# Developer
#: Show or not developer options in the application to help debugging
SHOW_DEV: bool = False
