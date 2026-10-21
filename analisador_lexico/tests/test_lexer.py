import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from lexer import TwoBufferStream, analyze


class TwoBufferTests(unittest.TestCase):
    def test_crosses_multiple_buffer_boundaries(self):
        stream = TwoBufferStream("abcdefghijkl", buffer_size=3)
        result = ""

        while not stream.at_end:
            result += stream.advance()

        self.assertEqual(result, "abcdefghijkl")
        self.assertEqual(stream.forward, 12)

    def test_lexeme_can_cross_buffer_boundary(self):
        tokens, symbols = analyze("identificadorMuitoLongo identificadorMuitoLongo", buffer_size=4)

        self.assertEqual(tokens[0].lexeme, "identificadorMuitoLongo")
        self.assertEqual(tokens[0].type, "IDENTIFIER")
        self.assertEqual(symbols, {"identificadorMuitoLongo": 2})


class LexerTests(unittest.TestCase):
    def test_keywords_identifiers_and_symbol_counts(self):
        tokens, symbols = analyze("public int valor; valor = 2;")

        self.assertEqual(symbols, {"valor": 2})
        self.assertEqual(tokens[0].type, "KEYWORD")
        self.assertEqual(tokens[1].type, "KEYWORD")

    def test_string_and_args_are_identifiers(self):
        tokens, symbols = analyze("public static void main(String[] args) {}")
        token_types = {token.lexeme: token.type for token in tokens if token.lexeme}

        self.assertEqual(token_types["String"], "IDENTIFIER")
        self.assertEqual(token_types["args"], "IDENTIFIER")
        self.assertEqual(symbols["String"], 1)
        self.assertEqual(symbols["args"], 1)

    def test_literals_operators_and_comments(self):
        source = "int x=12; float y=3.14; char c='\\n'; String s=\"oi\\n\"; // fim"
        tokens, _ = analyze(source, buffer_size=5)
        types = [token.type for token in tokens]

        self.assertIn("INTEGER_LITERAL", types)
        self.assertIn("FLOAT_LITERAL", types)
        self.assertIn("CHAR_LITERAL", types)
        self.assertIn("STRING_LITERAL", types)
        self.assertIn("OPERATOR", types)
        self.assertNotIn("ERROR", types)

    def test_required_lexical_errors(self):
        tokens, _ = analyze('float x=3,14; int 2abc=1; String s="ab\n')
        errors = [token for token in tokens if token.type == "ERROR"]

        self.assertEqual([token.lexeme for token in errors], ["3,14", "2abc", '"ab'])

    def test_invalid_character_literal(self):
        tokens, _ = analyze("char c = 'ab';")
        errors = [token for token in tokens if token.type == "ERROR"]

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].lexeme, "'ab'")

    def test_comments_are_ignored(self):
        tokens, symbols = analyze("int x; /* x escondido */ // x escondido\nx++;")

        self.assertEqual(symbols, {"x": 2})
        self.assertFalse(any("escondido" in token.lexeme for token in tokens))

    def test_unterminated_block_comment_is_error(self):
        tokens, _ = analyze("int x; /* nunca fecha")

        self.assertEqual(tokens[-2].type, "ERROR")
        self.assertEqual(tokens[-2].attribute, "comentario de bloco nao terminado")

    def test_token_line_and_column(self):
        tokens, _ = analyze("\n  int x;")

        self.assertEqual((tokens[0].line, tokens[0].column), (2, 3))
        self.assertEqual((tokens[1].line, tokens[1].column), (2, 7))

    def test_relational_logical_and_assignment_operators(self):
        tokens, _ = analyze("a >= b && b != c; a += 1;")
        operators = [token.lexeme for token in tokens if token.type == "OPERATOR"]

        self.assertEqual(operators, [">=", "&&", "!=", "+="])

    def test_unknown_character_generates_error(self):
        tokens, _ = analyze("int x = 1; $")
        errors = [token for token in tokens if token.type == "ERROR"]

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].lexeme, "$")
        self.assertEqual((errors[0].line, errors[0].column), (1, 12))


if __name__ == "__main__":
    unittest.main()
