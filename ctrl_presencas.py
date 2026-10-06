import tkinter as tk
from tkinter import ttk
from ligacao import conn
from datetime import date
from tkinter import messagebox
import widgets as w 
from widgets import *
import cores


# Criar a classe chamada PaginaPresencas
# Herda o tk.Frame(janela/área dentro da aplicação)
class PaginaPresencas(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=cores.CARD)

        # Cursor da base de dados
        self.cursor = conn.cursor(buffered=True)

        w.criar_estilo_tabela()
        
        # Titulo 
        w.criar_titulo(self,"CONTROLO DE PRESENÇAS").pack(pady=(30,20))
        
        # FRAME
        frame_kpi= tk.Frame(self)
        frame_kpi.pack(pady=10)

        # KPI total de funcionários
        self.label_total_kpi = tk.Frame(frame_kpi, width=220, height=110, relief = "solid", borderwidth=1)
        self.label_total_kpi.pack(side=tk.LEFT,padx=10)
        self.label_total_kpi.pack_propagate(False)

        # LABEL total funcionários
        w.criar_label(self.label_total_kpi, "TOTAL DE FUNCIONÁRIOS").pack(pady=(15,5))
        self.label_funcionarios = w.criar_label(self.label_total_kpi, "0", negrito=True)
        self.label_funcionarios.config(font=("Arial", 22, "bold"))
        self.label_funcionarios.pack()


        # KPI funcionários presentes
        self.label_funcionarios_presentes = tk.Frame(frame_kpi, width=220, height=110, relief="solid", borderwidth=1)
        self.label_funcionarios_presentes.pack(side=tk.LEFT, padx=10)
        self.label_funcionarios_presentes.pack_propagate(False)

       
        # LABEL Funcionários presentes
        w.criar_label(self.label_funcionarios_presentes,"PRESENTES").pack(pady=(15,5))
        self.label_presentes = w.criar_label(self.label_funcionarios_presentes, "0", negrito=True, cor="green")
        self.label_presentes.config(font=("Arial", 22, "bold"))
        self.label_presentes.pack()


        # KPI funcionários ausentes
        self.label_funcionarios_ausentes = tk.Frame(frame_kpi, width=220, height=110, relief="solid", borderwidth=1)
        self.label_funcionarios_ausentes.pack(side=tk.LEFT, padx=10)
        self.label_funcionarios_ausentes.pack_propagate(False)

        # LABEL Funcionários ausentes
        w.criar_label(self.label_funcionarios_ausentes,"AUSENTES").pack(pady=(15,5))
        self.label_ausentes = w.criar_label(self.label_funcionarios_ausentes, "0", negrito=True, cor="red")
        self.label_ausentes.config(font=("Arial", 22, "bold"))
        self.label_ausentes.pack()


        # FRAME FORMULÁRIO
        frame_formulario = tk.Frame(self)
        frame_formulario.pack(pady=10)

        # pesquisa por id 

        self.id_pesquisa = tk.StringVar()
        w.criar_label(frame_formulario, "ID Funcionário:").pack(side=tk.LEFT, padx=5)
        self.entry_id = w.criar_entrada(frame_formulario, textvariable=self.id_pesquisa)
        self.entry_id.pack(side=tk.LEFT, padx=10, pady=10)


        self.filtro = tk.StringVar(value="Todos")
        w.criar_label(frame_formulario, "Estado").pack(side=tk.LEFT, padx=5)


        # Caixa para escolher o filtro
        # ("Em Pausa" reposto: sem esta opção, quem está em pausa não
        # aparecia em nenhum filtro específico, só em "Todos".)

        combo_filtro = ttk.Combobox(frame_formulario, textvariable=self.filtro,
            values=(
                "Todos",
                "Presentes",
                "Ausentes"
                ),
                state="readonly",
                width=16)

        combo_filtro.pack(side=tk.LEFT, padx=10, pady=5)


        # FRAME BOTÃO
        frame_botoes = tk.Frame(self)
        frame_botoes.pack(pady=10)

        w.criar_botao(frame_botoes, "Pesquisar", self.atualizar_presenca).pack(side=tk.LEFT, padx=5)


        # FRAME TABELA
        frame_tabela = tk.Frame(self)
        frame_tabela.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Tabela
        self.tabela_presencas = ttk.Treeview(
            frame_tabela,
            columns=(
                "id_funcionario",
                "nome",
                "estado"
            ),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela")

        # Cabeçalhos
        self.tabela_presencas.heading("id_funcionario",text="ID_Funcionário")
        self.tabela_presencas.heading("nome",text="Funcionário")
        self.tabela_presencas.heading("estado",text="Estado")


        # Largura das colunas
        self.tabela_presencas.column("id_funcionario",width=60,anchor="center")
        self.tabela_presencas.column("nome",width=250)
        self.tabela_presencas.column("estado",width=150,anchor="center")


        # Scroll 
        scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela_presencas.yview)
        self.tabela_presencas.configure(yscrollcommand=scroll.set)
        self.tabela_presencas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Cores da tabela
        self.tabela_presencas.tag_configure("presente",foreground="green")
        self.tabela_presencas.tag_configure("ausente",foreground="red")

        self.atualizar_presenca()

    def atualizar_presenca(self):

        for linha in self.tabela_presencas.get_children():
              self.tabela_presencas.delete(linha)

        # data de hoje
        hoje = date.today()


        # procurar na base de dados
        # (picagem.anulada = 0 no ON, não no WHERE, para continuar a ser um
        # LEFT JOIN de verdade: um funcionário cujas únicas picagens de hoje
        # estejam anuladas continua a aparecer, como AUSENTE, em vez de
        # desaparecer da lista.)

        self.cursor.execute("""
        SELECT 
            funcionarios.id_funcionario,
            funcionarios.nome,
            picagem.tipo
        
        FROM funcionarios
        
        LEFT JOIN picagem
        ON funcionarios.id_funcionario = picagem.id_funcionario 
        AND DATE(picagem.data) = %s
        AND picagem.anulada = 0
            
        ORDER BY 
        funcionarios.id_funcionario,
        picagem.data""", (hoje,))

        # Guardar os resultados
        picagens = self.cursor.fetchall()


        # Criar o dicionário 
        dicionario_funcionarios = {}

        # percorrer todas as picagens
        # (como a query está ordenada por picagem.data crescente, a última
        # picagem de cada funcionário sobrescreve as anteriores no
        # dicionário — fica sempre a mais recente do dia.)

        for picagem in picagens:
            id_funcionario = picagem[0]
            nome = picagem[1]
            tipo = picagem[2]

            # guardar os dados do funcionário
            dicionario_funcionarios[id_funcionario] = {
                "nome": nome,
                "tipo": tipo}


        # Atualizar os kpis
        self.atualizar_kpis(dicionario_funcionarios)

        # ID que foi pesquisado 
        id_pesquisado = self.id_pesquisa.get()

        # Filtro selecionado
        filtro = self.filtro.get()

        # verificamos se o id existe
        if id_pesquisado:

            funcionario_encontrado = False

            # percorrer os funcionários 
            for id_funcionario, dados in dicionario_funcionarios.items():
                if str(id_funcionario) != id_pesquisado:
                    continue

                # encontramos o funcionario 
                funcionario_encontrado = True

                nome = dados["nome"]
                tipo = dados["tipo"]


                # determinar o estado
                # ENTRADA (PRESENTE).
                # SAIDA (AUSENTE).

                if tipo == "ENTRADA":
                    estado = "PRESENTE"
                    tag = "presente"

                else: 
                    estado = "AUSENTE"
                    tag = "ausente"

                # Verificar o filtro 
                if filtro == "Presentes" and estado !="PRESENTE":
                    continue

                if filtro == "Ausentes" and estado != "AUSENTE":
                    continue

                self.tabela_presencas.insert(
                    "",
                    "end",
                    values=(
                        id_funcionario,
                        nome,
                        estado
                    ),
                    tags=(tag,)
                )
                
            # Verificar se o id pesquisado existe
            if not funcionario_encontrado:
                messagebox.showwarning(
                    "Funcionário", 
                    "ID não existe.")

        # Se não for introduzido ID utilizar o filtro
        else:
            for id_funcionario, dados in dicionario_funcionarios.items():

                nome = dados["nome"]
                tipo = dados["tipo"]


                if tipo == "ENTRADA":
                    estado = "PRESENTE"
                    tag = "presente"
                    
                else:  # tipo == "SAIDA" ou tipo is None
                    estado = "AUSENTE"
                    tag = "ausente"

                # Filtro presente
                if self.filtro.get() == "Presentes" and estado != "PRESENTE":
                    continue

                # Filtro ausente
                if self.filtro.get() == "Ausentes" and estado != "AUSENTE":
                    continue

                self.tabela_presencas.insert(
                    "",
                    "end",
                    values=(
                        id_funcionario,
                        nome,
                        estado),
                        tags=(tag,)
                    )

    def atualizar_kpis(self, dicionario_funcionarios):

        # calcular o total
        total = len(dicionario_funcionarios)
        presentes = 0 
        ausentes = 0

        # percorrer os dados dos funcionários
        for dados in dicionario_funcionarios.values():
            tipo = dados["tipo"]

            if tipo == "ENTRADA":
                presentes += 1

            else:

                ausentes += 1


        # mostrar os valores nos kpis
        self.label_funcionarios.config(text=str(total))
        self.label_presentes.config(text=str(presentes))
        self.label_ausentes.config(text=str(ausentes))