"""Gramatica e algoritmos para construcao automatica de um analisador LL(1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


EPSILON = "ε"
ENDMARKER = "$"
START_SYMBOL = "PROG"

# Uma producao vazia representa epsilon. A ordem e mantida para que conjuntos,
# mensagens e a tabela tenham uma apresentacao deterministica.
GRAMMAR: dict[str, tuple[tuple[str, ...], ...]] = {
    "PROG": (("public", "class", "id", "{", "public", "static", "void", "id", "(", ")", "{", "CMDS", "}", "}"),),
    "CMDS": (("CMD", "CMDS"), ()),
    "CMD": (("DECL",), ("ATRIB",), ("IF_STMT",)),
    "DECL": (("TIPO", "id", ";"),),
    "TIPO": (("int",), ("float",), ("char",)),
    "ATRIB": (("id", "=", "E", ";"),),
    "IF_STMT": (("if", "(", "COND", ")", "{", "CMDS", "}", "SENAO"),),
    "SENAO": (("else", "{", "CMDS", "}"), ()),
    "COND": (("E", "OP_REL", "E"),),
    "OP_REL": (("==",), ("!=",), ("<",), (">",)),
    "E": (("T", "E'"),),
    "E'": (("+", "T", "E'"), ("-", "T", "E'"), ()),
    "T": (("F", "T'"),),
    "T'": (("*", "F", "T'"), ("/", "F", "T'"), ()),
    "F": (("(", "E", ")"), ("id",), ("num",)),
}

TERMINAL_ORDER = (
    "public", "class", "static", "void", "int", "float", "char", "if", "else",
    "(", "id", "num", "+", "-", "*", "/", "=", "==", "!=", "<", ">",
    ")", "{", "}", ";", ENDMARKER,
)

Production = tuple[str, ...]
ParseTable = dict[tuple[str, str], Production]


class GrammarConflictError(ValueError):
    """Indica que duas producoes tentam ocupar a mesma celula da tabela."""


@dataclass(frozen=True)
class GrammarAnalysis:
    first: dict[str, set[str]]
    follow: dict[str, set[str]]
    table: ParseTable


def nonterminals(grammar: dict[str, tuple[Production, ...]] = GRAMMAR) -> set[str]:
    return set(grammar)


def terminals(grammar: dict[str, tuple[Production, ...]] = GRAMMAR) -> set[str]:
    nts = nonterminals(grammar)
    return {
        symbol
        for alternatives in grammar.values()
        for production in alternatives
        for symbol in production
        if symbol not in nts
    }


def first_of_sequence(
    sequence: Iterable[str],
    first: dict[str, set[str]],
    grammar: dict[str, tuple[Production, ...]] = GRAMMAR,
) -> set[str]:
    """Calcula FIRST para uma sequencia usando os conjuntos ja conhecidos."""
    symbols = tuple(sequence)
    if not symbols:
        return {EPSILON}

    result: set[str] = set()
    nts = nonterminals(grammar)
    for symbol in symbols:
        symbol_first = first[symbol] if symbol in nts else {symbol}
        result.update(symbol_first - {EPSILON})
        if EPSILON not in symbol_first:
            break
    else:
        result.add(EPSILON)
    return result


def compute_first(
    grammar: dict[str, tuple[Production, ...]] = GRAMMAR,
) -> dict[str, set[str]]:
    first = {nt: set() for nt in grammar}
    changed = True
    while changed:
        changed = False
        for nt, alternatives in grammar.items():
            for production in alternatives:
                before = len(first[nt])
                first[nt].update(first_of_sequence(production, first, grammar))
                changed |= len(first[nt]) != before
    return first


def compute_follow(
    first: dict[str, set[str]],
    grammar: dict[str, tuple[Production, ...]] = GRAMMAR,
    start_symbol: str = START_SYMBOL,
) -> dict[str, set[str]]:
    follow = {nt: set() for nt in grammar}
    follow[start_symbol].add(ENDMARKER)
    nts = nonterminals(grammar)

    changed = True
    while changed:
        changed = False
        for left, alternatives in grammar.items():
            for production in alternatives:
                for index, symbol in enumerate(production):
                    if symbol not in nts:
                        continue
                    suffix_first = first_of_sequence(production[index + 1 :], first, grammar)
                    before = len(follow[symbol])
                    follow[symbol].update(suffix_first - {EPSILON})
                    if EPSILON in suffix_first:
                        follow[symbol].update(follow[left])
                    changed |= len(follow[symbol]) != before
    return follow


def build_parse_table(
    first: dict[str, set[str]],
    follow: dict[str, set[str]],
    grammar: dict[str, tuple[Production, ...]] = GRAMMAR,
) -> ParseTable:
    table: ParseTable = {}
    for left, alternatives in grammar.items():
        for production in alternatives:
            production_first = first_of_sequence(production, first, grammar)
            lookaheads = set(production_first - {EPSILON})
            if EPSILON in production_first:
                lookaheads.update(follow[left])
            for lookahead in lookaheads:
                key = (left, lookahead)
                previous = table.get(key)
                if previous is not None and previous != production:
                    raise GrammarConflictError(
                        f"conflito em M[{left}, {lookahead}]: "
                        f"{format_production(previous)} / {format_production(production)}"
                    )
                table[key] = production
    return table


def analyze_grammar(
    grammar: dict[str, tuple[Production, ...]] = GRAMMAR,
    start_symbol: str = START_SYMBOL,
) -> GrammarAnalysis:
    first = compute_first(grammar)
    follow = compute_follow(first, grammar, start_symbol)
    table = build_parse_table(first, follow, grammar)
    return GrammarAnalysis(first, follow, table)


def format_production(production: Production) -> str:
    return " ".join(production) if production else EPSILON


def ordered_symbols(symbols: Iterable[str]) -> list[str]:
    order = {symbol: index for index, symbol in enumerate(TERMINAL_ORDER)}
    return sorted(symbols, key=lambda symbol: (order.get(symbol, len(order)), symbol))
