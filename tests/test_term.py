"""Tests for the Term monoid."""
from fractions import Fraction

import pytest

import sympy

from commutation import Operator, Term


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
        Term(1.5)  # type: ignore[arg-type]  # float is not allowed


def test_is_scalar():
    # a Term is "scalar" iff it carries no operators (a pure coefficient)
    a = Operator("a")
    assert Term(sympy.Symbol("K")).is_scalar is True
    assert Term(3).is_scalar is True
    assert Term(a).is_scalar is False
    assert Term(sympy.Symbol("K"), a).is_scalar is False


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
    c.multiplier = sympy.Integer(5)
    assert t.multiplier == 1
