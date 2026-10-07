"""Tests for CommutatorAlgebra: relation storage and operator reordering.

These cover the TODO's "some well known commutator reductions" item using the
SU(2) spin algebra  [az, ap] = ap,  [az, am] = -am,  [ap, am] = 2 az.
"""
import warnings

import pytest

from commutation import (
    Operator,
    Scalar,
    Expression,
    CommutatorAlgebra,
    CommutatorUnknownException,
)


# --------------------------------------------------------------------------
# relation storage
# --------------------------------------------------------------------------
def test_set_commutator_stores_antisymmetric_partner(spin):
    ca, az, ap, am = spin
    assert ca.relations["ap"]["am"] == 2 * az
    assert ca.relations["am"]["ap"] == -2 * az


def test_get_commutator_scalar_is_zero(spin):
    ca, az, ap, am = spin
    K = Scalar("K")
    assert ca.get_commutator(K, az) == 0
    assert ca.get_commutator(az, K) == 0


def test_get_commutator_unknown_warns_and_assumes_commute(spin):
    ca, az, ap, am = spin
    unknown = Operator("unknown")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = ca.get_commutator(unknown, az)
    assert result == 0
    assert any(issubclass(x.category, UserWarning) for x in w)


def test_strict_mode_raises_for_unknown():
    az, ap = Operator("az"), Operator("ap")
    ca = CommutatorAlgebra(strict=True)
    ca.set_commutator(az, ap)(ap)
    am = Operator("am")  # never registered
    with pytest.raises(CommutatorUnknownException):
        ca.move_right(Expression(az * ap * am), az)


# --------------------------------------------------------------------------
# elementary reductions
# --------------------------------------------------------------------------
def test_move_right_single_swap(spin):
    # ap*az -> az*ap + [ap, az] = az*ap - ap
    ca, az, ap, am = spin
    e = Expression(ap * az)
    ca.move_right(e, ap)
    e.collect()
    assert e == az * ap - ap


def test_move_right_noop_when_already_rightmost(spin):
    # az is already at the right end; nothing to move past.
    ca, az, ap, am = spin
    e = Expression(ap * az)
    ca.move_right(e, az)
    e.collect()
    assert e == ap * az


def test_move_right_readme_example(spin):
    ca, az, ap, am = spin
    e = Expression(az * ap * az * az * am)
    ca.move_right(e, az)
    e.collect()
    assert e == ap * am * az * az * az - 2 * ap * am * az * az + ap * am * az


def test_scalars_commute_through(spin):
    ca, az, ap, am = spin
    KA = Scalar("KA")
    e = Expression(az * ap * am * KA * am)
    ca.move_right(e, az)
    e.collect()
    assert e == ap * am * KA * am * az - ap * am * KA * am


def test_unknown_operator_during_move_warns(spin):
    ca, az, ap, am = spin
    c = Operator("c")  # not in the database
    e = Expression(az * ap * am * c * am)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ca.move_right(e, az)
    e.collect()
    assert any(issubclass(x.category, UserWarning) for x in w)
    assert e == ap * am * c * am * az - ap * am * c * am


# --------------------------------------------------------------------------
# move_left
# --------------------------------------------------------------------------
def test_move_left_single_swap(spin):
    # ap*az -> az*ap + [ap, az] = az*ap - ap
    ca, az, ap, am = spin
    e = Expression(ap * az)
    ca.move_left(e, az)
    e.collect()
    assert e == az * ap - ap


def test_move_left_readme_example(spin):
    ca, az, ap, am = spin
    e = Expression(az * ap * az * az * am)
    ca.move_left(e, am)
    e.collect()
    expected = (
        am * az * ap * az * az
        - 2 * am * az * ap * az
        + 2 * az * az * az * az
        - am * ap * az * az
        + am * az * ap
        - 4 * az * az * az
        + 2 * am * ap * az
        + 2 * az * az
        - am * ap
    )
    assert e == expected
