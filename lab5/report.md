# Chomsky Normal Form

### Course: Formal Languages & Finite Automata
### Author: Rustem Cimendur

----

## Theory

Chomsky Normal Form (CNF) is a restricted form of a context-free grammar where each production must have one of the following shapes: `A -> BC` or `A -> a`. In some definitions, the rule `S -> epsilon` is also allowed if the start symbol can derive the empty word. This normal form is useful because it simplifies parsing algorithms and makes grammar transformations easier to reason about.

To transform a grammar into CNF, the grammar is usually normalized in several steps. First, epsilon productions are removed, then unit productions are eliminated, and after that inaccessible and non-productive symbols are removed. Finally, productions that are too long or mix terminals with non-terminals are rewritten so that every rule respects the CNF restrictions.

For this laboratory work, I implemented a general normalization pipeline and tested it on Variant 6. The program does not only print the final grammar, but also shows the intermediate normalization steps, which makes the transformation easier to follow and verify.

## Objectives:

* Study the concept of Chomsky Normal Form and understand why it is used.
* Apply the standard normalization steps on a context-free grammar.
* Implement a reusable Python method that can normalize an input grammar, not only the grammar from the assigned variant.
* Execute and test the implementation on Variant 6.

## Implementation Description

* **Grammar representation**: I used a `Grammar` dataclass to store the sets of non-terminals, terminals, productions, and the start symbol. Productions are stored as tuples, which makes them easy to compare, deduplicate, and rewrite during the normalization process.

```python
@dataclass
class Grammar:
    non_terminals: Set[Symbol]
    terminals: Set[Symbol]
    productions: Dict[Symbol, Set[Production]]
    start_symbol: Symbol
```

* **Normalization pipeline**: The `GrammarNormalizer` class encapsulates the full workflow. The method `normalize_to_cnf()` applies all requested operations in order: epsilon elimination, renaming elimination, removal of inaccessible symbols, removal of non-productive symbols, and final conversion to CNF.

```python
def normalize_to_cnf(self) -> Grammar:
    self.add_step("Started grammar normalization.")
    self.eliminate_epsilon_productions()
    self.eliminate_renaming()
    self.eliminate_inaccessible_symbols()
    self.eliminate_non_productive_symbols()
    self.to_chomsky_normal_form()
    return self.grammar
```

* **Epsilon elimination**: To remove epsilon productions correctly, the program first computes the set of nullable non-terminals. Then it generates all valid right-hand-side combinations obtained by optionally removing nullable symbols, while preserving the language as much as possible.

```python
def _find_nullable_symbols(self) -> Set[Symbol]:
    nullable: Set[Symbol] = set()
    changed = True

    while changed:
        changed = False
        for left, rights in self.grammar.productions.items():
            if left in nullable:
                continue
            if any(
                len(right) == 0
                or all(symbol in nullable for symbol in right)
                for right in rights
            ):
                nullable.add(left)
                changed = True
    return nullable
```

* **Unit production removal**: Renaming productions such as `A -> B` are removed by computing the closure of reachable non-terminals through unit rules. After the closure is known, the program copies all non-unit productions of the reachable symbols into the source non-terminal.

```python
for non_terminal in self.grammar.non_terminals:
    closure = {non_terminal}
    queue = deque([non_terminal])
    while queue:
        current = queue.popleft()
        for right in self.grammar.productions.get(current, set()):
            if len(right) == 1 and right[0] in self.grammar.non_terminals:
                target = right[0]
                if target not in closure:
                    closure.add(target)
                    queue.append(target)
```

* **Conversion to CNF**: The final stage replaces terminals that appear inside longer productions with helper non-terminals such as `T_A2 -> a` and `T_B1 -> b`. After that, long productions are binarized with fresh helper symbols like `X3` and `X4`, so every remaining rule has either one terminal or two non-terminals on the right side.

```python
for left, rights in list(self.grammar.productions.items()):
    for right in rights:
        if len(right) <= 2:
            binarized.setdefault(left, set()).add(right)
            continue

        symbols = list(right)
        current_left = left
        while len(symbols) > 2:
            first = symbols.pop(0)
            helper = self._new_non_terminal("X")
            binarized.setdefault(current_left, set()).add((first, helper))
            current_left = helper
        binarized.setdefault(current_left, set()).add(tuple(symbols))
```

* **Variant definition and execution**: I also added a dedicated `variant_6_grammar()` function and a `run_demo()` entry point. This keeps the example grammar separate from the normalization logic and makes it easy to test another grammar later by passing a different `Grammar` instance.

```python
def variant_6_grammar() -> Grammar:
    return build_grammar(
        non_terminals={"S", "A", "B", "C", "E"},
        terminals={"a", "b"},
        productions={
            "S": [("a", "B"), ("A", "C")],
            "A": [("a",), ("A", "S", "C"), ("B", "C")],
            "B": [("b",), ("b", "S")],
            "C": [tuple(), ("B", "A")],
            "E": [("b", "B")],
        },
        start_symbol="S",
    )
```

## Conclusions / Screenshots / Results

The implementation successfully normalized the grammar from Variant 6. During execution, the program detected that `C` is nullable, removed epsilon productions, confirmed that there were no non-productive symbols to remove, and detected that `E` is inaccessible from the start symbol `S`, so it was removed.

The final grammar satisfies the CNF form because every production is either of the form `A -> a` or `A -> BC`. The helper non-terminals introduced during the last step are expected and are part of the standard CNF conversion process.

**Command used to run the program:**

```powershell
python lab5\main.py
```

**Program output:**

```text
Initial grammar
VN = {A, B, C, E, S}
VT = {a, b}
Start = S
P:
  A -> ASC | BC | a
  B -> b | bS
  C -> epsilon | BA
  E -> bB
  S -> AC | aB

Normalization steps:
1. Started grammar normalization.
2. Nullable non-terminals: C.
3. Eliminated epsilon productions.
4. Eliminated renaming productions.
5. Eliminated inaccessible symbols: E.
6. Eliminated non-productive symbols: none.
7. Converted grammar to Chomsky Normal Form.

Grammar in Chomsky Normal Form
VN = {A, B, C, S, T_A2, T_B1, X3, X4}
VT = {a, b}
Start = S
P:
  A -> AS | AX4 | BC | T_B1S | a | b
  B -> T_B1S | b
  C -> BA
  S -> AC | AS | AX3 | BC | T_A2B | T_B1S | a | b
  T_A2 -> a
  T_B1 -> b
  X3 -> SC
  X4 -> SC
```

## References

1. Hopcroft, J. E., Motwani, R., & Ullman, J. D. *Introduction to Automata Theory, Languages, and Computation*.
2. Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. *Compilers: Principles, Techniques, and Tools*.
3. Chomsky, N. *Three Models for the Description of Language*.
