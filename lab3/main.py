import enum

# 1. Define Token Types
class TokenType(enum.Enum):
    # Keywords
    SELECT = "SELECT"
    FROM = "FROM"
    WHERE = "WHERE"
    AND = "AND"
    OR = "OR"
    LIMIT = "LIMIT"
    
    # Literals
    IDENTIFIER = "IDENTIFIER"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    
    # Operators
    EQ = "="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    NEQ = "!="
    
    # Punctuation
    COMMA = ","
    ASTERISK = "*"
    LPAREN = "("
    RPAREN = ")"
    
    # Special
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"

# 2. The Token Class
class Token:
    def __init__(self, token_type, lexeme, literal, line, column):
        self.type = token_type      # The category (e.g., TokenType.FLOAT)
        self.lexeme = lexeme        # The raw text (e.g., "12.5")
        self.literal = literal      # The processed value (e.g., the actual float 12.5)
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name: <10} | Lexeme: '{self.lexeme: <8}' | Val: {self.literal} | Pos: {self.line}:{self.column})"

# 3. The Lexer
class SQLLexer:
    KEYWORDS = {"SELECT", "FROM", "WHERE", "AND", "OR", "LIMIT"}

    def __init__(self, source_code):
        self.source = source_code
        self.pos = 0
        self.line = 1
        self.column = 1

    def advance(self):
        # Moves the pointer forward and returns the consumed character.
        if self.pos >= len(self.source):
            return None
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def peek(self):
        # Looks at the current character without consuming it.
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def skip_whitespace(self):
        while self.peek() is not None and self.peek().isspace():
            self.advance()

    def next_token(self):
        # The core dispatcher method.
        self.skip_whitespace()
        
        start_col = self.column
        char = self.peek()

        if char is None:
            return Token(TokenType.EOF, "", None, self.line, start_col)

        # Dispatch based on the first character
        if char.isalpha() or char == '_':
            return self.read_identifier()
        if char.isdigit():
            return self.read_number()
        if char == "'":
            return self.read_string()

        # Handle operators and punctuation
        self.advance() # Consume the character

        if char == '=':
            return Token(TokenType.EQ, "=", None, self.line, start_col)
        elif char == '>':
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.GTE, ">=", None, self.line, start_col)
            return Token(TokenType.GT, ">", None, self.line, start_col)
        elif char == '<':
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.LTE, "<=", None, self.line, start_col)
            elif self.peek() == '>': # SQL alternative for !=
                self.advance()
                return Token(TokenType.NEQ, "<>", None, self.line, start_col)
            return Token(TokenType.LT, "<", None, self.line, start_col)
        elif char == '!':
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.NEQ, "!=", None, self.line, start_col)
            return Token(TokenType.ILLEGAL, char, None, self.line, start_col)
        elif char == ',':
            return Token(TokenType.COMMA, ",", None, self.line, start_col)
        elif char == '*':
            return Token(TokenType.ASTERISK, "*", None, self.line, start_col)
        elif char == '(':
            return Token(TokenType.LPAREN, "(", None, self.line, start_col)
        elif char == ')':
            return Token(TokenType.RPAREN, ")", None, self.line, start_col)
        
        # If it matches nothing, it's an illegal character
        return Token(TokenType.ILLEGAL, char, None, self.line, start_col)

    def read_identifier(self):
        start_col = self.column
        lexeme = ""
        while self.peek() is not None and (self.peek().isalnum() or self.peek() == '_'):
            lexeme += self.advance()
        
        upper_lexeme = lexeme.upper()
        if upper_lexeme in self.KEYWORDS:
            # It's a keyword
            token_type = getattr(TokenType, upper_lexeme)
            return Token(token_type, lexeme, None, self.line, start_col)
        
        # It's a standard identifier
        return Token(TokenType.IDENTIFIER, lexeme, lexeme, self.line, start_col)

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

    def read_string(self):
        start_col = self.column
        self.advance() # Consume opening quote
        lexeme = ""
        
        while self.peek() is not None and self.peek() != "'":
            lexeme += self.advance()
            
        if self.peek() == "'":
            self.advance() # Consume closing quote
        else:
            # Handle unclosed string error gracefully
            return Token(TokenType.ILLEGAL, f"'{lexeme}", "Unclosed String", self.line, start_col)
            
        return Token(TokenType.STRING, f"'{lexeme}'", lexeme, self.line, start_col)
    
if __name__ == "__main__":
    test_query = """
    SeLecT id, name, salary 
    FROM employees 
    WHERE age >= 25 AND rating = 4.5
    LIMIT 10;
    """
    
    lexer = SQLLexer(test_query)
    
    print("Extracting Tokens...\n")
    while True:
        tok = lexer.next_token()
        print(tok)
        if tok.type == TokenType.EOF:
            break