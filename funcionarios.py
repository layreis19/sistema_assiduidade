
# Pra que serve esse ficheiro?
# Este ficheiro é responsável por criar a página de gestão de funcionários, permitindo adicionar novos funcionários, editar informações existentes
#  e ativar/desativar funcionários da base de dados. Ele também lida com a validação de entrada e
#  a comunicação com a base de dados para garantir que as operações sejam realizadas corretamente.
 
 
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import bcrypt
import mysql.connector
from ligacao import conn
import cores
import widgets as w
from tkcalendar import DateEntry
 
 
class PaginaFuncionarios(tk.Frame):
 
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
 
        # buffered=True para evitar problemas de cursor fechado
        # varias consultas podem ser feitas com o mesmo cursor
        self.cursor = conn.cursor(buffered=True)
        w.criar_estilo_tabela()
        w.criar_titulo(
            self,
            "GESTÃO DE FUNCIONÁRIOS").pack(pady=15)
 
        # formulario para adicionar funcionário
        frame_formulario = tk.Frame(self)
        frame_formulario.pack(pady=10)
 
        w.criar_label(frame_formulario, "Nome:").pack(side= tk.LEFT, padx=(0,20), pady=5)
 
        self.entry_nome = w.criar_entrada(frame_formulario,largura=25)
        self.entry_nome.pack(side= tk.LEFT, padx=(0,20), pady=5)
 
        w.criar_label(frame_formulario, "Senha:").pack(side= tk.LEFT, padx=(0,20), pady=5)
 
        self.entry_senha = w.criar_entrada(frame_formulario, largura=25, senha=True)
        self.entry_senha.pack(side= tk.LEFT, padx=(0,20), pady=5)
 
        # Tipo
        w.criar_label(frame_formulario, "Tipo:").pack(side= tk.LEFT, padx=(0,20), pady=5)
 
        self.combo_tipo = ttk.Combobox(frame_formulario, values=["Admin", "Colaborador"],state="readonly", width=22)
        self.combo_tipo.pack(side= tk.LEFT, padx=(0,20), pady=5)
 
        # caixa de botoes para adicionar, alterar e ativar/desativar funcionário
        frame_botoes = tk.Frame(self)
        frame_botoes.pack(pady=10)
 
        # Botão adicionar funcionário
        w.criar_botao(frame_botoes, "Adicionar", self.adicionar_funcionario).pack(side=tk.LEFT, padx=10, pady=10)
 
        # Botão alterar funcionário
        w.criar_botao(frame_botoes,"Alterar", self.alterar_funcionario).pack(side=tk.LEFT, padx=10, pady=10)
 
        # Botão ativar/desativar funcionário
        w.criar_botao(frame_botoes,"Ativar/Desativar",self.ativar_desativar_funcionario).pack(side=tk.LEFT, padx=10, pady=10)
 

        # Tabela para exibir os funcionários
        self.tabela = ttk.Treeview(
            self,
            columns=("id_funcionario", "nome", "tipo", "estado", "data_adesao","data_demissao"),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela"
        )

        self.tabela.tag_configure("inativo", foreground="red")

        self.tabela.heading("id_funcionario", text="ID")
        self.tabela.heading("nome", text="Funcionário")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("estado", text="Estado")
        self.tabela.heading("data_adesao", text="Data de Adesão")
        self.tabela.heading("data_demissao", text="Data de Demissão")

        # Largura das colunas
        self.tabela.column("id_funcionario",width=60,anchor="center")
        self.tabela.column("nome",width=250, anchor="center")
        self.tabela.column("tipo",width=150,anchor="center")
        self.tabela.column("estado",width=150,anchor="center")
        self.tabela.column("data_adesao",width=100,anchor="center")
        self.tabela.column("data_demissao",width=100,anchor="center")
 
        self.tabela.pack(fill="both", expand=True, padx=30, pady=20)
 
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
 
            novo_id = self.cursor.lastrowid
 
            conn.commit()
 
            aviso_admin_padrao_removido = ""
 
            # Assim que for criado um admin a sério, o admin padrão criado
            # pelo script SQL (nome 'admin', só para o primeiro login) já
            # não faz falta e passa a ser um risco de segurança (senha
            # padrão, previsível). "id_funcionario != %s" garante que, se
            # alguém genuinamente chamar 'Admin' a este novo admin, não se
            # elimina a si próprio por engano.
            if tipo == "ADMIN":
                try:
                    self.cursor.execute(
                        """
                        DELETE FROM funcionarios
                        WHERE LOWER(nome) = 'admin'
                          AND tipo = 'ADMIN'
                          AND id_funcionario != %s
                        """,
                        (novo_id,)
                    )
 
                    if self.cursor.rowcount > 0:
                        conn.commit()
                        aviso_admin_padrao_removido = "\n\nO admin padrão inicial foi removido automaticamente."
 
                except mysql.connector.Error:
                    # Se o admin padrão já tiver alguma referência (ex:
                    # aprovou uma ausência, retificou uma picagem) a
                    # eliminação pode falhar por causa de uma FK — não
                    # deve impedir a criação do novo admin, que já está
                    # gravada. Nesse caso, o admin padrão fica por
                    # remover e pode ser desativado manualmente depois.
                    conn.rollback()
 
            messagebox.showinfo(
                "Sucesso",
                f"Funcionário '{nome}' adicionado!{aviso_admin_padrao_removido}"
            )
 
            # Limpar campos
            self.entry_nome.delete(0, tk.END)
            self.entry_senha.delete(0, tk.END)
            self.combo_tipo.set("")
 
            # atualizar tabela para o novo funcionario aparecer
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

            estado = funcionario[3]

            if estado.upper() == "INATIVO":
                tag = "inativo"

            else: 
                tag = ""

            self.tabela.insert(
                "",
                "end",
                values=funcionario,
                tags=(tag,)
            )
 
 
    # CONSULTAR FUNCIONÁRIOS
    def consultar_funcionarios(self):
        try:
            self.cursor.execute(
                """
                SELECT 
                    id_funcionario, nome, tipo, estado, DATE_FORMAT(data_adesao,'%d/%m/%Y'), IFNULL(DATE_FORMAT(data_demissao,'%d/%m/%Y'), '-')
                FROM funcionarios 
                ORDER BY 
                    CASE 
                        WHEN estado = "ATIVO" THEN 1 
                        ELSE 2 
                    END, 
                    nome ASC
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
        data_adesao_atual = item["values"][4]
        
 
        # Criar uma nova janela para alterar os dados do funcionário
        self.janela_alterar = tk.Toplevel(self)
        self.janela_alterar.title("Alterar Funcionário")
 
        # Nome
        w.criar_label(self.janela_alterar,"Nome:").pack(pady=5)
        self.entry_nome_alterar = w.criar_entrada(self.janela_alterar,largura=25)
        self.entry_nome_alterar.insert(0, nome_atual)
        self.entry_nome_alterar.pack(pady=5)
 
        # Tipo
        w.criar_label(self.janela_alterar, "Tipo:").pack(pady=5)
        self.combo_tipo_alterar = ttk.Combobox(self.janela_alterar, values=["Admin", "Colaborador"], state="readonly", width=22)
        # a tabela mostra ADMIN/COLABORADOR; o combobox usa Admin/Colaborador
        self.combo_tipo_alterar.set(str(tipo_atual).capitalize())
        self.combo_tipo_alterar.pack(pady=5)
        
        #data de adesao
        w.criar_label(self.janela_alterar, "Data de Adesão:").pack(pady=(5,0))
        self.calendario_adesao = DateEntry(
            self.janela_alterar, width=20, bootstyle=cores.PRIMARY_DARK, date_pattern="yyy-mm-dd"
        )
        
        
        
        
        try:
            from datetime import datetime
            data_obj = datetime.strptime(data_adesao_atual, "%d/%m/%Y")
            self.calendario_adesao.set_date(data_obj)
        except Exception:
            
            pass  #se falhar assume a data de hj
        
        self.calendario_adesao.pack(pady=5)
        
    
        # Senha
        w.criar_label(self.janela_alterar,"Senha:").pack(pady=5)
        self.entry_senha_alterar = w.criar_entrada(self.janela_alterar,largura=25, senha=True)
        self.entry_senha_alterar.pack(pady=5)
 
        # Botão para guardar as alterações
        w.criar_botao(self.janela_alterar,"Guardar",self.guardar_alteracoes
        ).pack(pady=10)
 
    # função para guardar alterações na base de dados
    def guardar_alteracoes(self):
 
        novo_nome = self.entry_nome_alterar.get().strip().capitalize()
        novo_tipo = self.combo_tipo_alterar.get().strip().upper()
        data_selecionada = self.calendario_adesao.get_date().strftime('%Y-%m-%d')
        nova_senha = self.entry_senha_alterar.get().strip()
       
        nova_data_adesao = f"{data_selecionada} 00:00:00"
        
 
        if not novo_nome or not novo_tipo  or not nova_data_adesao or not nova_senha:
            messagebox.showerror(
                "Erro",
                "Nome, Tipo, Data de Adesão e Senha são obrigatórios!"
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
                    data_adesao= %s,
                    senha = %s
                WHERE id_funcionario = %s
                """,
                (
                    novo_nome,
                    novo_tipo,
                    nova_data_adesao,
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
 
    # ativar ou desativar funcionário
    def ativar_desativar_funcionario(self):
 
        # Obter o funcionário selecionado na tabela
        item_selecionado = self.tabela.selection()
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
        
        if estado_atual.upper() == "ATIVO":
            self.pedir_data_demissao(id_funcionario,nome)
            return
        
         #reativa e apaga a data de demissao
        try:
            
            self.cursor.execute(
                """
                UPDATE funcionarios
                SET estado = 'ATIVO',
                    data_demissao= NULL
                WHERE id_funcionario = %s
                
                """,
                ( id_funcionario,)
            )
 
            conn.commit()
 
            messagebox.showinfo("Sucesso", f"Funcionário '{nome}' ficou ATIVO.")
            self.atualizar_funcionarios()
 
            self.atualizar_funcionarios()
 
        except mysql.connector.Error as err:
            messagebox.showerror(
                "Erro",
                f"Erro ao ativar/desativar funcionário: {err}"
            )
    
    def pedir_data_demissao(self, id_funcionario, nome):
        janela= tk.Toplevel(self)
        janela.title("Data de Demissão")
        janela.grab_set()
        
        
        w.criar_label(janela,f"Data de Saída de {nome}:").pack(padx=20, pady=(15,5))
        
        calendario= DateEntry(janela, width=20, date_pattern= "yyy-mm-dd")
        calendario.pack(pady=5)
        
        def confirmar():
            data_demissao = calendario.get_date()
            
            try:
            
                self.cursor.execute(
                    """
                    UPDATE funcionarios
                    SET estado= 'INATIVO',
                    data_demissao=%s
                    WHERE id_funcionario =%s
                    """,
                    (data_demissao,id_funcionario)
                    
                )
                conn.commit()
                messagebox.showinfo("Sucesso", f"Funcionário '{nome}' ficou INATIVO.")
                janela.destroy()
                self.atualizar_funcionarios()

            except mysql.connector.Error as erro:
                conn.rollback()
                messagebox.showerror("Erro", f"Erro ao desativar funcionário: {erro}")

        w.criar_botao(janela, "Confirmar", confirmar).pack(pady=15)
            
        
        
        
        
        
        
        
        
        
 
