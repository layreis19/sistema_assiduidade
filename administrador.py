"""
O QUE ESTE FICHEIRO FAZ?
Mostra o formulário de login do administrador (nome e senha).
- Procura o nome na tabela FUNCIONARIOS (só tipo ADMIN).
- Verifica se a conta está ativa e se a senha está certa (bcrypt).
- Se estiver tudo bem, avisa o main.py para mostrar os botões de admin.
- Tem a função reiniciar_login(), usada pelo botão Sair.
"""

import tkinter as tk
from tkinter import messagebox
import bcrypt
import mysql.connector
from ligacao import conn

BG = "#EAF6FF"             # Fundo principal
PRIMARY = "#3F8FC1"        # Azul principal
PRIMARY_DARK = "#2F78A8"   # Azul mais escuro
BLUE_LIGHT = "#B5D9EA"     # Azul claro
BLUE_VERY_LIGHT = "#D9EDF7"
CARD = "#FFFFFF"           # Branco
TEXT = "#1E3A52"           # Texto principal
TEXT_SECONDARY = "#6B879C" # Texto secundário
BORDER = "#C7E3F2"


class PaginaAdministrador(tk.Frame):
    def __init__(self, parent, mostrar_botoes_admin):
        super().__init__(parent, bg=BG)
        self.parent = parent
        self.mostrar_botoes_admin = mostrar_botoes_admin
        self.cursor = conn.cursor(buffered=True)
        self.frame_login = None

        # mostrar o formulário de login
        self.tela_login()

    #login
    def tela_login(self):
        self.frame_login = tk.Frame(
            self,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1)
        self.frame_login.pack(expand=True, padx=40, ipadx=30, ipady=30)

        tk.Label(self.frame_login,
                 text="ÁREA ADMINISTRATIVA",
                 font=("Arial", 16, "bold"),
                 bg=CARD, fg=TEXT).pack(pady=(10, 20))

        # Nome
        tk.Label(self.frame_login,
                 text="Nome:", 
                 font=("Arial", 10, "bold"),
                 bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(5, 2)
                )
        
        self.ent_nome = tk.Entry(
            self.frame_login,
            font=("Arial", 11), 
            width=25,
            bg=BLUE_VERY_LIGHT,
            fg=TEXT, bd=0,
            highlightbackground=BORDER, highlightthickness=1
        )
        self.ent_nome.pack(padx=20, pady=(0, 15), ipady=4)

        # Senha
        tk.Label(self.frame_login, text="Senha:", font=("Arial", 10, "bold"),
                 bg=CARD, fg=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(5, 2))

        self.ent_senha = tk.Entry(
            self.frame_login, show="*", font=("Arial", 11), width=25,
            bg=BLUE_VERY_LIGHT, fg=TEXT, bd=0,
            highlightbackground=BORDER, highlightthickness=1
        )
        self.ent_senha.pack(padx=20, pady=(0, 20), ipady=4)

        # Botão
        tk.Button(
            self.frame_login, 
            text="Autenticar",
            font=("Arial", 11, "bold"),
            bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK,
            activeforeground="white", bd=0, cursor="hand2", width=15,
            command=self.autenticar_admin
        ).pack(pady=(10, 10), ipady=5)

    
    #  BOTÃO "SAIR": volta a mostrar o login vazio
    
    def reiniciar_login(self):
        if self.frame_login is not None and self.frame_login.winfo_exists():
            self.frame_login.destroy()
        self.tela_login()

   
    # AUTENTICAR
    def autenticar_admin(self):
        usuario = self.ent_nome.get().strip()
        senha_digitada = self.ent_senha.get().strip()

        if not usuario or not senha_digitada:
            messagebox.showwarning("Aviso", "Por favor, preencha todos os campos!")
            return

        try:
            # LOWER dos dois lados: "ana", "Ana" e "ANA" encontram a mesma pessoa.
            # tipo = 'ADMIN' garante que só administradores entram.
            self.cursor.execute(
                """
                SELECT nome, senha, estado
                FROM FUNCIONARIOS
                WHERE LOWER(nome) = LOWER(%s)
                  AND tipo = 'ADMIN'
                """,
                (usuario,)
            )
            resultado = self.cursor.fetchone()

            if resultado is None:
                messagebox.showerror("Erro", "Funcionário não encontrado!")
                return

            nome_real, senha, estado = resultado

            if estado != "ATIVO":
                messagebox.showerror("Acesso Negado", "Esta conta está desativada.")
                return

            if not senha:
                messagebox.showerror("Erro", "Esta conta não tem senha definida.")
                return

            if bcrypt.checkpw(senha_digitada.encode("utf-8"), senha.encode("utf-8")):
                messagebox.showinfo("Sucesso", f"Bem-Vindo, {nome_real}!")

                self.frame_login.destroy()
                self.mostrar_botoes_admin()   # o main trata do resto
            else:
                messagebox.showerror("Erro", "Senha incorreta!")

        except mysql.connector.Error as erro:
            messagebox.showerror("Erro", f"Erro na base de dados: {erro}")