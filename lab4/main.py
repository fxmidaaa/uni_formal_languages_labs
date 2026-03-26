from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Set
import sys


MAX_UNBOUNDED_REPETITIONS = 5


class RegexSyntaxError(ValueError):
    pass


class StepRecorder:
    def __init__(self) -> None:
        self.steps: List[str] = []

    def add(self, message: str) -> None:
        self.steps.append(f"{len(self.steps) + 1}. {message}")


@dataclass(frozen=True)
class RegexNode:
    pass


@dataclass(frozen=True)
class EpsilonNode(RegexNode):
    pass


@dataclass(frozen=True)
class LiteralNode(RegexNode):
    value: str


@dataclass(frozen=True)
class ConcatNode(RegexNode):
    parts: tuple[RegexNode, ...]


@dataclass(frozen=True)
class AlternationNode(RegexNode):
    options: tuple[RegexNode, ...]


@dataclass(frozen=True)
class RepeatNode(RegexNode):
    node: RegexNode
    min_times: int
    max_times: int
    label: str


def render(node: RegexNode) -> str:
    if isinstance(node, EpsilonNode):
        return "eps"
    if isinstance(node, LiteralNode):
        return node.value
    if isinstance(node, ConcatNode):
        return " ".join(render_concat_part(part) for part in node.parts)
    if isinstance(node, AlternationNode):
        return "(" + "|".join(render(option) for option in node.options) + ")"
    if isinstance(node, RepeatNode):
        base = render_repeat_base(node.node)
        return f"{base}{node.label}"
    raise TypeError(f"Unsupported node type: {type(node)!r}")


def render_concat_part(node: RegexNode) -> str:
    if isinstance(node, AlternationNode):
        return render(node)
    return render(node)


def render_repeat_base(node: RegexNode) -> str:
    if isinstance(node, LiteralNode):
        return render(node)
    if isinstance(node, EpsilonNode):
        return render(node)
    if isinstance(node, AlternationNode):
        return render(node)
    return f"({render(node)})"


class RegexParser:
    def __init__(self, source: str, recorder: StepRecorder | None = None) -> None:
        self.source = source.strip()
        self.position = 0
        self.recorder = recorder

    def parse(self) -> RegexNode:
        if self.recorder is not None:
            self.recorder.add(
                f"Received regex '{self.source}' and ignored whitespace during parsing."
            )

        node = self.parse_expression()
        self.skip_whitespace()
        if self.position != len(self.source):
            raise RegexSyntaxError(
                f"Unexpected symbol '{self.source[self.position]}' at position {self.position + 1}."
            )

        if self.recorder is not None:
            self.recorder.add(f"Built syntax tree for '{render(node)}'.")
        return node

    def parse_expression(self) -> RegexNode:
        branches = [self.parse_term()]

        while self.peek() == "|":
            self.advance()
            branches.append(self.parse_term())

        if len(branches) == 1:
            return branches[0]

        node = AlternationNode(tuple(branches))
        if self.recorder is not None:
            self.recorder.add(
                f"Combined {len(branches)} branches into alternation '{render(node)}'."
            )
        return node

    def parse_term(self) -> RegexNode:
        factors: List[RegexNode] = []

        while True:
            current = self.peek()
            if current is None or current in "|)":
                break
            factors.append(self.parse_factor())

        if not factors:
            return EpsilonNode()
        if len(factors) == 1:
            return factors[0]

        node = ConcatNode(tuple(factors))
        if self.recorder is not None:
            self.recorder.add(
                f"Collapsed {len(factors)} adjacent parts into concatenation '{render(node)}'."
            )
        return node

    def parse_factor(self) -> RegexNode:
        node = self.parse_atom()
        current = self.peek()

        if current == "?":
            self.advance()
            repeated = RepeatNode(node=node, min_times=0, max_times=1, label="?")
            if self.recorder is not None:
                self.recorder.add(f"Applied '?' to '{render(node)}'.")
            return repeated

        if current == "*":
            self.advance()
            repeated = RepeatNode(
                node=node,
                min_times=0,
                max_times=MAX_UNBOUNDED_REPETITIONS,
                label="*",
            )
            if self.recorder is not None:
                self.recorder.add(
                    f"Applied '*' to '{render(node)}' with limit {MAX_UNBOUNDED_REPETITIONS}."
                )
            return repeated

        if current == "+":
            self.advance()
            repeated = RepeatNode(
                node=node,
                min_times=1,
                max_times=MAX_UNBOUNDED_REPETITIONS,
                label="+",
            )
            if self.recorder is not None:
                self.recorder.add(
                    f"Applied '+' to '{render(node)}' with limit {MAX_UNBOUNDED_REPETITIONS}."
                )
            return repeated

        if current == "^":
            self.advance()
            postfix = self.peek()
            if postfix == "*":
                self.advance()
                repeated = RepeatNode(
                    node=node,
                    min_times=0,
                    max_times=MAX_UNBOUNDED_REPETITIONS,
                    label="^*",
                )
                if self.recorder is not None:
                    self.recorder.add(
                        f"Applied '^*' to '{render(node)}' with limit {MAX_UNBOUNDED_REPETITIONS}."
                    )
                return repeated

            if postfix == "+":
                self.advance()
                repeated = RepeatNode(
                    node=node,
                    min_times=1,
                    max_times=MAX_UNBOUNDED_REPETITIONS,
                    label="^+",
                )
                if self.recorder is not None:
                    self.recorder.add(
                        f"Applied '^+' to '{render(node)}' with limit {MAX_UNBOUNDED_REPETITIONS}."
                    )
                return repeated

            count = self.read_number()
            repeated = RepeatNode(
                node=node,
                min_times=count,
                max_times=count,
                label=f"^{count}",
            )
            if self.recorder is not None:
                self.recorder.add(f"Applied exact repetition '^{count}' to '{render(node)}'.")
            return repeated

        return node

    def parse_atom(self) -> RegexNode:
        current = self.peek()
        if current is None:
            raise RegexSyntaxError("Unexpected end of regex.")

        if current == "(":
            self.advance()
            if self.recorder is not None:
                self.recorder.add("Started grouped subexpression.")
            node = self.parse_expression()
            if self.peek() != ")":
                raise RegexSyntaxError("Missing closing ')'.")
            self.advance()
            if self.recorder is not None:
                self.recorder.add(f"Closed group '{render(node)}'.")
            return node

        if current == "\\":
            self.advance()
            escaped = self.peek()
            if escaped is None:
                raise RegexSyntaxError("Dangling escape at the end of the regex.")
            self.advance()
            node = LiteralNode(escaped)
            if self.recorder is not None:
                self.recorder.add(f"Read escaped literal '{escaped}'.")
            return node

        if current in "|)*+?^":
            raise RegexSyntaxError(
                f"Unexpected symbol '{current}' at position {self.position + 1}."
            )

        self.advance()
        node = LiteralNode(current)
        if self.recorder is not None:
            self.recorder.add(f"Read literal '{current}'.")
        return node

    def read_number(self) -> int:
        self.skip_whitespace()
        start = self.position
        while self.position < len(self.source) and self.source[self.position].isdigit():
            self.position += 1

        if start == self.position:
            raise RegexSyntaxError("Expected a number after '^'.")

        return int(self.source[start:self.position])

    def peek(self) -> str | None:
        self.skip_whitespace()
        if self.position >= len(self.source):
            return None
        return self.source[self.position]

    def advance(self) -> None:
        self.position += 1

    def skip_whitespace(self) -> None:
        while self.position < len(self.source) and self.source[self.position].isspace():
            self.position += 1


def repeat_words(words: Sequence[str], count: int) -> Set[str]:
    if count == 0:
        return {""}

    result: Set[str] = {""}
    for _ in range(count):
        result = {
            prefix + suffix
            for prefix in result
            for suffix in words
        }
    return result


def expand_node(
    node: RegexNode,
    recorder: StepRecorder | None = None,
) -> Set[str]:
    if isinstance(node, EpsilonNode):
        if recorder is not None:
            recorder.add("Expanded epsilon to the empty string.")
        return {""}

    if isinstance(node, LiteralNode):
        if recorder is not None:
            recorder.add(f"Expanded literal '{node.value}' to one word.")
        return {node.value}

    if isinstance(node, AlternationNode):
        result: Set[str] = set()
        if recorder is not None:
            recorder.add(f"Resolving alternation '{render(node)}'.")
        for index, option in enumerate(node.options, start=1):
            if recorder is not None:
                recorder.add(
                    f"Processing alternation branch {index}/{len(node.options)}: '{render(option)}'."
                )
            result.update(expand_node(option, recorder))
        if recorder is not None:
            recorder.add(
                f"Alternation '{render(node)}' produced {len(result)} distinct words."
            )
        return result

    if isinstance(node, ConcatNode):
        combined: Set[str] = {""}
        if recorder is not None:
            recorder.add(f"Resolving concatenation '{render(node)}'.")
        for index, part in enumerate(node.parts, start=1):
            part_words = expand_node(part, recorder)
            combined = {
                prefix + suffix
                for prefix in combined
                for suffix in part_words
            }
            if recorder is not None:
                recorder.add(
                    f"After concatenation part {index}/{len(node.parts)}, there are {len(combined)} partial words."
                )
        return combined

    if isinstance(node, RepeatNode):
        base_words = sorted(expand_node(node.node, recorder))
        result: Set[str] = set()
        if recorder is not None:
            recorder.add(
                f"Resolving repetition '{render(node)}' for counts {node.min_times}..{node.max_times}."
            )
        for count in range(node.min_times, node.max_times + 1):
            repeated_words = repeat_words(base_words, count)
            result.update(repeated_words)
            if recorder is not None:
                recorder.add(
                    f"Repetition count {count} produced {len(repeated_words)} words."
                )
        if recorder is not None:
            recorder.add(
                f"Repetition '{render(node)}' produced {len(result)} distinct words."
            )
        return result

    raise TypeError(f"Unsupported node type: {type(node)!r}")


def sort_words(words: Iterable[str]) -> List[str]:
    return sorted(set(words), key=lambda word: (len(word), word))


def generate_words(regex: str) -> List[str]:
    syntax_tree = RegexParser(regex).parse()
    return sort_words(expand_node(syntax_tree))


def generate_words_for_many(regexes: Sequence[str]) -> dict[str, List[str]]:
    return {regex: generate_words(regex) for regex in regexes}


def processing_steps(regex: str) -> List[str]:
    recorder = StepRecorder()
    syntax_tree = RegexParser(regex, recorder).parse()
    expand_node(syntax_tree, recorder)
    return recorder.steps


def print_report(regexes: Sequence[str]) -> None:
    generated = generate_words_for_many(regexes)

    print(f"Unbounded quantifiers use limit = {MAX_UNBOUNDED_REPETITIONS}\n")

    for regex in regexes:
        words = generated[regex]
        print(f"Regex: {regex}")
        print(f"Total valid words: {len(words)}")
        print(f"Example valid word: {words[0] if words else '<empty>'}")
        preview_limit = 20
        print("Generated words:")
        preview_words = words[:preview_limit]
        for word in preview_words:
            shown = word if word else "eps"
            print(f"  {shown}")
        if len(words) > preview_limit:
            print(f"  ... {len(words) - preview_limit} more words omitted from the preview")
        print("\nProcessing sequence:")
        for step in processing_steps(regex):
            print(f"  {step}")
        print()


EXAMPLE_REGEXES = [
    "M?N^2(O|P)^3Q^*R^+",
    "(X|Y|Z)^3 8^+(9|0)",
    "(H|I)(J|K)L*N?",
]


if __name__ == "__main__":
    regexes = sys.argv[1:] if len(sys.argv) > 1 else EXAMPLE_REGEXES
    print_report(regexes)
