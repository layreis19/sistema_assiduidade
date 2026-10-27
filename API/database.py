import os
import mysql.connector
from dotenv import load_dotenv

#procura o env na pasta do projeto
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ENV = os.path.join(PASTA_PROJETO, ".." ,".env")
load_dotenv(CAMINHO_ENV)


def obter_ligacao():
    """""Abre uma ligaçao nova á base de dados (uma por pedido)"""
    
    return mysql.connector.connect(
        host= os.getenv("DB_HOST"),
        port= os.getenv("DB_PORT"),
        user= os.getenv("DB_USER"),
        password= os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        collation="utf8mb4_general_ci"
         
    )
