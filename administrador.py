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
import widgets as w


class PaginaAdministrador(tk.Frame):
    def __init__(self,parent, mostrar_botoes_admin):
        super().__init__(parent, bg=w.COR_FUNDO)
        self.parent = parent
        self.mostrar_botoes_admin= mostrar_botoes_admin
        self.cursor = conn.cursor(buffered=True)


       #mostrar a tela login
        self.tela_login()

 # Função  Login

    def tela_login(self):
        # cartão branco com borda, centrado na página
        self.frame_login = tk.Frame(
            self, bg=w.COR_FUNDO,
            highlightbackground=w.COR_BORDA, highlightthickness=1)
        self.frame_login.pack(expand=True, padx=40, ipadx=30, ipady=30)

        w.criar_titulo(self.frame_login, "ÁREA ADMINISTRATIVA").pack(pady=(10, 20))

        # nome
        w.criar_label(self.frame_login, "Nome:", negrito=True).pack(anchor="w", padx=20, pady=(5, 2))
        self.ent_nome = w.criar_entrada(self.frame_login)
        self.ent_nome.pack(padx=20, pady=(0, 15), ipady=4)

        # senha
        w.criar_label(self.frame_login, "Senha:", negrito=True).pack(anchor="w", padx=20, pady=(5, 2))
        self.ent_senha = w.criar_entrada(self.frame_login, senha=True)
        self.ent_senha.pack(padx=20, pady=(0, 20), ipady=4)

        # botão autenticar
        w.criar_botao(self.frame_login, "Autenticar", self.autenticar_admin, largura=15).pack(pady=10, ipady=5)

        #botao sair
    def reiniciar_login(self):
        
        if self.frame_login is not None and self.frame_login.winfo_exists():
            self.frame_login.destroy()
        self.tela_login()

        #função autenticar

    def autenticar_admin(self):
        usuario = self.ent_nome.get().strip()
        senha_digitada = self.ent_senha.get().strip()

        if not usuario or not senha_digitada:
            messagebox.showwarning("Aviso", "Por favor, preencha todos os campos!")
            return

        try:
            # Comparação de nome sem distinção de maiúsculas/minúsculas
            # (LOWER dos dois lados), em vez de tentar adivinhar a
            # capitalização certa no lado do Python — "ana costa",
            # "Ana Costa" e "ANA COSTA" devem encontrar a mesma pessoa.
            #
            # "AND tipo = 'ADMIN'" já filtra aqui: um colaborador com o
            # mesmo nome de um admin nunca é confundido com ele nesta
            # consulta, porque só candidatos a admin são considerados.
            self.cursor.execute(
                """
                SELECT nome, senha, estado
                FROM funcionarios
                WHERE LOWER(nome) = LOWER(%s)
                  AND tipo = 'ADMIN'
                """,
                (usuario,)
            )
            resultado = self.cursor.fetchone()

            if resultado is None:
                messagebox.showerror("Erro", "Funcionario não encontrado!")
                return

            nome_real, senha, estado = resultado

            # Comparar sempre com o valor real do ENUM ("ATIVO"/"INATIVO"),
            # nunca com "Inativo" — a comparação anterior nunca disparava
            # porque a base de dados guarda sempre em maiúsculas.
            if estado != "ATIVO":
                messagebox.showerror("Acesso Negado", "Esta conta está desativada.")
                return

            if bcrypt.checkpw(senha_digitada.encode('utf-8'), senha.encode('utf-8')):
                messagebox.showinfo("Sucesso", f"Bem-Vindo, {nome_real}!")

                self.frame_login.destroy()
                
                self.mostrar_botoes_admin()
                
              
            else:
                messagebox.showerror("Erro", "Senha incorreta!")

        except mysql.connector.Error as erro:
            messagebox.showerror("Erro", f"Erro na base de dados: {erro}")