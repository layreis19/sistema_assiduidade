# Pra que serve esse ficheiro?
# Este ficheiro é responsável por criar a página de gestão de funcionários, permitindo adicionar novos funcionários, editar informações existentes
#  e eliminar funcionários da base de dados. Ele também lida com a validação de entrada e
#  a comunicação com a base de dados para garantir que as operações sejam realizadas corretamente.


import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
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

        #formulario para adicionar funcionário

        nome_label = tk.Label( self,text="Nome:", font=("Arial", 12) )
        nome_label.pack(pady=5)

        self.entry_nome = tk.Entry(self)
        self.entry_nome.pack(pady=5)

        senha_label = tk.Label(
            self,
            text="Senha:",
            font=("Arial", 12)
        )
        senha_label.pack(pady=5)

        self.entry_senha = tk.Entry(self, show="*")
        self.entry_senha.pack(pady=5)

        # Tipo
        tipo_label = tk.Label( self, text="Tipo:", font=("Arial", 12)  )
        tipo_label.pack(pady=5)

        self.combo_tipo = ttk.Combobox(self, values=["Admin", "Colaborador"])
        self.combo_tipo['values'] = ("Admin", "Colaborador")
        self.combo_tipo.pack(pady=5)


        #caixa de botoes para adicionar, alterar e ativar/desativar funcionário
        frame_botoes=tk.Frame(self)
        frame_botoes.pack(pady=10)

        # Botão adicionar funcionário
        btn_adicionar = tk.Button( frame_botoes, text="Adicionar",command=self.adicionar_funcionario )
        btn_adicionar.pack(side=tk.LEFT, padx=10, pady=10)

         #Botão alterar funcionário
        btn_alterar = tk.Button( frame_botoes, text="Alterar", command= self.alterar_funcionario )
        btn_alterar.pack(side=tk.LEFT, padx=10, pady=10)

        # Botão ativar/desativar funcionário
        btn_ativar_desativar = tk.Button( frame_botoes, text="Ativar/Desativar", command= self.ativar_desativar_funcionario )
        btn_ativar_desativar.pack(side=tk.LEFT, padx=10, pady=10)

     

       

        self.tabela = ttk.Treeview( self, columns=("id_funcionario", "nome", "tipo", "estado"), show="headings")
        self.tabela.heading("id_funcionario", text="ID")
        self.tabela.heading("nome", text="Funcionário")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("estado", text="Estado")
        
        self.tabela.pack( fill="both",expand=True, padx=30, pady=20 )



    # CRIAR UM FUNCIONÁRIO
    def adicionar_funcionario(self):

        nome = self.entry_nome.get().strip().capitalize()
        senha = self.entry_senha.get().strip()
        tipo = self.combo_tipo.get().strip() 
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

            # Inserir o funcionário na base de dados
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
            self.combo_tipo.set("")

        except mysql.connector.IntegrityError:
            messagebox.showerror(
                "Erro",
                "Funcionário já existe!"

            )


        # Atualizar a tabela de funcionários
        self.atualizar_funcionarios()
    

    def atualizar_funcionarios(self):
        # Limpar a tabela
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        # Consultar os funcionários na base de dados
        funcionarios = self.consultar_funcionarios()

        # Adicionar os funcionários à tabela
        for funcionario in funcionarios:
            self.tabela.insert(
                "",
                "end",
                values=funcionario
            )


    #CONSULTAR FUNCIONÁRIOS

    def consultar_funcionarios(self):
        self.cursor.execute(
            """
            SELECT id_funcionario, nome, tipo, estado
            FROM funcionarios
            """
        )
        return self.cursor.fetchall()


    def alterar_funcionario(self):

        # Obter o funcionário selecionado na tabela
        item_selecionado = self.tabela.selection()
        if not item_selecionado:
            messagebox.showerror(
                "Erro",
                "Selecione um funcionário para alterar!"
            )
            return

        # Obter os dados do funcionário selecionado
        item = self.tabela.item(item_selecionado[0])
        id_funcionario = item["values"][0]
        nome_atual = item["values"][1]
        tipo_atual = item["values"][2]

        # Criar uma nova janela para alterar os dados do funcionário
        janela_alterar = tk.Toplevel(self)
        janela_alterar.title("Alterar Funcionário")

        # Nome
        nome_label = tk.Label(janela_alterar, text="Nome:")
        nome_label.pack(pady=5)
        entry_nome = tk.Entry(janela_alterar)
        entry_nome.insert(0, nome_atual)
        entry_nome.pack(pady=5)

        # Tipo
        tipo_label = tk.Label(janela_alterar, text="Tipo:")
        tipo_label.pack(pady=5)
        combo_tipo = ttk.Combobox(janela_alterar, values=["Admin", "Colaborador"])
        combo_tipo.set(tipo_atual)
        combo_tipo.pack(pady=5)

        #senha
        senha_label = tk.Label(janela_alterar, text="Senha:")
        senha_label.pack(pady=5)
        entry_senha = tk.Entry(janela_alterar, show="*")
        entry_senha.pack(pady=5)





   #ativaou desativar funcionário
    def ativar_desativar_funcionario(self):

        # Obter o funcionário selecionado na tabela
        item_selecionado= self.tabela.selection()
        if not item_selecionado:
            messagebox.showerror(
                "Erro",
                "Selecione um funcionário para ativar/desativar!"
            )
            return
        
        # Obter os dados do funcionário selecionado
        item = self.tabela.item(item_selecionado[0])
        id_funcionario = item["values"][0]
        nome = item["values"][1]
        estado_atual = item["values"][3]

        try:
            if estado_atual == "Ativo":

                novo_estado = "Desativado"
            else:

                novo_estado="Ativo"


            self.cursor.execute(
                """
                UPDATE funcionarios
                SET estado = %s
                WHERE id_funcionario = %s
                """,
                (novo_estado, id_funcionario)
            )

            
            messagebox.showinfo(
                "Sucesso",
                f"Funcionário '{nome}' ativado/desativado!")



            
            conn.commit()


        except mysql.connector.Error as err:
            messagebox.showerror(
                "Erro",
                f"Erro ao ativar/desativar funcionário: {err}"
            )

