# Commutation Station for Operator Elimination

A proof assistant tool for the busy physicist, to be used in evaluating large commutator expressions.
This package does symbolic algebra on noncommutative objects. 

The relevant objects for most purposes are `CommutatorAlgebra`, `Expression` and `Term`. An `Expression` is a list of `Term`s, together with standard vector space operations.



# TODO
 - Export functionality for easier copying into Mathematica or similar
 - Input validation / standardisation of symbol types
 - change fundamental type from strings to objects: restrict purpose of Term to single terms
 - Implement use of anticommutator algebra
 - Scalar subclass of Term (in general, import sympy to simplify scalar coefficients?



# Future

## `Term` class functionality
`Term.as_latex()`
`Term.as_mathematica()`
`Term.__str__()`
`Constant(Term)`
does NOT have any built-in multiplier: this nastiness is handled by the new `Expression` class
`Expression.as_latex()`
`Expression.as_mathematica()`
internal structure: `[([1],[t1, t2]),([3/4 ka k2], [t3, t4])] -> t1 t2 + t3 t4
