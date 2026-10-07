"""Shared pytest fixtures for the Commutation test suite.

The package lives under a src-layout; ``pythonpath = ["src"]`` in
``pyproject.toml`` makes ``import commutation`` work from the repo root
without an editable install.
"""
import pytest

from commutation import Operator, Scalar, CommutatorAlgebra


@pytest.fixture
def ops():
    """Four generic non-commuting operators a, b, c, d."""
    return (
        Operator("a"),
        Operator("b"),
        Operator("c"),
        Operator("d"),
    )


@pytest.fixture
def scalar():
    """A commuting scalar symbol."""
    return Scalar("K")


@pytest.fixture
def spin():
    """An SU(2) spin algebra:  [az, ap] = ap,  [az, am] = -am,  [ap, am] = 2 az.

    Returns ``(ca, az, ap, am)`` where ``ca`` is a configured CommutatorAlgebra.
    This is the canonical "well-known reduction" fixture.
    """
    az = Operator("az", "S^z")
    ap = Operator("ap", "S^+")
    am = Operator("am", "S^-")

    ca = CommutatorAlgebra()
    ca.set_commutator(az, ap)(ap)
    ca.set_commutator(az, am)(-1 * am)
    ca.set_commutator(ap, am)(2 * az)

    return ca, az, ap, am
