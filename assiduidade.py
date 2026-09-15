import datetime
import os
from dotenv import load_dotenv
import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime  

load_dotenv()  



conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = conn.cursor()

print("Ligação bem sucedida!")


#JANELA

janela = tk.Tk()
janela.title("Gestão de Assiduidade")
janela.geometry("800x800")


titulo = tk.Label(
    janela,
    text="RELÓGIO DE PONTO",
    font=("Arial", 20)
)

titulo.pack(pady=20)

#RELOGIO

relogio = tk.Label(
    janela,
    font=("Arial", 20)
)

relogio.pack(pady=20)


def atualizar_relogio():

    hora = datetime.now().strftime("%H:%M:%S")

    relogio.config(text=hora)

    # Atualiza novamente daqui a 1 segundo
    janela.after(1000, atualizar_relogio)

atualizar_relogio()

#funcao para carregar os funcionarios   MYSQL 
def carregar_funcionarios():
    cursor.execute("SELECT nome FROM FUNCIONARIOS")
    funcionarios = [row[0] for row in cursor.fetchall()]
    combo_funcionarios['values'] = funcionarios


# ENTRADA DO NOME
nome_label = tk.Label(janela,text="Funcionário: ",font=("Arial", 14))
nome_label.pack(pady=10)

combo_funcionarios = ttk.Combobox(janela,font=("Arial"))
combo_funcionarios.pack(pady=10)
carregar_funcionarios()

# ENTRADA_PASSWORD

password_label = tk.Label(janela, text="Password:",font=("Arial", 14)
)
password_label.pack(pady=10)

entrada_password = tk.Entry(janela, font=("Arial", 14),show="*")
entrada_password.pack(pady=10)  








#RODAR JANELA

janela.mainloop()