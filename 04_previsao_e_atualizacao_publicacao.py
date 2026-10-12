import sqlite3
from datetime import datetime

import numpy as np


# ============================================================
# 1. CONFIGURAÇÕES GERAIS
# ============================================================

# CONFIGURAÇÃO DO BANCO DE DADOS (ADAPTE ANTES DE EXECUTAR)
# 1. Crie ou utilize um banco SQLite (.db) com seus próprios dados históricos.
# 2. Substitua o caminho abaixo pelo local do arquivo em seu computador.
#    Exemplo no Windows: r"C:\seu_caminho\seu_banco.db"
#    Exemplo no Linux/macOS: "/home/usuario/dados/seu_banco.db"
# 3. Crie uma tabela chamada "cotacoes" (ou altere NOME_TABELA abaixo)
#    contendo pelo menos as colunas:
#       data        -> data do fechamento em formato AAAA-MM-DD (texto)
#       ativo       -> identificação do ativo (texto)
#       fechamento  -> preço de fechamento (numérico)
#    A coluna de preço também pode ter um dos outros nomes aceitos
#    pela função descobrir_coluna_preco().
# 4. Para permitir a atualização de preços com ON CONFLICT(data, ativo),
#    a combinação (data, ativo) deve ser UNIQUE ou PRIMARY KEY na tabela.
# 5. Instale a dependência externa: pip install numpy
# 6. O programa usa os 20 fechamentos mais recentes por ativo.
#    É necessário ter pelo menos 20 registros de preço por ativo.
# ATENÇÃO: não publique chaves de API, senhas ou dados confidenciais.
CAMINHO_BANCO = r"C:\seu_caminho\seu_banco.db"

# Nome da tabela que contém os preços históricos.
NOME_TABELA = "cotacoes"

# Quantidade de fechamentos usados em cada janela.
TAMANHO_JANELA = 20

# Ordem dos estados usada no vetor e na matriz.
ESTADOS_UNICOS = ["F", "A", "Q", "S"]

# Limite usado para definir se um vetor indica alta ou queda.
LIMITE_DIRECIONAL = 0.55



# ============================================================
# 2. CONECTAR AO BANCO DE DADOS
# ============================================================

def conectar_banco():
    """
    Abre a conexão com o banco de dados SQLite.
    """

    conexao = sqlite3.connect(CAMINHO_BANCO)

    return conexao


# ============================================================
# 3. VERIFICAR SE A TABELA EXISTE
# ============================================================

def verificar_tabela(conexao):
    """
    Verifica se a tabela cotacoes existe no banco.
    """

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
    """, (NOME_TABELA,))

    resultado = cursor.fetchone()

    if resultado is None:
        raise ValueError(
            f"A tabela '{NOME_TABELA}' não foi encontrada no banco."
        )


# ============================================================
# 4. IDENTIFICAR AS COLUNAS DA TABELA
# ============================================================

def obter_colunas_tabela(conexao):
    """
    Retorna os nomes das colunas existentes na tabela cotacoes.
    """

    cursor = conexao.cursor()

    cursor.execute(f"""
        PRAGMA table_info("{NOME_TABELA}")
    """)

    resultado = cursor.fetchall()

    colunas = [linha[1] for linha in resultado]

    return colunas


def descobrir_coluna_preco(conexao):
    """
    Procura automaticamente a coluna que armazena o preço.

    O programa aceita diferentes nomes possíveis.
    """

    colunas = obter_colunas_tabela(conexao)

    nomes_possiveis = [
        "fechamento",
        "ultimo",
        "Último",
        "último",
        "preco",
        "Preço",
        "preço",
        "valor"
    ]

    for nome in nomes_possiveis:

        if nome in colunas:
            return nome

    raise ValueError(
        "Não foi possível identificar a coluna de preço.\n"
        f"Colunas encontradas: {colunas}"
    )


# ============================================================
# 5. BUSCAR TODOS OS ATIVOS
# ============================================================

def buscar_ativos(conexao):
    """
    Busca todos os ativos cadastrados no banco.

    Os ativos são devolvidos em ordem alfabética.
    """

    cursor = conexao.cursor()

    cursor.execute(f"""
        SELECT DISTINCT ativo
        FROM "{NOME_TABELA}"
        WHERE ativo IS NOT NULL
        ORDER BY ativo
    """)

    resultado = cursor.fetchall()

    ativos = [linha[0] for linha in resultado]

    return ativos


# ============================================================
# 6. BUSCAR OS 20 ÚLTIMOS FECHAMENTOS
# ============================================================

def buscar_ultimos_fechamentos(
    conexao,
    ativo,
    coluna_preco
):
    """
    Busca os últimos 20 fechamentos de um ativo.

    O banco seleciona os dados do mais recente para o mais
    antigo. Depois, a lista é invertida para ficar em ordem
    cronológica:

        mais antigo -> mais recente
    """

    cursor = conexao.cursor()

    consulta = f"""
        SELECT data, "{coluna_preco}"
        FROM "{NOME_TABELA}"
        WHERE ativo = ?
          AND "{coluna_preco}" IS NOT NULL
        ORDER BY data DESC
        LIMIT ?
    """

    cursor.execute(
        consulta,
        (ativo, TAMANHO_JANELA)
    )

    resultado = cursor.fetchall()

    # Inverte a ordem para ficar do mais antigo ao mais recente.
    resultado.reverse()

    datas = []
    precos = []

    for data, preco in resultado:

        datas.append(data)
        precos.append(float(preco))

    return datas, precos


# ============================================================
# 7. CALCULAR OS RETORNOS
# ============================================================

def calcular_retornos(precos):
    """
    Calcula os retornos entre preços consecutivos.

    Fórmula:

        retorno = preço seguinte / preço atual - 1

    Com 20 preços, o programa calcula 19 retornos.
    """

    retornos = []

    for i in range(len(precos) - 1):

        preco_atual = precos[i]
        preco_seguinte = precos[i + 1]

        if preco_atual == 0:
            raise ZeroDivisionError(
                "Foi encontrado um preço igual a zero."
            )

        retorno = (preco_seguinte / preco_atual) - 1

        retornos.append(retorno)

    return retornos


# ============================================================
# 8. CALCULAR A MÉDIA DOS RETORNOS
# ============================================================

def calcular_media_retornos(retornos):
    """
    Calcula a média aritmética dos retornos.
    """

    media = sum(retornos) / len(retornos)

    return media


# ============================================================
# 9. CALCULAR O DESVIO MÉDIO
# ============================================================

def calcular_desvio_medio(retornos, media):
    """
    Calcula o desvio médio.

    Para cada retorno, calcula:

        |retorno - média|

    Depois, soma todos os resultados e divide pela quantidade
    de retornos.

    Este cálculo não é o desvio padrão.
    """

    soma_desvios = 0

    for retorno in retornos:

        soma_desvios += abs(retorno - media)

    desvio_medio = soma_desvios / len(retornos)

    return desvio_medio


# ============================================================
# 10. CLASSIFICAR OS ESTADOS
# ============================================================

def classificar_estados(retornos, desvio_medio):
    """
    Classifica cada retorno em um dos quatro estados.

    F: retorno >= desvio médio

    A: 0 <= retorno < desvio médio

    Q: -desvio médio < retorno < 0

    S: retorno <= -desvio médio
    """

    estados = []

    for retorno in retornos:

        if retorno >= desvio_medio:

            estados.append("F")

        elif 0 <= retorno < desvio_medio:

            estados.append("A")

        elif -desvio_medio < retorno < 0:

            estados.append("Q")

        else:

            estados.append("S")

    return estados


# ============================================================
# 11. CONSTRUIR O VETOR INICIAL V0
# ============================================================

def construir_vetor_inicial(estados):
    """
    Constrói o vetor inicial pela frequência de cada estado.

    Ordem:

        V0 = [F, A, Q, S]
    """

    total = len(estados)

    vetor = []

    for estado in ESTADOS_UNICOS:

        quantidade = estados.count(estado)

        frequencia = quantidade / total

        vetor.append(frequencia)

    V0 = np.array(vetor, dtype=float)

    return V0


# ============================================================
# 12. CONTAR AS TRANSIÇÕES
# ============================================================

def contar_transicoes(estados):
    """
    Conta todas as transições entre estados consecutivos.

    Exemplo:

        F -> A -> Q

    Transições contadas:

        F para A
        A para Q
    """

    contagem = {
        origem: {
            destino: 0
            for destino in ESTADOS_UNICOS
        }
        for origem in ESTADOS_UNICOS
    }

    for i in range(len(estados) - 1):

        atual = estados[i]
        proximo = estados[i + 1]

        contagem[atual][proximo] += 1

    return contagem


# ============================================================
# 13. CONSTRUIR A MATRIZ DE TRANSIÇÃO
# ============================================================

def construir_matriz_transicao(estados):
    """
    Constrói a matriz de transição P.

    A ordem das linhas e colunas é:

        F, A, Q, S

    Cada linha representa o estado atual.
    Cada coluna representa o próximo estado.

    Caso um estado não possua nenhuma saída, a linha dele
    será formada por quatro zeros.
    """

    contagem = contar_transicoes(estados)

    matriz = []

    for origem in ESTADOS_UNICOS:

        total_origem = sum(
            contagem[origem].values()
        )

        if total_origem == 0:

            linha = [0, 0, 0, 0]

        else:

            linha = []

            for destino in ESTADOS_UNICOS:

                probabilidade = (
                    contagem[origem][destino]
                    / total_origem
                )

                linha.append(probabilidade)

        matriz.append(linha)

    P = np.array(matriz, dtype=float)

    return P, contagem


# ============================================================
# 14. CALCULAR O VETOR V1
# ============================================================

def calcular_vetor_previsto(V0, P):
    """
    Calcula o vetor previsto por meio da multiplicação:

        V1 = V0 @ P
    """

    V1 = V0 @ P

    return V1


# ============================================================
# 15. OBTER O VETOR DO ESTADO ATUAL
# ============================================================

def obter_vetor_estado_atual(
    ultimo_estado,
    P
):
    """
    Seleciona a linha da matriz de transição correspondente
    ao último estado da sequência.

    Exemplo:

        se o último estado for Q, utiliza a linha Q de P.
    """

    indice = ESTADOS_UNICOS.index(
        ultimo_estado
    )

    vetor_estado_atual = P[indice].copy()

    if np.isclose(
        vetor_estado_atual.sum(),
        0.0
    ):

        return None

    return vetor_estado_atual


# ============================================================
# 16. CALCULAR AS PROBABILIDADES DIRECIONAIS
# ============================================================

def calcular_probabilidades_direcionais(vetor):
    """
    Calcula:

        probabilidade de alta = F + A
        probabilidade de queda = Q + S
    """

    prob_alta = float(
        vetor[0] + vetor[1]
    )

    prob_queda = float(
        vetor[2] + vetor[3]
    )

    return prob_alta, prob_queda


# ============================================================
# 17. CLASSIFICAR A DIREÇÃO
# ============================================================

def classificar_direcao(
    prob_alta,
    prob_queda
):
    """
    ALTA:
        probabilidade de alta maior que 55%.

    QUEDA:
        probabilidade de queda maior que 55%.

    NEUTRO:
        nenhuma das duas ultrapassa 55%.
    """

    if prob_alta > LIMITE_DIRECIONAL:

        return "ALTA"

    elif prob_queda > LIMITE_DIRECIONAL:

        return "QUEDA"

    else:

        return "NEUTRO"


# ============================================================
# 18. CLASSIFICAR A PREVISÃO FINAL
# ============================================================

def classificar_previsao(
    V1,
    vetor_estado_atual
):
    """
    Calcula as direções de:

        1. V1;
        2. vetor condicionado ao estado atual.

    Em cada vetor:

        ALTA:
            probabilidade de alta > 55%.

        QUEDA:
            probabilidade de alta < 45%.

        NEUTRO:
            probabilidade de alta entre 45% e 55%.

    A decisão final usa a condição lógica "E":

        COMPRA:
            V1 indica ALTA
            E
            o vetor condicionado indica ALTA.

        VENDA:
            V1 indica QUEDA
            E
            o vetor condicionado indica QUEDA.

        NEUTRO:
            qualquer outra situação.
    """

    prob_alta_v1, prob_queda_v1 = (
        calcular_probabilidades_direcionais(V1)
    )

    prob_alta_cond, prob_queda_cond = (
        calcular_probabilidades_direcionais(
            vetor_estado_atual
        )
    )

    direcao_v1 = classificar_direcao(
        prob_alta_v1,
        prob_queda_v1
    )

    direcao_condicional = classificar_direcao(
        prob_alta_cond,
        prob_queda_cond
    )

    if (
        direcao_v1 == "ALTA"
        and direcao_condicional == "ALTA"
    ):

        classificacao = "COMPRA"

    elif (
        direcao_v1 == "QUEDA"
        and direcao_condicional == "QUEDA"
    ):

        classificacao = "VENDA"

    else:

        classificacao = "NEUTRO"

    return {
        "prob_alta_v1": prob_alta_v1,
        "prob_queda_v1": prob_queda_v1,
        "direcao_v1": direcao_v1,

        "prob_alta_condicional": prob_alta_cond,
        "prob_queda_condicional": prob_queda_cond,
        "direcao_condicional": direcao_condicional,

        "classificacao": classificacao
    }


# ============================================================
# 19. ANALISAR UM ATIVO
# ============================================================

def analisar_ativo(
    conexao,
    ativo,
    coluna_preco
):
    """
    Executa toda a análise de um único ativo.
    """

    datas, precos = buscar_ultimos_fechamentos(
        conexao,
        ativo,
        coluna_preco
    )

    if len(precos) < TAMANHO_JANELA:

        return {
            "ativo": ativo,
            "erro": (
                f"O ativo possui apenas {len(precos)} "
                f"fechamentos. São necessários "
                f"{TAMANHO_JANELA}."
            )
        }

    retornos = calcular_retornos(precos)

    media = calcular_media_retornos(retornos)

    desvio_medio = calcular_desvio_medio(
        retornos,
        media
    )

    estados = classificar_estados(
        retornos,
        desvio_medio
    )

    V0 = construir_vetor_inicial(estados)

    P, contagem = construir_matriz_transicao(
        estados
    )

    V1 = calcular_vetor_previsto(V0, P)

    ultimo_estado = estados[-1]

    vetor_estado_atual = (
        obter_vetor_estado_atual(
            ultimo_estado,
            P
        )
    )

    if vetor_estado_atual is None:

        return {
            "ativo": ativo,
            "erro": (
                "O último estado não possui transições "
                "de saída observadas nesta janela."
            )
        }

    decisao = classificar_previsao(
        V1,
        vetor_estado_atual
    )

    resultado = {
        "ativo": ativo,
        "data_inicial": datas[0],
        "data_final": datas[-1],
        "precos": precos,
        "retornos": retornos,
        "media": media,
        "desvio_medio": desvio_medio,
        "estados": estados,
        "contagem": contagem,
        "V0": V0,
        "P": P,
        "V1": V1,
        "ultimo_estado": ultimo_estado,
        "vetor_estado_atual": vetor_estado_atual,

        "prob_alta_v1":
            decisao["prob_alta_v1"],

        "prob_queda_v1":
            decisao["prob_queda_v1"],

        "direcao_v1":
            decisao["direcao_v1"],

        "prob_alta_condicional":
            decisao["prob_alta_condicional"],

        "prob_queda_condicional":
            decisao["prob_queda_condicional"],

        "direcao_condicional":
            decisao["direcao_condicional"],

        "classificacao":
            decisao["classificacao"],

        "erro": None
    }

    return resultado


# ============================================================
# 20. MOSTRAR O RESULTADO DE UM ATIVO
# ============================================================

def mostrar_resultado(resultado):
    """
    Exibe os cálculos e a previsão de um ativo.
    """

    print("\n" + "=" * 76)
    print(f"ATIVO: {resultado['ativo']}")
    print("=" * 76)

    if resultado["erro"] is not None:

        print("\nNão foi possível calcular a previsão.")
        print("Motivo:", resultado["erro"])

        return

    print(
        "\nJanela utilizada:",
        resultado["data_inicial"],
        "até",
        resultado["data_final"]
    )

    print(
        "Quantidade de fechamentos:",
        len(resultado["precos"])
    )

    print(
        "Quantidade de retornos:",
        len(resultado["retornos"])
    )

    print(
        "\nMédia dos retornos:",
        f"{resultado['media']:.8f}"
    )

    print(
        "Desvio médio:",
        f"{resultado['desvio_medio']:.8f}"
    )

    print("\nSequência de estados:")

    print(" → ".join(resultado["estados"]))

    print(
        "\nÚltimo estado da sequência:",
        resultado["ultimo_estado"]
    )

    print("\nV0 =")

    print(
        np.round(
            resultado["V0"],
            4
        )
    )

    print("\nMatriz de transição P =")

    print(
        np.round(
            resultado["P"],
            4
        )
    )

    print("\nV1 =")

    print(
        np.round(
            resultado["V1"],
            4
        )
    )

    print("\nVetor condicionado ao estado atual =")

    print(
        np.round(
            resultado["vetor_estado_atual"],
            4
        )
    )

    print(
        "\nProbabilidade de alta em V1:",
        f"{resultado['prob_alta_v1']:.4f}"
    )

    print(
        "Probabilidade de queda em V1:",
        f"{resultado['prob_queda_v1']:.4f}"
    )

    print(
        "Direção de V1:",
        resultado["direcao_v1"]
    )

    print(
        "\nProbabilidade condicional de alta:",
        f"{resultado['prob_alta_condicional']:.4f}"
    )

    print(
        "Probabilidade condicional de queda:",
        f"{resultado['prob_queda_condicional']:.4f}"
    )

    print(
        "Direção condicional:",
        resultado["direcao_condicional"]
    )

    print(
        "\nPREVISÃO:",
        resultado["classificacao"]
    )


# ============================================================
# 21. MOSTRAR UM RESUMO DAS PREVISÕES
# ============================================================

def mostrar_resumo(resultados):
    """
    Mostra uma tabela resumida com todos os ativos.
    """

    print("\n")
    print("=" * 116)
    print("RESUMO DAS PREVISÕES")
    print("=" * 116)

    print(
        f"{'ATIVO':<12}"
        f"{'ALTA V1':>11}"
        f"{'QUEDA V1':>12}"
        f"{'ALTA COND.':>13}"
        f"{'QUEDA COND.':>14}"
        f"{'PREVISÃO':>14}"
    )

    print("-" * 116)

    for resultado in resultados:

        if resultado["erro"] is not None:

            print(
                f"{resultado['ativo']:<12}"
                f"{'---':>11}"
                f"{'---':>12}"
                f"{'---':>13}"
                f"{'---':>14}"
                f"{'SEM DADOS':>14}"
            )

        else:

            print(
                f"{resultado['ativo']:<12}"
                f"{resultado['prob_alta_v1']:>11.4f}"
                f"{resultado['prob_queda_v1']:>12.4f}"
                f"{resultado['prob_alta_condicional']:>13.4f}"
                f"{resultado['prob_queda_condicional']:>14.4f}"
                f"{resultado['classificacao']:>14}"
            )

    print("=" * 116)


# ============================================================
# 22. ANALISAR TODOS OS ATIVOS
# ============================================================

def analisar_todos_os_ativos(
    conexao,
    ativos,
    coluna_preco
):
    """
    Executa a análise para todos os ativos cadastrados.
    """

    resultados = []

    for ativo in ativos:

        try:

            resultado = analisar_ativo(
                conexao,
                ativo,
                coluna_preco
            )

        except Exception as erro:

            resultado = {
                "ativo": ativo,
                "erro": str(erro)
            }

        resultados.append(resultado)

        mostrar_resultado(resultado)

    mostrar_resumo(resultados)

    return resultados


# ============================================================
# 23. VALIDAR A DATA DIGITADA
# ============================================================

def converter_data(data_digitada):
    """
    Aceita datas nos formatos:

        21/07/2026
        21-07-2026
        2026-07-21

    A data é devolvida no formato usado pelo banco:

        2026-07-21
    """

    formatos = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d"
    ]

    for formato in formatos:

        try:

            data = datetime.strptime(
                data_digitada,
                formato
            )

            return data.strftime("%Y-%m-%d")

        except ValueError:

            continue

    raise ValueError(
        "Data inválida. Use DD/MM/AAAA."
    )


# ============================================================
# 24. LER UM PREÇO DIGITADO
# ============================================================

def converter_preco(texto):
    """
    Converte o preço digitado para número.

    Aceita tanto vírgula quanto ponto decimal.

    Exemplos:

        15,37
        15.37
    """

    texto = texto.strip()

    # Remove espaços.
    texto = texto.replace(" ", "")

    # Caso o usuário digite no formato brasileiro:
    # 1.234,56
    if "," in texto and "." in texto:

        texto = texto.replace(".", "")
        texto = texto.replace(",", ".")

    else:

        texto = texto.replace(",", ".")

    preco = float(texto)

    if preco <= 0:

        raise ValueError(
            "O fechamento deve ser maior que zero."
        )

    return preco


# ============================================================
# 25. SALVAR UM NOVO FECHAMENTO
# ============================================================

def salvar_fechamento(
    conexao,
    data,
    ativo,
    preco,
    coluna_preco
):
    """
    Insere o fechamento no banco.

    Caso já exista um registro para o mesmo ativo e a mesma
    data, o preço é atualizado.
    """

    cursor = conexao.cursor()

    consulta = f"""
        INSERT INTO "{NOME_TABELA}"
        (data, ativo, "{coluna_preco}")
        VALUES (?, ?, ?)

        ON CONFLICT(data, ativo)
        DO UPDATE SET
            "{coluna_preco}" = excluded."{coluna_preco}"
    """

    cursor.execute(
        consulta,
        (data, ativo, preco)
    )


# ============================================================
# 26. PEDIR OS FECHAMENTOS DO NOVO DIA
# ============================================================

def cadastrar_novos_fechamentos(
    conexao,
    ativos,
    coluna_preco
):
    """
    Pergunta a data e o fechamento de cada ativo.

    Deixar o campo vazio faz o programa pular o ativo.

    Os preços são salvos no banco somente depois que todos
    os ativos forem percorridos.
    """

    print("\n")
    print("=" * 70)
    print("CADASTRO DOS NOVOS FECHAMENTOS")
    print("=" * 70)

    while True:

        data_digitada = input(
            "\nDigite a data do fechamento "
            "(DD/MM/AAAA): "
        ).strip()

        try:

            data_banco = converter_data(
                data_digitada
            )

            break

        except ValueError as erro:

            print("\nErro:", erro)

    print(
        "\nDigite os fechamentos na ordem apresentada."
    )

    print(
        "Pressione ENTER sem digitar nada para pular um ativo."
    )

    print(
        "Digite CANCELAR para abandonar todo o cadastro.\n"
    )

    registros = []

    quantidade_ativos = len(ativos)

    for indice, ativo in enumerate(ativos, start=1):

        while True:

            texto = input(
                f"[{indice}/{quantidade_ativos}] "
                f"{ativo}: "
            ).strip()

            if texto.upper() == "CANCELAR":

                print(
                    "\nCadastro cancelado. "
                    "Nenhum fechamento foi salvo."
                )

                return False

            if texto == "":

                print(f"{ativo}: ignorado.")

                break

            try:

                preco = converter_preco(texto)

                registros.append(
                    (ativo, preco)
                )

                break

            except ValueError:

                print(
                    "Valor inválido. Digite, por exemplo, "
                    "15,37 ou deixe vazio para pular."
                )

    if len(registros) == 0:

        print(
            "\nNenhum fechamento foi informado."
        )

        return False

    print("\n" + "-" * 70)
    print("CONFIRMAÇÃO DOS DADOS")
    print("-" * 70)

    print("Data:", data_banco)

    for ativo, preco in registros:

        print(
            f"{ativo:<15} "
            f"{preco:.4f}"
        )

    while True:

        confirmar = input(
            "\nDeseja salvar esses fechamentos? "
            "(S/N): "
        ).strip().upper()

        if confirmar in ["S", "SIM"]:

            try:

                for ativo, preco in registros:

                    salvar_fechamento(
                        conexao,
                        data_banco,
                        ativo,
                        preco,
                        coluna_preco
                    )

                conexao.commit()

                print(
                    "\nFechamentos salvos com sucesso!"
                )

                return True

            except Exception:

                conexao.rollback()

                print(
                    "\nOcorreu um erro. "
                    "Nenhuma alteração foi salva."
                )

                raise

        elif confirmar in ["N", "NAO", "NÃO"]:

            print(
                "\nCadastro cancelado. "
                "Nenhum fechamento foi salvo."
            )

            return False

        else:

            print(
                "Resposta inválida. Digite S ou N."
            )


# ============================================================
# 27. MENU PRINCIPAL
# ============================================================

def mostrar_menu():
    """
    Mostra as opções disponíveis depois das previsões.
    """

    print("\n")
    print("=" * 70)
    print("O QUE DESEJA FAZER?")
    print("=" * 70)

    print("1 - Cadastrar os fechamentos do novo dia")
    print("2 - Recalcular e mostrar novamente as previsões")
    print("3 - Encerrar o programa")

    opcao = input("\nDigite a opção: ").strip()

    return opcao


# ============================================================
# 28. FUNÇÃO PRINCIPAL
# ============================================================

def main():
    """
    Controla todo o funcionamento do programa.

    Fluxo:

    1. conecta ao banco;
    2. busca os ativos;
    3. calcula todas as previsões;
    4. abre o menu;
    5. permite cadastrar os novos fechamentos;
    6. depois do cadastro, reinicia os cálculos;
    7. continua aberto até o usuário escolher encerrar.
    """

    print("\n")
    print("=" * 70)
    print("ML QUANT - PREVISÃO COM V1 E ESTADO ATUAL")
    print("=" * 70)

    try:

        conexao = conectar_banco()

        verificar_tabela(conexao)

        coluna_preco = descobrir_coluna_preco(
            conexao
        )

        print(
            "\nBanco conectado com sucesso."
        )

        print(
            "Coluna de preço identificada:",
            coluna_preco
        )

        # O laço mantém o programa aberto.
        while True:

            ativos = buscar_ativos(conexao)

            if len(ativos) == 0:

                print(
                    "\nNenhum ativo foi encontrado no banco."
                )

                break

            print(
                f"\nQuantidade de ativos encontrados: "
                f"{len(ativos)}"
            )

            analisar_todos_os_ativos(
                conexao,
                ativos,
                coluna_preco
            )

            while True:

                opcao = mostrar_menu()

                if opcao == "1":

                    salvou = cadastrar_novos_fechamentos(
                        conexao,
                        ativos,
                        coluna_preco
                    )

                    if salvou:

                        print(
                            "\nOs dados foram atualizados."
                        )

                        print(
                            "As previsões serão recalculadas "
                            "com a nova janela de 20 dias."
                        )

                        input(
                            "\nPressione ENTER para continuar..."
                        )

                        # Sai do menu interno e volta ao começo
                        # do laço principal.
                        break

                elif opcao == "2":

                    print(
                        "\nRecalculando as previsões..."
                    )

                    input(
                        "\nPressione ENTER para continuar..."
                    )

                    # Sai do menu e recalcula tudo.
                    break

                elif opcao == "3":

                    print(
                        "\nPrograma encerrado."
                    )

                    return

                else:

                    print(
                        "\nOpção inválida. "
                        "Digite 1, 2 ou 3."
                    )

    except sqlite3.Error as erro:

        print("\nErro relacionado ao banco de dados:")

        print(erro)

    except Exception as erro:

        print("\nOcorreu um erro durante a execução:")

        print(erro)

    finally:

        # Fecha a conexão mesmo que algum erro aconteça.
        if "conexao" in locals():

            conexao.close()

            print(
                "\nConexão com o banco encerrada."
            )


# ============================================================
# 29. INICIAR O PROGRAMA
# ============================================================

if __name__ == "__main__":

    main()
