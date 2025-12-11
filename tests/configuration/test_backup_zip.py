"""Test the integrity of the crowd data saved in a zip file."""

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

import zipfile
from pathlib import Path
from typing import Callable, Optional

import pytest

import configuration.backup.crowd_to_dict as fun_dict
import configuration.backup.crowd_to_zip_and_reverse as fun_zip
import configuration.backup.dict_to_xml_and_reverse as fun_xml
from configuration.models.crowd import Crowd
from configuration.utils.typing_custom import (
    DynamicCrowdDataType,
    GeometryDataType,
    InteractionsDataType,
    MaterialsDataType,
    StaticCrowdDataType,
)


@pytest.fixture(name="crowd_fixture")
def crowd_fixture() -> Crowd:
    """
    Initialize and set up the Crowd object.

    This fixture creates a `Crowd` instance, initializes agents, and packs them with forces.

    Returns
    -------
    Crowd
        An initialized `Crowd` object.
    """
    crowd_instance = Crowd()
    crowd_instance.create_agents()
    crowd_instance.pack_agents_with_forces()
    return crowd_instance


@pytest.fixture(name="output_zip_path_fixture")
def output_zip_path_fixture(crowd_fixture: Crowd) -> Path:
    """
    Save crowd data to a zip file and return the path.

    Parameters
    ----------
    crowd_fixture : Crowd
        The `Crowd` object containing simulation data.

    Returns
    -------
    Path
        The path to the saved zip file.
    """
    output_file_path = Path.cwd().parent.parent / "data" / "tutorial_configuration_files" / "crowd_ANSURII.zip"
    fun_zip.save_crowd_data_to_zip(crowd_fixture, output_file_path)
    return output_file_path


@pytest.fixture(name="original_data_dicts_fixture")
def original_data_dicts_fixture(
    crowd_fixture: Crowd,
) -> dict[str, StaticCrowdDataType | MaterialsDataType | DynamicCrowdDataType | GeometryDataType | InteractionsDataType]:
    """
    Retrieve original data dictionaries from the Crowd object.

    This fixture collects static, materials, dynamic, and geometry parameters from the `Crowd` object.

    Parameters
    ----------
    crowd_fixture : Crowd
        The `Crowd` object containing simulation data.

    Returns
    -------
    dict[str, StaticCrowdDataType | MaterialsDataType | DynamicCrowdDataType | GeometryDataType | InteractionsDataType]
        A dictionary containing original simulation data categorized by type.
        Keys include "static", "materials", "dynamic", "geometry" and "interactions".
    """
    return {
        "static": fun_dict.get_static_params(crowd_fixture),
        "materials": fun_dict.get_materials_params(),
        "dynamic": fun_dict.get_dynamic_params(crowd_fixture),
        "geometry": fun_dict.get_geometry_params(crowd_fixture),
    }


@pytest.fixture(name="loaded_xml_data_fixture")
def loaded_xml_data_fixture(output_zip_path_fixture: Path) -> dict[str, Optional[bytes]]:
    """
    Extract XML content from the zip file.

    This fixture reads XML files from the zip archive and categorizes them based on their content type.

    Parameters
    ----------
    output_zip_path_fixture : Path
        The path to the zip file containing XML data.

    Returns
    -------
    dict[str, Optional[bytes]]
        A dictionary containing XML content categorized by type.
        Keys include "static", "materials", "dynamic", and "geometry".
        Values are the raw XML content as bytes or None if not found.
    """
    xml_data: dict[str, Optional[bytes]] = {
        "static": None,
        "materials": None,
        "dynamic": None,
        "geometry": None,
    }

    with zipfile.ZipFile(output_zip_path_fixture, "r") as zip_file:
        # List all files in the ZIP archive
        file_names = zip_file.namelist()

        # Filter only XML files
        xml_files = [file for file in file_names if file.endswith(".xml")]

        for xml_file in xml_files:
            with zip_file.open(xml_file, "r") as file:
                xml_content = file.read()

                # Assign each XML file to its respective variable based on naming conventions.
                if "agents" in xml_file.lower():
                    xml_data["static"] = xml_content
                elif "materials" in xml_file.lower():
                    xml_data["materials"] = xml_content
                elif "dynamics" in xml_file.lower():
                    xml_data["dynamic"] = xml_content
                elif "geometry" in xml_file.lower():
                    xml_data["geometry"] = xml_content

    return xml_data


@pytest.mark.parametrize(
    "key, parse_function",
    [
        ("static", fun_xml.static_xml_to_dict),
        ("materials", fun_xml.materials_xml_to_dict),
        ("dynamic", fun_xml.dynamic_xml_to_dict),
        ("geometry", fun_xml.geometry_xml_to_dict),
    ],
)
def test_crowd_data_integrity(
    key: str,
    parse_function: Callable[
        [Optional[bytes]],
        dict[str, StaticCrowdDataType | MaterialsDataType | DynamicCrowdDataType | GeometryDataType],
    ],
    original_data_dicts_fixture: dict[str, StaticCrowdDataType | MaterialsDataType | DynamicCrowdDataType | GeometryDataType],
    loaded_xml_data_fixture: dict[str, Optional[bytes]],
) -> None:
    """
    Test that the parsed XML data matches the original data dictionaries.

    Parameters
    ----------
    key : str
        The key representing a specific type of data (e.g., static, materials).
    parse_function :  Callable[[Optional[bytes]], dict[str, StaticCrowdDataType | MaterialsDataType |
                                                            DynamicCrowdDataType | GeometryDataType]]
        The function used to parse the XML data into a dictionary.
    original_data_dicts_fixture : dict[str, StaticCrowdDataType | MaterialsDataType | DynamicCrowdDataType |
                                            GeometryDataType ]
        The original data dictionaries categorized by type.
    loaded_xml_data_fixture : dict[str, Optional[bytes]]
        The XML data loaded from the zip file categorized by type.
    """
    assert loaded_xml_data_fixture[key] is not None, f"{key} XML data is missing!"

    parsed_data = parse_function(loaded_xml_data_fixture[key])
    print(f"Parsed {key} data: {parsed_data}")
    print(f"Original {key} data: {original_data_dicts_fixture[key]}")
    assert parsed_data == original_data_dicts_fixture[key], f"{key} data mismatch!"
    assert parsed_data == original_data_dicts_fixture[key], f"{key} data mismatch!"
