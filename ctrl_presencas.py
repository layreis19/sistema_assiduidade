

import tkinter as tk
from tkinter import ttk
from ligacao import conn


class PaginaPresencas(tk.Frame):

    def __init__(self, parent):

        super().__init__(parent)

        titulo = tk.Label(
            self,
            text="CONTROLO DE PRESENÇAS",
            font=("Arial", 24)
        )

        titulo.pack(pady=50)

        self.tabela = ttk.Treeview(
            self, 
            columns=("nome", "estado"),
            show="headings")
                        
        self.tabela.heading("nome", text="Funcionário")
        self.tabela.heading("estado", text="Estado")

        self.tabela.pack(pady=10)
           

        cursor = conn.cursor()

        cursor.execute("""
            SELECT picagem.id_funcionario,
                    funcionarios.nome,
                    picagem.tipo
            FROM picagem
            JOIN funcionarios
            ON funcionarios.id_funcionario = picagem.id_funcionario
            ORDER BY picagem.id_funcionario, picagem.data
        """)

        picagens = cursor.fetchall()
        print(picagens)


        dicionario_funcionarios = {}

        for picagem in picagens:

            id_funcionario = picagem[0]
            nome = picagem[1]
            tipo = picagem[2]

            dicionario_funcionarios[id_funcionario] = {
                "nome": nome,
                "tipo": tipo
            }

        print(dicionario_funcionarios)

        # Limpar a tabela
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        # Criar as cores
        self.tabela.tag_configure("presente", foreground="green")
        self.tabela.tag_configure("ausente", foreground="red")



        # Percorrer os funcionários
        for id_funcionario, dados in dicionario_funcionarios.items():

            nome = dados["nome"]
            tipo = dados["tipo"]

            print(nome)
            print(tipo)


            if tipo == "ENTRADA":
                estado = "PRESENTE"
                tag = "presente"

            elif tipo == "SAIDA":
                estado = "AUSENTE"
                tag = "ausente"

            self.tabela.insert(
                "",
                "end",
                values=(nome, estado),
                tags=(tag,))