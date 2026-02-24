# Lab 2 Report

## Topic

Determinism in Finite Automata. Conversion from NDFA to DFA. Chomsky Hierarchy.

## Course

Formal Languages and Finite Automata

## Objective

For this lab, I implemented:

1. grammar classification by Chomsky hierarchy
2. conversion from finite automaton to regular grammar
3. NDFA determinism check
4. conversion from NDFA to DFA (subset construction)
5. execution demo using the variant automaton

## Variant used

- `Q = {q0, q1, q2, q3, q4}`
- `Sigma = {a, b}`
- `F = {q4}`
- `delta(q0, a) = q1`
- `delta(q1, b) = q1`
- `delta(q1, b) = q2`
- `delta(q2, b) = q3`
- `delta(q3, a) = q1`
- `delta(q2, a) = q4`

## Implementation details

All code is in `lab2/main.py`.

### 1) Chomsky hierarchy classification

The `Grammar` class provides `classify_chomsky()`.

Decision logic:

- Type-3 if productions are linear (right-linear or left-linear)
- Type-2 if each left side is exactly one non-terminal
- Type-1 if no production decreases length (except `S -> epsilon`)
- Type-0 otherwise

The grammar from lab1 is detected as **Type-3 (Regular Grammar)**.

### 2) FA to regular grammar conversion

The `FiniteAutomaton` class provides `to_regular_grammar()`.

For each transition `p --x--> q`, the grammar gets production `p -> xq`.
If `q` is final, it also adds `p -> x`.
Each final state gets `final -> epsilon`.

For this variant:

- `q0 -> aq1`
- `q1 -> bq1 | bq2`
- `q2 -> aq4 | a | bq3`
- `q3 -> aq1`
- `q4 -> epsilon`

### 3) Determinism check

The `is_deterministic()` method returns `False` when:

- a transition has more than one target for the same `(state, symbol)` pair
- epsilon transitions exist

For this variant, the automaton is **non-deterministic** because:

- `delta(q1, b) = {q1, q2}`

### 4) NDFA to DFA conversion

Implemented in `to_dfa()` using subset construction with epsilon-closure support.

Generated DFA states:

- `{q0}`
- `{q1}`
- `{q1,q2}`
- `{q1,q2,q3}`
- `{q1,q4}`
- `{q4}`
- `{}` (dead state)

Final DFA states are any subsets containing `q4`:

- `{q1,q4}`
- `{q4}`

### 5) Execution demo

Running `python lab2/main.py` prints:

- grammar type by Chomsky hierarchy
- original automaton transitions
- determinism result
- converted regular grammar
- DFA transitions and DFA final states
- NDFA vs DFA acceptance check on sample strings

## Conclusion

The required functionality was implemented for the provided variant.
The program confirms that the given FA is an NDFA, converts it to regular grammar, and constructs an equivalent DFA that matches NDFA acceptance results on tested strings.
