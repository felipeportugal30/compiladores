import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(REPOSITORY_ROOT))

from analisador_lexico.lexer import analyze
from parser import PredictiveParser


EXAMPLES_DIR = PROJECT_DIR / "examples"


def parse_example(name):
    source = (EXAMPLES_DIR / name).read_text(encoding="utf-8")
    tokens, _ = analyze(source)
    lexical_errors = [token for token in tokens if token.type == "ERROR"]
    if lexical_errors:
        raise AssertionError(f"erro lexico inesperado: {lexical_errors}")
    return PredictiveParser().parse(tokens)


class ParserTests(unittest.TestCase):
    def test_success_example_is_accepted(self):
        result = parse_example("Exemplo1_Sucesso.java")

        self.assertTrue(result.accepted)
        self.assertEqual(result.errors, [])
        self.assertTrue(result.trace)
        self.assertEqual(result.trace[-1].action, "casar $")

    def test_table_error_example_reports_missing_operand(self):
        result = parse_example("Exemplo2_ErroTabela.java")

        self.assertFalse(result.accepted)
        self.assertEqual(len(result.errors), 1)
        error = result.errors[0]
        self.assertEqual(error.kind, "tabela")
        self.assertEqual(error.unexpected, ")")
        self.assertEqual(set(error.expected), {"(", "id", "num"})
        self.assertIn("derivar T", error.message)

    def test_stack_error_example_reports_missing_closing_parenthesis(self):
        result = parse_example("Exemplo3_ErroPilha.java")

        self.assertFalse(result.accepted)
        self.assertEqual(len(result.errors), 1)
        error = result.errors[0]
        self.assertEqual(error.kind, "pilha")
        self.assertEqual(error.unexpected, ";")
        self.assertEqual(error.expected, (")",))

    def test_empty_command_list_is_accepted(self):
        source = "public class Vazia { public static void main() { } }"
        tokens, _ = analyze(source)

        result = PredictiveParser().parse(tokens)

        self.assertTrue(result.accepted)

    def test_if_without_else_is_accepted(self):
        source = """
            public class SemElse {
                public static void main() {
                    int a;
                    if (a == 1) { a = 2; }
                }
            }
        """
        tokens, _ = analyze(source)

        result = PredictiveParser().parse(tokens)

        self.assertTrue(result.accepted)

    def test_panic_mode_finds_more_than_one_error(self):
        source = """
            public class DoisErros {
                public static void main() {
                    int a
                    a = 1 + ;
                }
            }
        """
        tokens, _ = analyze(source)

        result = PredictiveParser().parse(tokens)

        self.assertFalse(result.accepted)
        self.assertGreaterEqual(len(result.errors), 2)

    def test_tree_contains_epsilon_and_matched_lexemes(self):
        result = parse_example("Exemplo1_Sucesso.java")
        tree_text = "\n".join(result.tree.preorder_lines())

        self.assertIn("TesteSucesso", tree_text)
        self.assertIn("ε", tree_text)


if __name__ == "__main__":
    unittest.main()
