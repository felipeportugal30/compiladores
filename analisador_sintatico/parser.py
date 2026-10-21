"""Analisador sintatico descendente preditivo dirigido por tabela LL(1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from grammar import (
    ENDMARKER,
    EPSILON,
    GRAMMAR,
    START_SYMBOL,
    GrammarAnalysis,
    Production,
    analyze_grammar,
    format_production,
    ordered_symbols,
)


@dataclass(frozen=True)
class ParserToken:
    terminal: str
    lexeme: str
    line: int
    column: int

    @property
    def trace_label(self) -> str:
        if self.terminal in {"id", "num"}:
            return f"{self.terminal}({self.lexeme})"
        return self.terminal


@dataclass
class ParseNode:
    symbol: str
    children: list["ParseNode"] = field(default_factory=list)
    token: ParserToken | None = None

    def preorder_lines(self, depth: int = 0) -> list[str]:
        suffix = ""
        if self.token is not None:
            suffix = f" → {self.token.lexeme!r} [linha {self.token.line}, coluna {self.token.column}]"
        lines = [f"{'  ' * depth}{self.symbol}{suffix}"]
        for child in self.children:
            lines.extend(child.preorder_lines(depth + 1))
        return lines


@dataclass(frozen=True)
class TraceStep:
    number: int
    stack: str
    input_text: str
    action: str


@dataclass(frozen=True)
class SyntaxErrorDetail:
    kind: str
    line: int
    column: int
    unexpected: str
    expected: tuple[str, ...]
    message: str


@dataclass
class ParseResult:
    accepted: bool
    errors: list[SyntaxErrorDetail]
    trace: list[TraceStep]
    tree: ParseNode


def normalize_token(token: Any) -> ParserToken:
    """Converte um token do Trabalho 1 para um terminal da gramatica."""
    if token.type == "IDENTIFIER":
        terminal = "id"
    elif token.type in {"INTEGER_LITERAL", "FLOAT_LITERAL"}:
        terminal = "num"
    elif token.type == "EOF":
        terminal = ENDMARKER
    else:
        terminal = token.lexeme
    return ParserToken(terminal, token.lexeme, token.line, token.column)


def normalize_tokens(tokens: Iterable[Any]) -> list[ParserToken]:
    return [normalize_token(token) for token in tokens if token.type != "ERROR"]


class PredictiveParser:
    """Executa o algoritmo de pilha e recupera erros por modo panico."""

    def __init__(self, analysis: GrammarAnalysis | None = None) -> None:
        self.analysis = analysis or analyze_grammar()
        self.nonterminals = set(GRAMMAR)

    def parse(self, lexical_tokens: Iterable[Any]) -> ParseResult:
        tokens = normalize_tokens(lexical_tokens)
        if not tokens or tokens[-1].terminal != ENDMARKER:
            last = tokens[-1] if tokens else ParserToken(ENDMARKER, "", 1, 1)
            tokens.append(ParserToken(ENDMARKER, "", last.line, last.column))

        root = ParseNode(START_SYMBOL)
        stack: list[tuple[str, ParseNode | None]] = [
            (ENDMARKER, None),
            (START_SYMBOL, root),
        ]
        errors: list[SyntaxErrorDetail] = []
        trace: list[TraceStep] = []
        index = 0
        step = 1

        while stack:
            top, node = stack[-1]
            current = tokens[min(index, len(tokens) - 1)]
            stack_text = " ".join(symbol for symbol, _ in stack)
            input_text = " ".join(token.trace_label for token in tokens[index:])

            if top in self.nonterminals:
                production = self.analysis.table.get((top, current.terminal))
                if production is not None:
                    stack.pop()
                    children = self._expand(node, production)
                    for symbol, child in reversed(list(zip(production, children))):
                        stack.append((symbol, child))
                    action = f"{top} → {format_production(production)}"
                else:
                    expected = self._expected_for(top)
                    errors.append(self._table_error(top, current, expected))
                    if current.terminal in self.analysis.follow[top] or current.terminal in {";", "}", ENDMARKER}:
                        stack.pop()
                        action = f"erro: sincronizar removendo {top} da pilha"
                    else:
                        index += 1
                        action = f"erro: descartar {current.trace_label} da entrada"
            elif top == current.terminal:
                stack.pop()
                if node is not None:
                    node.token = current
                index += 1
                action = f"casar {current.trace_label}"
            else:
                stack.pop()
                errors.append(self._stack_error(top, current))
                action = f"erro: inserir simbolicamente {top}"

            trace.append(TraceStep(step, stack_text, input_text, action))
            step += 1

        accepted = not errors and index == len(tokens)
        return ParseResult(accepted, errors, trace, root)

    @staticmethod
    def _expand(node: ParseNode | None, production: Production) -> list[ParseNode]:
        if node is None:
            return []
        if not production:
            node.children = [ParseNode(EPSILON)]
            return []
        node.children = [ParseNode(symbol) for symbol in production]
        return node.children

    def _expected_for(self, nonterminal: str) -> tuple[str, ...]:
        values = {
            terminal
            for (left, terminal) in self.analysis.table
            if left == nonterminal
        }
        return tuple(ordered_symbols(values))

    @staticmethod
    def _token_description(token: ParserToken) -> str:
        return ENDMARKER if token.terminal == ENDMARKER else token.lexeme

    @classmethod
    def _table_error(
        cls,
        nonterminal: str,
        token: ParserToken,
        expected: tuple[str, ...],
    ) -> SyntaxErrorDetail:
        message = (
            f"Erro sintático (tabela): token {cls._token_description(token)!r} inesperado; "
            f"esperava-se {_format_expected(expected)} para derivar {nonterminal} "
            f"(linha {token.line}, coluna {token.column})."
        )
        return SyntaxErrorDetail(
            "tabela", token.line, token.column, cls._token_description(token), expected, message
        )

    @classmethod
    def _stack_error(cls, expected: str, token: ParserToken) -> SyntaxErrorDetail:
        unexpected = cls._token_description(token)
        message = (
            f"Erro sintático (pilha): encontrado {unexpected!r}, mas esperava-se "
            f"{expected!r} no topo da pilha (linha {token.line}, coluna {token.column})."
        )
        return SyntaxErrorDetail(
            "pilha", token.line, token.column, unexpected, (expected,), message
        )


def _format_expected(expected: tuple[str, ...]) -> str:
    quoted = [repr(symbol) for symbol in expected]
    if not quoted:
        return "nenhum terminal válido"
    if len(quoted) == 1:
        return quoted[0]
    return ", ".join(quoted[:-1]) + f" ou {quoted[-1]}"
