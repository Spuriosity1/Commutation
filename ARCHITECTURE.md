# Commutation — Architecture & Code Reference

A symbolic-algebra package for noncommutative objects, aimed at evaluating large
commutator expressions (physics operator algebra). The public API is a thin
re-export (`src/commutation/__init__.py`); all logic lives in two modules.

- **`expression.py`** — the algebraic data model (`Operator`, `Term`, `Expression`).
- **`commutatoralgebra.py`** — commutator/anticommutator relation tables and the
  operator-reordering engine (`CommutatorAlgebra`, `AntiCommutatorAlgebra`).
- **`style.py`** — `show()`, LaTeX rendering for Jupyter notebooks.

`README.md` covers user-facing usage; this file documents the internals.

## The data model (`expression.py`)

The algebra is built in three layers, each a standard algebraic structure:

```
Operator          a single non-commutative symbol  (e.g. S^z_a)
  └─ Term         coefficient × ordered product of Operators   (monoid)
       └─ Expression   sum of Terms                            (abelian group)
```

### `Operator`
A single symbol. Key fields:
- `name` — display string and the **key** used in commutator tables (`str(op)`).
- `latex_string` — optional prettier form for `as_latex()`; defaults to `name`.

Operator arithmetic promotes upward: `op * x → Term`, `op + x → Expression`,
`-op → Term` (multiplier `-1`). `__eq__` is defined *algebraically* —
`a == b` evaluates `a + (-1)*b == 0`, so it works across Operator/Term/Expression.

Scalars (commuting constants) are **not** operators — they live in a term's
SymPy `multiplier`. Use `sympy.Symbol('J')` rather than a flagged operator.

### `Term`
Reads as `multiplier * ops[0] * ops[1] * ...`.
- `multiplier` — a generic **SymPy** coefficient (`sympy.Expr`). Python `int` and
  `fractions.Fraction` are accepted and promoted to exact sympy numbers;
  `float` is rejected (see `coerce_coeff`). This lets a term be scaled by
  symbols (`sympy.Symbol('J')`), exact rationals, or algebraic numbers such as
  `sympy.I` (`I**2 == -1`).
- `ops` — a list of `Operator`s; `[]` means the identity `1`.

Important contract (see the class docstring): `ops` holds **shallow** references
to `Operator` objects so that tweaking an `Operator` propagates everywhere;
`Term` itself is copied with `copy.copy` in the arithmetic dunders.

Notable methods:
- `findall(glob)` — indices of **non-overlapping** occurrences of a subproduct
  (`aaaa.findall(aa) → [0, 2]`). Used by substitution and the move engine.
- `is_scalar` (True iff `ops` is empty, i.e. a pure coefficient), `sign`,
  `order` (= `len(ops)`) — properties.

### `Expression`
A list of `Term`s read as a sum. The `terms` list is deep-copied on construction
(new `Term` objects, but the underlying `Operator` references are preserved).

Core algebraic ops: `collect()` folds like-terms (keyed by `'*'.join(op.name)`)
and drops zero-multiplier terms; `sort(strategy)` orders terms (`'first'`,
`'last'`, `'multiplier'`); `__eq__` subtracts, collects, and checks for empty.

Term-rewriting / CAS operations:
- `substitute(glob, sub)` (alias `sub`) — replace every non-overlapping occurrence
  of a subproduct `glob` with an arbitrary expression `sub`. Pure (returns new
  Expression). Single-term `glob` only for now.
- `replaceall((glob, sub), ...)` — multiple simultaneous rewrite rules, applied
  left-to-right across each term.
- `factor(side, x)` — pull out a common left/right factor. With no `x`, finds the
  longest common prefix (`side='right'`) or suffix (`side='left'`) across all terms;
  with an explicit `x`, factors that operator out. Asserts `front * back == self`.
  Does **not** factor nested subunits.
- `coefficient(term, side)` — collect the coefficient-expression multiplying a
  given left/right factor.

`as_latex()` on each class builds a LaTeX string; fractions render as `\frac{}{}`.

## The commutator engine (`commutatoralgebra.py`)

### Relation storage — `AbstractCommutatorAlgebra`
`self.relations` is a dict-of-dicts: `relations[l_name][r_name]` holds the
(anti)commutator of two operators as an `Expression` (or `0`/`None`).
`_add_operator` grows this as a dense square table, backfilling defaults for every
already-known operator so the table stays rectangular. `strict` mode controls
whether unknown pairs raise or default to commuting.

### The reordering algorithm
`_move_right` / `_move_left` are the heart of the package. To push operator `A`
toward one end of every term they repeatedly apply the elementary swap

```
A B  →  B A + [A, B]      (commutator case)
A B  →  −B A + {A, B}      (anticommutator case)
```

A swap generates an `extra_terms` expression (from the (anti)commutator), which is
itself **recursively** reordered and then merged back in, followed by `collect()`.
The two concrete algebras inject their own single-swap function
(`_move_operator_right_once` / `_left_once`) via the `r_mover`/`l_mover` parameter —
a clean strategy-pattern split between "how to swap one pair" and "how to sweep".

> ⚠️ As the README warns, pathological relations (where `[A,B]` reintroduces `A`
> next to `B`) make the recursion loop forever. There is no cycle guard.

### `CommutatorAlgebra`
- `set_commutator(l, r)` returns a *setter* — call it a second time with the RHS:
  `ca.set_commutator(az, ap)(ap)` sets `[az, ap] = ap`. It automatically stores the
  antisymmetric partner `[r, l] = −[l, r]`.
- `get_commutator` warns (or raises `CommutatorUnknownException` under `strict`)
  and assumes commuting for operators not in the database.
- `move_right(expr, A)` / `move_left(expr, A)` — public entry points (mutate `expr`).

### `AntiCommutatorAlgebra`
Parallel structure using anticommutators; the swap also flips the term's sign.
Defaults `{A, A} = 2A`, returns `None` for unknown pairs, and raises
`AntiCommutatorUnknownException` when it cannot proceed. (Per `TODO.md`,
anticommutator support is newer / less exercised than the commutator path.)

## Conventions & gotchas

- **Exact arithmetic only** — coefficients are `sympy.Expr`; `int` and `Fraction`
  are accepted and promoted to exact sympy numbers, Python `float` is not
  (it would introduce inexact arithmetic). Use `Fraction` or `sympy.Rational`.
- **Operators compared by `name`** in the relation tables, but by object elsewhere
  via algebraic `__eq__`. Two distinct `Operator`s sharing a `name` will collide as
  table keys.
- **Mutation vs. purity is mixed**: `substitute`/`factor`/`replaceall` return new
  objects; `move_left`/`move_right`/`collect`/`sort` mutate in place.
- **No parser yet** — `from_str` raises `NotImplementedError` on both `Term` and
  `Expression`.
- **`show()` is Jupyter-only** — it needs `IPython.display`; raises `AttributeError`
  outside a notebook.

## Repo layout

```
Commutation/
├── pyproject.toml          setuptools build, src-layout, deps: ipython, sympy
├── README.md               usage examples
├── TODO.md                 roadmap (anticommutators, spin helpers)
├── ARCHITECTURE.md         this file
├── src/commutation/
│   ├── __init__.py         public API re-exports
│   ├── expression.py       data model
│   ├── commutatoralgebra.py  (anti)commutator engine
│   └── style.py            LaTeX display
├── Examples/               Jupyter notebooks (spin algebra, ring-flip, hexamer, …)
└── .github/workflows/      python-package (CI) + python-publish (PyPI release)
```

## Status / open work (from `TODO.md`)

- Harden anticommutator algebra.
- Helper constructors for spin operators (currently built by hand).

Resolved: the test suite now lives under `tests/`; algebraic-number support
(including `I² = −1`) comes for free now that coefficients are generic SymPy
expressions.
