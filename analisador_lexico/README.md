# Analisador Lexico Manual

Implementacao em Python de um analisador lexico para um subconjunto de Java. O
projeto nao utiliza expressoes regulares nem geradores como Lex, Flex, PLY ou
ANTLR.

## Execucao

Requer Python 3.10 ou superior e nao possui dependencias externas.

```bash
cd analisador_lexico
python3 main.py examples/Valido.java
python3 main.py examples/ComErros.java
```

O programa aceita somente arquivos `.java`, imprime a tabela de tokens e a
tabela de simbolos e retorna codigo de saida `1` quando encontra erros lexicos.
O tamanho de cada buffer pode ser alterado para fins de demonstracao:

```bash
python3 main.py examples/Valido.java --buffer-size 8
```

## Testes

```bash
python3 -m unittest discover -s tests -v
```

## Organizacao

- `lexer.py`: fluxo de dois buffers, tokens, regras lexicas e tabela de simbolos;
- `main.py`: leitura do `.java` e apresentacao das tabelas;
- `examples/Valido.java`: exemplo sem erros;
- `examples/ComErros.java`: exemplo com erros lexicos;
- `tests/test_lexer.py`: testes automatizados.

## Estrategia de dois buffers

O codigo-fonte completo e carregado em memoria. `TwoBufferStream` divide a
leitura em blocos fixos e os carrega alternadamente em dois buffers. O ponteiro
`forward` avanca caractere por caractere e `begin` marca o inicio do lexema. Ao
ultrapassar o limite de um buffer, o bloco seguinte e carregado no outro. O
lexema reconhecido corresponde ao intervalo `source[begin:forward]`.

## Categorias reconhecidas

- palavras-chave Java (mais de 50) e identificadores ASCII;
- inteiros decimais, reais com ponto, caracteres e strings com escapes;
- operadores aritmeticos, relacionais, logicos e de atribuicao;
- delimitadores;
- comentarios de linha e de bloco, que sao descartados;
- erros para caractere desconhecido, identificador iniciado por numero, decimal
  com virgula, string/comentario nao terminado e literal de caractere invalido.

Cada token registra tipo, lexema, atributo, linha e coluna. Palavras-chave nao
sao incluidas na tabela de simbolos.
