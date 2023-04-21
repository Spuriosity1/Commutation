from .expression import Operator, Term, Expression
from warnings import warn

class CommutatorAlgebra(object):
    def __init__(self, strict=False):
        self.relations = {}
        self.strict=strict
        
    def add_operator(self, op):
        assert isinstance(op, Operator)
        s = str(op)
        
        if s not in self.relations:
            col = {}
            for k in self.relations:
                if self.strict:
                    self.relations[k][s] = [None, None]
                    col[k] = [None, None]
                else:
                    self.relations[k][s] = [0, None]
                    col[k] = [0, None]
            col[s] = [0, op*2] # everything commutes with itself and anticommutes to twice itself
            self.relations[s] = col 
    
    def set_relation(self, l_op, r_op, anticommute=False):
        assert isinstance(l_op, Operator)
        assert isinstance(r_op, Operator)
        l = l_op.name
        r = r_op.name
        
        if l not in self.relations:
            self.add_operator(l_op)
        if r not in self.relations:
            self.add_operator(r_op)
        
        ac = int(anticommute)
        def setter(rhs):
            rel = Expression(rhs) if rhs is not None else None
            if rel is not None:
                if l == r and ac==0:
                    s = 'Setting [%s, %s] to something other than default (0) ... are you sure?' % (l,r)
                    warn(s)
                self.relations[l][r][ac] = rel
                self.relations[r][l][ac] = rel*-1
            else:
                # Ensure that there is at least one good relation to work with!
                if self.relations[l][r][ac-1] is not None:
                    raise RuntimeError('Attempt to set both + and - commutators to None. At least one must be specified.')
                else:
                    self.relations[l][r][ac] = None
                    self.relations[r][l][ac] = None
                        
        return setter
    
    def get_commutator(self, l: Operator, r :Operator):
        assert isinstance(l, Operator)
        assert isinstance(r, Operator)
        if l.is_scalar or r.is_scalar:
            return 0
        elif l.name not in self.relations:
            s = 'Non-scalar operator "'+str(l)+'" is not in the commutator database, assuming it commutes...'
            if self.strict:
                raise RuntimeError(s)
            else:
                warn(s)
            return 0
        elif r.name not in self.relations:
            s = 'Non-scalar operator "'+str(r)+'" is not in the commutator database, assuming it commutes...'
            if self.strict:
                raise RuntimeError(s)
            else:
                warn(s)
            return 0
        else:
            return self.relations[l.name][r.name][0]
        
    def get_anticommutator(self, l, r):
        assert isinstance(l, Operator)
        assert isinstance(r, Operator)
        if l.is_scalar or r.is_scalar:
            return None
        elif not (l.name in self.relations and r.name in self.relations):
            return None
        else:
            return self.relations[l.name][r.name][1]
        
    
    def set_commutator(self,l,r):
        return self.set_relation(l,r, False)
    
    def set_anticommutator(self,l,r):
        return self.set_relation(l,r, True)
    

    
    def move_right(self, expr, A, default_to_commutator=True):
        assert isinstance(A, Operator)
        
        # Strategy: Go through each term in self.terms
        # Within each term's operator list, iteratively keep moving it up in index using the elementary operation
        #  AB -> BA + [A, B]
        # repeat until done
#         expr = Expression(expr)

        if A.name not in expr.operators:
            return expr
        
        extra_terms = Expression()
        for term in expr.terms:
            indices = reversed(term.findall(A))
            
            s = term.multiplier
            
            for I in indices:
                for i in range(I,len(term.ops) - 1):
                    assert term.ops[i] == A
                    front = Term(*term.ops[:i])
                    back = Term(*term.ops[i+2:])

#                     c = self.get_commutator(term.ops[i], term.ops[i+1])
#                     extra_terms += front * c * back
                
                    if default_to_commutator:
                        c = self.get_commutator(term.ops[i], term.ops[i+1])
                        if c is not None:
                            extra_terms += front * c * back * s
                        else:
                            raise NotImplementedError
                            # only anticommutators work!
                            c = self.get_anticommutator(term.ops[i], term.ops[i+1])
                            extra_terms += Expression(front) * c * Expression(back)*s
                            s *= -1
                    else:
                        raise NotImplementedError
                        c = self.get_anticommutator(term.ops[i], term.ops[i+1])
                        if c is not None:
                            extra_terms += Expression(front) * c * Expression(back)*s
                            s *= -1
                        else:
                            # only commutators work!
                            c = self.get_commutator(term.ops[i], term.ops[i+1])
                            extra_terms += Expression(front) * c * Expression(back)*s

                    term.ops[i], term.ops[i+1] = term.ops[i+1], term.ops[i]
               
        self.move_right(extra_terms, A, default_to_commutator) 
        expr.terms+=extra_terms.terms
        expr.collect()
        
        
        
    def move_left(self, expr, A, default_to_commutator=True):
        assert isinstance(A, Operator)
        
        # Strategy: Go through each term in self.terms
        # Within each term's operator list, iteratively keep moving it up in index using the elementary operation
        #  AB -> BA + [A, B]
        # repeat until done
#         expr = Expression(expr)

        if A.name not in expr.operators:
            return expr
        
        extra_terms = Expression()
        for term in expr.terms:
            indices = term.findall(A)
            
            s = term.multiplier
            
            for I in indices:
                for i in range(I, 0, -1):
                    assert term.ops[i] == A
                    front = Term(*term.ops[:i-1])
                    back = Term(*term.ops[i+1:])

                
                    if default_to_commutator:
                        c = self.get_commutator(term.ops[i-1], term.ops[i])
                        if c is not None:
                            extra_terms += front * c * back * s
                        else:
                            raise NotImplementedError
                            # only anticommutators work!
                            c = self.get_anticommutator(term.ops[i-1], term.ops[i])
                            extra_terms += Expression(front) * c * Expression(back)*s
                            s *= -1
                    else:
                        raise NotImplementedError
                        c = self.get_anticommutator(term.ops[i-1], term.ops[i])
                        if c is not None:
                            extra_terms += Expression(front) * c * Expression(back)*s
                            s *= -1
                        else:
                            # only commutators work!
                            c = self.get_commutator(term.ops[i-1], term.ops[i])
                            extra_terms += Expression(front) * c * Expression(back)*s

                    term.ops[i-1], term.ops[i] = term.ops[i], term.ops[i-1]
               
        self.move_left(extra_terms, A, default_to_commutator) 
        expr.terms+=extra_terms.terms
        expr.collect()
        
        
    def order_like(self, expr, target, default_to_commutator=True):
        assert isinstance(target, Term)
        for op in target.ops:
            self.move_tight(expr, op)
        