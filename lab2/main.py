from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple


EPSILON = "epsilon"


@dataclass
class Grammar:
    non_terminals: Set[str]
    terminals: Set[str]
    start_symbol: str
    productions: Dict[str, List[str]]

    def _tokenize(self, text: str) -> List[str]:
        normalized = text.strip()
        if normalized in {"", EPSILON}:
            return []
        if " " in normalized:
            return [symbol for symbol in normalized.split(" ") if symbol]
        return list(normalized)

    def classify_chomsky(self) -> str:
        right_linear = True
        left_linear = True
        context_free = True
        context_sensitive = True

        for lhs, rhs_list in self.productions.items():
            lhs_symbols = self._tokenize(lhs)

            lhs_nt_count = sum(symbol in self.non_terminals for symbol in lhs_symbols)
            if lhs_nt_count == 0:
                context_free = False
                context_sensitive = False
                right_linear = False
                left_linear = False

            if len(lhs_symbols) != 1 or lhs_symbols[0] not in self.non_terminals:
                context_free = False
                right_linear = False
                left_linear = False

            for rhs in rhs_list:
                rhs_symbols = self._tokenize(rhs)

                if len(lhs_symbols) > len(rhs_symbols) and not (
                    lhs == self.start_symbol and len(rhs_symbols) == 0
                ):
                    context_sensitive = False

                nt_positions = [
                    index
                    for index, symbol in enumerate(rhs_symbols)
                    if symbol in self.non_terminals
                ]
                has_only_terminals = all(
                    symbol in self.terminals for symbol in rhs_symbols
                )

                if len(nt_positions) > 1:
                    right_linear = False
                    left_linear = False
                elif len(nt_positions) == 1:
                    nt_index = nt_positions[0]
                    if nt_index != len(rhs_symbols) - 1:
                        right_linear = False
                    if nt_index != 0:
                        left_linear = False

                    for symbol in rhs_symbols:
                        if symbol not in self.terminals and symbol not in self.non_terminals:
                            right_linear = False
                            left_linear = False
                elif not has_only_terminals:
                    right_linear = False
                    left_linear = False

        if context_free and (right_linear or left_linear):
            return "Type-3 (Regular Grammar)"
        if context_free:
            return "Type-2 (Context-Free Grammar)"
        if context_sensitive:
            return "Type-1 (Context-Sensitive Grammar)"
        return "Type-0 (Unrestricted Grammar)"

    def formatted_productions(self) -> str:
        rows: List[str] = []
        for lhs in sorted(self.productions.keys()):
            rhs_text = " | ".join(self.productions[lhs])
            rows.append(f"{lhs} -> {rhs_text}")
        return "\n".join(rows)


@dataclass
class FiniteAutomaton:
    states: Set[str]
    alphabet: Set[str]
    transitions: Dict[Tuple[str, str], Set[str]]
    start_state: str
    final_states: Set[str]

    def _epsilon_closure(self, states: Iterable[str]) -> Set[str]:
        closure = set(states)
        stack = list(states)

        while stack:
            state = stack.pop()
            for epsilon_symbol in ("", EPSILON):
                for target in self.transitions.get((state, epsilon_symbol), set()):
                    if target not in closure:
                        closure.add(target)
                        stack.append(target)

        return closure

    def string_belongs_to_language(self, input_string: str) -> bool:
        current_states = self._epsilon_closure({self.start_state})

        for symbol in input_string:
            if symbol not in self.alphabet:
                return False

            next_states: Set[str] = set()
            for state in current_states:
                next_states.update(self.transitions.get((state, symbol), set()))

            current_states = self._epsilon_closure(next_states)
            if not current_states:
                return False

        return any(state in self.final_states for state in current_states)

    def is_deterministic(self) -> bool:
        for (state, symbol), targets in self.transitions.items():
            if symbol in {"", EPSILON} and targets:
                return False
            if len(targets) > 1:
                return False
            if state not in self.states:
                return False
        return True

    def to_regular_grammar(self) -> Grammar:
        productions_map: Dict[str, Set[str]] = {state: set() for state in self.states}

        for (source, symbol), targets in self.transitions.items():
            if symbol in {"", EPSILON}:
                continue

            for target in targets:
                productions_map[source].add(f"{symbol}{target}")
                if target in self.final_states:
                    productions_map[source].add(symbol)

        for final_state in self.final_states:
            productions_map.setdefault(final_state, set()).add(EPSILON)

        productions = {
            lhs: sorted(rhs_set)
            for lhs, rhs_set in productions_map.items()
            if rhs_set
        }

        return Grammar(
            non_terminals=set(self.states),
            terminals=set(self.alphabet),
            start_symbol=self.start_state,
            productions=productions,
        )

    @staticmethod
    def _format_state_set(state_set: Set[str]) -> str:
        if not state_set:
            return "{}"
        return "{" + ",".join(sorted(state_set)) + "}"

    def to_dfa(self) -> "FiniteAutomaton":
        dfa_transitions: Dict[Tuple[str, str], Set[str]] = {}
        dfa_states: Set[str] = set()
        dfa_finals: Set[str] = set()

        start_subset = frozenset(self._epsilon_closure({self.start_state}))
        queue = deque([start_subset])
        visited: Set[frozenset[str]] = {start_subset}

        subset_name: Dict[frozenset[str], str] = {
            start_subset: self._format_state_set(set(start_subset))
        }

        while queue:
            current_subset = queue.popleft()
            current_name = subset_name[current_subset]
            dfa_states.add(current_name)

            if set(current_subset) & self.final_states:
                dfa_finals.add(current_name)

            for symbol in sorted(self.alphabet):
                next_ndfa_states: Set[str] = set()
                for ndfa_state in current_subset:
                    next_ndfa_states.update(
                        self.transitions.get((ndfa_state, symbol), set())
                    )

                next_subset = frozenset(self._epsilon_closure(next_ndfa_states))
                if next_subset not in subset_name:
                    subset_name[next_subset] = self._format_state_set(set(next_subset))

                next_name = subset_name[next_subset]
                dfa_transitions[(current_name, symbol)] = {next_name}

                if next_subset not in visited:
                    visited.add(next_subset)
                    queue.append(next_subset)

        return FiniteAutomaton(
            states=dfa_states,
            alphabet=set(self.alphabet),
            transitions=dfa_transitions,
            start_state=subset_name[start_subset],
            final_states=dfa_finals,
        )

    def transition_table(self) -> str:
        rows: List[str] = []
        for state in sorted(self.states):
            for symbol in sorted(self.alphabet | {EPSILON}):
                targets = self.transitions.get((state, symbol), set())
                if targets:
                    rows.append(f"delta({state}, {symbol}) = {sorted(targets)}")
        return "\n".join(rows)


def build_variant_automaton() -> FiniteAutomaton:
    transitions: Dict[Tuple[str, str], Set[str]] = {
        ("q0", "a"): {"q1"},
        ("q1", "b"): {"q1", "q2"},
        ("q2", "b"): {"q3"},
        ("q3", "a"): {"q1"},
        ("q2", "a"): {"q4"},
    }

    return FiniteAutomaton(
        states={"q0", "q1", "q2", "q3", "q4"},
        alphabet={"a", "b"},
        transitions=transitions,
        start_state="q0",
        final_states={"q4"},
    )


def build_lab1_grammar() -> Grammar:
    return Grammar(
        non_terminals={"S", "I", "J", "K"},
        terminals={"a", "b", "c", "e", "n", "f", "m"},
        start_symbol="S",
        productions={
            "S": ["cI"],
            "I": ["bJ", "fI", "eK", "e"],
            "J": ["nJ", "cS"],
            "K": ["nK", "m"],
        },
    )


if __name__ == "__main__":
    grammar = build_lab1_grammar()
    print("1) Chomsky hierarchy classification:")
    print(f"   {grammar.classify_chomsky()}")

    automaton = build_variant_automaton()
    print("\n2) Given finite automaton:")
    print(automaton.transition_table())
    print(f"   Deterministic: {automaton.is_deterministic()}")

    regular_grammar = automaton.to_regular_grammar()
    print("\n3) Finite automaton -> regular grammar:")
    print(regular_grammar.formatted_productions())

    dfa = automaton.to_dfa()
    print("\n4) NDFA -> DFA conversion:")
    print(dfa.transition_table())
    print(f"   DFA states: {sorted(dfa.states)}")
    print(f"   DFA final states: {sorted(dfa.final_states)}")

    test_strings = ["a", "ab", "abb", "abba", "abbaab", "abbbba"]
    print("\n5) Validation on sample strings (NDFA and DFA must match):")
    for candidate in test_strings:
        ndfa_result = automaton.string_belongs_to_language(candidate)
        dfa_result = dfa.string_belongs_to_language(candidate)
        print(f"   {candidate!r}: NDFA={ndfa_result}, DFA={dfa_result}")
