import tkinter as tk
from tkinter import messagebox
import bcrypt
import mysql.connector
from ligacao import conn 








class PaginaFuncionarios(tk.Frame):
    

    def __init__(self, parent):
        super().__init__(parent)

        self.cursor = conn.cursor()

        titulo = tk.Label(
            self,
            text="GESTÃO DE FUNCIONÁRIOS",
            font=("Arial", 24)
        )
        titulo.pack(pady=50)

        # Nome
        nome_label = tk.Label(
            self,
            text="Nome:",
            font=("Arial", 12)
        )
        nome_label.pack(pady=5)

        self.entry_nome = tk.Entry(self)
        self.entry_nome.pack(pady=5)

        # Senha
        senha_label = tk.Label(
            self,
            text="Senha:",
            font=("Arial", 12)
        )
        senha_label.pack(pady=5)

        self.entry_senha = tk.Entry(self, show="*")
        self.entry_senha.pack(pady=5)

        # Tipo
        tipo_label = tk.Label(
            self,
            text="Tipo:",
            font=("Arial", 12)
        )
        tipo_label.pack(pady=5)

        self.entry_tipo = tk.Entry(self)
        self.entry_tipo.pack(pady=5)

        # Botão
        btn_adicionar = tk.Button(
            self,
            text="Adicionar Funcionário",
            command=self.adicionar_funcionario

        )
        btn_adicionar.pack(pady=10)

    # Adicionar funcionário
    def adicionar_funcionario(self):

        nome = self.entry_nome.get().strip()
        senha = self.entry_senha.get().strip()
        tipo = self.entry_tipo.get().strip()

        if not nome or not senha or not tipo:
            messagebox.showerror(
                "Erro",
                "Todos os campos são obrigatórios!"
            )
            return

        try:
            # Criar hash da senha introduzida
            senha_hash = bcrypt.hashpw(
                senha.encode("utf-8"),
                bcrypt.gensalt()
            )

            self.cursor.execute(
                """
                INSERT INTO funcionarios(nome, senha, tipo)
                VALUES (%s, %s, %s)
                """,
                (nome, senha_hash, tipo)
            )
            

            conn.commit()
           

            messagebox.showinfo(
                "Sucesso",
                f"Funcionário '{nome}' adicionado!"
            )

            # Limpar campos
            self.entry_nome.delete(0, tk.END)
            self.entry_senha.delete(0, tk.END)
            self.entry_tipo.delete(0, tk.END)

        except mysql.connector.IntegrityError:
            messagebox.showerror(
                "Erro",
                "Funcionário já existe!"

            )