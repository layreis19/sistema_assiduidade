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
from relatorios import PaginaRelatorios




BG = "#EAF6FF"             # Fundo principal
PRIMARY = "#3F8FC1"        # Azul principal
PRIMARY_DARK = "#2F78A8"   # Azul mais escuro
BLUE_LIGHT = "#B5D9EA"     # Azul claro
BLUE_VERY_LIGHT = "#D9EDF7"
CARD = "#FFFFFF"           # Branco
TEXT = "#1E3A52"           # Texto principal
TEXT_SECONDARY = "#6B879C" # Texto secundário
BORDER = "#C7E3F2"


class PaginaFuncionarios(tk.Frame):
    

    def __init__(self, parent):
        super().__init__(parent,bg= CARD)
        self.parent = parent


        #buffered=True para evitar problemas de cursor fechado
        #varias consultas podem ser feitas com o mesmo cursor
        #sem buffered=True, o cursor fecha após a primeira consulta, impedindo consultas subsequentes
        self.cursor = conn.cursor(buffered=True)

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

        
        
        
        

     

       # Tabela para exibir os funcionários
        self.tabela = ttk.Treeview( self, columns=("id_funcionario", "nome", "tipo", "estado"), show="headings")
        self.tabela.heading("id_funcionario", text="ID")
        self.tabela.heading("nome", text="Funcionário")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("estado", text="Estado")
 
        self.tabela.pack( fill="both",expand=True, padx=30, pady=20 )

        # Atualizar a tabela com os funcionários existentes
        self.atualizar_funcionarios()   
    
      
      
    # CRIAR UM FUNCIONÁRIO
    def adicionar_funcionario(self):

        nome = self.entry_nome.get().strip().capitalize()
        senha = self.entry_senha.get().strip()
        tipo = self.combo_tipo.get().strip().upper()

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
            ).decode("utf-8")

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


            #atualizar tabela para o novo funcionario aparecer
            self.atualizar_funcionarios()
            

        except mysql.connector.Error as erro:
            messagebox.showerror(
                "Erro",
                f"Erro ao adicionar funcionário: {erro}"
            )


            
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
        try:
            self.cursor.execute(
                """
                SELECT id_funcionario, nome, tipo, estado
                FROM funcionarios
                """
            )
            return self.cursor.fetchall()

        except mysql.connector.Error as erro:

            messagebox.showerror(
                "Erro", 
                f"Erro ao consultar funcionário: {erro}"
            )


            return []


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
        self.id_funcionario_alterar = item["values"][0]
        nome_atual = item["values"][1]
        tipo_atual = item["values"][2]

        # Criar uma nova janela para alterar os dados do funcionário
        self.janela_alterar = tk.Toplevel(self)
        self.janela_alterar.title("Alterar Funcionário")

        # Nome
        nome_label = tk.Label(self.janela_alterar, text="Nome:")
        nome_label.pack(pady=5)
        self.entry_nome_alterar = tk.Entry(self.janela_alterar)
        self.entry_nome_alterar.insert(0, nome_atual)
        self.entry_nome_alterar.pack(pady=5)

        # Tipo
        tipo_label = tk.Label(self.janela_alterar, text="Tipo:")
        tipo_label.pack(pady=5)
        self.combo_tipo_alterar = ttk.Combobox(self.janela_alterar, values=["Admin", "Colaborador"])
        self.combo_tipo_alterar.set(tipo_atual)
        self.combo_tipo_alterar.pack(pady=5)

        # Senha
        senha_label = tk.Label(self.janela_alterar, text="Senha:")
        senha_label.pack(pady=5)
        self.entry_senha_alterar = tk.Entry(self.janela_alterar, show="*")
        self.entry_senha_alterar.pack(pady=5)
        
        

        # Botão para guardar as alterações
        btn_guardar = tk.Button(
            self.janela_alterar,
            text="Guardar",
            command=self.guardar_alteracoes
        )
        btn_guardar.pack(pady=10)


    # função para guardar alterações na base de dados
    def guardar_alteracoes(self):

            novo_nome = self.entry_nome_alterar.get().strip().capitalize()
            novo_tipo = self.combo_tipo_alterar.get().strip().upper()
            nova_senha = self.entry_senha_alterar.get().strip()

            if not novo_nome or not novo_tipo or not nova_senha:
                messagebox.showerror(
                    "Erro",
                    "Nome, Tipo e Senha são obrigatórios!"
                )
                return

            try:

                senha_hash = bcrypt.hashpw(
                    nova_senha.encode("utf-8"),
                    bcrypt.gensalt()
                ).decode("utf-8")

                self.cursor.execute(
                    """
                    UPDATE funcionarios
                    SET nome = %s,
                        tipo = %s,
                        senha = %s
                    WHERE id_funcionario = %s
                    """,
                    (
                        novo_nome,
                        novo_tipo,
                        senha_hash,
                        self.id_funcionario_alterar
                    )
                )

                conn.commit()

                messagebox.showinfo(
                    "Sucesso",
                    f"Funcionário {novo_nome} alterado com sucesso!"
                )

                self.atualizar_funcionarios()
                self.janela_alterar.destroy()

            except mysql.connector.Error as erro:

                conn.rollback()

                messagebox.showerror(
                    "Erro",
                    f"Erro ao alterar funcionário:\n{erro}"
                )
                    
        
    
        
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

            if estado_atual.upper() == "ATIVO":

                novo_estado = "INATIVO"
            else:

                novo_estado="ATIVO"


            self.cursor.execute(
                """
                UPDATE funcionarios
                SET estado = %s
                WHERE id_funcionario = %s
                """,
                (novo_estado, id_funcionario)
            )

            conn.commit()

            
            messagebox.showinfo(
                "Sucesso",
                f"Funcionário '{nome}' ativado/desativado!")

            self.atualizar_funcionarios()



        except mysql.connector.Error as err:
            messagebox.showerror(
                "Erro",
                f"Erro ao ativar/desativar funcionário: {err}"
            )

      

