"""Tests for the Term monoid."""
from fractions import Fraction

import pytest

from commutation import Operator, Scalar, Term


def test_construction_products_operators_and_scalars():
    a, b = Operator("a"), Operator("b")
    t = Term(2, a, 3, b)
    assert t.multiplier == 6
    assert t.ops == [a, b]


def test_identity_term_is_empty():
    t = Term()
    assert t.multiplier == 1
    assert t.ops == []
    assert len(t) == 0


def test_nested_term_flattens():
    a, b = Operator("a"), Operator("b")
    t = Term(Term(2, a), Term(3, b))
    assert t.multiplier == 6
    assert t.ops == [a, b]


def test_bad_type_raises():
    with pytest.raises(TypeError):
        Term(1.5)  # float is not allowed, only int / Fraction / Operator


def test_is_scalar():
    a = Operator("a")
    assert Term(Scalar("K"), Scalar("J")).is_scalar is True
    assert Term(a).is_scalar is False


def test_order_sign_len():
    a, b = Operator("a"), Operator("b")
    t = -2 * Term(a, b)
    assert t.order == 2
    assert len(t) == 2
    assert t.sign == -1
    assert (2 * Term(a)).sign == 1


def test_mul_rmul_truediv():
    a, b = Operator("a"), Operator("b")
    assert (Term(a) * b).ops == [a, b]
    assert (b * Term(a)).ops == [b, a]
    assert (Term(a) * 4).multiplier == 4
    assert (Term(4, a) / 2).multiplier == Fraction(2, 1)


def test_neg_copies():
    a = Operator("a")
    t = Term(a)
    n = -t
    assert n.multiplier == -1
    assert t.multiplier == 1  # original untouched


def test_factor_scalars():
    a = Operator("a")
    K = Scalar("K")
    scal, ops = Term(3, K, a).factor_scalars()
    assert scal == Term(3, K)
    assert ops == Term(a)


def test_move_scalars_left_and_right():
    a, b = Operator("a"), Operator("b")
    K = Scalar("K")

    left = Term(a, K, b)
    left.move_scalars("left")
    assert [str(o) for o in left.ops] == ["K", "a", "b"]

    right = Term(a, K, b)
    right.move_scalars("right")
    assert [str(o) for o in right.ops] == ["a", "b", "K"]


def test_move_scalars_bad_side():
    a = Operator("a")
    with pytest.raises(IndexError):
        Term(a).move_scalars("sideways")


def test_findall_non_overlapping():
    a, b = Operator("a"), Operator("b")
    assert Term(a, a, a).findall(Term(a, a)) == [0]
    assert Term(a, a, a, a).findall(Term(a, a)) == [0, 2]
    assert Term(a, b, a, b).findall(Term(a, b)) == [0, 2]
    assert Term(a, b).findall(Term(b, a)) == []


def test_eq():
    a, b = Operator("a"), Operator("b")
    assert Term(2, a, b) == Term(2, a, b)
    assert Term(2, a, b) != Term(3, a, b)
    assert Term(a, b) != Term(b, a)
    assert Term(a) != "a"


def test_copy_is_independent():
    a = Operator("a")
    t = Term(a)
    c = t.copy()
    c.multiplier = 5
    assert t.multiplier == 1
