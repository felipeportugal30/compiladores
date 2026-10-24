import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(REPOSITORY_ROOT))

from grammar import EPSILON, analyze_grammar


class GrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analysis = analyze_grammar()

    def test_first_sets(self):
        self.assertEqual(self.analysis.first["PROG"], {"public"})
        self.assertEqual(
            self.analysis.first["CMDS"],
            {"int", "float", "char", "id", "if", EPSILON},
        )
        self.assertEqual(self.analysis.first["E"], {"(", "id", "num"})
        self.assertEqual(self.analysis.first["T'"], {"*", "/", EPSILON})

    def test_follow_sets(self):
        self.assertEqual(self.analysis.follow["PROG"], {"$"})
        self.assertIn("}", self.analysis.follow["CMDS"])
        self.assertTrue({";", ")", "==", "!=", "<", ">"}.issubset(self.analysis.follow["E"]))

    def test_predictive_table_has_expected_productions(self):
        self.assertEqual(self.analysis.table[("F", "(")], ("(", "E", ")"))
        self.assertEqual(self.analysis.table[("F", "id")], ("id",))
        self.assertEqual(self.analysis.table[("E'", ")")], ())
        self.assertEqual(self.analysis.table[("SENAO", "else")], ("else", "{", "CMDS", "}"))

    def test_grammar_is_ll1(self):
        analyze_grammar()


if __name__ == "__main__":
    unittest.main()
