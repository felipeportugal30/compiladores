from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from analisador_lexico.lexer import analyze

from grammar import (
    ENDMARKER,
    EPSILON,
    GRAMMAR,
    GrammarAnalysis,
    analyze_grammar,
    format_production,
    ordered_symbols,
)
from parser import ParseResult, PredictiveParser


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisador sintático preditivo LL(1) para um subconjunto de Java"
    )
    parser.add_argument("arquivo", type=Path, help="arquivo-fonte com extensão .java")
    parser.add_argument(
        "--buffer-size", type=int, default=64, help="tamanho dos buffers do analisador léxico"
    )
    parser.add_argument("--sem-conjuntos", action="store_true", help="não exibe FIRST e FOLLOW")
    parser.add_argument("--sem-tabela", action="store_true", help="não exibe a tabela preditiva")
    parser.add_argument("--sem-trace", action="store_true", help="não exibe o passo a passo da pilha")
    parser.add_argument("--sem-arvore", action="store_true", help="não exibe a árvore em pré-ordem")
    return parser.parse_args()


def format_sets(analysis: GrammarAnalysis) -> str:
    lines = ["CONJUNTOS FIRST"]
    for nonterminal in GRAMMAR:
        values = ordered_symbols(analysis.first[nonterminal])
        lines.append(f"FIRST({nonterminal}) = {{ {', '.join(values)} }}")
    lines.append("\nCONJUNTOS FOLLOW")
    for nonterminal in GRAMMAR:
        values = ordered_symbols(analysis.follow[nonterminal])
        lines.append(f"FOLLOW({nonterminal}) = {{ {', '.join(values)} }}")
    return "\n".join(lines)


def format_table(analysis: GrammarAnalysis) -> str:
    lines = ["TABELA DE ANÁLISE PREDITIVA (células não vazias)"]
    for nonterminal in GRAMMAR:
        entries = [
            (terminal, production)
            for (left, terminal), production in analysis.table.items()
            if left == nonterminal
        ]
        order = {terminal: index for index, terminal in enumerate(ordered_symbols(t for t, _ in entries))}
        entries.sort(key=lambda item: order[item[0]])
        for terminal, production in entries:
            lines.append(
                f"M[{nonterminal}, {terminal}] = {nonterminal} → {format_production(production)}"
            )
    return "\n".join(lines)


def format_trace(result: ParseResult) -> str:
    lines = ["TRACE DA PILHA"]
    for item in result.trace:
        lines.extend(
            (
                f"[{item.number:03d}] Pilha:   {item.stack}",
                f"      Entrada: {item.input_text}",
                f"      Ação:    {item.action}",
            )
        )
    return "\n".join(lines)


def format_tree(result: ParseResult) -> str:
    return "ÁRVORE DE DERIVAÇÃO (PRÉ-ORDEM)\n" + "\n".join(result.tree.preorder_lines())


def main() -> int:
    args = parse_args()
    if args.arquivo.suffix.lower() != ".java":
        print("Erro: o arquivo de entrada deve possuir a extensão .java.")
        return 2

    try:
        source = args.arquivo.read_text(encoding="utf-8")
        tokens, symbols = analyze(source, args.buffer_size)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Erro ao ler o arquivo: {error}")
        return 2

    print(
        f"Análise léxica: {len(tokens) - 1} token(s), "
        f"{len(symbols)} identificador(es) distinto(s)."
    )
    lexical_errors = [token for token in tokens if token.type == "ERROR"]
    if lexical_errors:
        print("\nERROS LÉXICOS")
        for token in lexical_errors:
            print(
                f"- {token.attribute}: {token.lexeme!r} "
                f"(linha {token.line}, coluna {token.column})"
            )
        print("\nVEREDITO: programa rejeitado na análise léxica.")
        return 1

    analysis = analyze_grammar()
    result = PredictiveParser(analysis).parse(tokens)

    if not args.sem_conjuntos:
        print("\n" + format_sets(analysis))
    if not args.sem_tabela:
        print("\n" + format_table(analysis))
    if not args.sem_trace:
        print("\n" + format_trace(result))
    if not args.sem_arvore:
        print("\n" + format_tree(result))

    if result.accepted:
        print("\nVEREDITO: programa sintaticamente válido — ACEITO COM SUCESSO.")
        return 0

    print("\nERROS SINTÁTICOS")
    for error in result.errors:
        print(f"- {error.message}")
    print(
        f"\nVEREDITO: programa sintaticamente inválido — "
        f"{len(result.errors)} erro(s) encontrado(s)."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
