# Lexical Analysis: A SQL-Select Lexer Implementation

### Course: Formal Languages & Finite Automata

### Author: Rustem Cimendur

---

## Theory

Lexical analysis is the foundational phase of processing a formal language. It acts as a text scanner, reading a raw stream of characters (source code) and grouping them into meaningful sequences called **lexemes**. Each lexeme is then categorized into a **token**, which represents its grammatical role in the language (e.g., a keyword, an identifier, or a literal).

The distinction between a lexeme and a token is critical: a lexeme is the literal substring found in the source text (such as `"25.5"` or `"SELECT"`), while the token is an abstract data structure containing the type of the lexeme, its processed value (a floating-point number or a standardized uppercase keyword), and metadata like its line and column position.

To perform this extraction, lexers often rely on principles derived from Deterministic Finite Automata (DFA). The lexer reads characters one by one, changing its internal state until it reaches a terminal state that resolves into a recognized token or an error state for illegal characters.

## Objectives:

* Understand the fundamental concepts of lexical analysis and its role in processing formal languages.
* Get familiar with the inner workings of a custom lexer/scanner by managing state, character iteration, and token generation.
* Implement a custom, functional lexer for a subset of the SQL language, demonstrating the ability to parse complex tokens like floating-point numbers, multi-character operators, and strings.

## Implementation description

The lexer is implemented in Python using an object-oriented approach. It relies on a stateful, lookahead iterator design to process the source text character by character.

**1. Token Representation**
The `Token` class encapsulates both the raw text and its parsed meaning. It stores the `TokenType` (via Python's `Enum`), the raw `lexeme`, the processed `literal` value, and positional tracking for accurate error reporting.

* **Why this is better:** By explicitly separating the raw string (`lexeme`) from the parsed data (`literal`), the downstream parser doesn't have to re-evaluate data types.
* **Trade-offs:** Storing both representations slightly increases the memory footprint per token, but the improvement in debugging clarity and structural separation is worth the cost.

```python
class Token:
    def __init__(self, token_type, lexeme, literal, line, column):
        self.type = token_type      
        self.lexeme = lexeme        
        self.literal = literal      
        self.line = line
        self.column = column

```

**2. The Dispatcher (`next_token`)**
Instead of using a massive, nested regular expression to parse the entire text, the lexer uses a "Dispatcher" pattern. It peeks at the current character and routes the execution to a specific helper method (like `read_number` or `read_string`).

* **Why this is better:** It provides granular control over state transitions. If a string is left unclosed, the manual iterator can stop cleanly and report the exact column where the error began, behaving exactly like a formal Finite State Machine.
* **Trade-offs:** The code is much more verbose than a Regex-based approach, requiring manual pointer management to ensure characters aren't accidentally skipped or double-read.

```python
    def next_token(self):
        self.skip_whitespace()
        start_col = self.column
        char = self.peek()

        if char is None:
            return Token(TokenType.EOF, "", None, self.line, start_col)

        if char.isalpha() or char == '_':
            return self.read_identifier()
        if char.isdigit():
            return self.read_number()
        # ... operator dispatching logic ...

```

**3. Parsing Numbers (Integers and Floats)**
To satisfy the requirement of parsing both integers and floats, the `read_number` method consumes digits until it hits a non-digit. If it encounters a period (`.`), it transitions to a floating-point parsing state and continues consuming digits.

* **Why this is better:** It handles the entire numeric parsing logic in a single, isolated pass, accurately distinguishing between a standard integer and a floating-point literal, directly returning the respective Python data type.
* **Trade-offs:** This specific implementation assumes a standard `[0-9]+.[0-9]+` format and does not currently support scientific notation (e.g., `1e-5`), which would require expanding the state machine.

```python
    def read_number(self):
        start_col = self.column
        lexeme = ""
        is_float = False

        while self.peek() is not None and self.peek().isdigit():
            lexeme += self.advance()

        if self.peek() == '.':
            is_float = True
            lexeme += self.advance()
            while self.peek() is not None and self.peek().isdigit():
                lexeme += self.advance()

        if is_float:
            return Token(TokenType.FLOAT, lexeme, float(lexeme), self.line, start_col)
        return Token(TokenType.INTEGER, lexeme, int(lexeme), self.line, start_col)

```

## Conclusions / Screenshots / Results

The implementation successfully demonstrates a working lexical analyzer for a SQL-like DSL. Testing the lexer with a complex query shows that it accurately identifies keywords (case-insensitively), isolates identifiers, correctly parses floating-point numbers, and tracks line and column data.

**Input Query:**

```sql
SeLecT id, name, salary 
FROM employees 
WHERE age >= 25 AND rating = 4.5
LIMIT 10;

```

**Output:**

```text
Token(SELECT     | Lexeme: 'SeLecT'   | Val: None | Pos: 2:5)
Token(IDENTIFIER | Lexeme: 'id'       | Val: id | Pos: 2:12)
Token(COMMA      | Lexeme: ','        | Val: None | Pos: 2:14)
Token(IDENTIFIER | Lexeme: 'name'     | Val: name | Pos: 2:16)
...
Token(IDENTIFIER | Lexeme: 'age'      | Val: age | Pos: 4:11)
Token(GTE        | Lexeme: '>='       | Val: None | Pos: 4:15)
Token(INTEGER    | Lexeme: '25'       | Val: 25 | Pos: 4:18)
...
Token(FLOAT      | Lexeme: '4.5'      | Val: 4.5 | Pos: 4:30)
Token(ILLEGAL    | Lexeme: ';'        | Val: None | Pos: 5:13)
Token(EOF        | Lexeme: ''         | Val: None | Pos: 6:5)

```

*(Notice that the `;` character was accurately flagged as an ILLEGAL token, as it was not defined in our strict grammar alphabet, proving the error-handling works).*

## References

[1] [A sample of a lexer implementation](https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/LangImpl01.html)

[2] [Lexical analysis - Wikipedia](https://en.wikipedia.org/wiki/Lexical_analysis)
