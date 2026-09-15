import datetime
import os
from dotenv import load_dotenv
import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime  

load_dotenv()  # load significa carregar e dotenv é o ficheiro .env



conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = conn.cursor()

print("Ligação bem sucedida!")

#funcao para carregar os funcionarios   MYSQL 
def carregar_funcionarios():
    cursor.execute("SELECT nome FROM FUNCIONARIOS")
    funcionarios = [row[0] for row in cursor.fetchall()]
    combo_funcionarios['values'] = funcionarios

    
#função  para registar a picagem do funcionário
def registar_picagem():
    nome = combo_funcionarios.get().strip()
    senha = entrada_password.get().strip()

    #Aviso caso falte preencher algum campo
    if not nome or not senha:
        messagebox.showwarning(
            "Campos em falta",
            "Preencha o nome e a senha."
        )
        return

    try:
        # 1. Procurar o funcionário
        cursor.execute(
            """
            SELECT id_funcionario
            FROM funcionarios
            WHERE nome = %s AND senha = SHA2(%s, 256)
            """,
            (nome, senha)
        )

        funcionario = cursor.fetchone()

        if funcionario is None:
            messagebox.showerror(
                "Erro",
                "Funcionário ou senha incorretos."
            )
            return

        funcionario_id = funcionario[0]

        # 2. Obter a última picagem deste funcionário
        cursor.execute(
            """
            SELECT tipo
            FROM picagem
            WHERE id_funcionario = %s
            ORDER BY data DESC
            LIMIT 1
            """,
            (funcionario_id,)
        )

        ultima_picagem = cursor.fetchone()

        # 3. Determinar se é entrada ou saída
        if ultima_picagem is None or ultima_picagem[0] == "SAIDA":
            tipo = "ENTRADA"
        else:
            tipo = "SAIDA"

        # 4. Inserir a nova picagem
        cursor.execute(
            """
            INSERT INTO picagem
            (id_funcionario, data, tipo)
            VALUES (%s, %s, %s)
            """,
            (funcionario_id, datetime.now(), tipo)
        )
     

        conn.commit()
        atualizar_tabela()


        messagebox.showinfo(
            "Picagem registada",
            f"{tipo.capitalize()} registada com sucesso!"
        )

        # 5. Limpar os campos
        combo_funcionarios.set("")
        entrada_password.delete(0, tk.END)

    except mysql.connector.Error as erro:
        conn.rollback()

        messagebox.showerror(
            "Erro na base de dados",
            f"Ocorreu um erro:\n{erro}"
        )


#funcao para atualizar a tabela de picagens
def atualizar_tabela():
    for i in tabela.get_children():
        tabela.delete(i)

    cursor.execute("""
        SELECT funcionarios.nome, picagem.data, picagem.tipo
        FROM picagem, funcionarios 
        WHERE funcionarios.id_funcionario = picagem.id_funcionario
    """)

    resultados = cursor.fetchall()

    for linha in resultados:
        tabela.insert("", tk.END, values=linha)



#JANELA

janela = tk.Tk() # criar o site 
janela.title("Gestão de Assiduidade") # título da janela 
janela.geometry("800x800") # tamanho da janela


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


# ENTRADA DO NOME
nome_label = tk.Label(janela,text="Funcionário: ",font=("Arial", 14))
nome_label.pack(pady=10)



combo_funcionarios = ttk.Combobox(janela,font=("Arial"))
combo_funcionarios.pack(pady=10)
carregar_funcionarios()



# ENTRADA_PASSWORD

password_label = tk.Label(
    janela,
    text="Senha:",
    font=("Arial", 14)
)
password_label.pack(pady=10)



entrada_password = tk.Entry(
    janela,
    font=("Arial", 14),
    show="*"
)
entrada_password.pack(pady=10)  


# 
registo = tk.Button(
    janela,
    text="Confirmar",
    font=("Arial",14),
    command=registar_picagem
)

registo.pack(padx=10)

#lista de picagens

tabela = ttk.Treeview(
    janela,
    columns=("nome", "data", "tipo"),
    show="headings"
)

tabela.heading("nome", text="Funcionário")
tabela.heading("data", text="Data/Hora")
tabela.heading("tipo", text="Tipo")

tabela.pack(pady=20)

cursor.execute("""
    SELECT funcionarios.nome, picagem.data, picagem.tipo
    FROM picagem, funcionarios where funcionarios.id_funcionario = picagem.id_funcionario
""")

resultados = cursor.fetchall()


for linha in resultados:
    tabela.insert("", tk.END, values=linha)
    
    
#chamada da função para atualizar a tabela de picagens
atualizar_tabela()


cursor.execute("""
    SELECT picagem.id_funcionario, funcionarios.nome, 
           DATE_FORMAT(picagem.data, '%d/%m/%Y %H:%i:%s') AS data,
           picagem.tipo
    FROM picagem
    JOIN FUNCIONARIOS 
    ON funcionarios.id_funcionario = picagem.id_funcionario
    ORDER BY picagem.id_funcionario, picagem.data
""")

picagens = cursor.fetchall()


# Criar um dicionário 
dicionario_funcionarios = {}

# listas que guardam quais funcionários estão ou não na empresa
a_trabalhar = []
a_descansar = []

# percorrer a lista das picagens 
for picagem in picagens:
    id_funcionario = picagem[0]
    nome = picagem[1]
    data = picagem[2]
    tipo = picagem[3]

    dicionario_funcionarios[id_funcionario] = {
        "nome": nome,
        "tipo": tipo
    }


for id_funcionario in dicionario_funcionarios:

    nome = dicionario_funcionarios[id_funcionario]["nome"]
    tipo = dicionario_funcionarios[id_funcionario]["tipo"]

    if tipo == "ENTRADA":
        a_trabalhar.append(nome) # adicionar à lista a_trabalhar 
        print(f"{nome}, está na empresa")
    else:
        a_descansar.append(nome) # adicionar à lista a_descansar
        print(f"{nome}, não está na empresa")
        

#RODAR JANELA

janela.mainloop()