"""Tests for generic SymPy coefficients on Terms / Expressions.

Coefficients used to be ``fractions.Fraction``; they are now arbitrary
``sympy.Expr`` objects, so a term may be scaled by symbols, exact rationals or
algebraic numbers such as ``sympy.I``.
"""
from fractions import Fraction

import pytest
import sympy

from commutation import Operator, Term, Expression


# --------------------------------------------------------------------------
# coefficient coercion
# --------------------------------------------------------------------------
def test_int_and_fraction_promote_to_sympy():
    a = Operator("a")
    t = Term(Fraction(3, 4), a)
    assert isinstance(t.multiplier, sympy.Expr)
    assert t.multiplier == sympy.Rational(3, 4)


def test_symbol_coefficient_is_preserved():
    a = Operator("a")
    J = sympy.Symbol("J")
    t = Term(J, a)
    assert t.multiplier == J
    assert t.ops == [a]


def test_float_is_rejected():
    a = Operator("a")
    with pytest.raises(TypeError):
        Term(1.5, a)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Term(a) * 1.5  # type: ignore[operator]


def test_sympy_float_is_allowed_when_explicit():
    # a user explicitly opting into a sympy Float is their choice
    a = Operator("a")
    t = Term(sympy.Float(1.5), a)
    assert t.multiplier == sympy.Float(1.5)


# --------------------------------------------------------------------------
# arithmetic with symbolic coefficients
# --------------------------------------------------------------------------
def test_collect_gathers_symbolic_coefficients():
    a = Operator("a")
    J, k = sympy.symbols("J k")
    e = Term(J, a) + Term(k, a) + Term(a)
    e.collect()
    assert len(e.terms) == 1
    assert e.terms[0].multiplier == J + k + 1


def test_symbolic_terms_cancel():
    a = Operator("a")
    k = sympy.Symbol("k")
    e = Term(k, a) - Term(k, a)
    e.collect()
    assert e.terms == []


def test_equality_is_symbolic():
    a, b = Operator("a"), Operator("b")
    k = sympy.Symbol("k")
    assert Expression(Term(k, a), Term(k, b)) == k * (a + b)
    assert Expression(Term(2 * k, a)) == Term(k, a) + Term(k, a)


def test_imaginary_unit_squares_to_minus_one():
    # (i a)(i b) == - a b
    a, b = Operator("a"), Operator("b")
    lhs = Expression(Term(sympy.I, a)) * Expression(Term(sympy.I, b))
    lhs.collect()
    assert lhs == -(a * b)


def test_division_stays_exact_and_symbolic():
    a = Operator("a")
    J = sympy.Symbol("J")
    assert (Term(J, a) / 2).multiplier == J / 2
    assert (Term(4, a) / 2).multiplier == 2


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def test_latex_symbolic_coefficient():
    a = Operator("a")
    J = sympy.Symbol("J")
    assert Term(J, a).as_latex() == "+J a"
    assert Term(sympy.Rational(-1, 2) * J, a).as_latex() == r"- \frac{J}{2} a"


def test_repr_handles_symbolic_and_negative():
    a = Operator("a")
    k = sympy.Symbol("k")
    assert str(Term(k, a)) == "+k a"
    assert str(Term(-k, a)) == "-k a"


# --------------------------------------------------------------------------
# the commutator engine carries symbolic prefactors through
# --------------------------------------------------------------------------
def test_move_right_preserves_symbolic_prefactor(spin):
    ca, az, ap, am = spin
    J = sympy.Symbol("J")
    e = Expression(Term(J, ap, az))
    ca.move_right(e, ap)
    e.collect()
    # ap*az -> az*ap - ap, scaled by J
    assert e == J * (az * ap) - J * ap
