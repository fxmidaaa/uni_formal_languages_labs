from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import product
from typing import Dict, Iterable, List, Sequence, Set, Tuple


Symbol = str
Production = Tuple[Symbol, ...]


@dataclass
class Grammar:
    non_terminals: Set[Symbol]
    terminals: Set[Symbol]
    productions: Dict[Symbol, Set[Production]]
    start_symbol: Symbol

    def clone(self) -> "Grammar":
        return Grammar(
            non_terminals=set(self.non_terminals),
            terminals=set(self.terminals),
            productions={
                left: {tuple(right) for right in rights}
                for left, rights in self.productions.items()
            },
            start_symbol=self.start_symbol,
        )

    def normalize(self) -> None:
        for non_terminal in self.non_terminals:
            self.productions.setdefault(non_terminal, set())

    def format_production(self, right: Production) -> str:
        if not right:
            return "epsilon"
        return "".join(right)

    def format_rules(self) -> List[str]:
        lines: List[str] = []
        for left in sorted(self.non_terminals):
            right_parts = sorted(
                (self.format_production(right) for right in self.productions.get(left, set())),
                key=lambda value: (value != "epsilon", value),
            )
            if right_parts:
                lines.append(f"{left} -> {' | '.join(right_parts)}")
        return lines


class GrammarNormalizer:
    def __init__(self, grammar: Grammar) -> None:
        self.grammar = grammar.clone()
        self.grammar.normalize()
        self.step_log: List[str] = []
        self._cnf_counter = 1

    def add_step(self, message: str) -> None:
        self.step_log.append(f"{len(self.step_log) + 1}. {message}")

    def eliminate_epsilon_productions(self) -> None:
        nullable = self._find_nullable_symbols()
        nullable_without_start = nullable - {self.grammar.start_symbol}

        self.add_step(
            "Nullable non-terminals: "
            + (", ".join(sorted(nullable)) if nullable else "none")
            + "."
        )

        updated: Dict[Symbol, Set[Production]] = {
            left: set() for left in self.grammar.non_terminals
        }

        for left, rights in list(self.grammar.productions.items()):
            for right in rights:
                if not right:
                    continue
                for candidate in self._expand_nullable_variants(right, nullable_without_start):
                    if candidate:
                        updated[left].add(candidate)

        if self.grammar.start_symbol in nullable:
            updated[self.grammar.start_symbol].add(tuple())

        self.grammar.productions = updated
        self.add_step("Eliminated epsilon productions.")

    def eliminate_renaming(self) -> None:
        closures: Dict[Symbol, Set[Symbol]] = {}

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
            closures[non_terminal] = closure

        updated: Dict[Symbol, Set[Production]] = {
            left: set() for left in self.grammar.non_terminals
        }

        for left, closure in closures.items():
            for target in closure:
                for right in self.grammar.productions.get(target, set()):
                    if len(right) == 1 and right[0] in self.grammar.non_terminals:
                        continue
                    updated[left].add(right)

        self.grammar.productions = updated
        self.add_step("Eliminated renaming productions.")

    def eliminate_inaccessible_symbols(self) -> None:
        reachable = {self.grammar.start_symbol}
        queue = deque([self.grammar.start_symbol])

        while queue:
            current = queue.popleft()
            for right in self.grammar.productions.get(current, set()):
                for symbol in right:
                    if symbol in self.grammar.non_terminals and symbol not in reachable:
                        reachable.add(symbol)
                        queue.append(symbol)

        removed = self.grammar.non_terminals - reachable
        self.grammar.non_terminals = reachable
        self.grammar.productions = {
            left: rights
            for left, rights in self.grammar.productions.items()
            if left in reachable
        }
        self.grammar.normalize()
        self.add_step(
            "Eliminated inaccessible symbols: "
            + (", ".join(sorted(removed)) if removed else "none")
            + "."
        )

    def eliminate_non_productive_symbols(self) -> None:
        productive: Set[Symbol] = set()
        changed = True

        while changed:
            changed = False
            for left, rights in self.grammar.productions.items():
                if left in productive:
                    continue
                for right in rights:
                    if all(
                        symbol in self.grammar.terminals or symbol in productive
                        for symbol in right
                    ):
                        productive.add(left)
                        changed = True
                        break

        removed = self.grammar.non_terminals - productive
        updated: Dict[Symbol, Set[Production]] = {}

        for left in productive:
            kept: Set[Production] = set()
            for right in self.grammar.productions.get(left, set()):
                if all(
                    symbol in self.grammar.terminals or symbol in productive
                    for symbol in right
                ):
                    kept.add(right)
            updated[left] = kept

        self.grammar.non_terminals = productive
        self.grammar.productions = updated
        self.grammar.normalize()
        self.add_step(
            "Eliminated non-productive symbols: "
            + (", ".join(sorted(removed)) if removed else "none")
            + "."
        )

    def to_chomsky_normal_form(self) -> None:
        terminal_aliases: Dict[Symbol, Symbol] = {}
        updated: Dict[Symbol, Set[Production]] = {
            left: set() for left in self.grammar.non_terminals
        }

        for left, rights in list(self.grammar.productions.items()):
            for right in rights:
                if len(right) <= 1:
                    updated[left].add(right)
                    continue

                converted = list(right)
                for index, symbol in enumerate(converted):
                    if symbol in self.grammar.terminals:
                        alias = terminal_aliases.get(symbol)
                        if alias is None:
                            alias = self._new_non_terminal(f"T_{symbol.upper()}")
                            terminal_aliases[symbol] = alias
                            updated.setdefault(alias, set()).add((symbol,))
                        converted[index] = alias
                updated[left].add(tuple(converted))

        self.grammar.productions = updated
        self.grammar.normalize()

        binarized: Dict[Symbol, Set[Production]] = {
            left: set() for left in self.grammar.non_terminals
        }

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

        self.grammar.productions = binarized
        self.grammar.normalize()
        self.add_step("Converted grammar to Chomsky Normal Form.")

    def normalize_to_cnf(self) -> Grammar:
        self.add_step("Started grammar normalization.")
        self.eliminate_epsilon_productions()
        self.eliminate_renaming()
        self.eliminate_inaccessible_symbols()
        self.eliminate_non_productive_symbols()
        self.to_chomsky_normal_form()
        return self.grammar

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

    def _expand_nullable_variants(
        self,
        right: Production,
        nullable: Set[Symbol],
    ) -> Set[Production]:
        choices: List[Sequence[Symbol]] = []
        for symbol in right:
            if symbol in nullable:
                choices.append((symbol, ""))
            else:
                choices.append((symbol,))

        variants: Set[Production] = set()
        for combination in product(*choices):
            candidate = tuple(symbol for symbol in combination if symbol)
            variants.add(candidate)
        return variants

    def _new_non_terminal(self, base: str) -> Symbol:
        while True:
            candidate = f"{base}{self._cnf_counter}"
            self._cnf_counter += 1
            if candidate not in self.grammar.non_terminals and candidate not in self.grammar.terminals:
                self.grammar.non_terminals.add(candidate)
                self.grammar.productions.setdefault(candidate, set())
                return candidate


def build_grammar(
    non_terminals: Iterable[Symbol],
    terminals: Iterable[Symbol],
    productions: Dict[Symbol, Iterable[Sequence[Symbol]]],
    start_symbol: Symbol,
) -> Grammar:
    normalized_productions: Dict[Symbol, Set[Production]] = {
        left: {tuple(right) for right in rights}
        for left, rights in productions.items()
    }
    return Grammar(
        non_terminals=set(non_terminals),
        terminals=set(terminals),
        productions=normalized_productions,
        start_symbol=start_symbol,
    )


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


def print_grammar(title: str, grammar: Grammar) -> None:
    print(title)
    print(f"VN = {{{', '.join(sorted(grammar.non_terminals))}}}")
    print(f"VT = {{{', '.join(sorted(grammar.terminals))}}}")
    print(f"Start = {grammar.start_symbol}")
    print("P:")
    for rule in grammar.format_rules():
        print(f"  {rule}")
    print()


def run_demo(grammar: Grammar) -> None:
    print_grammar("Initial grammar", grammar)

    normalizer = GrammarNormalizer(grammar)
    cnf_grammar = normalizer.normalize_to_cnf()

    print("Normalization steps:")
    for step in normalizer.step_log:
        print(step)
    print()

    print_grammar("Grammar in Chomsky Normal Form", cnf_grammar)


if __name__ == "__main__":
    run_demo(variant_6_grammar())
