from fractions import Fraction
import copy as cp
from .operator import Operator
from .expression import Expression

# try:
#     import IPython.display as ipdisp
# except ImportError:
#     ipdisp=None

    
class Term(object):
    """Terms should be read as (Fraction * Term1*Terms2*...).
        These implement a noncommutative monoid structure for Term.
        
        Term.multiplier -> a Fraction, which absorbs scalar multiples of Terms.
        Term.ops        -> a list of Operators, which are understood as producted together.
                            "1" is written as [].
                            These should only ever be shallow-copied: want to retain ability to tune Operator objects on the fly
        """
    
    def __init__(self, *variables):
        """Term constructor
            Usage: Term(x1, x2, x3, ...)
            xi can be Operator, Fraction or int. These are all producted together.
        """
        self.multiplier = Fraction(1,1) # rational numbers!
        self.ops = []
        
        for t in variables:
            if isinstance(t,Term):
                self.ops += t.ops
                self.multiplier *= t.multiplier
            elif isinstance(t, Operator):
                self.ops.append(t)
            elif type(t) in [int, Fraction]:
                self.multiplier *= t
            else:
                raise TypeError('cannot initialise Term from ' + str(type(t)))

    @property
    def is_scalar(self):
        for o in self.ops:
            if not o.is_scalar:
                return False
        return True
                
    def from_str(self, s):
        # cursed parser code, a problem for another day!
        raise NotImplementedError
        
        
    def factor_scalars(self):
        scalars = []
        ops = []
        for o in self.ops:
            if o.is_scalar:
                scalars.append(o)
            else:
                ops.append(o)
        return Term(*scalars)*self.multiplier, Term(*ops)

    def move_scalars(self, side='left'):
        scalars = []
        ops = []
        for o in self.ops:
            if o.is_scalar:
                scalars.append(o)
            else:
                ops.append(o)
                
        if side in ['l','left']:
            self.ops = scalars + ops
        elif side in ['r','right']:
            self.ops = ops + scalars
        else:
            raise IndexError("Side must be one of 'l', 'r', 'left', 'right'")
                
        
    def __len__(self):
        return len(self.ops)
        
    def __str__(self):
        if self.multiplier > 0:
            s = '+'+str(self.multiplier)
        else:
            s = str(self.multiplier)
        for op in self.ops:
            s += ' '+str(op)
        return s
    
    def as_latex(self):
        if self.multiplier.denominator == 1:
            s = '%+d' % self.multiplier.numerator
        else:
            s = '+' if self.multiplier >= 0 else '-'
            s += r'\frac{%d}{%d}' % (abs(self.multiplier.numerator), self.multiplier.denominator)
        
        for o in self.ops:
            s += ' ' + o.latex_string
        return s
        
    def __neg__(self):
        t = cp.copy(self)
        t.multiplier = -t.multiplier
        return t
    
    def __add__(self, other):
        retval = Expression()
        retval += self
        retval += other
        return retval
    
    def __radd__(self, other):
        retval = Expression()
        retval += other
        retval += self
        return retval
    
    def __sub__(self, other):
        return self + (other*-1)
            
    def __mul__(self, other):
        copy = cp.copy(self)
        if type(other) in (int, Fraction):
            copy.multiplier *= Fraction(other)
            return copy
        elif isinstance(other, Operator):
            copy.ops = copy.ops + [other]
            return copy
        elif isinstance(other, Term):
            copy.multiplier *= other.multiplier
            copy.ops = copy.ops + other.ops
            return copy
        else:
            return NotImplemented
        
    def __rmul__(self, other):
        copy = cp.copy(self)
        if type(other) in [int, Fraction]:
            copy.multiplier *= other
            return copy
        elif isinstance(other, Operator):
            copy.ops = [other] + copy.ops
            return copy
        else:
            return NotImplemented
    

    def findall(self, glob):
        """Finds all instances of subterm `glob` in the present operator product.
        This returns a list of indices [i1, i2, ...] such that
        self.ops[i1:i1+len(glob)] == glob.ops
        Collisions in are ignored - e.g.
        aaa.findall(aa) -> [0]
        aaaa.findall(aa) -> [0,2]
        """
        if not isinstance(glob, Term):
            glob = Term(glob)
        hits = []
        i = 0
        N = len(glob.ops)
        while (i < len(self.ops)-N+1):
            if self.ops[i:i+N]==glob.ops:
                hits.append(i)
                # skip duplicates when we have e.g. aaaaaa.find(aa)
                i += N-1
            i += 1
        return hits
        
#     def replaceall(self, *rules):
#         """Usage: term.replaceall((target, replacement),(target, replacement)...)
#         This method only works with Term for Term/Operator substitutions: 
#         """
#         i=0
#         while i < len(self.ops):
#             move_next = True
#             for glob, repl in rules:
#                 glob = Term(glob)
# #                 print([str(u) for u in self.ops[i:i+len(glob)]])
#                 if self.ops[i:i+len(glob)] == glob.ops:
#                     t = Term(repl)
#                     self.ops = self.ops[:i] + t.ops + self.ops[i+len(glob):]
#                     self.multiplier *= t.multiplier/glob.multiplier
#                     i += len(glob)-1
#                     move_next = False
#             if move_next:
#                 i += 1
                
                    
        
    
    @property
    def sign(self):
        return 1 if self.multiplier > 0 else -1
    
    @property
    def order(self):
        return len(self.ops)
    
    def copy(self):
        return Term(self)
    
    def __eq__(self, other):
        if not isinstance(other, Term):
            return False
        if self.multiplier != other.multiplier or len(self) != len(other):
            return False
        return all([ t == o for (t,o) in zip(self.ops, other.ops)])

        
        
