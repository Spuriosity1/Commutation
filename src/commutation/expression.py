from fractions import Fraction
import copy as cp

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

        
        

            
        
class Expression(object):
    """Implements an Abelian group operation + on Term objects,
    allowing for representation of arbitrary polynomials.
    Expression.terms = [] has only Term elements, and should be read as x1 + x2 + ...
    This list needs to be deep-copied.
    """
    def __init__(self, *termlist):
        """
        Expression(x1,x2,x3,...)
        Should be read as x1 + x2 + ...
        xi can be Expression, Term, Operator, Fraction or int. All of these are summed
        """
        self.terms = []
        
        for term in termlist:
            if isinstance(term, Expression):
                # this ensures that we make new Term objets, but the 
                # underlying references to Operator are preserved
                for t in term.terms:
                    self.terms.append(Term(t))
            elif term != 0:
                self.terms.append(Term(term))
            
    def __str__(self):
        s = ''
        for term in self.terms:
            s += '  ' + str(term)
        return s
    
    @property
    def is_scalar(self):
        for t in self.terms:
            if not t.is_scalar:
                return False
        return True
    
    @property
    def order(self):
        maxlen = 0
        for t in self.terms:
            l = t.order
            maxlen = maxlen if l < maxlen else l
            
        return maxlen
                
    @property
    def operators(self):
        s = set({})
        for term in self.terms:
            for op in term.ops:
                s.add(op.name)
        return s

    def __neg__(self):
        copy = Expression(self)
        for t in copy.terms:
            t.multiplier *= -1
        return copy
    
    def __sub__(self, other):
        return self + other*-1
    
    def __add__(self, other):
        copy = Expression(self)
        if isinstance(other, Expression):
            for t in other.terms:
                copy.terms.append(Term(t))
        elif isinstance(other, Term):
            if other.multiplier != 0:
                copy.terms.append(Term(other))
        elif isinstance(other, (Operator, int, Fraction)):
            copy.terms.append(Term(other))
        else:
            return NotImplemented
        return copy

    
    def __radd__(self, other):
        copy = Expression(self)
        if isinstance(other, Operator) or type(other) in [int, Fraction]:
            copy.terms =[Term(other)] + copy.terms
            return copy
        else:
            return NotImplemented

    
    def __mul__(self, other):
        if isinstance(other, (Term, Operator, int, Fraction)):
            copy = Expression(self)
            # right-multiplying by Term
            for i, t in enumerate(copy.terms):
                copy.terms[i] = t * other
            return copy  
        elif isinstance(other, Expression):
            r = []
            for left in self.terms:
                for right in other.terms:
                    r.append(left * right)
            return Expression(*r)
            
        else:
            return NotImplemented

    def __rmul__(self, other):
        if type(other) in (int, Fraction):
            copy = Expression(self)
            # scalar multiplicaiton
            for i, t in enumerate(copy.terms):
                copy.terms[i] =  t* other
            return copy
        elif isinstance(other, (Term, Operator)):
            copy = Expression(self)
            # right-multiplying by Term
            for i, t in enumerate(copy.terms):
                copy.terms[i] =  other * t
            return copy
        else:
            return NotImplemented
        
            
    def __eq__(self, other):
        diff = self + -Expression(other)
        diff.collect()
        return diff.terms == []
    
#     def to_operator(self):
#         # Ensure that the expression is castable to Term
#         assert len(self.terms) == 1
#         # ensure that the Term only has one thing in it
#         assert len(self.terms[0].ops) == 1
#         if self.terms[0].multiplier != 1:
#             warn("Ignoring multiplier")
#         return self.terms[0].ops[0]

    def replaceall(self, *rule_args):
        """Usage: term.replaceall((target, replacement),(target, replacement)...)
        targets must be Terms, but replacemnts may be any expression_like
        """
        # make it mutable
        rules = []
        # promote to Term and Expression
        for glob, sub in rule_args:
            rules.append( (Term(glob), Expression(sub)) )
            
        result = Expression()
        for t in self.terms:
            expression_product = []
            i = 0
            old_i = 0
            while i < len(t):
                step = True
                
                for glob, sub in rules:
#                     print([str(o) for o in t.ops[i:i+len(glob)]], glob)
                    if t.ops[i:i+len(glob)] == glob.ops:
                        pre = Term(*t.ops[old_i:i])
                        expression_product.append(pre)
                        expression_product.append(sub)
                        i += len(glob)
                        old_i = i
                        step = False
                if step:
                    i += 1
            expression_product.append(Term(*t.ops[old_i:]))
                
            x = Term(t.multiplier)
            for fragment in expression_product:
                x = x * fragment
            result += x
            
        return result


        
    def from_str(self, s):
        # cursed parser code, a problem for another day!
        raise NotImplementedError
        
        
    def as_latex(self):
        s = ''
        for term in self.terms:
            s += term.as_latex() + ' '
        return s
        
        
    def move_scalars(self, side='left'):
        for t in self.terms:
            t.move_scalars(side='left')
        
    def factor(self, side='left',x = None):
        # usage: factor (ABC + ABD) ---> AB, C+D
        # Does NOT factor subunits! That's too hard!
        minorder = min([len(t.ops) for t in self.terms])
        
        if x is None:
            # search through and find the longest forestring
            if side in ['right','r']:
                back = Expression(self)
                front_arr = []
                for n in range(minorder):
                    a = self.terms[0].ops[n]
                    if all([t.ops[n] == a for t in self.terms]):
                        front_arr.append(a)
                        for t in back.terms:
                            del t.ops[0]
                    else:
                        break
                front = Term(*front_arr)
            
            elif side in ['left', 'l']:
                front = Expression(self)
                back_arr = []
                for n in range(minorder):
                    a = self.terms[0].ops[-n-1]
                    p = [t.ops[-n-1] == a for t in self.terms]
                    if all(p):
                        back_arr = [a] + back_arr
                        for t in front.terms:
                            del t.ops[-1]
                    else:
                        break
                back = Term(*back_arr)
            else:
                raise IndexError("Side must be one of 'l', 'r', 'left', 'right'")


        elif type(x) in [Term, Operator]:
            rem = self.coefficient(x, side)
            if len(rem.terms) == len(self.terms):
                if side in ['right','r']:
                    front = Term(x)
                    back = rem
                elif side in ['left', 'l']:
                    front = rem
                    back = Term(x)
            else:
                if side in ['right','r']:
                    front = Term()
                    back = Expression(self)
                elif side in ['left', 'l']:
                    front = Expression(self)
                    back = Term()
                
        assert front*back == self
        return front, back
            
        
            
    def collect(self):
        agg = {}
        
        for t in self.terms:
            h = '*'.join([str(o) for o in t.ops])
            if h not in agg:
                agg[h] = t.copy()
                assert type(t.multiplier) is Fraction
            else:
                agg[h].multiplier += t.multiplier
        self.terms = [t for t in agg.values() if t.multiplier != 0]
            
        
    def sort(self, strategy='first'):
        #order the elements        
        self.collect()
        sorters = {
            'first': lambda tup: ' '.join([str(o) for o in tup.ops ]),
            'last': lambda tup: ' '.join([str(o) for o in reversed(tup.ops) ]),
            'multiplier': lambda tup : tup.multiplier
        }
        
        self.terms.sort(key=sorters[strategy])
                
        
    def coefficient(self, term, side='left'):
        self.collect()
        if type(term) in [Operator, int, Fraction]:
            term = Term(term)
        elif not isinstance(term, Term):
            raise TypeError('Cannot factor type '+str(type(term)))
        termstr = Expression()
        M = len(term.ops)
        if side=='right' or side=='r':
            for t in self.terms:
                if t.ops[:M] == term.ops:
                    termstr += Term( *t.ops[M:] )*(t.multiplier/term.multiplier)
        elif side=='left' or side=='l':
            for t in self.terms:
                if t.ops[-M:] == term.ops:
                    termstr += Term( *t.ops[:-M] )*(t.multiplier/term.multiplier)
            
        return termstr
           

    def sub(self, glob, sub):
        '''an alias for substitute'''
        return self.substitute(glob,sub)
        
    def substitute(self, glob, sub):
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
            pieces = []
            # Slice up the list
            oldj = -N
            for j in idx:
                pieces.append(t.ops[oldj+N:j])
                oldj = j
            last = t.ops[oldj+N:]
            
            # product the pieces together
            x = Expression(1)
            for p in pieces:
                x = x*Term(*p)*sub
            retval += x*Term(*last)*(t.multiplier/glob.multiplier)
        return retval
        