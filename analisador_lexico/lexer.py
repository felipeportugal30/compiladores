"""Analisador lexico manual para um subconjunto da linguagem Java.

O modulo nao usa expressoes regulares nem geradores de analisadores. A entrada e
percorrida por :class:`TwoBufferStream`, que simula o esquema classico de dois
buffers com os ponteiros ``begin`` e ``forward``.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch",
    "char", "class", "const", "continue", "default", "do", "double",
    "else", "enum", "extends", "final", "finally", "float", "for", "if",
    "implements", "import", "instanceof", "int", "interface", "long",
    "native", "new", "package", "private", "protected", "public",
    "return", "short", "static", "strictfp", "super", "switch",
    "synchronized", "this", "throw", "throws", "transient", "try", "void",
    "volatile", "while", "true", "false", "null",
}
OPERATORS = {
    ">>>=", "<<=", ">>=", "===", "!==",
    "++", "--", "==", "!=", "<=", ">=", "&&", "||", "+=", "-=",
    "*=", "/=", "%=", "&=", "|=", "^=", "<<", ">>", "->", "::",
    "+", "-", "*", "/", "%", "<", ">", "!", "=", "&", "|", "^", "~", "?", ":",
}
DELIMITERS = {";", ",", ".", "(", ")", "{", "}", "[", "]", "@"}
VALID_ESCAPES = {"b", "t", "n", "f", "r", '"', "'", "\\"}


@dataclass(frozen=True)
class Token:
    type: str
    lexeme: str
    attribute: str | int | float | None
    line: int
    column: int


class TwoBufferStream:

    def __init__(self, source: str, buffer_size: int = 64) -> None:
        if buffer_size < 2:
            raise ValueError("buffer_size deve ser maior ou igual a 2")
        self.source = source
        self.buffer_size = buffer_size
        self.buffers = ["", ""]
        self.buffer_blocks = [-1, -1]
        self.begin = 0
        self.forward = 0
        self._load_block(0)
        self._load_block(1)

    def _load_block(self, block: int) -> None:
        slot = block % 2
        start = block * self.buffer_size
        self.buffers[slot] = self.source[start : start + self.buffer_size]
        self.buffer_blocks[slot] = block

    def char_at(self, position: int) -> str:
        if position < 0 or position >= len(self.source):
            return ""
        block = position // self.buffer_size
        slot = block % 2
        if self.buffer_blocks[slot] != block:
            self._load_block(block)
        return self.buffers[slot][position % self.buffer_size]

    def peek(self, offset: int = 0) -> str:
        return self.char_at(self.forward + offset)

    def advance(self) -> str:
        char = self.peek()
        if char:
            self.forward += 1
        return char

    def start_lexeme(self) -> None:
        self.begin = self.forward

    def lexeme(self) -> str:
        return self.source[self.begin : self.forward]

    @property
    def at_end(self) -> bool:
        return self.forward >= len(self.source)


class Lexer:
    def __init__(self, source: str, buffer_size: int = 64) -> None:
        self.stream = TwoBufferStream(source, buffer_size)
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.symbol_table: Counter[str] = Counter()

    @staticmethod
    def _is_letter(char: str) -> bool:
        return bool(char) and ("a" <= char <= "z" or "A" <= char <= "Z" or char == "_")

    @classmethod
    def _is_identifier_part(cls, char: str) -> bool:
        return cls._is_letter(char) or (bool(char) and char.isascii() and char.isdigit())

    def _advance(self) -> str:
        char = self.stream.advance()
        if char == "\n":
            self.line += 1
            self.column = 1
        elif char:
            self.column += 1
        return char

    def _add(self, token_type: str, line: int, column: int, attribute=None) -> None:
        self.tokens.append(Token(token_type, self.stream.lexeme(), attribute, line, column))

    def tokenize(self) -> tuple[list[Token], dict[str, int]]:
        while not self.stream.at_end:
            if self.stream.peek().isspace():
                self._advance()
                continue

            self.stream.start_lexeme()
            line, column = self.line, self.column
            char = self.stream.peek()

            if self._is_letter(char):
                self._scan_identifier(line, column)
            elif char.isascii() and char.isdigit():
                self._scan_number(line, column)
            elif char == '"':
                self._scan_string(line, column)
            elif char == "'":
                self._scan_character(line, column)
            elif char == "/" and self.stream.peek(1) in {"/", "*"}:
                self._scan_comment(line, column)
            elif char in DELIMITERS:
                self._advance()
                self._add("DELIMITER", line, column, char)
            elif self._scan_operator(line, column):
                pass
            else:
                self._advance()
                self._add("ERROR", line, column, "caractere invalido")

        self.stream.start_lexeme()
        self._add("EOF", self.line, self.column)
        return self.tokens, dict(sorted(self.symbol_table.items()))

    def _scan_identifier(self, line: int, column: int) -> None:
        while self._is_identifier_part(self.stream.peek()):
            self._advance()
        lexeme = self.stream.lexeme()
        if lexeme in KEYWORDS:
            self._add("KEYWORD", line, column, lexeme)
        else:
            self.symbol_table[lexeme] += 1
            self._add("IDENTIFIER", line, column, lexeme)

    def _scan_number(self, line: int, column: int) -> None:
        while self.stream.peek().isascii() and self.stream.peek().isdigit():
            self._advance()

        if self._is_letter(self.stream.peek()):
            while self._is_identifier_part(self.stream.peek()):
                self._advance()
            self._add("ERROR", line, column, "identificador iniciado por numero")
            return

        if self.stream.peek() == "," and self.stream.peek(1).isdigit():
            self._advance()
            while self.stream.peek().isascii() and self.stream.peek().isdigit():
                self._advance()
            self._add("ERROR", line, column, "use ponto como separador decimal")
            return

        if self.stream.peek() == "." and self.stream.peek(1).isdigit():
            self._advance()
            while self.stream.peek().isascii() and self.stream.peek().isdigit():
                self._advance()
            self._add("FLOAT_LITERAL", line, column, float(self.stream.lexeme()))
            return

        self._add("INTEGER_LITERAL", line, column, int(self.stream.lexeme()))

    def _scan_string(self, line: int, column: int) -> None:
        self._advance()  # aspas iniciais
        valid = True
        reason = "string nao terminada"
        while not self.stream.at_end and self.stream.peek() not in {'"', "\n", "\r"}:
            if self.stream.peek() == "\\":
                self._advance()
                if self.stream.at_end:
                    break
                if self.stream.peek() not in VALID_ESCAPES:
                    valid, reason = False, "escape invalido em string"
            self._advance()
        if self.stream.peek() == '"':
            self._advance()
            if valid:
                self._add("STRING_LITERAL", line, column, self._decode_quoted(self.stream.lexeme()))
            else:
                self._add("ERROR", line, column, reason)
        else:
            self._add("ERROR", line, column, "string nao terminada")

    def _scan_character(self, line: int, column: int) -> None:
        self._advance()  # aspas iniciais
        valid = True
        if self.stream.peek() in {"", "\n", "\r", "'"}:
            valid = False
        elif self.stream.peek() == "\\":
            self._advance()
            if self.stream.peek() not in VALID_ESCAPES:
                valid = False
            if self.stream.peek():
                self._advance()
        else:
            self._advance()

        if self.stream.peek() == "'":
            self._advance()
        else:
            valid = False
            while not self.stream.at_end and self.stream.peek() not in {"'", "\n", "\r"}:
                self._advance()
            if self.stream.peek() == "'":
                self._advance()

        if valid:
            self._add("CHAR_LITERAL", line, column, self._decode_quoted(self.stream.lexeme()))
        else:
            self._add("ERROR", line, column, "literal de caractere invalido")

    def _scan_comment(self, line: int, column: int) -> None:
        self._advance()
        kind = self._advance()
        if kind == "/":
            while not self.stream.at_end and self.stream.peek() not in {"\n", "\r"}:
                self._advance()
            return
        while not self.stream.at_end:
            if self.stream.peek() == "*" and self.stream.peek(1) == "/":
                self._advance()
                self._advance()
                return
            self._advance()
        self._add("ERROR", line, column, "comentario de bloco nao terminado")

    def _scan_operator(self, line: int, column: int) -> bool:
        for size in (4, 3, 2, 1):
            candidate = "".join(self.stream.peek(i) for i in range(size))
            if candidate in OPERATORS:
                for _ in range(size):
                    self._advance()
                if candidate in {"===", "!=="}:
                    self._add("ERROR", line, column, "operador invalido em Java")
                else:
                    self._add("OPERATOR", line, column, candidate)
                return True
        return False

    @staticmethod
    def _decode_quoted(lexeme: str) -> str:
        content = lexeme[1:-1]
        replacements = {
            "\\b": "\b", "\\t": "\t", "\\n": "\n", "\\f": "\f",
            "\\r": "\r", '\\"': '"', "\\'": "'", "\\\\": "\\",
        }
        for escaped, value in replacements.items():
            content = content.replace(escaped, value)
        return content


def analyze(source: str, buffer_size: int = 64) -> tuple[list[Token], dict[str, int]]:
    return Lexer(source, buffer_size).tokenize()
