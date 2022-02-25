from fractions import Fraction
from warnings import warn
from IPython.display import display, Latex


# typ.call structure:
# Term([4, 'Sz_a', 'Sz_b'])
# noncommuttive (except for ints!)
class Term(object):
    def __init__(self, variables):
        self.multiplier = Fraction(1,1) # rational numbers!
        self.ops = []
        if isinstance(variables, Term):
            self.multiplier = variables.multiplier
            self.ops = variables.ops
        elif type(variables) is list:
            for t in variables:
                if type(t) is int:
                    self.multiplier *= t
                elif '/' in t:
                    self.multiplier *= Fraction(t)
                elif type(t) is str:
                    self.ops.append(t)
        elif type(variables) is str:
            if variables == '':
                self.multiplier=0
            self.ops.append(variables)
        
    def from_str(self, s):
        # cursed parser code, a problem for another day!
        raise NotImplementedException
        
    def __str__(self):
        if self.multiplier > 0:
            s = '+'+str(self.multiplier)
        else:
            s = str(self.multiplier)
        for op in self.ops:
            s += ' '+op
        return s
        
    def __neg__(self):
        t = Term(self)
        t.multiplier = -t.multiplier
        return t
    
#     def __imul__(self, other):
#         if type(other) in [int, Fraction, str]:
#             self.multiplier *= Fraction(other)
#         else:
#             raise TypeError("Multiplication is only defined for scalars")
            
    def __mul__(self, other):
        copy = Term(self)
        if type(other) in [int, Fraction, str]:
            copy.multiplier *= Fraction(other)
            return copy
        elif isinstance(other, Term):
            copy.multiplier *= other.multiplier
            copy.ops = copy.ops + other.ops
            return copy
        elif isinstance(other, Expression):
            return other.__rmul__(self)
        else:
            raise TypeError("Multiplication is only defined for scalars and Terms")
        
#     def __rmul__(self, other):
#         copy = Term(self)
#         if type(other) in [int, Fraction, str]:
#             copy.multiplier *= Fraction(other)
#             return copy
#         else:
#             raise TypeError("Multiplication is only defined for scalars")
    
    # finds all instances of subterm 'term' in 
    def findall(self, glob):
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
        
    
    @property
    def sign(self):
        return self.multiplier[0]*self.multiplier[1]
    
    def copy(self):
        return Term(self)

        
        
class Expression(object):
    def __init__(self, *t):
        self.terms = []
        
        # copy constructor
        if len(t) == 1 and isinstance(t[0], Expression):
            for myTerm in t[0].terms:
                self.terms.append(myTerm.copy())
        else:
            for term in t:
                if term != 0:
                    if not isinstance(term, Term):
                        term = Term(term)
                    self.terms.append(term)
            
    def __str__(self):
        s = ''
        for term in self.terms:
            s += '  ' + str(term)
        return s
    
    @property
    def order(self):
        maxlen = 0
        for t in self.terms:
            l = len(t.ops)
            maxlen = maxlen if l < maxlen else l
            
        return maxlen
                
    @property
    def operators(self):
        s = set({})
        for term in self.terms:
            for op in term.ops:
                s.add(op)
        return s
    
    def copy(self):
        l = []
        for t in self.terms:
            l.append(t)
        return Expression(*l)

    def __neg__(self):
        l = []
        for t in self.terms:
            l.append(-t)
        return Expression(*l)
    
    def __imul__(self, other):
        if type(other) in [int, Fraction, str]:
            for t in self.terms:
                 t *= Fraction(other)
        else:
            raise TypeError("Involutive multiplication is only defined for scalars")
    
    def __add__(self, other):
        copy = Expression()
        if isinstance(other, Expression):
            copy.terms = self.terms + other.terms
        elif isinstance(other, Term):
            if other.multiplier != 0 and len(other.ops)>0:
                copy.terms.append(other)
        else:
            raise TypeError
        return copy
    
    def __iadd__(self, other):
        if isinstance(other, Expression):
            self.terms += other.terms
        elif isinstance(other, Term):
            if other.multiplier != 0:
                self.terms.append(other)
        else:
            raise TypeError
        return self
    
    def __radd__(self, other):
        copy = Expression()
        copy.terms = other.terms + self.terms
        return copy
    
    def __mul__(self, other):
        if type(other) in [int, Fraction, str] or isinstance(other, Term):
            copy = Expression()
            copy.terms = self.terms.copy()
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
            raise TypeError("Multiplication is only defined for scalars, Terms and Expressions")

    def __rmul__(self, other):
        if type(other) in [int, Fraction, str] or isinstance(other, Term):
            copy = Expression()
            copy.terms = self.terms.copy()
            # right-multiplying by Term
            for i, t in enumerate(copy.terms):
                copy.terms[i] =  other * t
            return copy
        else:
            raise TypeError("Multiplication is only defined for scalars, Terms and Expressions")
            
    def __eq__(self, other):
        diff = self + -Expression(other)
        diff.collect()
        return diff.terms == []
        
    def from_str(self, s):
        # cursed parser code, a problem for another day!
        raise NotImplementedException
        
        
    def show(self):
        display(Latex('$'+str(self)+'$'))
        
            
    def collect(self):
        agg = {}
        
        for t in self.terms:
            h = str(t.ops)
            if h not in agg:
                agg[h] = t.copy()
            else:
                agg[h].multiplier += t.multiplier
        self.terms = [t for t in agg.values() if t.multiplier != 0]
        
    def drop(self, termstr):
        toDrop = []
        for i, t in enumerate(self.terms):
            if termstr in t.ops:
                toDrop.append(i)
                
        for i in toDrop:
            del self.terms[i]
            
    def sort(self, rule='multiplier', reverse=False):
        # Sorts by commutative addition
        compfuncs = {
               'multiplier': lambda t : t.multiplier.numerator,
               'first': lambda t : t.ops[0] if len(t.ops)>0 else 0,
               'last': lambda t : t.ops[-1] if len(t.ops)>0 else 0
        }
        self.terms.sort(reverse=reverse, key=compfuncs[rule])
                
        
    def coefficient(self, term, side='left'):
        assert isinstance(term, Term)
        termstr = Expression()
        M = len(term.ops)
        if side=='right' or side=='r':
            for t in self.terms:
                if t.ops[:M] == term.ops:
                    termstr += Term( t.ops[M:] )*(t.multiplier/term.multiplier)
        elif side=='left' or side=='l':
            for t in self.terms:
                if t.ops[-M:] == term.ops:
                    termstr += Term( t.ops[:-M] )*(t.multiplier/term.multiplier)
            
        return termstr
           
        
    def substitute(self, glob, sub, I=0):
        glob = Term(glob)
        if isinstance(sub, Term):
            sub = Expression([sub])
        assert isinstance(sub, Expression)
        # we cannot do any fancy multiterm substitutions... yet!
        retval = Expression()
        for i, t in enumerate(self.terms):
            idx = t.findall(glob)
            N = len(glob.ops)
            pieces = []
    
            # Slice up the string
            oldj = -N
            for j in idx:
                pieces.append(t.ops[oldj+N:j])
                oldj = j
            last = t.ops[oldj+N:]
            
            x = Expression(1)
            for p in pieces:
                x = x*Expression(p)*sub
            retval += x*Expression(last)*(t.multiplier/glob.multiplier)
        return retval
                    
            
        
        
        
class CommutatorAlgebra(object):
    def __init__(self):
        self.commutators = {}
        

    def add_operator(self, name):
        if name not in self.commutators:
            col = {}
            for k in self.commutators:
                self.commutators[k][name] = 0
                col[k] = 0
            col[name] = 0
            self.commutators[name] = col # everything commutes with itself
        
    # defines [a, b] syntax
    def __setitem__(self, arg, value):
        assert len(arg) == 2
        assert type(arg) is tuple
        assert isinstance(value, Term) or isinstance(value, Expression)
        value = Expression(value)
        

        # these do nothing if the operator is already known
        self.add_operator(arg[0])
        self.add_operator(arg[1])
            
        
        if value == 0:
            self.commutators[arg[0]][arg[1]] = 0
            self.commutators[arg[1]][arg[0]] = 0
        else:
            self.commutators[arg[0]][arg[1]] = value.copy()
            self.commutators[arg[1]][arg[0]] = -value
        
        
    def __getitem__(self, arg):
        if arg[0] not in self.commutators or arg[1] not in self.commutators:
            return 0
        else:
            return self.commutators[arg[0]][arg[1]]
        
    @property
    def operators(self):
        return set(self.commutators.keys())
        
        
    # moves all occurrences of the operator A, occurring in 'expression', as far right as possible
    def move_right(self, expr, A, I=0):
            # Strategy: Go through each term in self.terms
            # Within each term's operator list, iteratively keep moving it up in index using the elementary operation
            #  AB -> BA + [A, B]
            # repeat until done

            if A not in expr.operators:
                return expr
            
            if A not in self.operators:
                s = 'Symbol "'+str(A)+'" is not in the commutator database, assuming scalar...'
                warn(s)

            new_terms = []
            for term in expr.terms:
                N = len(term.ops)
                # do not need to do anything if A is at the end
                for i in range(I, N-1):
                    if term.ops[i] == A:
                        # calculate the commutator
                        c = self[term.ops[i], term.ops[i+1]]
    #                     print(c)
                        if c != 0:
                            front = term.ops[:i]
                            back = term.ops[i+2:]
                            for commutedTerm in c.terms:
                                t2 = Term(front) * commutedTerm  * Term(back)
                                t2.multiplier = term.multiplier*commutedTerm.multiplier
                                new_terms.append(t2)

                        # swap the operators
                        term.ops[i], term.ops[i+1] = term.ops[i+1], term.ops[i]

            # append the newly cooked terms
            expr.terms += new_terms

            if I == expr.order-1:
                return expr
            else:
                return self.move_right(expr, A, I+1)

    def move_left(self, expr, A, I=None):
            # Strategy: Go through each term in self.terms
            # Within each term's operator list, iteratively keep moving it up in index using the elementary operation
            #  AB -> BA + [A, B]
            # repeat until done
            if I is None:
                I = expr.order

            if A not in expr.operators:
                return expr
            
            if A not in self.operators:
                s = 'Symbol "'+str(A)+'" is not in the commutator database, assuming scalar...'
                warn(s)

            new_terms = []
            for term in expr.terms:
                N = len(term.ops)
                # do not need to do anything if A is at the end
                for i in range(1, min(I,N)):
                    if term.ops[i] == A:
                        # calculate the commutator
                        c = self[term.ops[i-1], term.ops[i]]
    #                     print(c)
                        if c != 0:
                            front = term.ops[:i-1]
                            back = term.ops[i+1:]
                            for commutedTerm in c.terms:
                                t2 = Term(front) * commutedTerm  * Term(back)
                                t2.multiplier = term.multiplier*commutedTerm.multiplier
                                new_terms.append(t2)

                        # swap the operators
                        term.ops[i-1], term.ops[i] = term.ops[i], term.ops[i-1]

            # append the newly cooked terms
            expr.terms += new_terms

            if I <= 1:
                return expr
            else:
                return self.move_left(expr, A, I-1)    
    
