from enum import Enum, auto

class TokenType(Enum):
    """
    Enumeration of all possible token types in the Trisynth language.
    """
    # --- Literals ---
    INTEGER = auto()        # 123
    FLOAT = auto()          # 12.34
    IDENTIFIER = auto()     # variable_name
    STRING = auto()         # "string literal" (Reserved for future)
    CHAR = auto()           # 'c'

    # --- Keywords (Types) ---
    KW_INT = auto()         # int
    KW_UINT32 = auto()      # uint32
    KW_FLOAT = auto()       # float
    KW_BOOL = auto()        # bool
    KW_CHAR = auto()        # char
    KW_VOID = auto()        # void

    # --- Keywords (Control Flow) ---
    KW_IF = auto()          # if
    KW_ELSE = auto()        # else
    KW_WHILE = auto()       # while
    KW_FOR = auto()         # for
    KW_BREAK = auto()       # break
    KW_CONTINUE = auto()    # continue
    KW_RETURN = auto()      # return

    # --- Keywords (I/O & Built-ins) ---
    KW_PRINT = auto()       # print
    KW_READ_INT = auto()    # readInt
    KW_TRUE = auto()        # true
    KW_FALSE = auto()       # false

    # --- Operators (Arithmetic) ---
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    MODULO = auto()         # %
    INCREMENT = auto()      # ++
    DECREMENT = auto()      # --

    # --- Operators (Relational) ---
    EQ = auto()             # ==
    NEQ = auto()            # !=
    LT = auto()             # <
    GT = auto()             # >
    LTE = auto()            # <=
    GTE = auto()            # >=

    # --- Operators (Logical) ---
    AND = auto()            # &&
    OR = auto()             # ||
    NOT = auto()            # !

    # --- Assignment ---
    ASSIGN = auto()         # =

    # --- Delimiters ---
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    SEMICOLON = auto()      # ;
    COMMA = auto()          # ,

    # --- Special ---
    EOF = auto()            # End of File
    ERROR = auto()          # Lexical Error (Unknown character)


class Token:
    """
    Represents a single lexical unit (token) in the source code.
    """
    def __init__(self, type: TokenType, value: str, line: int, column: int):
        """
        Initialize a new Token.

        Args:
            type (TokenType): The type of the token.
            value (str): The actual text content of the token (lexeme).
            line (int): The line number where the token starts (1-based).
            column (int): The column number where the token starts (1-based).
        """
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        """
        String representation of the token for debugging purposes.
        Format: Token(Type, 'Value', Line:Col)
        """
        return f"Token({self.type.name}, {repr(self.value)}, {self.line}:{self.column})"

    def __eq__(self, other):
        """
        Equality check for testing convenience.
        """
        if not isinstance(other, Token):
            return False
        return (self.type == other.type and
                self.value == other.value and
                self.line == other.line and
                self.column == other.column)
