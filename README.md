# Modelagem do Mercado Financeiro com Cadeias de Markov

## Sobre o projeto

Este repositório apresenta uma implementação computacional, desenvolvida em Python, para a modelagem de séries financeiras por meio de cadeias de Markov.

O projeto foi desenvolvido no contexto de uma pesquisa de Iniciação Científica em Matemática, com o objetivo de investigar a aplicação de modelos probabilísticos na análise do comportamento de ativos financeiros.

A implementação utiliza preços históricos de fechamento, calcula retornos, classifica as variações em estados discretos e estima probabilidades de transição. A partir dessas informações, são construídas previsões probabilísticas sobre o comportamento futuro dos ativos.





## Funcionalidades

O programa permite:

- Conectar-se a um banco de dados SQLite contendo preços históricos de ativos financeiros.
- Identificar os ativos cadastrados.
- Selecionar os últimos 20 preços de fechamento de cada ativo.
- Calcular os retornos e suas medidas estatísticas.
- Classificar os retornos nos quatro estados.
- Construir a matriz de transição.
- Calcular os vetores \(V_0\) e \(V_1\).
- Comparar a previsão baseada em \(V_1\) com a previsão condicionada ao último estado.
- Apresentar classificações indicativas de COMPRA, VENDA ou NEUTRO.
- Cadastrar novos fechamentos e atualizar os resultados.

As classificações utilizam um limite direcional de 55%, exigindo concordância entre as duas avaliações para indicar COMPRA ou VENDA.

## Tecnologias utilizadas

- **Python:** implementação dos cálculos e da lógica do programa.
- **NumPy:** operações com vetores e matrizes.
- **SQLite:** armazenamento e consulta dos dados financeiros.

## Como utilizar

### 1. Requisitos

É necessário ter o Python instalado e instalar a biblioteca NumPy:

```bash
pip install numpy
```

As bibliotecas `sqlite3` e `datetime` fazem parte da biblioteca padrão do Python.

### 2. Configuração do banco de dados

O programa utiliza um banco de dados SQLite, que deve ser criado ou configurado pelo usuário.

A tabela esperada chama-se `cotacoes` e deve conter, no mínimo, as seguintes colunas:

| Coluna | Descrição |
|---|---|
| `data` | Data do fechamento, no formato AAAA-MM-DD |
| `ativo` | Identificador do ativo financeiro |
| `fechamento` | Preço de fechamento |

Para permitir a atualização de registros existentes, recomenda-se definir a combinação `(data, ativo)` como chave única.

Exemplo de criação da tabela:

```sql
CREATE TABLE cotacoes (
    data TEXT NOT NULL,
    ativo TEXT NOT NULL,
    fechamento REAL NOT NULL,
    PRIMARY KEY (data, ativo)
);
```

Caso a tabela utilize outro nome para a coluna de preços, consulte os nomes aceitos pelo programa ou adapte a função responsável pela identificação dessa coluna.

### 3. Configuração do código

No arquivo `04_previsao_e_atualizacao_publicacao.py`, localize a variável `CAMINHO_BANCO` e substitua seu valor pelo caminho do banco de dados SQLite utilizado.

O banco precisa conter os registros históricos dos ativos que serão analisados.

### 4. Execução

Após configurar o banco de dados, execute:

```bash
python 04_previsao_e_atualizacao_publicacao.py
```

O programa apresentará as análises disponíveis e um menu para atualização dos fechamentos ou recálculo das previsões.

## Considerações metodológicas

A implementação disponibilizada utiliza uma janela de 20 preços de fechamento, correspondente a 19 retornos consecutivos.

As probabilidades são estimadas a partir das transições observadas nessa janela. Por isso, os resultados dependem da quantidade e da distribuição dos dados disponíveis.

Em particular, podem ocorrer estados sem transições de saída observadas. A versão disponibilizada requer atenção a esses casos, pois a ausência de transições não permite estimar diretamente uma distribuição de probabilidades para aquela linha da matriz.

As classificações COMPRA, VENDA e NEUTRO são indicadores experimentais derivados do modelo probabilístico. Não constituem recomendações de investimento nem garantem resultados futuros.

## Finalidade acadêmica

Este repositório tem finalidade educacional e científica, buscando demonstrar como conceitos da teoria das cadeias de Markov podem ser implementados computacionalmente e aplicados à análise de dados financeiros.

O código pode ser estudado e adaptado para diferentes ativos, períodos e bases de dados, respeitando as hipóteses e limitações do modelo.
