# Intro to Formal Languages. Regular Grammars. Finite Automata

### Course: Formal Languages & Finite Automata

### Author: Rustem Cimendur

---

## Theory

A formal language is a structured system used to describe valid strings constructed from a finite alphabet according to specific grammatical rules.
Any formal language is defined by:

* **Alphabet (VT)** – the set of terminal symbols that appear in strings.
* **Non-terminals (VN)** – symbols used to define production rules.
* **Productions (P)** – transformation rules that describe how strings are generated.
* **Start symbol (S)** – the symbol from which generation begins.

Regular grammars are a restricted class of grammars where productions have the form:

* **A → aB** (terminal followed by non-terminal)
* **A → a** (terminal only)

Such grammars are equivalent in expressive power to **finite automata**, meaning every regular grammar can be transformed into a finite automaton that recognizes the same language.

---

## Objectives

* Understand the concept of a formal language and its components.
* Implement a **regular grammar model** in code.
* Generate **valid strings** using grammar productions.
* Convert the grammar into a **finite automaton**.
* Implement a **string membership check** using the automaton.

---

## Implementation description

### Grammar representation

A `Grammar` class was implemented containing:

* sets of **non-terminals**, **terminals**,
* **production rules**,
* **start symbol**.

The class also includes a method for **random generation of valid strings** by repeatedly applying production rules until a terminal-only rule is reached.

### Finite automaton representation

A `FiniteAutomaton` class was created with:

* set of **states**,
* **alphabet**,
* **transition function**,
* **initial state**,
* **final states**.

The automaton uses **NFA simulation** to check whether a string belongs to the language.

### Grammar → Automaton conversion

Each production rule is converted as follows:

* **A → aB** → transition `A --a--> B`
* **A → a** → transition `A --a--> FINAL`

A unique final state is added to complete the construction.

---

### Code snippet (main execution)

```python
if __name__ == "__main__":
    g = build_variant_6_grammar()
    fa = grammar_to_fa(g)

    words = []
    while len(words) < 5:
        w = g.generate_string()
        if fa.accepts(w):
            words.append(w)

    print("5 generated valid strings:")
    for i, w in enumerate(words, 1):
        print(i, w)
```

---

## Conclusions / Results

* A **regular grammar** was successfully modeled in Python.
* The grammar correctly **generates valid strings** of the language.
* An equivalent **finite automaton** was constructed from the grammar.
* The automaton correctly **verifies string membership**.

This demonstrates the **theoretical equivalence between regular grammars and finite automata** and provides a practical implementation of both concepts.

---

## References

* Course materials: *Formal Languages & Finite Automata*.
* Hopcroft, Motwani, Ullman – *Introduction to Automata Theory, Languages, and Computation*.
* Lecture notes provided during the course.
