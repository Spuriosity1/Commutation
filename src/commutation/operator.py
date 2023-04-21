from fractions import Fraction
from warnings import warn
# import copy as cp

from .term import Term
from .expression import Expression

# try:
#     import IPython.display as ipdisp
# except ImportError:
#     ipdisp=None
    


class Operator(object):
    """Represents (non-commutative) symbols. 
    Terms are built from lists of Operators.
    
    """
    def __init__(self, name, latex_string=None, scalar=False):
        """Operator constructor
        name         -> display name, result of str(Operator), 
                        used for keys in CommutatorAlgebra
        latex_string -> allows fancier formatting for as_latex() methods in
                        enclosing classes, defaults to name if not provided.
        is_scalar    -> Flags whether CommutatorAlgebra should treat this as a scalar
        """
        self.is_scalar = scalar
        if type(name) is not str:
            raise TypeError('Names must be str')
        if latex_string is None:
            latex_string = name
        elif type(latex_string) is not str:
            raise TypeError('Latex strings must be str')
        self.name = name
        self.latex_string = latex_string
    
    def __mul__(self, other):
        if isinstance(other, (int, Fraction, Operator)):
            return Term(self, other)
        else:
            return NotImplemented
    
    def __rmul__(self, other):
        if type(other) in (int, Fraction):
            return Term(other, self)
        return NotImplemented
    
    def __add__(self, other):
        return Expression(self,other)
    
    def __sub__(self, other):
        return self + (other*-1)
    
    def __str__(self):
        return self.name
    
    def as_latex(self):
        return self.latex_string
    
    def __eq__(self, other):
        if isinstance(other, (Operator, Term, Expression)):
            return self + other*-1 == 0
        return False
    
