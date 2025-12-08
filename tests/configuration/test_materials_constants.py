"""
Unit tests for materials constants calculations.

Tests cover:
    - k_from_EG function with identical materials
    - k_from_EG function with different materials
    - G_from_E_nu function with basic and edge cases
"""

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

import pytest

from configuration.utils.functions import G_from_E_nu, k_from_EG


def test_G_from_E_nu_basic() -> None:
    """Verify that the function returns expected shear moduli for simple combinations of Young's modulus and Poisson's ratio."""
    assert G_from_E_nu(100.0, 0.0) == pytest.approx(50.0)
    assert G_from_E_nu(100.0, 0.5) == pytest.approx(100.0 / 3.0)


@pytest.mark.parametrize(
    "E, nu",
    [
        (210e9, 0.30),
        (70e9, 0.25),
        (1e6, 0.49),
    ],
)
def test_G_from_E_nu_formula(E: float, nu: float) -> None:
    r"""
    Test G_from_E_nu against its defining formula :math:`G = E / (2 (1 + \\nu))`.

    Parameters
    ----------
    E : float
        Young's modulus used as input to the function.
    nu : float
        Poisson's ratio used as input to the function.
    """
    expected = E / (2.0 * (1.0 + nu))
    assert G_from_E_nu(E, nu) == pytest.approx(expected)


def test_k_from_EG_identical_materials_matches_analytic() -> None:
    r"""
    Test k_from_EG for identical materials.

    For identical materials, the expressions simplify to
    :math:`k^{\\perp}=\frac{2G^2}{4G-E}` and :math:`k^{\\parallel}=\frac{4G^2}{6G-E}`.
    """
    E = 210e9
    nu = 0.3
    G = G_from_E_nu(E, nu)

    k_perp, k_par = k_from_EG(E, G, E, G)
    expected_k_perp = 2.0 * G**2 / (4.0 * G - E)
    expected_k_par = 4.0 * G**2 / (6.0 * G - E)

    assert k_perp == pytest.approx(expected_k_perp)
    assert k_par == pytest.approx(expected_k_par)


def test_k_from_EG_symmetric_in_materials() -> None:
    """Test that k_from_EG is symmetric with respect to material ordering."""
    E1, G1 = 210e9, 80e9
    E2, G2 = 70e9, 26e9

    k_perp_12, k_par_12 = k_from_EG(E1, G1, E2, G2)
    k_perp_21, k_par_21 = k_from_EG(E2, G2, E1, G1)

    assert k_perp_12 == pytest.approx(k_perp_21)
    assert k_par_12 == pytest.approx(k_par_21)


def test_k_from_EG_raises_on_zero_shear_modulus() -> None:
    """Test that k_from_EG fails when a shear modulus is zero."""
    E1, G1 = 1.0, 0.0
    E2, G2 = 1.0, 1.0
    with pytest.raises(ZeroDivisionError):
        k_from_EG(E1, G1, E2, G2)
