# Commutation Station for Operator Elimination

A proof assistant tool for the busy physicist, to be used in evaluating large commutator expressions.
This package does symbolic algebra on noncommutative objects.

Example usage:

### Creating Expressions from Operators
```python
from commutation import *
from fractions import Fraction

a = Operator('a','S^x_a')
b = Operator('b','S^z_b')
c = Operator('c','S^z_c')
d = Operator('d','S^z_d')

# building everything up from elementary operators

x = a-9*b*c + a*b*a
print(x)
# +1 a  -9 b c  +1 a b a
```

### Complicated substitutions
```python
x = a*b*b*b*a*c*a*a*c*a*b + 1

y = x.substitute(a*b,c+d)
print(x) # +1 a b b b a c a a c a b  +1
print(y) # +1 c b b a c a a c c  +1 c b b a c a a c d  +1 d b b a c a a c c  +1 d b b a c a a c d  +1
```

### Factorisations

```python
xx = 7*a*b*b + Fraction(4,5)*a*c*b*b + a*d*b*b + a*c*a*a*b*b + 3*a*b*b
fr, ba = xx.factor('right')
print(str(fr) + ' * [' + str(ba) + '  ] = ' +str(fr*ba)) # +1 a * [  +10 b b  +4/5 c b b  +1 d b b  +1 c a a b b  ] =   +10 a b b  +4/5 a c b b  +1 a d b b  +1 a c a a b b

fr, ba = xx.factor()
print('['+str(fr) + '  ] * ' + str(ba) + ' = ' +str(fr*ba)) # [  +10 a  +4/5 a c  +1 a d  +1 a c a a  ] * +1 b b =   +10 a b b  +4/5 a c b b  +1 a d b b  +1 a c a a b b
```

### Commutators

```python
ca = CommutatorAlgebra()

az = Operator('az','S^z_a')
ap = Operator('a⁺','S^+_a')
am = Operator('a⁻','S^-_a')

KA = Operator('KA', 'K_A', scalar=True)

# note the funky bracket sequence - set_commutator actually returns a function
ca.set_commutator(az,ap)(ap)
ca.set_commutator(az,am)(-1*am)
ca.set_commutator(ap,am)(2*az)

# there are two modes: move_left and move_right
# Note that pathological commutators will make these fall into recursion loops...

xpr = Expression(az*ap*az*az*am)
ca.move_right(xpr, az)
xpr.collect()
print(xpr) # +1 a⁺ a⁻ az az az  -2 a⁺ a⁻ az az  +1 a⁺ a⁻ az

xpr = Expression(az*ap*az*az*am)
ca.move_left(xpr, am)
xpr.collect()
print(xpr) # +1 a⁻ az a⁺ az az  -2 a⁻ az a⁺ az  +2 az az az az  -1 a⁻ a⁺ az az  +1 a⁻ az a⁺  -4 az az az  +2 a⁻ a⁺ az  +2 az az  -1 a⁻ a⁺

# these will warn you if you add an unknown operator...
xpr2 = Expression(az*ap*am*c*am)
ca.move_right(xpr2, az) # UserWarning: Non-scalar operator "c" is not in the commutator database, assuming it commutes...
xpr2.collect()
print(xpr2) #   +1 a⁺ a⁻ c a⁻ az  -1 a⁺ a⁻ c a⁻

# # ... but scalars are fine.
xpr3 = Expression(az*ap*am*KA*am)
ca.move_right(xpr3, az)
xpr3.collect()
print(xpr3) #   +1 a⁺ a⁻ KA a⁻ az  -1 a⁺ a⁻ KA a⁻
```
