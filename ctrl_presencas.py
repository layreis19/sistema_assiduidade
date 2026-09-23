import tkinter as tk
from tkinter import ttk
from ligacao import conn
from datetime import date
from tkinter import messagebox

# Criar a classe chamada PaginaPresencas
# Herda o tk.Frame(janela/área dentro da aplicação)
class PaginaPresencas(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)


        # Cursor da base de dados
        self.cursor = conn.cursor(buffered=True)

        # Titulo 
        titulo = tk.Label(
                    self,
                    text="CONTROLO DE PRESENÇAS",
                    font=("Arial", 24)
                )
        
        titulo.pack(pady=50)

        # KPI´S
        self.frame_kpis = tk.Frame(self)
        self.frame_kpis.pack(pady=10)



        # KPI total de funcionários

        self.total_kpi = tk.Frame(
            self.frame_kpis,
            width=220,
            height=110,
            relief = "solid",
            borderwidth=1
        )

        self.total_kpi.pack(
            side="left",
            padx=10
        )

        self.total_kpi.pack_propagate(False)

        tk.Label(self.total_kpi,
                 text="TOTAL DE FUNCIONÁRIOS",
                 font=("Arial", 11)
                 ).pack(pady=(15,5))


        self.label_total = tk.Label(
            self.total_kpi,
            text="0",
            font=("Arial", 26, "bold")
        )


        self.label_total.pack()


        # KPI´s funcionários presentes

        self.presentes_kpi = tk.Frame(
            self.frame_kpis,
            width=220,
            height=110,
            relief="solid",
            borderwidth=1
        )

        self.presentes_kpi.pack(
            side="left",
            padx=10 )

        self.presentes_kpi.pack_propagate(False)

        tk.Label(
            self.presentes_kpi,
            text="TOTAL DE FUNCIONÁRIOS PRESENTES",
            font=("Arial", 11)).pack(
                pady=(15,5)
            )

        self.label_presentes = tk.Label(
            self.presentes_kpi,
            text="0",
            font=("Arial", 26, "bold"),
            fg="green"
        )

        self.label_presentes.pack()


        # KPI funcionários ausentes

        self.ausentes_kpi = tk.Frame(
            self.frame_kpis,
            width=220,
            height=110,
            relief="solid",
            borderwidth=1
        )

        self.ausentes_kpi.pack(side="left",
                               padx=10)

        self.ausentes_kpi.pack_propagate(False)

        tk.Label(
            self.ausentes_kpi,
            text="TOTAL DE FUNCIONÁRIOS AUSENTES",
            font=("Arial", 11)).pack(
                pady=(15,5)
        )


        self.label_ausentes = tk.Label(
            self.ausentes_kpi,
            text="0",
            font=("Arial", 26, "bold"),
            fg="red"
        )

        self.label_ausentes.pack()


        # FILTROS

        self.frame_filtros = tk.Frame(self)

        self.frame_filtros.pack(
            padx=10,
            pady=20
        )

        # pesquisa por id 



        # pesquisa por id 

        self.id_pesquisa = tk.StringVar()

        tk.Label(
            self.frame_filtros,
            text="ID Funcionário:"
        ).pack(
            side="left", padx=5)


        entrada_id = tk.Entry(
            self.frame_filtros,
            textvariable=self.id_pesquisa,
            width=10
        )

        entrada_id.pack(side="left", padx=5)


        # botão para pesquisar

        botao_pesquisar = tk.Button(
            self.frame_filtros,
            text="Pesquisar",
            command=self.atualizar_presenca
        )

        botao_pesquisar.pack(side="left", padx=5)


        # filtrar por estado 

        self.filtro = tk.StringVar(
            value="Todos"
        )


        tk.Label(
            self.frame_filtros,
            text="Estado:"
        ).pack(
            side="left",
            padx=5
        )


        # Caixa para escolher o filtro

        combo_filtro = ttk.Combobox(
            self.frame_filtros,
            textvariable=self.filtro,
            values=(
                "Todos",
                "Presentes",
                "Ausentes"),
                state="readonly",
                width=12
        )

        combo_filtro.pack(
            side="left",
            padx=5
        )


        # escolher opção atualizar tabela

        combo_filtro.bind(
            "<<ComboboxSelected>>",
            lambda filtro: self.atualizar_presenca()

        )


        # criar a tabela

        self.tabela = ttk.Treeview(
            self,
            columns=(
                "id_funcionario",
                "nome",
                "estado"
            ),
            show="headings"
        )

        # cabeçalho 

        self.tabela.heading(
            "id_funcionario",
            text="ID_Funcionário"
        )


        self.tabela.heading(
            "nome",
            text="Nome"
        )


        self.tabela.heading(
            "estado",
            text="Estado"
        )


        # Largura das colunas

        self.tabela.column(
            "id_funcionario",
            width=120,
            anchor="center"
        )

        self.tabela.column(
            "nome",
            width=250
        )

        self.tabela.column(
            "estado",
            width=150,
            anchor="center"
        )

        self.tabela.pack(pady=10)


        # Cores da tabela

        self.tabela.tag_configure(
            "presente",
            foreground="green"
        )


        self.tabela.tag_configure(
            "ausente",
            foreground="red"
        )

        self.atualizar_presenca()

    def atualizar_presenca(self):

        for linha in self.tabela.get_children():
              self.tabela.delete(linha)

        # data de hoje
        
        hoje = date.today()


        # procurar na base de dados

        self.cursor.execute("""
        SELECT 
            funcionarios.id_funcionario,
            funcionarios.nome,
            picagem.tipo
        
        FROM funcionarios
        
        LEFT JOIN picagem
        ON funcionarios.id_funcionario = picagem.id_funcionario 
        AND DATE(picagem.data) = %s
            
        ORDER BY 
        funcionarios.id_funcionario,
        picagem.data""", (hoje,))

            # Guardar os resultados

        picagens = self.cursor.fetchall()


        # Criar o dicionário 

        dicionario_funcionarios = {}

        # percorrer todas as picagens

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

        
            # id que foi pesquisado 
        id_pesquisado = self.id_pesquisa.get()
            # verificamos se o id existe

        funcionario_encontrado = False

            # percorrer os funcionários 
        for id_funcionario, dados in dicionario_funcionarios.items():
            if id_pesquisado and str(id_funcionario) != id_pesquisado:
                continue

            # encontramos o funcionario 

            funcionario_encontrado = True

            nome = dados["nome"]
            tipo = dados["tipo"]


            # determinar o estado

            if tipo is None:
                estado = "AUSENTE"
                tag = "ausente"


            elif tipo == "ENTRADA":
                estado = "PRESENTE"
                tag = "presente"

            elif tipo == "SAIDA":
                estado = "AUSENTE"
                tag = "ausente"


            # aplicar o filtro

            if (
                self.filtro.get() == "Presentes"
                and estado != "PRESENTE"
                ):

                continue

            if (self.filtro.get() == "Ausentes"
                and estado != "AUSENTE"):

                continue


            # colocar funcionário na tabela

            self.tabela.insert(
                "",
                "end",
                values=(
                    id_funcionario,
                    nome,
                    estado),
                    tags=(tag,)
                )

            # verificar se o id pesquisado exsite
        if id_pesquisado and not funcionario_encontrado:
            messagebox.showwarning(
                "Funcionário",
                "ID não existe."
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

        self.label_total.config(
            text=str(total)
        )

        self.label_presentes.config(
            text=str(presentes)
        )

        self.label_ausentes.config(
            text=str(ausentes)
        )



