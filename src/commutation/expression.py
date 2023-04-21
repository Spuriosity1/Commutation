from fractions import Fraction

# import copy as cp

from .operator import Operator
from .term import Term
            
        
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
        