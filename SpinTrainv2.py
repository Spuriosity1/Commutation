from fractions import Fraction
from warnings import warn
from IPython.display import display, Latex

import copy

    

        
class Algebra(object):
    def __init__(self, ring_type, monoid_element, x0):
        self.ring_type=ring_type
        self.monoid_element=monoid_element
        self.terms = self.gen_termlist(x0)
        
            
    def gen_termlist(self, x0):
        x0 = copy.deepcopy(x0)
        t = []
        if x0 is None:
            return []
        if type(x0) is type(self):
            t += x0.terms
        elif type(x0) is self.monoid_element:
            t.append([self.ring_type(1), [x0]])
        elif type(x0) in (self.ring_type, int, Fraction):
            if x0 != 0:
                t.append([self.ring_type(x0), []])
        else:
            raise TypeError('Cast not defined for type '+str(type(x0)))
        return t
    
    def collect(self):
        # reorder nicely
        agg = {}
        for term in self.terms:
#             h = str(t[1])
            h = '*'.join([str(m) for m in term[1]])
            if h not in agg:
                agg[h] = copy.deepcopy(term)
            else:
                agg[h][0] += term[0]
                
        self.terms = [t for t in agg.values() if t != 0]
        
    def sort(self):
        raise NotImplementedError
    
    def __len__(self):
        return len(self.terms)
        
    def __iadd__(self, other):
        # cast up to the current status
        try:
            other = self.__class__(other)
            self.terms += other.terms
            return self
        except TypeError:
            return NotImplemented
    
    def __isub__(self, other):
        self += other*-1
        return self
    
    def __mul__(self, other):
        try:
            other = self.__class__(other)
            result = self.__class__()
            for s1, t1 in self.terms:
                for s2, t2 in other.terms:
                    result.terms.append( [s1*s2, t1 + t2])
            return result
        except TypeError:
            return NotImplemented
    
    def __eq__(self, other):
        diff = self - other
        diff.collect()
        return len(diff.terms) == 1 and diff.terms[0][0] == 0
    
    def __add__(self, other):
        rval = copy.deepcopy(self)
        rval += other
        return rval
        
    def __sub__(self, other):
        rval = copy.deepcopy(self)
        rval -= other
        return rval

    
    # for dealing with int * obj
    def __rmul__(self, other):
        if type(other) in (Fraction, int):
            return self * other
        else:
            return NotImplemented

    
    
class ScalarExpression(Algebra):
    def __init__(self, x0=None):
        super().__init__(ring_type=Fraction, monoid_element=Scalar, x0=x0)
        
    def __str__(self):
        if len(self.terms) > 1:
            s='('
        else:
            s = ''
        for num, t  in self.terms:
            if num<0:
                if num == -1:
                    s += ' -'
                elif num != 1:
                    s += str(num)
            else:
                s += ' +'
                if num != 1:
                    s += str(num)
            for l in t:
                s += ' ' + str(l)
                
        if len(self.terms) > 1:
            s += ')'
                
        return s
    
    def as_latex(self):
        if len(self.terms) > 1:
            s = r'\left('
        else:
            s = ''
        for num, t  in self.terms:
            num = Fraction(num)
            if num<0:
                s += '  -'
            else:
                s += '  +'
            if abs(num) != 1:
                if num.denominator == 1:
                    s += str(abs(num))
                else:
                    s += r'\frac{%d}{%d}' % (abs(num.numerator), num.denominator)

            for l in t:
                s += l.as_latex + ' '
                
        if len(self.terms) > 1:
            s += r'\right)'
                
        return s
    
    
    def collect(self):
        # order each term before collecting, makes everything smoother
        for n, t in self.terms:
            t.sort()
        super().collect()
    
    def sort(self, strategy='first'):
        # order each term
        for n, t in self.terms:
            t.sort()
        #order the elements
        
        sorters = {
            'first': lambda tup: '+'.join([str(t) for t in tup[1] ]),
            'last': lambda tup: '+'.join([str(t) for t in reversed(tup[1]) ]),
            'multiplier': lambda tup : str(t[0])
        }
        
        self.terms.sort(key=sorters[strategy])
    
    def show(self):
        display(Latex('$'+self.as_latex()+'$'))

# special values: terms = [] -> 0
#terms = [ [1,[]] ] -> 1
        
class Expression(Algebra):
    def __init__(self, *termsum):
        super().__init__(ring_type=ScalarExpression, monoid_element=Term, x0=None)
        for termproduct in termsum:
            if type(termproduct) is not list:
                if type(termproduct) is Expression:
                    self.terms += copy.deepcopy(termproduct.terms)
                    continue
                else:
                    termproduct = [termproduct]
            self.terms.append([ScalarExpression(1),[]])
            for t in termproduct:
                if type(t) in [ScalarExpression, Scalar, int, Fraction]:
                    self.terms[-1][0] *= t
                elif type(t) is Term:
                    self.terms[-1][1].append(t)
                else:
                    raise TypeError('Unexpected type when parsing initialiser list')
                
        
       
    def __rmul__(self, other):
        retval = copy.deepcopy(self)
        if type(other) in (Scalar, ScalarExpression, int, Fraction):
            for s, t in retval.terms:
                s *= ScalarExpression(other)
            return retval
        else:
            return NotImplemented
        
    def collect(self):
        super().collect()
        n=0
        for i, t in enumerate(self.terms):
            t[0].collect()
            if t[0] == 0:
                del self.terms[i-n]
                n+= 1
    
    # override parent method
    def gen_termlist(self, x0):
        if type(x0) is Scalar:
            if x0 != 0:
                return [[ScalarExpression(x0), []]]
            else:
                return []
        else:
            return super().gen_termlist(x0)
    
    def __str__(self):
        s = ''
        
        for i, (r, m) in enumerate(self.terms):
            if i != 0:
                s += '  '
                if len(r)>1:
                    s += '+'
                    
            s += str(r)
            if (r == 1 or r == -1) and len(m) == 0:
                s += '1'
                
            # print the monoid part
            if len(m) > 0 and not (r==1 or r== -1):
                s += '•'
            for term in m:
                s += str(term) + ' '

                
        return s
    
    def as_latex(self):
        s = ''
        
        for i, (r, m) in enumerate(self.terms):
            if i != 0:
                s += '  '
                if len(r)>1:
                    s += '+'
            s += r.as_latex()
            for term in m:
                s += term.as_latex + ' '
                
        return s
    
    def operators(self):
        ops = set()
        for t in self.terms:
            for o in t[1]:
                ops.add(o.name)
                
        return ops
        
    def show(self):
        display(Latex('$'+self.as_latex()+'$'))
        

# if this works it will be a miracle
class Term(object):
    def __init__(self, name, as_latex=None):
        assert type(name) is str
        if as_latex is None:
            as_latex = name
        assert type(as_latex) is str
        
        self.as_latex = as_latex
        self.name = name
        self.isscalar=False
        
    def __str__(self):
        return self.name
    
    def show(self):
        display(Latex('$'+self.as_latex+'$'))
    
    def __eq__(self, other):
        if type(other) is type(self):
            return (self.name,self.as_latex) == (other.name,other.as_latex)
        else:
            return False

    def __lt__(self, other):
        return (self.name,self.as_latex) < (other.name,other.as_latex)
    
    def get_retcopy(self, other):
        # picks the correct type
        if type(other) in [Term, Expression, Scalar, ScalarExpression, int, Fraction]:
            x = Expression(self)
        else:
            raise TypeError
        return x
        
    def __add__(self, other):
        try:
            x = self.get_retcopy(other)
            x += other
            return x
        except TypeError:
            return NotImplemented
    
    def __sub__(self, other):
        try:
            x = self.get_retcopy(other)
            x -= other
            return x
        except TypeError:
            return NotImplemented
    
    def __mul__(self, other):
        try:
            x = self.get_retcopy(other)
            x *= other
            return x
        except TypeError:
            return NotImplemented
    
    def __rmul__(self, other):
        if type(other) in (Fraction, int):
            return self * other
        elif type(other) in (ScalarExpression , Scalar):
            x = Expression(self)
            x *= Expression(other)
            return x
        else:
            return NotImplemented
        
        
class Scalar(Term):
    def __init__(self, name, as_latex=None):
        super().__init__(name, as_latex)
        self.isscalar=True
        
    def __str__(self):
        return super().__str__()
        
    # overwrite this
    def get_retcopy(self, other):
        # picks the correct type
        if type(other) in [Scalar, ScalarExpression, int, Fraction]:
            x = ScalarExpression(self)
        elif type(other) in [Term, Expression]:
            x = Expression(self)
        else:
            raise TypeError('No know multplication rule for these operators')
        return x
    
class CommutatorAlgebra(object):
    def __init__(self):
        self.relations = {}
        
    def add_operator(self, t):
        assert isinstance(t, Term)
        s = str(t)
        
        if s not in self.relations:
            col = {}
            for k in self.relations:
                self.relations[k][s] = [0, None]
                col[k] = [0, None]
            col[s] = [0, t*2] # everything commutes with itself and anticommutes to twice itself
            self.relations[s] = col 
    
    def set_relation(self, l_term, r_term, anticommute=False):
        assert isinstance(l_term, Term)
        assert isinstance(r_term, Term)
        l = l_term.name
        r = r_term.name
        
        if l not in self.relations:
            self.add_operator(l_term)
        if r not in self.relations:
            self.add_operator(r_term)
        
        ac = int(anticommute)
        def setter(rhs):
            rel = Expression(rhs) if rhs is not None else None
            if rel is not None:
                if l == r and ac==0:
                    s = 'Setting [%s, %s] to something other than default (0)... are you sure?' % (l,r)
                    warn(s)
                self.relations[l][r][ac] = rel
                self.relations[r][l][ac] = rel*-1
            else:
                # Ensure that there is at least one good relation to work with!
                if self.relations[l][r][ac-1] is not None:
                    raise UserError('Attempt to set both + and - commutators to None. At least one must be specified.')
                else:
                    self.relations[l][r][ac] = None
                    self.relations[r][l][ac] = None
                        
        return setter
    
    def get_relation(self, l, r, anticommute=False):
        return self.relations[l.name][r.name][int(anticommute)]
    
    def set_commutator(self,l,r):
        return self.set_relation(l,r, False)
    
    def set_anticommutator(self,l,r):
        return self.set_relation(l,r, True)
    
    def get_commutator(self,l,r):
        return self.get_relation(l,r, False)
    
    def get_anticommutator(self,l,r):
        return self.get_relation(l,r, True)
    
    
    def move_right(self, expr, term, default_to_commutator=True):
        assert isinstance(term, Term)
        
        # Strategy: Go through each term in self.terms
        # Within each term's operator list, iteratively keep moving it up in index using the elementary operation
        #  AB -> BA + [A, B]
        # repeat until done
        
        # Bug (?) : Only bubbles the first instance of the target to the right.
        # Happens rarely enough that we can just call move_right multiple times if we need to.

        if term .name not in expr.operators():
            return expr

        if term.name not in self.relations:
            s = 'Symbol "'+str(term)+'" is not in the commutator database, assuming it commutes...'
            warn(s)
        
        extra_terms = Expression()
        for s, tlist in expr.terms:
            # s is a ScalarExpression, t is [Term, Term, ... ]
            # both are mutable (?)
            for i in range(len(tlist) - 1):
                if tlist[i] != term:
                    continue
                front = tlist[:i]
                back = tlist[i+2:]
                c = self.get_commutator(tlist[i], tlist[i+1])
                print('[',tlist[i],',',tlist[i+1],'] -> ',c)
                
                if len(front) == 0:
                    front = 1
                if len(back) ==0:
                    back=1
                extra_terms += Expression(front) * c * Expression(back)*s
                print(extra_terms)
#                 if default_to_commutator:
#                     c = self.get_commutator(tlist[i], tlist[i+1])
#                     if c is not None:
#                         extra_terms += Expression(front) * c * Expression(back)*s
#                     else:
#                         # only anticommutators work!
#                         c = self.get_anticommutator(tlist[i], tlist[i+1])
#                         extra_terms += Expression(front) * c * Expression(back)*s
#                         s *= -1
#                 else:
#                     c = self.get_anticommutator(tlist[i], tlist[i+1])
#                     if c is not None:
#                         extra_terms += Expression(front) * c * Expression(back)*s
#                         s *= -1
#                     else:
#                         # only commutators work!
#                         c = self.get_commutator(tlist[i], tlist[i+1])
#                         extra_terms += Expression(front) * c * Expression(back)*s
                        
                tlist[i], tlist[i+1] = tlist[i+1], tlist[i]
            print(Expression(tlist),s)
            
            extra_terms += Expression(tlist)*s
                

        expr.terms=extra_terms.terms
                
                

        
    