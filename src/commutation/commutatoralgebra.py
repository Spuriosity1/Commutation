from .expression import Operator, Term, Expression
from warnings import warn

class CommutatorUnknownException(Exception):
    def __init__(self, o1, o2):
        super().__init__(f"commutator algebra does not know [{o1}, {o2}]_-")


class AntiCommutatorUnknownException(Exception):
    def __init__(self, o1, o2):
        super().__init__(f"anticommutator algebra does not know [{o1}, {o2}]_+")

class AbstractCommutatorAlgebra:
    def __init__(self, strict=False):
        self.strict = strict
        self.relations = {}


    def _add_operator(self, op, default_self, default_rel):
        assert isinstance(op, Operator)
        s = str(op)

        if s not in self.relations:
            col = {}
            for k in self.relations:
                self.relations[k][s] = default_rel
                col[k] = default_rel

            col[s] = default_self
            self.relations[s] = col


    def _move_right(self, r_mover, expr:Expression, A):
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

            for I in indices:
                for i in range(I, len(term.ops) - 1):
                    assert term.ops[i] == A
                    extra_terms += r_mover(term, i)

        self._move_right(r_mover, extra_terms, A)
        expr.terms += extra_terms.terms
        expr.collect()


    def _move_left(self, l_mover, expr:Expression, A):
        '''
        Moves all instances of the operator 'A' to the left of the expression.
        '''
        assert isinstance(A, Operator)

#        # Strategy: Go through each term in self.terms
#        # Within each term's operator list, iteratively keep moving it up in index using the elementary operation
#        #  AB -> BA + [A, B]
        if A.name not in expr.operators:
            return expr

        extra_terms = Expression()
        for term in expr.terms:
            indices = term.findall(A)
            for I in indices:
                for i in range(I, 0, -1):
                    assert term.ops[i] == A
                    extra_terms += l_mover(term, i)

        self._move_left(l_mover, extra_terms, A)
        expr.terms += extra_terms.terms
        expr.collect()




class CommutatorAlgebra(AbstractCommutatorAlgebra):
    def add_operator(self, op):
        if self.strict:
            self._add_operator(op, 0, None)
        else:
            self._add_operator(op, 0, 0)

    def set_commutator(self, l_op, r_op):
        assert isinstance(l_op, Operator)
        assert isinstance(r_op, Operator)
        l = l_op.name
        r = r_op.name

        if l not in self.relations:
            self.add_operator(l_op)
        if r not in self.relations:
            self.add_operator(r_op)

        def setter(rhs):
            rel = Expression(rhs) if rhs is not None else None
            if l == r:
                s = 'Setting [%s, %s] to something other than default (0) ... are you sure?' % (l, r)
                warn(s)
            if rel is None:
                self.relations[l][r] = None
                self.relations[r][l] = None
            else:
                self.relations[l][r] = rel
                self.relations[r][l] = -rel

        return setter

    def get_commutator(self, l: Operator, r: Operator):
        assert isinstance(l, Operator)
        assert isinstance(r, Operator)
        if l.is_scalar or r.is_scalar:
            return 0
        elif l.name not in self.relations:
            s = 'Non-scalar operator "' + \
                str(l)+'" is not in the commutator database, assuming it commutes...'
            if self.strict:
                raise CommutatorUnknownException(l, r)
            else:
                warn(s)
            return 0
        elif r.name not in self.relations:
            s = 'Non-scalar operator "' + \
                str(r)+'" is not in the commutator database, assuming it commutes...'
            if self.strict:
                raise CommutatorUnknownException(l, r)
            else:
                warn(s)
            return 0
        else:
            return self.relations[l.name][r.name]

    
    def _move_operator_right_once(self, term:Term, i):
        front = Term(*term.ops[:i])
        back = Term(*term.ops[i+2:])
    
        c = self.get_commutator(term.ops[i], term.ops[i+1])
        extra = front * c * back * term.multiplier

        term.ops[i], term.ops[i+1] = term.ops[i+1], term.ops[i]
        return extra


    def _move_operator_left_once(self, term:Term, i, use_commutator=True):
        A = term.ops[i]
        B = term.ops[i-1]
        front = Term(*term.ops[:i-1])
        back = Term(*term.ops[i+1:])
 
        c = self.get_commutator(A, B)
        extra = front * c * back * term.multiplier
        
        term.ops[i-1], term.ops[i] = term.ops[i], term.ops[i-1]
        return extra

    def move_right(self, expr:Expression, A):
        self._move_right(self._move_operator_right_once, expr, A)

    def move_left(self, expr:Expression, A):
        self._move_left(self._move_operator_left_once, expr, A)



class AntiCommutatorAlgebra(AbstractCommutatorAlgebra):
    def add_operator(self, op):
        if self.strict:
            self._add_operator(op, 2*op, None)
        else:
            self._add_operator(op, 2*op, None)

    def set_anticommutator(self, l_op, r_op):
        assert isinstance(l_op, Operator)
        assert isinstance(r_op, Operator)
        l = l_op.name
        r = r_op.name

        if l not in self.relations:
            self.add_operator(l_op)
        if r not in self.relations:
            self.add_operator(r_op)

        def setter(rhs):
            rel = Expression(rhs) if rhs is not None else None
            if l == r:
                s = 'Setting {%s, %s} to something other than default (2%s) ... are you sure?' % (l, l, l)
                warn(s)
            self.relations[l][r] = rel
            self.relations[r][l] = rel

        return setter

    def get_anticommutator(self, l, r):
        assert isinstance(l, Operator)
        assert isinstance(r, Operator)
        if l.is_scalar or r.is_scalar:
            return None # no Grassman for you
        elif not (l.name in self.relations and r.name in self.relations):
            return None # idk how to commute this
        else:
            return self.relations[l.name][r.name]



    def _move_operator_right_once(self, term:Term, i):
        front = Term(*term.ops[:i])
        back = Term(*term.ops[i+2:])
    
        c = self.get_anticommutator(
            term.ops[i], term.ops[i+1])
        extra = Expression(front) * \
            c * Expression(back)*term.multiplier
        term.multiplier *= -1

        term.ops[i], term.ops[i+1] = term.ops[i+1], term.ops[i]
        return extra


    def _move_operator_left_once(self, term:Term, i):
        A = term.ops[i]
        B = term.ops[i-1]
        front = Term(*term.ops[:i-1])
        back = Term(*term.ops[i+1:])
 
        c = self.get_anticommutator(A, B)
        if c is None:
            raise AntiCommutatorUnknownException(A, B)
        extra = Expression(front) * c * Expression(back) * term.multiplier
        term.multiplier *= -1
        
        term.ops[i-1], term.ops[i] = term.ops[i], term.ops[i-1]
        return extra

    def move_right(self, expr:Expression, A):
        self._move_right(self._move_operator_right_once, expr, A)

    def move_left(self, expr:Expression, A):
        self._move_left(self._move_operator_left_once, expr, A)

