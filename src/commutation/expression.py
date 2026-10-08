"""The algebraic data model: ``Operator``, ``Term`` and ``Expression``.

Coefficients (the ``Term.multiplier``) are generic SymPy expressions, so a term
may be scaled by anything SymPy understands — exact rationals, symbols such as
``sympy.Symbol('J')`` or algebraic numbers like ``sympy.I`` (with ``I**2 == -1``).
Python ``int`` and ``fractions.Fraction`` are accepted and promoted; ``float`` is
rejected to keep arithmetic exact.
"""
from __future__ import annotations

import copy as cp
from fractions import Fraction
from typing import TypeAlias, cast

import sympy

# Anything accepted as a scalar coefficient. ``sympy.Expr`` covers sympy's own
# numbers (Integer, Rational, Float) as well as symbols and compound
# expressions. The union is a runtime ``types.UnionType`` so it doubles as an
# ``isinstance`` target.
ScalarCoeff = int | Fraction | sympy.Expr

# the same set of types as a plain tuple, for ``isinstance`` checks
_SCALAR_TYPES = (int, Fraction, sympy.Expr)

# Operands that can be producted into a Term / summed into an Expression
# (string forward references — the classes are defined further down).
TermLike: TypeAlias = "Operator | Term | ScalarCoeff"
ExprLike: TypeAlias = "Operator | Term | Expression | ScalarCoeff"


def coerce_coeff(x: ScalarCoeff) -> sympy.Expr:
    """Promote a scalar coefficient to a ``sympy.Expr``, rejecting floats.

    ``int`` and ``fractions.Fraction`` become exact sympy numbers; an existing
    ``sympy.Expr`` is returned unchanged. Python ``float`` is refused so that no
    inexact arithmetic sneaks in — pass a ``Fraction`` or ``sympy.Rational``
    instead.
    """
    if isinstance(x, float):
        raise TypeError(
            "floats are not allowed; use Fraction or sympy.Rational for exact arithmetic"
        )
    if not isinstance(x, _SCALAR_TYPES):
        raise TypeError(f"cannot use {type(x)!r} as a scalar coefficient")
    return cast(sympy.Expr, sympy.sympify(x))


class Operator:
    """Represents (non-commutative) symbols.

    Terms are built from lists of Operators.
    """

    def __init__(self, name: str, latex_string: str | None = None):
        """Operator constructor

        name         -> display name, result of str(Operator),
                        used for keys in CommutatorAlgebra
        latex_string -> allows fancier formatting for as_latex() methods in
                        enclosing classes, defaults to name if not provided.
        """
        if not isinstance(name, str):
            raise TypeError('Names must be str')
        if latex_string is None:
            latex_string = name
        elif not isinstance(latex_string, str):
            raise TypeError('Latex strings must be str')
        self.name = name
        self.latex_string = latex_string

    def __mul__(self, other: TermLike) -> Term:
        if isinstance(other, (Operator, int, Fraction, sympy.Expr)):
            return Term(self, other)
        return NotImplemented

    def __rmul__(self, other: ScalarCoeff) -> Term:
        if isinstance(other, _SCALAR_TYPES):
            return Term(other, self)
        return NotImplemented

    def __add__(self, other: ExprLike) -> Expression:
        return Expression(self, other)

    def __radd__(self, other: ExprLike) -> Expression:
        return Expression(other, self)

    def __sub__(self, other: ExprLike) -> Expression:
        return self + (other * -1)

    def __rsub__(self, other: ExprLike) -> Expression:
        return other + (-1 * self)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def as_latex(self) -> str:
        return self.latex_string

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (Operator, Term, Expression)):
            return self + other * -1 == 0
        return False

    def __neg__(self) -> Term:
        t = Term(self)
        t.multiplier = -t.multiplier
        return t


class Term:
    """Terms should be read as (coefficient * Term1*Term2*...).

    These implement a noncommutative monoid structure for Term.

    Term.multiplier -> a ``sympy.Expr`` coefficient, which absorbs scalar
                        multiples of Terms (exact rationals, symbols, etc.).
    Term.ops        -> a list of Operators, which are understood as producted
                        together. "1" is written as [].
                        These should only ever be shallow-copied: want to retain
                        ability to tune Operator objects on the fly.
    """

    def __init__(self, *variables: TermLike):
        """Term constructor

        Usage: Term(x1, x2, x3, ...)
        xi can be an Operator, a Term, or a scalar coefficient (int, Fraction or
        sympy.Expr). These are all producted together.
        """
        self.multiplier: sympy.Expr = sympy.Integer(1)  # generic sympy coefficient
        self.ops: list[Operator] = []

        for t in variables:
            if isinstance(t, Term):
                self.ops += t.ops
                self.multiplier *= t.multiplier
            elif isinstance(t, Operator):
                self.ops.append(t)
            elif isinstance(t, _SCALAR_TYPES):
                self.multiplier *= coerce_coeff(t)
            else:
                raise TypeError('cannot initialise Term from ' + str(type(t)))

    @property
    def is_scalar(self) -> bool:
        """True when the term is a pure coefficient (no operators)."""
        return not self.ops

    def from_str(self, s: str):
        # cursed parser code, a problem for another day!
        raise NotImplementedError

    def __len__(self) -> int:
        return len(self.ops)

    def __repr__(self) -> str:
        # a leading '-' already carries the sign; otherwise show an explicit '+'
        coeff = str(self.multiplier)
        s = coeff if coeff.startswith('-') else '+' + coeff
        for op in self.ops:
            s += ' ' + str(op)
        return s

    def __str__(self) -> str:
        return self.__repr__()

    def as_latex(self) -> str:
        m = self.multiplier
        if m.is_number and m.is_rational:
            # exact integer / rational: keep the historical +N / +\frac{}{} form
            if m.is_integer:
                s = '%+d' % int(m)
            else:
                sign = '-' if m.is_negative else '+'
                s = sign + sympy.latex(abs(m))
        else:
            # general symbolic (or complex) coefficient
            latex = sympy.latex(m)
            s = latex if latex.startswith('-') else '+' + latex

        for o in self.ops:
            s += ' ' + o.latex_string
        return s

    def __neg__(self) -> Term:
        t = cp.copy(self)
        t.multiplier = -t.multiplier
        return t

    def __add__(self, other: ExprLike) -> Expression:
        retval = Expression()
        retval += self
        retval += other
        return retval

    def __radd__(self, other: ExprLike) -> Expression:
        retval = Expression()
        retval += other
        retval += self
        return retval

    def __sub__(self, other: ExprLike) -> Expression:
        return self + (other * -1)

    def __rsub__(self, other: ExprLike) -> Expression:
        return (other * -1) + self

    def __mul__(self, other: TermLike) -> Term:
        copy = cp.copy(self)
        if isinstance(other, _SCALAR_TYPES):
            copy.multiplier *= coerce_coeff(other)
            return copy
        elif isinstance(other, Term):
            copy.multiplier *= other.multiplier
            copy.ops = copy.ops + other.ops
            return copy
        elif isinstance(other, Operator):
            copy.ops = copy.ops + [other]
            return copy
        else:
            return NotImplemented

    def __truediv__(self, other: ScalarCoeff) -> Term:
        copy = cp.copy(self)
        if isinstance(other, _SCALAR_TYPES):
            copy.multiplier /= coerce_coeff(other)
            return copy
        else:
            return NotImplemented

    def __rmul__(self, other: ScalarCoeff | Operator) -> Term:
        copy = cp.copy(self)
        if isinstance(other, _SCALAR_TYPES):
            copy.multiplier *= coerce_coeff(other)
            return copy
        elif isinstance(other, Operator):
            copy.ops = [other] + copy.ops
            return copy
        else:
            return NotImplemented

    def findall(self, glob: Term | Operator) -> list[int]:
        """Finds all instances of subterm `glob` in the present operator product.

        This returns a list of indices [i1, i2, ...] such that
        self.ops[i1:i1+len(glob)] == glob.ops
        Collisions in are ignored - e.g.
        aaa.findall(aa) -> [0]
        aaaa.findall(aa) -> [0,2]
        """
        if not isinstance(glob, Term):
            glob = Term(glob)
        hits: list[int] = []
        i = 0
        N = len(glob.ops)
        while i < len(self.ops) - N + 1:
            if self.ops[i:i + N] == glob.ops:
                hits.append(i)
                # skip duplicates when we have e.g. aaaaaa.find(aa)
                i += N - 1
            i += 1
        return hits

    @property
    def sign(self) -> int:
        m = self.multiplier
        if m.is_number and m.is_negative:
            return -1
        return 1

    @property
    def order(self) -> int:
        return len(self.ops)

    def copy(self) -> Term:
        return Term(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Term):
            return False
        if self.multiplier != other.multiplier or len(self) != len(other):
            return False
        return all(t == o for (t, o) in zip(self.ops, other.ops))


class Expression:
    """Implements an Abelian group operation + on Term objects,
    allowing for representation of arbitrary polynomials.
    Expression.terms = [] has only Term elements, and should be read as x1 + x2 + ...
    This list needs to be deep-copied.
    """

    def __init__(self, *termlist: ExprLike):
        """
        Expression(x1,x2,x3,...)
        Should be read as x1 + x2 + ...
        xi can be an Expression, Term, Operator or scalar coefficient (int,
        Fraction or sympy.Expr). All of these are summed.
        """
        self.terms: list[Term] = []

        for term in termlist:
            if isinstance(term, Expression):
                # this ensures that we make new Term objects, but the
                # underlying references to Operator are preserved
                for t in term.terms:
                    self.terms.append(Term(t))
            elif term != 0:
                self.terms.append(Term(term))

    def __repr__(self) -> str:
        s = ''
        for term in self.terms:
            s += '  ' + str(term)
        return s

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def is_scalar(self) -> bool:
        return all(t.is_scalar for t in self.terms)

    @property
    def order(self) -> int:
        maxlen = 0
        for t in self.terms:
            l = t.order
            maxlen = maxlen if l < maxlen else l
        return maxlen

    @property
    def operators(self) -> set[str]:
        s: set[str] = set()
        for term in self.terms:
            for op in term.ops:
                s.add(op.name)
        return s

    def __neg__(self) -> Expression:
        copy = Expression(self)
        for t in copy.terms:
            t.multiplier *= -1
        return copy

    def __sub__(self, other: ExprLike) -> Expression:
        return self + other * -1

    def __add__(self, other: ExprLike) -> Expression:
        copy = Expression(self)
        if isinstance(other, Expression):
            for t in other.terms:
                copy.terms.append(Term(t))
        elif isinstance(other, Term):
            if other.multiplier != 0:
                copy.terms.append(Term(other))
        elif isinstance(other, (Operator, int, Fraction, sympy.Expr)):
            copy.terms.append(Term(other))
        else:
            return NotImplemented
        return copy

    def __radd__(self, other: ExprLike) -> Expression:
        copy = Expression(self)
        if isinstance(other, (Operator, int, Fraction, sympy.Expr)):
            copy.terms = [Term(other)] + copy.terms
            return copy
        else:
            return NotImplemented

    def __mul__(self, other: ExprLike) -> Expression:
        if isinstance(other, (Term, Operator, int, Fraction, sympy.Expr)):
            copy = Expression(self)
            # right-multiplying by Term
            for i, t in enumerate(copy.terms):
                copy.terms[i] = t * other
            return copy
        elif isinstance(other, Expression):
            r: list[Term] = []
            for left in self.terms:
                for right in other.terms:
                    r.append(left * right)
            return Expression(*r)
        else:
            return NotImplemented

    def __rmul__(self, other: ScalarCoeff | Term | Operator) -> Expression:
        if isinstance(other, _SCALAR_TYPES):
            copy = Expression(self)
            # scalar multiplication
            for i, t in enumerate(copy.terms):
                copy.terms[i] = t * other
            return copy
        elif isinstance(other, (Term, Operator)):
            copy = Expression(self)
            # left-multiplying by Term
            for i, t in enumerate(copy.terms):
                copy.terms[i] = other * t
            return copy
        else:
            return NotImplemented

    def __eq__(self, other: object) -> bool:
        diff = self + -Expression(cast(ExprLike, other))
        diff.collect()
        return diff.terms == []

    def replaceall(self, *rule_args: tuple[TermLike, ExprLike]) -> Expression:
        """Usage: term.replaceall((target, replacement),(target, replacement)...)
        targets must be Terms, but replacements may be any expression_like.
        Applies the rules in order specified.
        """
        # make it mutable
        rules: list[tuple[Term, Expression]] = []
        # promote to Term and Expression
        for glob, sub in rule_args:
            rules.append((Term(glob), Expression(sub)))

        result = Expression()
        for t in self.terms:
            expression_product: list[Term | Expression] = []
            i = 0
            old_i = 0
            while i < len(t):
                step = True

                for glob, sub in rules:
                    if t.ops[i:i + len(glob)] == glob.ops:
                        pre = Term(*t.ops[old_i:i])
                        expression_product.append(pre)
                        expression_product.append(sub)
                        i += len(glob)
                        old_i = i
                        step = False
                if step:
                    i += 1
            expression_product.append(Term(*t.ops[old_i:]))

            x: Term | Expression = Term(t.multiplier)
            for fragment in expression_product:
                x = x * fragment
            result += x

        return result

    def from_str(self, s: str):
        # cursed parser code, a problem for another day!
        raise NotImplementedError

    def as_latex(self) -> str:
        s = ''
        for term in self.terms:
            s += term.as_latex() + ' '
        return s

    def factor(self, side: str = 'left', x: Term | Operator | None = None) -> tuple[Expression | Term, Expression | Term]:
        # usage: factor (ABC + ABD) ---> AB, C+D
        # Does NOT factor subunits! That's too hard!
        minorder = min(len(t.ops) for t in self.terms)
        front: Expression | Term = Term()
        back: Expression | Term = Expression(self)

        if x is None:
            # search through and find the longest forestring
            if side in ('right', 'r'):
                back = Expression(self)
                front_arr: list[Operator] = []
                for n in range(minorder):
                    a = self.terms[0].ops[n]
                    if all(t.ops[n] == a for t in self.terms):
                        front_arr.append(a)
                        for t in back.terms:
                            del t.ops[0]
                    else:
                        break
                front = Term(*front_arr)

            elif side in ('left', 'l'):
                front = Expression(self)
                back_arr: list[Operator] = []
                for n in range(minorder):
                    a = self.terms[0].ops[-n - 1]
                    p = [t.ops[-n - 1] == a for t in self.terms]
                    if all(p):
                        back_arr = [a] + back_arr
                        for t in front.terms:
                            del t.ops[-1]
                    else:
                        break
                back = Term(*back_arr)
            else:
                raise ValueError(
                    "Side must be one of 'l', 'r', 'left', 'right'")

        elif isinstance(x, (Term, Operator)):
            rem = self.coefficient(x, side)
            if len(rem.terms) == len(self.terms):
                if side in ('right', 'r'):
                    front = Term(x)
                    back = rem
                elif side in ('left', 'l'):
                    front = rem
                    back = Term(x)
            else:
                if side in ('right', 'r'):
                    front = Term()
                    back = Expression(self)
                elif side in ('left', 'l'):
                    front = Expression(self)
                    back = Term()

        assert front * back == self
        return front, back

    def collect(self) -> None:
        agg: dict[str, Term] = {}

        for t in self.terms:
            h = '*'.join(o.name for o in t.ops)
            if h not in agg:
                agg[h] = t.copy()
                assert isinstance(t.multiplier, sympy.Expr)
            else:
                agg[h].multiplier += t.multiplier
        self.terms = [t for t in agg.values() if t.multiplier != 0]

    def sort(self, strategy: str = 'first') -> None:
        # order the elements
        self.collect()
        sorters = {
            'first': lambda tup: ' '.join(str(o) for o in tup.ops),
            'last': lambda tup: ' '.join(str(o) for o in reversed(tup.ops)),
            'multiplier': lambda tup: str(tup.multiplier),
        }

        self.terms.sort(key=sorters[strategy])

    def coefficient(self, term: Term | Operator | ScalarCoeff, side: str = 'left') -> Expression:
        self.collect()
        if isinstance(term, (Operator, int, Fraction, sympy.Expr)):
            term = Term(term)
        elif not isinstance(term, Term):
            raise TypeError('Cannot factor type ' + str(type(term)))
        termstr = Expression()
        M = len(term.ops)
        if side in ('right', 'r'):
            for t in self.terms:
                if t.ops[:M] == term.ops:
                    termstr += Term(*t.ops[M:]) * (t.multiplier / term.multiplier)
        elif side in ('left', 'l'):
            for t in self.terms:
                if t.ops[-M:] == term.ops:
                    termstr += Term(*t.ops[:-M]) * (t.multiplier / term.multiplier)

        return termstr

    def sub(self, glob: Term | Operator, sub: ExprLike) -> Expression:
        '''an alias for substitute'''
        return self.substitute(glob, sub)

    def substitute(self, glob: Term | Operator, sub: ExprLike) -> Expression:
        """Searches through each Term, runs Term.findall to
        find all non-overlapping occurrences of `glob`, and subs in Expression(sub)
        Returns a different Expression, no changes are made to self
        """
        # we cannot do any fancy multiterm substitutions... yet!
        if not isinstance(glob, Term):
            glob = Term(glob)

        sub = Expression(sub)

        retval = Expression()
        for i, t in enumerate(self.terms):
            idx = t.findall(glob)
            N = len(glob.ops)
            pieces: list[list[Operator]] = []
            # Slice up the list
            oldj = -N
            for j in idx:
                pieces.append(t.ops[oldj + N:j])
                oldj = j
            last = t.ops[oldj + N:]

            # product the pieces together
            x = Expression(1)
            for p in pieces:
                x = x * Term(*p) * sub
            retval += x * Term(*last) * (t.multiplier / glob.multiplier)
        return retval
