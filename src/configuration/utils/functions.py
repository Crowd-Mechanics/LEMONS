"""Contains utility functions for data processing and manipulation."""

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

import csv
import io
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.stats import truncnorm
from shapely.geometry import MultiPolygon, Polygon

import configuration.utils.constants as cst
from configuration.utils.typing_custom import Sex


@lru_cache(maxsize=4)
def load_pickle(file_path: str) -> Any:
    """
    Load data from a pickle file.

    Parameters
    ----------
    file_path : str
        A string object representing the path to the pickle file to be loaded.

    Returns
    -------
    Any
        The deserialized data loaded from the pickle file. The type of the returned object depends
        on what was serialized into the pickle file (e.g. list[float], NDArray[np.float64] etc.).

    Raises
    ------
    TypeError
        If `file_path` is not a `Path` object.
    FileNotFoundError
        If the specified file does not exist.
    """
    if not isinstance(file_path, str):
        raise TypeError("file_path must be a string.")
    if not Path(file_path).exists():
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    with open(file_path, "rb") as f:
        data = pickle.load(f)
    return data


def save_pickle(data: Any, file_path: Path) -> None:
    """
    Save data to a pickle file.

    Parameters
    ----------
    data : Any
        The data to be serialized and saved. This can be any Python object that is supported by the pickle module.
    file_path : Path
        A Path object representing the path where the pickle file will be saved.

    Raises
    ------
    TypeError
        If file_path is not a Path object.
    FileNotFoundError
        If the directory for file_path does not exist.
    """
    if not isinstance(file_path, Path):
        raise TypeError("file_path must be a Path object.")
    if not file_path.parent.exists():
        raise FileNotFoundError(f"The directory {file_path.parent} does not exist.")
    with open(file_path, "wb") as f:
        pickle.dump(data, f)


def load_csv(filename: Path) -> pd.DataFrame:
    """
    Load data from a CSV file into a pandas DataFrame.

    Parameters
    ----------
    filename : Path
        A Path object representing the path to the CSV file to be loaded.

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame containing the data from the CSV file.

    Raises
    ------
    TypeError
        If filename is not a Path object.
    FileNotFoundError
        If the specified file does not exist.
    ValueError
        If the file does not have a .csv extension.
    """
    if not isinstance(filename, Path):
        raise TypeError("filename must be a Path object.")
    if not filename.exists():
        raise FileNotFoundError(f"The file {filename} does not exist.")
    if not filename.suffix == ".csv":
        raise ValueError(f"The file {filename} is not a CSV file.")
    return pd.read_csv(filename)


def get_csv_buffer(data_dict: dict[str, list[float | None]]) -> str:
    """
    Generate CSV content from a dictionary for download (in memory).

    Parameters
    ----------
    data_dict : dict[str, list[float | None]]
        The dictionary containing the data to be saved. If a value is None, it will be written as an empty cell in the CSV.

    Returns
    -------
    str
        The CSV content as a string, ready to be used with Streamlit's download button.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    # Write the keys as the header row
    writer.writerow(data_dict.keys())

    # Find the maximum length of the value lists
    max_len = max(len(v) for v in data_dict.values())

    # Write each row of values
    for i in range(max_len):
        row = []
        for v in data_dict.values():
            if i < len(v):
                row.append("" if v[i] is None else v[i])
            else:
                row.append("")
        writer.writerow(row)

    return output.getvalue()


def wrap_angle(angle: float) -> float:
    """
    Wrap an angle to the range [-180, 180).

    Parameters
    ----------
    angle : float
        The angle in degrees to be wrapped. This can be any real number.

    Returns
    -------
    float
        The wrapped angle in the range [-180, 180).
    """
    return (angle + 180.0) % 360.0 - 180.0


def draw_from_trunc_normal(mean: float, std_dev: float, min_val: float, max_val: float) -> float:
    """
    Draw a sample from a truncated normal distribution.

    This function generates a random sample from a normal distribution that is truncated within the
    range [min_val, max_val]. The truncation ensures that the sample lies within the specified bounds.

    Parameters
    ----------
    mean : float
        The mean of the normal distribution.
    std_dev : float
        The standard deviation of the normal distribution.
    min_val : float
        The lower bound of the truncated normal distribution.
    max_val : float
        The upper bound of the truncated normal distribution.

    Returns
    -------
    float
        A sample drawn from the truncated normal distribution.

    Raises
    ------
    ValueError
        If std_dev is less than or equal to zero, or if min_val is greater than or equal to max_val.
    """
    if std_dev <= 0:
        raise ValueError("Standard deviation must be greater than zero.")

    if min_val >= max_val:
        raise ValueError("min_val must be less than max_val.")

    # Calculate standardized bounds for truncation
    a = (min_val - mean) / std_dev
    b = (max_val - mean) / std_dev

    # Draw a sample from the truncated normal distribution
    return float(truncnorm.rvs(a, b, loc=mean, scale=std_dev))


def draw_sex(p: float) -> Sex:
    """
    Randomly draw a sex (`male` or `female`) based on the input proportion of `male`.

    Parameters
    ----------
    p : float
        A proportion value in [0,1], representing the probability of selecting `male`.

    Returns
    -------
    Sex
        `male` if a randomly generated number is less than `p`; otherwise, `female`.

    Raises
    ------
    ValueError
        If the probability `p` is not in [0,1].
    """
    # Check if the probability is between 0 and 1
    if not 0 <= p <= 1:
        raise ValueError("Probability p must be between 0 and 1.")

    # Draw a random number and return the sex
    return np.random.choice(["male", "female"], p=[p, 1 - p])


def cross2d(Pn: NDArray[np.float64], Pn1: NDArray[np.float64]) -> float:
    """
    Compute the 2D cross product of two vectors defined as `Pn[0] * Pn1[1] - Pn[1] * Pn1[0]`.

    Parameters
    ----------
    Pn : NDArray[np.float64]
        A 1D NumPy array of shape (2,) representing the first 2D vector in the form [x, y].
    Pn1 : NDArray[np.float64]
        A 1D NumPy array of shape (2,) representing the second 2D vector in the form [x, y].

    Returns
    -------
    float
        The magnitude of the resulting perpendicular vector to the plane formed by the input vectors.
    """
    return float(Pn[0] * Pn1[1] - Pn[1] * Pn1[0])


def compute_moment_of_inertia(geometric_shape: Polygon | MultiPolygon, weight: float) -> float:
    """
    Compute the moment of inertia for a 2D Polygon or MultiPolygon.

    This function calculates the moment of inertia (I_z) for a 2D shape
    represented as a polygon based on its vertices and weight. The calculation
    is performed using the second moment of area formula, assuming the polygon
    is in the XY-plane. For more details on the second moment of area, refer to:
    https://en.wikipedia.org/wiki/Second_moment_of_area.

    Parameters
    ----------
    geometric_shape : Polygon | MultiPolygon
        The geometrical representation as a shapely Polygon or MultiPolygon object (cm).
    weight : float
        The agent weight (kg).

    Returns
    -------
    float
        The computed moment of inertia for the shape (kg·m²).

    Notes
    -----
    For the MultiPolygon case, it computes the moment of inertia for each polygon and sums them up, weighted by their respective areas.
    """

    def polygon_inertia(polygon: Polygon, poly_weight: float) -> float:
        """
        Compute the moment of inertia for a 2D Polygon.

        Parameters
        ----------
        polygon : Polygon
            The geometrical representation as a Polygon object (cm).
        poly_weight : float
            The agent weight (kg).

        Returns
        -------
        float
            The moment of inertia of the polygon (kg·m²).
        """
        vertices = np.array(polygon.exterior.coords)
        centroid = np.array(polygon.centroid.coords[0])
        vertices = vertices - centroid  # Shift to centroid
        N = len(vertices) - 1  # Last point repeats the first
        rho = poly_weight / polygon.area  # Density (mass per unit area)
        I_z = 0.0
        for n in range(N):
            Pn = np.array(vertices[n])
            Pn1 = np.array(vertices[(n + 1) % N])
            cross_product_magnitude = abs(cross2d(Pn, Pn1))
            dot_product_terms = np.dot(Pn, Pn) + np.dot(Pn, Pn1) + np.dot(Pn1, Pn1)
            I_z += cross_product_magnitude * dot_product_terms
        moment_of_inertia: float = rho * I_z / 12.0
        moment_of_inertia *= 1e-4  # convert to kg·m^2
        return moment_of_inertia

    if isinstance(geometric_shape, Polygon):
        return polygon_inertia(geometric_shape, weight)
    if isinstance(geometric_shape, MultiPolygon):
        total_area = geometric_shape.area
        moment = 0.0
        for poly in geometric_shape.geoms:
            poly_area = poly.area
            poly_weight = weight * (poly_area / total_area)
            moment += polygon_inertia(poly, poly_weight)
        return moment
    raise TypeError("Input must be a Shapely Polygon or MultiPolygon.")


def validate_material(material: str) -> None:
    """
    Validate if the given material is in MaterialNames.

    Parameters
    ----------
    material : str
        The material name to validate.
    """
    if material not in cst.MaterialNames.__members__:
        raise ValueError(f"Material '{material}' is not supported. Expected one of: {list(cst.MaterialNames.__members__.keys())}.")


def rotate_vectors(vector_dict: dict[str, tuple[float, float]], theta: float) -> dict[str, tuple[float, float]]:
    """
    Rotate 2D vectors in a dictionary by a given angle.

    Parameters
    ----------
    vector_dict : dict[str, tuple[float, float]]
        A dictionary where each key maps to a 2D vector represented as a tuple (x, y).
    theta : float
        The angle in degrees by which to rotate the vectors.

    Returns
    -------
    dict[str, tuple[float, float]]
        A dictionary with the same keys, where each vector has been rotated by the given angle.
    """
    theta_rad = np.radians(theta)  # Convert angle to radians

    rotated_dict = {}
    for key, (x, y) in vector_dict.items():
        # Apply rotation matrix
        x_rot = x * np.cos(theta_rad) - y * np.sin(theta_rad)
        y_rot = x * np.sin(theta_rad) + y * np.cos(theta_rad)
        rotated_dict[key] = (x_rot, y_rot)

    return rotated_dict


def compute_bideltoid_breadth_from_multipolygon(multi_polygon: MultiPolygon) -> float:
    """
    Compute the largest horizontal distance (bideltoid breadth) between points in a MultiPolygon object.

    Parameters
    ----------
    multi_polygon : MultiPolygon
        A MultiPolygon object.

    Returns
    -------
    float
        The largest horizontal distance (bideltoid breadth).

    Notes
    -----
    To accelerate that function, only pairs of points with almost the same y-coordinate are considered.
    Therefore it is assumed that the input is a MultiPolygon object coming from the body3D of a pedestrian that has not been rotated.
    """
    if not isinstance(multi_polygon, MultiPolygon):
        raise ValueError("Input must be a Shapely MultiPolygon object.")

    # Assuming multi_polygon is a Shapely MultiPolygon object
    center_of_mass = multi_polygon.centroid

    # Combine boundary coordinates from all polygons, subtracting centroid
    all_coords = np.array(
        [(coord[0] - center_of_mass.x, coord[1] - center_of_mass.y) for poly in multi_polygon.geoms for coord in poly.boundary.coords]
    )

    # Sort points by their y-coordinate
    sorted_coords = all_coords[np.argsort(all_coords[:, 1])]

    # Use a sliding window to find pairs of points with similar y-coordinates
    tolerance = 1e-1  # Adjust this value based on precision needs
    max_distance = 0.0
    i = 0
    while i < len(sorted_coords):
        j = i + 1
        while j < len(sorted_coords) and abs(sorted_coords[j, 1] - sorted_coords[i, 1]) <= tolerance:
            # Compute horizontal distance (x-difference)
            distance = abs(sorted_coords[j, 0] - sorted_coords[i, 0])
            max_distance = max(max_distance, distance)
            j += 1
        i += 1

    return max_distance


def compute_chest_depth_from_multipolygon(multi_polygon: MultiPolygon) -> float:
    """
    Compute the largest vertical distance (chest depth) in a MultiPolygon object.

    Parameters
    ----------
    multi_polygon : MultiPolygon
        A MultiPolygon object.

    Returns
    -------
    float
        The largest vertical distance (chest depth).

    Notes
    -----
    To accelerate that function, only pairs of points with almost the same x-coordinate are considered.
    Therefore it is assumed that the input is a MultiPolygon object coming from the body3D of a pedestrian that has not been rotated.
    """
    if not isinstance(multi_polygon, MultiPolygon):
        raise ValueError("Input must be a Shapely MultiPolygon object.")

    # Assuming multi_polygon is a Shapely MultiPolygon object
    center_of_mass = multi_polygon.centroid

    # Combine boundary coordinates from all polygons, subtracting centroid
    all_coords = np.array(
        [(coord[0] - center_of_mass.x, coord[1] - center_of_mass.y) for poly in multi_polygon.geoms for coord in poly.boundary.coords]
    )

    # Sort points by their x-coordinate
    sorted_coords = all_coords[np.argsort(all_coords[:, 0])]

    # Use a sliding window to find pairs of points with similar x-coordinates
    tolerance = 1e-1  # Adjust this value based on precision needs
    max_distance = 0.0
    i = 0
    while i < len(sorted_coords):
        j = i + 1
        while j < len(sorted_coords) and abs(sorted_coords[j, 0] - sorted_coords[i, 0]) <= tolerance:
            # Compute vertical distance (y-difference)
            distance = abs(sorted_coords[j, 1] - sorted_coords[i, 1])
            max_distance = max(max_distance, distance)
            j += 1
        i += 1

    return max_distance


def from_string_to_tuple(string: str) -> tuple[float, float]:
    """
    Convert a string representation of a tuple to an actual tuple of two floats.

    Parameters
    ----------
    string : str
        The string representation of the tuple, e.g., "1.0, 2.0" or "(1.0, 2.0)".

    Returns
    -------
    tuple[float, float]
        The converted tuple of floats, e.g., (1.0, 2.0).

    Raises
    ------
    ValueError
        If `string` is not in the expected format.
    """
    if not isinstance(string, str):
        raise ValueError("Input must be a string.")

    # Remove optional parentheses and strip whitespace
    s = string.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()

    parts = [x.strip() for x in s.split(",")]
    if len(parts) != 2:
        raise ValueError("`string` must contain exactly two numbers separated by a comma.")

    try:
        return float(parts[0]), float(parts[1])
    except ValueError as exc:
        raise ValueError("Both elements must be convertible to float.") from exc


def sigmoid(x: float, smoothing: float) -> float:
    """
    Compute the numerically stable sigmoid function.

    Parameters
    ----------
    x : float
        Input value.
    smoothing : float
        Smoothing parameter.

    Returns
    -------
    float
        The output of the sigmoid function.
    """
    if smoothing <= 0:
        raise ValueError("Smoothing parameter must be positive.")

    X = x / smoothing

    # Numerically stable sigmoid
    if X >= 0:
        z = np.exp(-X)
        return float(1.0 / (1.0 + z))
    z = np.exp(X)
    return float(z / (1.0 + z))


def rectangular_function(height: float, scale_xy: float, sex: Sex | str) -> float:
    """
    Compute the value of a door function evaluated in height, based on scale, and sex parameters.

    Parameters
    ----------
    height : float
        The variable of the function.
    scale_xy : float
        The scale parameter for the rectangular function.
    sex : Sex or str
        The sex of a pedestrian, either as a Sex enum or string ("male" or "female").

    Returns
    -------
    float
        The value of the rectangular function.

    Raises
    ------
    ValueError
        If an invalid sex is provided.
    """
    # Normalize sex input
    if isinstance(sex, str):
        sex = sex.lower()
        if sex == "male":
            sex_enum = cst.Sex.male.name
        elif sex == "female":
            sex_enum = cst.Sex.female.name
        else:
            raise ValueError(f"Invalid sex: {sex}")
    elif isinstance(sex, Sex):
        sex_enum = sex
    else:
        raise ValueError(f"Invalid sex type: {type(sex)}")

    if sex_enum == cst.Sex.female.name:
        neck_height = cst.NECK_HEIGHT_FEMALE
        knees_height = cst.KNEES_HEIGHT_FEMALE
    else:
        neck_height = cst.NECK_HEIGHT_MALE
        knees_height = cst.KNEES_HEIGHT_MALE

    return 1.0 + (scale_xy - 1.0) * sigmoid(neck_height - height, cst.EPSILON_SMOOTHING_NECK) * sigmoid(
        height - knees_height, cst.EPSILON_SMOOTHING_KNEES
    )


def direction_of_longest_side(polygon: Polygon) -> float:
    """
    Compute the direction (in degrees) of the longest side of a 4-vertex polygon.

    The direction is measured from the first vertex of the side to the second, relative to the positive x-axis.

    Parameters
    ----------
    polygon : Polygon
        A Polygon object.

    Returns
    -------
    float
        The direction of the longest side, in degrees [0-360).
    """
    coords = np.array(polygon.exterior.coords[:-1])  # Exclude the repeated last point
    assert coords.shape[0] == 4, "Polygon must have exactly 4 vertices."

    # Compute vectors for each side
    vectors = np.roll(coords, -1, axis=0) - coords  # shape (4, 2)
    lengths = np.linalg.norm(vectors, axis=1)
    angles_rad = np.arctan2(vectors[:, 1], vectors[:, 0])
    angles_deg = np.degrees(angles_rad)

    # Find the index of the longest side
    idx = np.argmax(lengths)
    return wrap_angle(angles_deg[idx])


def filter_dict_by_not_None_values(input_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Filter a dictionary to remove keys with None values.

    Parameters
    ----------
    input_dict : dict[str, Any]
        The input dictionary to be filtered.

    Returns
    -------
    dict[str, Any]
        A new dictionary containing only the key-value pairs where the value is not None.
    """
    return {k: v for k, v in input_dict.items() if v is not None and v != []}


def k_from_EG(E1: float, G1: float, E2: float, G2: float) -> tuple[float, float]:
    r"""
    Compute ``k_perp`` and ``k_par`` from ``E1``, ``G1``, ``E2``, ``G2``.

    The spring constants are given by:

    .. math::

       k^{\perp} = \left(\frac{4G_1 - E_1}{4G_1^2} + \frac{4G_2 - E_2}{4G_2^2}\right)^{-1}, \\
       k^{\parallel} = \left(\frac{6G_1 - E_1}{8G_1^2} + \frac{6G_2 - E_2}{8G_2^2}\right)^{-1}.

    Parameters
    ----------
    E1 : float
        Young's modulus of material 1 (N/m).
    G1 : float
        Shear modulus of material 1 (N/m).
    E2 : float
        Young's modulus of material 2 (N/m).
    G2 : float
        Shear modulus of material 2 (N/m).

    Returns
    -------
    k_perp : float
        Spring constant for the direction orthogonal to the surface contact (N/m).
    k_par : float
        Spring constant for the direction parallel to the surface contact (N/m).

    Notes
    -----
    The elastic moduli are assumed to be for 2D systems and thus have units of N/m.
    """
    inv_k_perp = (4 * G1 - E1) / (4 * G1**2) + (4 * G2 - E2) / (4 * G2**2)
    inv_k_par = (6 * G1 - E1) / (8 * G1**2) + (6 * G2 - E2) / (8 * G2**2)

    k_perp = 1.0 / inv_k_perp
    k_par = 1.0 / inv_k_par
    return k_perp, k_par


def EG_from_k(k_perp: float, k_par: float) -> tuple[float, float]:
    r"""
    Compute ``E`` and ``G`` from ``k_perp`` and ``k_par``, assuming both materials in contact are identical.

    The moduli are given by:

    .. math::

         G = \frac{k^{\parallel} k^{\perp}}{2 k^{\perp} - k^{\parallel}}, \\
         E = \frac{2 k^{\parallel} k^{\perp} (4 k^{\perp} - 3 k^{\parallel})}{(k^{\parallel} - 2 k^{\perp})^2}.

    Parameters
    ----------
    k_perp : float
        Spring constant for the direction orthogonal to the surface contact (N/m).
    k_par : float
        Spring constant for the direction parallel to the surface contact (N/m).

    Returns
    -------
    E : float
        Young's modulus (N/m).
    G : float
        Shear modulus (N/m).

    Notes
    -----
    The elastic moduli are assumed to be for 2D systems and thus have units of N/m.
    """
    G = k_par * k_perp / (2 * k_perp - k_par)
    E = 2 * k_par * k_perp * (4 * k_perp - 3 * k_par) / (k_par - 2 * k_perp) ** 2
    return E, G


def G_from_E_nu(E: float, nu: float) -> float:
    """
    Compute shear modulus G from Young's modulus E and Poisson's ratio nu.

    Parameters
    ----------
    E : float
        Young's modulus (N/m).
    nu : float
        Poisson's ratio (dimensionless).

    Returns
    -------
    float
        Shear modulus G (N/m).

    Notes
    -----
    The elastic moduli are assumed to be for 2D systems and thus have units of N/m.
    """
    return E / (2 * (1 + nu))
