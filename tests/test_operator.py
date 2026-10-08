"""Tests for the Operator primitives."""
import pytest

from commutation import Operator, Term, Expression


def test_name_must_be_str():
    with pytest.raises(TypeError):
        Operator(123)  # type: ignore[arg-type]


def test_latex_must_be_str():
    with pytest.raises(TypeError):
        Operator("a", 123)  # type: ignore[arg-type]


def test_latex_defaults_to_name():
    a = Operator("a")
    assert a.as_latex() == "a"


def test_latex_string_used_when_given():
    a = Operator("a", "S^z_a")
    assert a.as_latex() == "S^z_a"


def test_str_and_repr_are_name():
    a = Operator("a")
    assert str(a) == "a"
    assert repr(a) == "a"


def test_mul_by_int_gives_term():
    a = Operator("a")
    t = a * 3
    assert isinstance(t, Term)
    assert t.multiplier == 3
    assert t.ops == [a]


def test_rmul_by_int_gives_term():
    a = Operator("a")
    t = 3 * a
    assert isinstance(t, Term)
    assert t.multiplier == 3


def test_mul_by_operator_gives_term():
    a, b = Operator("a"), Operator("b")
    t = a * b
    assert isinstance(t, Term)
    assert t.ops == [a, b]


def test_add_gives_expression():
    a, b = Operator("a"), Operator("b")
    e = a + b
    assert isinstance(e, Expression)
    assert len(e.terms) == 2


def test_neg_gives_term_with_negative_multiplier():
    a = Operator("a")
    t = -a
    assert isinstance(t, Term)
    assert t.multiplier == -1


def test_eq_is_algebraic():
    a, b = Operator("a"), Operator("b")
    assert a == a
    assert a != b
    assert a == Term(a)
    assert (a - a) == 0


def test_subtraction_of_operators():
    a, b = Operator("a"), Operator("b")
    e = a - b
    assert e == Expression(Term(a), -Term(b))
