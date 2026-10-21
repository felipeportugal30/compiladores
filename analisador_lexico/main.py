"""Interface de linha de comando do analisador lexico."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lexer import Token, analyze


def _cell(value: object) -> str:
    if value is None:
        return "-"
    return json.dumps(value, ensure_ascii=False) if isinstance(value, str) else str(value)


def _table(headers: list[str], rows: list[list[object]]) -> str:
    text_rows = [[_cell(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in text_rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]
    line = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    output = [line, "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |", line]
    output.extend("| " + " | ".join(v.ljust(w) for v, w in zip(row, widths)) + " |" for row in text_rows)
    output.append(line)
    return "\n".join(output)


def print_result(tokens: list[Token], symbols: dict[str, int]) -> None:
    print("\nTABELA DE TOKENS")
    print(_table(
        ["#", "tipo", "lexema", "atributo", "linha", "coluna"],
        [[index, token.type, token.lexeme, token.attribute, token.line, token.column]
         for index, token in enumerate(tokens, 1)],
    ))
    print("\nTABELA DE SIMBOLOS")
    print(_table(
        ["identificador", "ocorrencias"],
        [[identifier, count] for identifier, count in symbols.items()],
    ) if symbols else "(vazia)")
    errors = sum(token.type == "ERROR" for token in tokens)
    print(f"\nResumo: {len(tokens) - 1} token(s), {len(symbols)} simbolo(s), {errors} erro(s).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analisador lexico manual para Java")
    parser.add_argument("arquivo", type=Path, help="arquivo-fonte com extensao .java")
    parser.add_argument("--buffer-size", type=int, default=64, help="tamanho de cada buffer (padrao: 64)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.arquivo.suffix.lower() != ".java":
        print("Erro: o arquivo de entrada deve possuir a extensao .java.")
        return 2
    try:
        source = args.arquivo.read_text(encoding="utf-8")
        tokens, symbols = analyze(source, args.buffer_size)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Erro ao ler o arquivo: {error}")
        return 2
    print_result(tokens, symbols)
    return 1 if any(token.type == "ERROR" for token in tokens) else 0


if __name__ == "__main__":
    raise SystemExit(main())
