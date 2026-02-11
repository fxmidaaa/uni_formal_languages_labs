import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class FiniteAutomaton:
    states: Set[str]
    alphabet: Set[str]
    transitions: Dict[Tuple[str, str], Set[str]]
    start_state: str
    final_states: Set[str]

    def stringBelongToLanguage(self, input_string: str) -> bool:
        current_states: Set[str] = {self.start_state}

        for symbol in input_string:
            if symbol not in self.alphabet:
                return False

            next_states: Set[str] = set()
            for state in current_states:
                next_states.update(self.transitions.get((state, symbol), set()))

            if not next_states:
                return False

            current_states = next_states

        return any(state in self.final_states for state in current_states)


class Grammar:
    def __init__(
        self,
        non_terminal_symbols: Set[str],
        terminal_symbols: Set[str],
        start_symbol: str,
        production_rules: Dict[str, List[str]],
    ) -> None:
        self.Vn = non_terminal_symbols
        self.Vt = terminal_symbols
        self.S = start_symbol
        self.P = production_rules

    def _split_rhs(self, rhs: str) -> Tuple[str, Optional[str]]:
        if rhs and rhs[-1] in self.Vn:
            terminals = rhs[:-1]
            next_non_terminal = rhs[-1]
        else:
            terminals = rhs
            next_non_terminal = None

        for symbol in terminals:
            if symbol not in self.Vt:
                raise ValueError(
                    f"Invalid production '{rhs}'. '{symbol}' is not a terminal symbol."
                )

        return terminals, next_non_terminal

    def generateString(self, max_steps: int = 200) -> str:
        current_non_terminal = self.S
        generated_parts: List[str] = []

        for _ in range(max_steps):
            options = self.P.get(current_non_terminal, [])
            if not options:
                raise ValueError(
                    f"No productions found for non-terminal '{current_non_terminal}'."
                )

            chosen_rhs = random.choice(options)
            terminals, next_non_terminal = self._split_rhs(chosen_rhs)
            generated_parts.append(terminals)

            if next_non_terminal is None:
                return "".join(generated_parts)

            current_non_terminal = next_non_terminal

        raise RuntimeError(
            "Generation exceeded max_steps. The chosen productions may be cycling."
        )

    @staticmethod
    def _add_transition(
        transitions: Dict[Tuple[str, str], Set[str]],
        source: str,
        symbol: str,
        target: str,
    ) -> None:
        transitions.setdefault((source, symbol), set()).add(target)

    def toFiniteAutomaton(self) -> FiniteAutomaton:
        states: Set[str] = set(self.Vn)
        alphabet: Set[str] = set(self.Vt)
        transitions: Dict[Tuple[str, str], Set[str]] = {}

        final_sink = "q_f"
        while final_sink in states:
            final_sink += "_"
        states.add(final_sink)

        final_states: Set[str] = {final_sink}
        helper_index = 0

        # Transition mapping logic:
        # 1) Every non-terminal becomes an FA state.
        # 2) A production A -> xB adds transition A -x-> B.
        # 3) A production A -> x (terminal-only) adds transition A -x-> q_f.
        # 4) If a production has multiple terminals (A -> xyzB or A -> xyz),
        #    helper states are inserted to keep one-symbol transitions in the FA.
        for left_non_terminal, rhs_list in self.P.items():
            for rhs in rhs_list:
                terminals, next_non_terminal = self._split_rhs(rhs)

                if terminals == "":
                    if next_non_terminal is None:
                        final_states.add(left_non_terminal)
                    else:
                        raise ValueError(
                            f"Epsilon transition '{left_non_terminal}->{rhs}' is unsupported."
                        )
                    continue

                source_state = left_non_terminal
                for index, symbol in enumerate(terminals):
                    is_last_terminal = index == len(terminals) - 1

                    if is_last_terminal:
                        target_state = next_non_terminal if next_non_terminal else final_sink
                    else:
                        helper_state = f"q_h{helper_index}"
                        helper_index += 1
                        while helper_state in states:
                            helper_state = f"q_h{helper_index}"
                            helper_index += 1
                        states.add(helper_state)
                        target_state = helper_state

                    self._add_transition(transitions, source_state, symbol, target_state)
                    source_state = target_state

        return FiniteAutomaton(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            start_state=self.S,
            final_states=final_states,
        )


if __name__ == "__main__":
    grammar = Grammar(
        non_terminal_symbols={"S", "I", "J", "K"},
        terminal_symbols={"a", "b", "c", "e", "n", "f", "m"},
        start_symbol="S",
        # Interpreted as the right-linear variant:
        # I -> bJ | fI | eK | e
        production_rules={
            "S": ["cI"],
            "I": ["bJ", "fI", "eK", "e"],
            "J": ["nJ", "cS"],
            "K": ["nK", "m"],
        },
    )

    generated_strings: List[str] = [grammar.generateString() for _ in range(5)]

    print("Generated valid strings:")
    for index, generated in enumerate(generated_strings, start=1):
        print(f"{index}. {generated}")

    automaton = grammar.toFiniteAutomaton()

    print("\nFinite automaton validation:")
    for generated in generated_strings:
        result = automaton.stringBelongToLanguage(generated)
        print(f"{generated} -> {result}")

    print("\nManual FA check (type 'exit' to stop):")
    while True:
        candidate = input("Input string: ").strip()
        if candidate.lower() == "exit":
            break

        is_accepted = automaton.stringBelongToLanguage(candidate)
        print(f"Accepted: {is_accepted}")
