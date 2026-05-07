# Parser and Abstract Syntax Tree

### Course: Formal Languages & Finite Automata
### Author: Rustem Cimendur

----

## Theory

Parsing is the stage that comes after lexical analysis. While the lexer breaks the input into tokens, the parser verifies whether those tokens follow the grammar of the language and extracts the syntactic structure of the input. In practice, this means that the parser turns a flat token stream into a hierarchical representation.

One of the most useful hierarchical representations is the **Abstract Syntax Tree (AST)**. Unlike a full parse tree, the AST keeps only the information that matters for later processing. Parentheses and some grammatical helper rules may disappear, while semantic constructs such as assignments, identifiers, literals, and operators remain explicit.

For this laboratory work, I implemented a small parser for a **logic-gate language**. The language supports assignments and boolean gate expressions using operators such as `AND`, `OR`, `NOT`, `XOR`, `NAND`, and `NOR`. The lexer uses **regular expressions** to classify tokens, and the parser builds an AST that describes the structure of a digital-logic expression in a form that is easy to inspect and extend.

## Objectives:

* Define a `TokenType` enumeration for the language tokens.
* Use regular expressions during lexical analysis to recognize token categories.
* Implement AST node structures suitable for logic-gate expressions.
* Build a parser that extracts the syntactic structure of the input and returns an AST.
* Demonstrate the result on a small logic-gate circuit description.

## Implementation Description

* **Token classification with regular expressions**: The lexer in `lab6/main.py` uses a `TokenType` enum and a list of compiled regex patterns for punctuation, boolean literals, and identifiers. Keywords such as `AND`, `OR`, `NOT`, `XOR`, `NAND`, and `NOR` are recognized after identifier matching by checking the uppercase lexeme against a keyword table.

```python
TOKEN_PATTERNS = [
    (TokenType.ASSIGN, re.compile(r"=")),
    (TokenType.SEMICOLON, re.compile(r";")),
    (TokenType.COMMA, re.compile(r",")),
    (TokenType.LPAREN, re.compile(r"\(")),
    (TokenType.RPAREN, re.compile(r"\)")),
    (TokenType.BOOLEAN, re.compile(r"(?:0|1)\b|TRUE\b|FALSE\b", re.IGNORECASE)),
    (TokenType.IDENTIFIER, re.compile(r"[A-Za-z_][A-Za-z0-9_]*")),
]
```

* **Lexer structure**: The `LogicGateLexer` processes the source text from left to right, skipping whitespace and line comments, while also tracking line and column positions for error reporting. This keeps the implementation simple and also makes syntax errors easier to localize.

```python
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
```

* **AST design**: The AST is built with Python `dataclasses`. I used a small node hierarchy: `Program` for the full input, `Assignment` for statements, `Identifier` and `BooleanLiteral` for atomic values, and `UnaryGate` / `BinaryGate` for logic operations. This representation is abstract enough to be reusable for later evaluation or circuit simulation.

```python
@dataclass
class BinaryGate(ASTNode):
    operator: str
    left: ASTNode
    right: ASTNode
```

* **Recursive-descent parser**: The `LogicGateParser` implements precedence-aware parsing. Unary `NOT` is parsed before binary gates; `AND` and `NAND` bind tighter than `XOR`, while `OR` and `NOR` are parsed at a lower level. This keeps the behavior deterministic and close to the way operator precedence is usually implemented in programming languages.

```python
def parse_expression(self) -> ASTNode:
    return self.parse_or_expression()

def parse_or_expression(self) -> ASTNode:
    node = self.parse_xor_expression()

    while self.current().token_type in self.BINARY_OR_LEVEL:
        operator = self.advance().token_type.name
        right = self.parse_xor_expression()
        node = BinaryGate(operator, node, right)

    return node
```

* **Function-style and infix gates**: The parser supports both infix expressions like `A XOR B` and function-like calls such as `AND(A, B)` or `NOR(sum_bit, NOT(carry_bit))`. This is handled in `parse_primary()` and `parse_gate_call()`, which allows the same AST classes to represent both forms.

```python
if current_token.token_type in self.FUNCTION_GATES and self.peek().token_type == TokenType.LPAREN:
    return self.parse_gate_call()
```

* **AST formatting for demonstration**: To make the result visible, I added `format_ast()`, which prints the AST as an indented tree. This is useful for debugging and also clearly demonstrates that the parser extracts syntax rather than only validating the input.

## Conclusions / Screenshots / Results

The implementation successfully tokenizes and parses a small logic-gate circuit description. The lexer recognizes identifiers, boolean literals, punctuation, and logic-gate keywords using regular expressions. The parser then builds a structured AST that preserves assignment statements and the nesting of unary and binary gate expressions.

**Command used to run the program:**

```powershell
python lab6\main.py
```

**Input used in the demo:**

```text
sum_bit = A XOR B;
carry_bit = AND(A, B);
output = NOR(sum_bit, NOT(carry_bit));
enabled = (output NAND 0) OR TRUE;
```

**Relevant output:**

```text
Tokens:
  IDENTIFIER 'sum_bit'    @ 3:5
  ASSIGN     '='          @ 3:13
  IDENTIFIER 'A'          @ 3:15
  XOR        'XOR'        @ 3:17
  IDENTIFIER 'B'          @ 3:21
  ...
  BOOLEAN    'TRUE'       @ 6:34
  SEMICOLON  ';'          @ 6:38
  EOF        ''           @ 7:5

Abstract Syntax Tree:
Program
  Assignment(sum_bit)
    BinaryGate(XOR)
      Identifier(A)
      Identifier(B)
  Assignment(carry_bit)
    BinaryGate(AND)
      Identifier(A)
      Identifier(B)
  Assignment(output)
    BinaryGate(NOR)
      Identifier(sum_bit)
      UnaryGate(NOT)
        Identifier(carry_bit)
  Assignment(enabled)
    BinaryGate(OR)
      BinaryGate(NAND)
        Identifier(output)
        BooleanLiteral(0)
      BooleanLiteral(1)
```

The result shows that the program does more than lexical analysis: it reconstructs the hierarchical structure of the logic expressions and stores it in a form that could later be evaluated, optimized, or translated into another internal representation.

## References

1. Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. *Compilers: Principles, Techniques, and Tools*.
2. Hopcroft, J. E., Motwani, R., & Ullman, J. D. *Introduction to Automata Theory, Languages, and Computation*.
3. Abstract syntax tree - Wikipedia.
