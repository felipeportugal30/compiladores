# Analisador Sintático LL(1)

Implementação manual, em Python, de um analisador sintático descendente preditivo
dirigido por tabela para o subconjunto de Java definido no Trabalho 2. O programa
reutiliza diretamente o analisador léxico do Trabalho 1 e não usa geradores como
Yacc, Bison, PLY ou ANTLR.

## Funcionalidades

- integração com `../analisador_lexico/lexer.py`;
- cálculo automático dos conjuntos FIRST e FOLLOW;
- construção dinâmica da tabela preditiva M, com detecção de conflitos LL(1);
- reconhecimento por pilha, registrando Pilha, Entrada e Ação em cada passo;
- mensagens distintas para erro em célula vazia da tabela e erro no topo da pilha;
- recuperação de erros por modo pânico, permitindo encontrar vários erros;
- árvore de derivação textual em pré-ordem;
- três exemplos solicitados no enunciado e testes automatizados.

Requer Python 3.10 ou superior e não possui dependências externas.

## Execução

A partir desta pasta:

```bash
python3 main.py examples/Exemplo1_Sucesso.java
python3 main.py examples/Exemplo2_ErroTabela.java
python3 main.py examples/Exemplo3_ErroPilha.java
```

Por padrão, a saída contém FIRST, FOLLOW, a tabela M, o trace, a árvore e o
veredito. Partes extensas podem ser ocultadas durante testes rápidos:

```bash
python3 main.py examples/Exemplo1_Sucesso.java \
  --sem-conjuntos --sem-tabela --sem-trace --sem-arvore
```

O código de saída é `0` para programa aceito, `1` para erro léxico/sintático e
`2` para erro de uso ou leitura do arquivo.

## Testes

```bash
python3 -m unittest discover -s tests -v
```

## Organização

- `grammar.py`: gramática, FIRST, FOLLOW e construção da tabela M;
- `parser.py`: normalização dos tokens, algoritmo de pilha, árvore e modo pânico;
- `main.py`: integração com o léxico, interface de linha de comando e relatórios;
- `examples/`: os três programas exigidos pelo enunciado;
- `tests/`: testes da gramática, tabela, parser, erros, árvore e recuperação;
- `ROTEIRO_APRESENTACAO.md`: sugestão de demonstração para o vídeo.

## Integração léxica

O parser não compara identificadores e números por seus lexemas. A adaptação é:

| Tipo produzido pelo léxico | Terminal da gramática |
|---|---|
| `IDENTIFIER` | `id` |
| `INTEGER_LITERAL` ou `FLOAT_LITERAL` | `num` |
| `KEYWORD`, `OPERATOR` ou `DELIMITER` | o próprio lexema |
| `EOF` | `$` |

Se houver um token `ERROR`, a execução termina com o diagnóstico léxico antes da
análise sintática.

## Algoritmo LL(1)

A pilha começa com `$ PROG`. Em cada iteração:

1. se o topo for não-terminal, consulta-se `M[topo, entrada]`, remove-se o topo
   e empilha-se o lado direito da produção em ordem inversa;
2. se topo e entrada forem o mesmo terminal, ambos avançam;
3. se a célula da tabela estiver vazia, registra-se um erro e o modo pânico usa
   FOLLOW, `;`, `}` e `$` como pontos de sincronização;
4. se dois terminais forem diferentes, o terminal esperado é retirado
   simbolicamente da pilha, permitindo continuar a análise.

A entrada é aceita somente quando `$` casa com `$` e nenhum erro foi registrado.

## Gramática

```text
PROG     -> public class id { public static void id ( ) { CMDS } }
CMDS     -> CMD CMDS | ε
CMD      -> DECL | ATRIB | IF_STMT
DECL     -> TIPO id ;
TIPO     -> int | float | char
ATRIB    -> id = E ;
IF_STMT  -> if ( COND ) { CMDS } SENAO
SENAO    -> else { CMDS } | ε
COND     -> E OP_REL E
OP_REL   -> == | != | < | >
E        -> T E'
E'       -> + T E' | - T E' | ε
T        -> F T'
T'       -> * F T' | / F T' | ε
F        -> ( E ) | id | num
```

Os conjuntos e a tabela não estão codificados manualmente: são recalculados a
cada execução a partir dessa representação em `GRAMMAR`.
