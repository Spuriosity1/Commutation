from .expression import Expression, Term, Operator
from fractions import Fraction

try:
    import IPython.display as ipdisp
except AttributeError:
    ipdisp=None

def show(x, max_len=200):
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
    else:
        raise TypeError("show may only be called on Expression, Operator, Term, Fraction or int")

    try:
        ipdisp.display(ipdisp.Latex('$'+s+'$'))
    except AttributeError:
        raise AttributeError("LaTeX rendering is only possible in a jupyter notebook.")