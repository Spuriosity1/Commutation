from __future__ import annotations

from fractions import Fraction

import sympy

from .expression import Expression, Term, Operator

try:
    import IPython.display as ipdisp
except ImportError:
    ipdisp = None


def show(x: Expression | Term | Operator | int | Fraction | sympy.Expr, max_len: int = 200) -> None:
    if isinstance(x, Expression):
        if len(x.terms) > max_len:
            raise RuntimeError('Expression too long (override with show(x, n), n is number of terms)')

    s = ''
    if isinstance(x, (Expression, Term, Operator)):
        s = x.as_latex()
    elif isinstance(x, int):
        s = str(x)
    elif isinstance(x, Fraction):
        s = '\\frac{%d}{%d}' % (x.numerator, x.denominator)
    elif isinstance(x, sympy.Expr):
        s = sympy.latex(x)
    else:
        raise TypeError("show may only be called on Expression, Operator, Term, Fraction, int or sympy.Expr")

    if ipdisp is None:
        raise AttributeError("LaTeX rendering is only possible in a jupyter notebook.")
    ipdisp.display(ipdisp.Latex('$' + s + '$'))
    
## Converts Expression, Term or Operator into Mathematica
# def as_mathematica(x):
