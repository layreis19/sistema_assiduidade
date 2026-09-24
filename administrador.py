import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import bcrypt
import mysql.connector
from ligacao import conn
from funcionarios import PaginaFuncionarios
import cores


class PaginaAdministrador(tk.Frame):
    def __init__(self,parent, mostrar_botoes_admin):
        super().__init__(parent, bg= BG)
        self.parent = parent
        self.mostrar_botoes_admin= mostrar_botoes_admin
        self.cursor = conn.cursor(buffered=True)


       #mostrar a tela login
        self.tela_login()

 # Função  Login

    def tela_login(self):
        #cria um sub-fram
        self.frame_login = tk.Frame(self,bg=cores.CARD, highlightbackground=cores.BORDER,highlightthickness=1)

        self.frame_login.pack(expand=True,padx=40,ipadx=30,ipady=30)

        titulo = tk.Label(self.frame_login, text= "ÁREA ADMINISTRATIVA", font= ("Arial",16,"bold"),bg=cores.CARD, fg=cores.TEXT)
        titulo.pack(pady=(10, 20))

        nome_login = tk.Label(self.frame_login, text= "Nome:",font=( "Arial",10,"bold"), bg= cores.CARD,fg= cores.TEXT)
        nome_login.pack(anchor="w", padx=20, pady=(5,2))

       #caixa de entrada nome
        self.ent_nome = tk.Entry(
            self.frame_login,
            font= ("Arial",11),
            width=25,
            bg=cores.BLUE_VERY_LIGHT,
            fg= cores.TEXT,
            bd= 0,
            highlightbackground= cores.BORDER,
            highlightthickness=1
            )
        self.ent_nome.pack(padx=20, pady=(0,15), ipady=4)

        senha_login= tk.Label(
            self.frame_login,
            text= "Senha:",
            font=("Arial", 10, "bold"),
            bg= cores.CARD,
            fg=cores.TEXT
        )
        senha_login.pack(anchor="w",padx=20,pady=(5,2))

        self.ent_senha = tk.Entry(
            self.frame_login,
            show="*",
            font=("Arial,11"),
            width=25,
            bg=cores.BLUE_VERY_LIGHT,
            fg=cores.TEXT,
            bd=0,
            highlightbackground=cores.BORDER,
            highlightthickness=1
        )
        self.ent_senha.pack(padx=20, pady=(0,20), ipady=4)

        #botao autenticar 

        btn_entrar = tk.Button(
            self.frame_login,
            text= "Autenticar",
            font=("Arial", 11, "bold"),
            bg= cores.PRIMARY,
            fg="white",
            activebackground= cores.PRIMARY_DARK,
            activeforeground="white",
            bd=0,
            cursor="hand2",
            width=15,
            command=self.autenticar_admin
        )
        btn_entrar.pack(pady=(10,10), ipady=5)

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
                self.gestao_funcionarios()
              
            else:
                messagebox.showerror("Erro", "Senha incorreta!")

        except mysql.connector.Error as erro:
            messagebox.showerror("Erro", f"Erro na base de dados: {erro}")

    def gestao_funcionarios(self):
        self.pagina_gestao = PaginaFuncionarios(self)
        self.pagina_gestao.pack(fill="both", expand= True)