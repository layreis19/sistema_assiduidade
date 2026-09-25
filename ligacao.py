# Pra que serve esse ficheiro?
# Liga à base de dados MySQL. Antes disso, garante duas coisas, para que
# o projeto funcione numa máquina nova sem passos manuais:
#   1. Se não existir um ficheiro .env, cria um agora, perguntando as
#      credenciais no terminal (com valores por omissão sugeridos).
#   2. Se a base de dados indicada no .env ainda não existir no servidor
#      MySQL, cria-a a partir do script SQL do projeto (SCRIPT_SQL) antes
#      de tentar ligar-se a ela.
#
# O resto do projeto continua a importar `conn` e `cursor` deste ficheiro
# exatamente como antes — nada muda do lado de quem usa a ligação.

import os
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv


PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ENV = os.path.join(PASTA_PROJETO, ".env")

# Nome do ficheiro com a estrutura da base de dados (CREATE TABLE, dados
# iniciais de HORARIO, o admin padrão, etc). Se este ficheiro for
# renomeado no projeto, atualizar também aqui.
SCRIPT_SQL = os.path.join(PASTA_PROJETO, "assiduidade2.sql")


def criar_env_interativo():
    """
    Pergunta as credenciais da base de dados no terminal e escreve um
    ficheiro .env com elas. Só é chamada quando o .env ainda não existe
    (ex: primeira vez que alguém corre o projeto numa máquina nova).
    Cada pergunta tem um valor por omissão sugerido entre parêntesis
    retos — basta premir Enter para o aceitar.
    """

    print("Não foi encontrado nenhum ficheiro .env — vamos criar um agora.")
    print("(prime Enter para aceitar o valor sugerido entre [colchetes])\n")

    def perguntar(rotulo, valor_por_omissao):
        resposta = input(f"{rotulo} [{valor_por_omissao}]: ").strip()
        return resposta if resposta else valor_por_omissao

    host = perguntar("Host da base de dados", "127.0.0.1")
    porta = perguntar("Porta", "3306")
    utilizador = perguntar("Utilizador MySQL", "root")
    senha = perguntar("Password MySQL", "")
    nome_bd = perguntar("Nome da base de dados", "ASSIDUIDADE2")

    conteudo = (
        f'DB_HOST={host}\n'
        f'DB_PORT={porta}\n'
        f'DB_NAME="{nome_bd}"\n'
        f'DB_USER={utilizador}\n'
        f'DB_PASSWORD={senha}\n'
    )

    with open(CAMINHO_ENV, "w", encoding="utf-8") as ficheiro:
        ficheiro.write(conteudo)

    print(f"\nFicheiro .env criado em: {CAMINHO_ENV}")
    print("(podes editá-lo manualmente a qualquer momento)\n")


def criar_estrutura_bd(host, porta, utilizador, senha):
    """
    Corre o script SQL do projeto para criar a base de dados e todas as
    tabelas, num servidor MySQL onde essa base de dados ainda não existe.
    Liga-se ao servidor SEM indicar nenhuma base de dados (o próprio
    script tem "CREATE DATABASE IF NOT EXISTS" + "USE"), corre o ficheiro
    todo de uma vez (multi=True processa os vários comandos separados
    por ";"), e fecha essa ligação temporária.
    """

    print(f"Base de dados ainda não existe — a criar a partir de {os.path.basename(SCRIPT_SQL)}...")

    with open(SCRIPT_SQL, "r", encoding="utf-8") as ficheiro:
        script = ficheiro.read()

    ligacao_temporaria = mysql.connector.connect(
        host=host,
        port=porta,
        user=utilizador,
        password=senha,
    )

    cursor_temporario = ligacao_temporaria.cursor()

    # Dividir o script em comandos individuais (separados por ";") e
    # correr um a um. Evitamos cursor.execute(script, multi=True) porque
    # esse parâmetro não está disponível em todas as versões/instalações
    # do mysql-connector-python (varia consoante a implementação do
    # driver usada) — dividir e executar um a um funciona sempre, seja
    # qual for a versão instalada. Isto é seguro para este script porque
    # nenhum comando tem ";" dentro de valores ou comentários.
    comandos = [comando.strip() for comando in script.split(";") if comando.strip()]

    for comando in comandos:
        try:
            cursor_temporario.execute(comando)
        except mysql.connector.Error as erro:
            # Mostra qual comando falhou, para facilitar corrigir o
            # script em vez de só saber "algo correu mal".
            print(f"Erro ao correr este comando do script:\n{comando}\n")
            raise erro

    ligacao_temporaria.commit()
    cursor_temporario.close()
    ligacao_temporaria.close()

    print("Base de dados criada com sucesso.")


def obter_ligacao():
    """
    Devolve uma ligação à base de dados configurada no .env, criando o
    .env e/ou a estrutura da base de dados primeiro, se for preciso.
    """

    if not os.path.exists(CAMINHO_ENV):
        criar_env_interativo()

    load_dotenv(CAMINHO_ENV)

    host = os.getenv("DB_HOST")
    porta = os.getenv("DB_PORT")
    utilizador = os.getenv("DB_USER")
    senha = os.getenv("DB_PASSWORD")
    nome_bd = os.getenv("DB_NAME")

    try:
        return mysql.connector.connect(
            host=host,
            port=porta,
            user=utilizador,
            password=senha,
            database=nome_bd,
        )

    except mysql.connector.Error as erro:
        # ER_BAD_DB_ERROR (1049) = "Unknown database" — é o sinal de que a
        # base de dados ainda não existe neste servidor. Qualquer outro
        # erro (credenciais erradas, servidor em baixo, etc.) continua a
        # ser propagado tal como antes, sem tentar "corrigir" nada.
        if erro.errno != errorcode.ER_BAD_DB_ERROR:
            raise

        criar_estrutura_bd(host, porta, utilizador, senha)

        return mysql.connector.connect(
            host=host,
            port=porta,
            user=utilizador,
            password=senha,
            database=nome_bd,
        )


conn = obter_ligacao()
cursor = conn.cursor(buffered=True)

print("Ligação bem sucedida!")