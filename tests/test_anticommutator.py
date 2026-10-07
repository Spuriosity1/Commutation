"""Tests for AntiCommutatorAlgebra.

Anticommutator support is newer than the commutator path (see TODO.md), so
these focus on the basics plus two documented rough edges.
"""
import pytest

from commutation import (
    Operator,
    Expression,
    AntiCommutatorAlgebra,
    AntiCommutatorUnknownException,
)


def _algebra():
    """Two fermion-like modes with {f1, f2} = 0."""
    f1, f2 = Operator("f1"), Operator("f2")
    ac = AntiCommutatorAlgebra()
    ac.set_anticommutator(f1, f2)(0)
    return ac, f1, f2


def test_set_anticommutator_is_symmetric():
    ac, f1, f2 = _algebra()
    assert ac.relations["f1"]["f2"] == ac.relations["f2"]["f1"]


def test_diagonal_defaults_to_twice_the_operator():
    ac, f1, f2 = _algebra()
    assert ac.relations["f1"]["f1"] == 2 * f1


def test_move_right_flips_sign_on_swap():
    # f1*f2 -> -f2*f1 + {f1, f2} = -f2*f1   (since {f1, f2} = 0)
    ac, f1, f2 = _algebra()
    e = Expression(f1 * f2)
    ac.move_right(e, f1)
    e.collect()
    assert e == -1 * (f2 * f1)


def test_move_left_unknown_raises_friendly_exception():
    ac, f1, f2 = _algebra()
    g = Operator("g")  # unregistered
    with pytest.raises(AntiCommutatorUnknownException):
        ac.move_left(Expression(g * f1), f1)


def test_move_right_unknown_raises_friendly_exception():
    ac, f1, f2 = _algebra()
    g = Operator("g")  # unregistered
    with pytest.raises(AntiCommutatorUnknownException):
        ac.move_right(Expression(f1 * g), f1)
