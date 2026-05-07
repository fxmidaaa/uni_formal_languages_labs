from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import List


class TokenType(enum.Enum):
    IDENTIFIER = "IDENTIFIER"
    BOOLEAN = "BOOLEAN"

    ASSIGN = "ASSIGN"
    SEMICOLON = "SEMICOLON"
    COMMA = "COMMA"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"

    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    XOR = "XOR"
    NAND = "NAND"
    NOR = "NOR"

    EOF = "EOF"


KEYWORDS = {
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "NOT": TokenType.NOT,
    "XOR": TokenType.XOR,
    "NAND": TokenType.NAND,
    "NOR": TokenType.NOR,
}


BOOLEAN_LITERALS = {
    "0": False,
    "1": True,
    "FALSE": False,
    "TRUE": True,
}


TOKEN_PATTERNS = [
    (TokenType.ASSIGN, re.compile(r"=")),
    (TokenType.SEMICOLON, re.compile(r";")),
    (TokenType.COMMA, re.compile(r",")),
    (TokenType.LPAREN, re.compile(r"\(")),
    (TokenType.RPAREN, re.compile(r"\)")),
    (TokenType.BOOLEAN, re.compile(r"(?:0|1)\b|TRUE\b|FALSE\b", re.IGNORECASE)),
    (TokenType.IDENTIFIER, re.compile(r"[A-Za-z_][A-Za-z0-9_]*")),
]


WHITESPACE_PATTERN = re.compile(r"\s+")
COMMENT_PATTERN = re.compile(r"(?:#|//)[^\n]*")


class LexerError(Exception):
    pass


class ParserError(Exception):
    pass


@dataclass(frozen=True)
class Token:
    token_type: TokenType
    lexeme: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.token_type.name:<10} {self.lexeme!r:<12} @ {self.line}:{self.column}"


class LogicGateLexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.position < len(self.source):
            if self._consume_ignored_text():
                continue

            token = self._next_token()
            if token is None:
                char = self.source[self.position]
                raise LexerError(
                    f"Unexpected character {char!r} at line {self.line}, column {self.column}."
                )
            tokens.append(token)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    def _consume_ignored_text(self) -> bool:
        for pattern in (WHITESPACE_PATTERN, COMMENT_PATTERN):
            match = pattern.match(self.source, self.position)
            if match:
                self._advance(match.group(0))
                return True
        return False

    def _next_token(self) -> Token | None:
        for token_type, pattern in TOKEN_PATTERNS:
            match = pattern.match(self.source, self.position)
            if not match:
                continue

            lexeme = match.group(0)
            line = self.line
            column = self.column
            self._advance(lexeme)

            if token_type == TokenType.IDENTIFIER:
                upper_lexeme = lexeme.upper()
                if upper_lexeme in KEYWORDS:
                    return Token(KEYWORDS[upper_lexeme], lexeme, line, column)
                if upper_lexeme in BOOLEAN_LITERALS:
                    return Token(TokenType.BOOLEAN, lexeme, line, column)

            return Token(token_type, lexeme, line, column)

        return None

    def _advance(self, text: str) -> None:
        self.position += len(text)
        for char in text:
            if char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1


class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    statements: List["Assignment"]


@dataclass
class Assignment(ASTNode):
    name: str
    expression: ASTNode


@dataclass
class Identifier(ASTNode):
    name: str


@dataclass
class BooleanLiteral(ASTNode):
    value: bool


@dataclass
class UnaryGate(ASTNode):
    operator: str
    operand: ASTNode


@dataclass
class BinaryGate(ASTNode):
    operator: str
    left: ASTNode
    right: ASTNode


class LogicGateParser:
    BINARY_AND_LEVEL = {TokenType.AND, TokenType.NAND}
    BINARY_OR_LEVEL = {TokenType.OR, TokenType.NOR}
    FUNCTION_GATES = {
        TokenType.AND,
        TokenType.OR,
        TokenType.XOR,
        TokenType.NAND,
        TokenType.NOR,
    }

    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.position = 0

    def parse(self) -> Program:
        statements: List[Assignment] = []
        while self.current().token_type != TokenType.EOF:
            statements.append(self.parse_statement())
        return Program(statements)

    def parse_statement(self) -> Assignment:
        name_token = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.ASSIGN)
        expression = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        return Assignment(name_token.lexeme, expression)

    def parse_expression(self) -> ASTNode:
        return self.parse_or_expression()

    def parse_or_expression(self) -> ASTNode:
        node = self.parse_xor_expression()

        while self.current().token_type in self.BINARY_OR_LEVEL:
            operator = self.advance().token_type.name
            right = self.parse_xor_expression()
            node = BinaryGate(operator, node, right)

        return node

    def parse_xor_expression(self) -> ASTNode:
        node = self.parse_and_expression()

        while self.match(TokenType.XOR):
            right = self.parse_and_expression()
            node = BinaryGate("XOR", node, right)

        return node

    def parse_and_expression(self) -> ASTNode:
        node = self.parse_unary_expression()

        while self.current().token_type in self.BINARY_AND_LEVEL:
            operator = self.advance().token_type.name
            right = self.parse_unary_expression()
            node = BinaryGate(operator, node, right)

        return node

    def parse_unary_expression(self) -> ASTNode:
        if self.match(TokenType.NOT):
            return UnaryGate("NOT", self.parse_unary_expression())
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        current_token = self.current()

        if current_token.token_type == TokenType.BOOLEAN:
            token = self.advance()
            return BooleanLiteral(BOOLEAN_LITERALS[token.lexeme.upper()])

        if current_token.token_type == TokenType.IDENTIFIER:
            return Identifier(self.advance().lexeme)

        if current_token.token_type in self.FUNCTION_GATES and self.peek().token_type == TokenType.LPAREN:
            return self.parse_gate_call()

        if self.match(TokenType.LPAREN):
            expression = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expression

        raise ParserError(
            "Expected an identifier, boolean literal, gate call, or parenthesized expression "
            f"at line {current_token.line}, column {current_token.column}."
        )

    def parse_gate_call(self) -> ASTNode:
        gate_token = self.advance()
        self.expect(TokenType.LPAREN)

        arguments = [self.parse_expression()]
        while self.match(TokenType.COMMA):
            arguments.append(self.parse_expression())

        self.expect(TokenType.RPAREN)
        return self._build_gate_node(gate_token, arguments)

    def _build_gate_node(self, gate_token: Token, arguments: List[ASTNode]) -> ASTNode:
        operator = gate_token.token_type.name
        expected_arity = 1 if gate_token.token_type == TokenType.NOT else 2

        if len(arguments) != expected_arity:
            raise ParserError(
                f"{operator} expects {expected_arity} argument(s), got {len(arguments)} "
                f"at line {gate_token.line}, column {gate_token.column}."
            )

        if expected_arity == 1:
            return UnaryGate(operator, arguments[0])
        return BinaryGate(operator, arguments[0], arguments[1])

    def current(self) -> Token:
        return self.tokens[self.position]

    def peek(self) -> Token:
        next_index = min(self.position + 1, len(self.tokens) - 1)
        return self.tokens[next_index]

    def advance(self) -> Token:
        token = self.current()
        if self.position < len(self.tokens) - 1:
            self.position += 1
        return token

    def match(self, token_type: TokenType) -> bool:
        if self.current().token_type == token_type:
            self.advance()
            return True
        return False

    def expect(self, token_type: TokenType) -> Token:
        token = self.current()
        if token.token_type != token_type:
            raise ParserError(
                f"Expected {token_type.name}, found {token.token_type.name} "
                f"at line {token.line}, column {token.column}."
            )
        return self.advance()


def format_ast(node: ASTNode, indent: int = 0) -> str:
    prefix = "  " * indent

    if isinstance(node, Program):
        lines = [f"{prefix}Program"]
        for statement in node.statements:
            lines.append(format_ast(statement, indent + 1))
        return "\n".join(lines)

    if isinstance(node, Assignment):
        lines = [f"{prefix}Assignment({node.name})", format_ast(node.expression, indent + 1)]
        return "\n".join(lines)

    if isinstance(node, Identifier):
        return f"{prefix}Identifier({node.name})"

    if isinstance(node, BooleanLiteral):
        return f"{prefix}BooleanLiteral({int(node.value)})"

    if isinstance(node, UnaryGate):
        lines = [f"{prefix}UnaryGate({node.operator})", format_ast(node.operand, indent + 1)]
        return "\n".join(lines)

    if isinstance(node, BinaryGate):
        lines = [
            f"{prefix}BinaryGate({node.operator})",
            format_ast(node.left, indent + 1),
            format_ast(node.right, indent + 1),
        ]
        return "\n".join(lines)

    raise TypeError(f"Unsupported AST node: {type(node)!r}")


def print_tokens(tokens: List[Token]) -> None:
    print("Tokens:")
    for token in tokens:
        print(f"  {token}")
    print()


def main() -> None:
    source_code = """
    # Logic-gate circuit description
    sum_bit = A XOR B;
    carry_bit = AND(A, B);
    output = NOR(sum_bit, NOT(carry_bit));
    enabled = (output NAND 0) OR TRUE;
    """

    lexer = LogicGateLexer(source_code)
    tokens = lexer.tokenize()
    parser = LogicGateParser(tokens)
    ast = parser.parse()

    print("Input:")
    print(source_code.strip())
    print()
    print_tokens(tokens)
    print("Abstract Syntax Tree:")
    print(format_ast(ast))


if __name__ == "__main__":
    main()
