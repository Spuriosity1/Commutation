"""Tests for the Expression abelian-group / CAS operations."""
from fractions import Fraction

import pytest

from commutation import Operator, Term, Expression


def test_construction_drops_zeros():
    a = Operator("a")
    e = Expression(a, 0, Term(a))
    assert len(e.terms) == 2


def test_empty_expression():
    assert Expression().terms == []


def test_add_sub_neg():
    a, b = Operator("a"), Operator("b")
    assert (a + b) - b == a
    assert -(a + b) == Expression(-Term(a), -Term(b))


def test_mul_distributes():
    a, b, c = Operator("a"), Operator("b"), Operator("c")
    e = (a + b) * c
    assert e == a * c + b * c


def test_scalar_mul():
    a, b = Operator("a"), Operator("b")
    assert 2 * (a + b) == (2 * a) + (2 * b)


def test_collect_folds_like_terms():
    a = Operator("a")
    e = Expression(a) + Expression(a) - Expression(a)
    e.collect()
    assert len(e.terms) == 1
    assert e.terms[0].multiplier == 1


def test_collect_drops_zero_terms():
    a = Operator("a")
    e = a - a
    e.collect()
    assert e.terms == []


def test_sort_strategies():
    a, b, c = Operator("a"), Operator("b"), Operator("c")
    e = Expression(c) + a + b
    e.sort("first")
    assert [str(t.ops[0]) for t in e.terms] == ["a", "b", "c"]


def test_operators_property():
    a, b, c = Operator("a"), Operator("b"), Operator("c")
    assert (a * b + c).operators == {"a", "b", "c"}


def test_order_property():
    a, b, c = Operator("a"), Operator("b"), Operator("c")
    assert (a * b * c + a).order == 3


def test_is_scalar_property():
    import sympy
    a = Operator("a")
    K = sympy.Symbol("K")
    assert Expression(Term(K), Term(K)).is_scalar is True
    assert (a + K).is_scalar is False


def test_eq_is_algebraic():
    a, b = Operator("a"), Operator("b")
    assert (a + b) == (b + a)  # collect ignores term order for matching keys
    assert (a + a) == (2 * a)
    assert (a + b) != (a + a)


def test_substitute_readme_example():
    a, b, c, d = (Operator(x) for x in "abcd")
    x = a * b * b * b * a * c * a * a * c * a * b + 1
    y = x.substitute(a * b, c + d)
    expected = (
        c * b * b * a * c * a * a * c * c
        + c * b * b * a * c * a * a * c * d
        + d * b * b * a * c * a * a * c * c
        + d * b * b * a * c * a * a * c * d
        + 1
    )
    assert y == expected


def test_substitute_preserves_multiplier():
    a, b, c = Operator("a"), Operator("b"), Operator("c")
    assert Expression(3 * a * b).substitute(a * b, c) == 3 * c


def test_sub_is_alias_for_substitute():
    a, b, c = Operator("a"), Operator("b"), Operator("c")
    e = Expression(a * b)
    assert e.sub(a * b, c) == e.substitute(a * b, c)


def test_replaceall():
    a, b, c = Operator("a"), Operator("b"), Operator("c")
    assert Expression(a * b * a * b).replaceall((a * b, c)) == c * c


def test_factor_no_x_right():
    a, b, c, d = (Operator(x) for x in "abcd")
    xx = 7 * a * b * b + Fraction(4, 5) * a * c * b * b + a * d * b * b
    front, back = xx.factor("right")
    assert front * back == xx
    assert front == Term(a)


def test_factor_no_x_left():
    a, b, c, d = (Operator(x) for x in "abcd")
    xx = 7 * a * b * b + Fraction(4, 5) * a * c * b * b + a * d * b * b
    front, back = xx.factor()  # default side = left
    assert front * back == xx
    assert back == Term(b, b)


def test_factor_explicit_x():
    a, b, c = Operator("a"), Operator("b"), Operator("c")
    front, back = (a * b + a * c).factor("right", a)
    assert front == Term(a)
    assert back == b + c
    assert front * back == (a * b + a * c)


def test_coefficient():
    a, b, c = Operator("a"), Operator("b"), Operator("c")
    assert (a * b + a * c).coefficient(a, "right") == b + c


def test_as_latex_fraction():
    a = Operator("a")
    assert (Fraction(4, 5) * Term(a)).as_latex() == r"+\frac{4}{5} a"


def test_from_str_not_implemented():
    with pytest.raises(NotImplementedError):
        Expression().from_str("a + b")
