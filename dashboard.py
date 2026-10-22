import tkinter as tk 
from ligacao import conn
import cores
import pandas as pd
from datetime import datetime, time, timedelta
import widgets as w
from tkinter import ttk
from ttkbootstrap.widgets import DateEntry
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
import matplotlib
matplotlib.use("TkAgg")

def converter_horas_segundos(hora):

    # verifica se existe um valor ou se é considerado valor em falta. Retorna None em vez de tentar fazer cálculos com valores inexistentes. 
    if hora is None or pd.isna(hora):
        return None
    
    # verifica se é timedelta se for transforma em segundos
    if isinstance(hora, timedelta):
        return hora.total_seconds()

    # verifica se é time e retorna em segundos
    if isinstance(hora, time):
        return hora.hour * 3600 + hora.minute * 60 + hora.second
    
    # verifica se é texto, e transforma em segundos 
    if isinstance(hora,str):
        hora = datetime.strptime(hora, "%H:%M:%S").time()
        return hora.hour * 3600 + hora.minute * 60 + hora.second
    
    return None
    
class PaginaDashboard(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=cores.BLUE_VERY_LIGHT)

        # Criar a página canva para o scroll na página completa
        self.canva_pagina = tk.Canvas(self, bg=cores.BLUE_VERY_LIGHT, highlightthickness=0)
        self.canva_pagina.pack(side="left", fill="both", expand=True)

        # criar a barra de scroll vertical d página 
        self.scroll_pagina = ttk.Scrollbar(self, orient="vertical", command=self.canva_pagina.yview)
        self.scroll_pagina.pack(side="right", fill="y")

        # ligar o canva à barra do scroll
        self.canva_pagina.configure(yscrollcommand=self.scroll_pagina.set)

        # criar o frame que contém todo o dashboard 
        self.pagina_dashboard = tk.Frame(self.canva_pagina, background=cores.BLUE_VERY_LIGHT)

        # colocar o dashboard dentro do canvas
        self.janela_pagina = self.canva_pagina.create_window(
            (0,0), 
            window=self.pagina_dashboard,
            anchor="nw")

        # atualizar a área percorróvel quando o conteúdo muda 
        self.pagina_dashboard.bind(
            "<Configure>",
            lambda i: self.canva_pagina.configure(scrollregion=self.canva_pagina.bbox("all"))
        )

        # ajustar a largura da dashboard disponível 
        self.canva_pagina.bind(
            "<Configure>",
            lambda i: self.canva_pagina.itemconfigure(
                self.janela_pagina,
                width=i.width))


        def scroll_pagina(evento):
            widget = evento.widget
            
            while widget is not None:
                if widget == self.canva_pagina:
                    self.canva_pagina.yview_scroll(int(-evento.delta), "units")

                return
            widget = getattr(widget, "master", None)  
            self.bind_all("<MouseWheel>", scroll_pagina)      

        self.pagina_dashboard.pack(fill="both", expand=True, padx=15, pady=10)

        # título 
        tk.Label(self.pagina_dashboard, 
                       text="DASHBOARD DE ASSIDUIDADE",
                       font=w.FONTE_TITULO_DASH,
                       bg=cores.BLUE_VERY_LIGHT,
                       fg=cores.PRIMARY_DARK).pack(pady=(30,20))

        # frame filtro
        self.frame_filtro = tk.Frame(self.pagina_dashboard, bg=cores.BLUE_VERY_LIGHT)
        self.frame_filtro.pack(fill="x", padx= 10, pady=(0,12))

        self.filtro_ano = ttk.Combobox(self.frame_filtro, 
                                       values=["2022", "2023", "2024", "2025", "2026", "2027"],
                                       state="readonly",
                                        width=8)
        self.filtro_ano.set("2026")
        self.filtro_ano.pack(side="right", padx=(0,10), anchor="e")

        # atualizar a box funcionários 
        self.filtro_ano.bind(
            "<<ComboboxSelected>>",
            lambda ano:( self.atualizar_funcionarios(),
            self.atualizar_faltas_medicas()))

        
        w.criar_label(self.frame_filtro,
                      "Ano:",
                      bg=cores.BLUE_VERY_LIGHT,
                      fg=cores.PRIMARY_DARK).pack(side="right", padx=(0,8))
    

        # criar frame kpis
        self.frame_kpis = tk.Frame(self.pagina_dashboard, bg=cores.BLUE_VERY_LIGHT)
        self.frame_kpis.pack(fill="x", pady=(0,18))
        self.frame_kpis.grid_columnconfigure(
            (0,1,2,3),
            weight=1, 
            uniform="kpis")

        # kpi funcionários
        self.kpi_funcionarios = tk.Frame(self.frame_kpis, 
                                         bg=cores.CARD, 
                                         padx=12, 
                                         pady=16,
                                         highlightbackground="#D6E3F0",
                                         highlightthickness=1)
        self.kpi_funcionarios.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # kpi faltas
        self.kpi_faltas = tk.Frame(self.frame_kpis,
                                   bg=cores.CARD, 
                                   padx=12,
                                   pady=16,
                                   highlightbackground="#D6E3F0",
                                   highlightthickness=1)
        self.kpi_faltas.grid(row=0, column=1,sticky="nsew", padx=5, pady=5)

        # kpi atrasos
        self.kpi_atrasos = tk.Frame(self.frame_kpis,
                                    bg=cores.CARD, 
                                    padx=12, 
                                    pady=16,
                                    highlightbackground="#D6E3F0",
                                    highlightthickness=1)
        self.kpi_atrasos.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        # kpi ausências (faltas, médicas)
        self.kpi_faltas_medicas = tk.Frame(self.frame_kpis,
                                           bg=cores.CARD,
                                           padx=12,
                                           pady=16)
        self.kpi_faltas_medicas.grid(row=0, column=3, sticky="nsew", padx=5, pady=5)


        # adicionar os valores
        w.criar_label(self.kpi_funcionarios, 
                    "FUNCIONÁRIOS",
                    font=w.FONTE_LABEL,
                    bg=cores.CARD,
                    fg=cores.PRIMARY_DARK).pack(anchor="center")
        
        self.label_funcionarios = w.criar_label(
            self.kpi_funcionarios,
            "-",
            font=("Arial", 22, "bold"),
            bg=cores.CARD,
            fg=cores.PRIMARY_DARK)
        self.label_funcionarios.pack(anchor="center", pady=(8,0))

        
        # adicionar faltas
        w.criar_label(self.kpi_faltas,
                    "TEMPO MÉDIO FALTAS",
                    font=w.FONTE_LABEL,
                    bg=cores.CARD,
                    fg=cores.PRIMARY_DARK).pack(anchor="center")
        
        self.label_faltas = w.criar_label(
            self.kpi_faltas, 
            "-",
            font=("Arial", 22, "bold"),
            bg=cores.CARD,
            fg=cores.PRIMARY_DARK)
        self.label_faltas.pack(anchor="center", pady=(8,0))

        # adicionar atrasos
        w.criar_label(self.kpi_atrasos,
                    "TEMPO MÉDIO ATRASOS",
                    font=w.FONTE_LABEL,
                    bg=cores.CARD,
                    fg=cores.PRIMARY).pack(anchor="center")
        
        self.label_atrasos = w.criar_label(
            self.kpi_atrasos,
            "-",
            font=("Arial", 22, "bold"),
            bg=cores.CARD,
            fg=cores.PRIMARY_DARK)
        self.label_atrasos.pack(anchor="center", pady=(8,0))

        # adicionar faltas médicas
        w.criar_label(self.kpi_faltas_medicas,
                    "Nº FALTAS MÉDICAS",
                    font=w.FONTE_LABEL,
                    bg=cores.CARD,
                    fg=cores.PRIMARY_DARK
                    ).pack(anchor="center")
        
        self.label_faltas_medicas = w.criar_label(
            self.kpi_faltas_medicas,
            "-",
            font=("Arial", 22, "bold"),
            bg=cores.CARD,
            fg=cores.PRIMARY_DARK)
        self.label_faltas_medicas.pack(anchor="center", pady=(8,0))


        # frame análise por período
        self.frame_datas = tk.Frame(self.pagina_dashboard, 
                                    bg=cores.BLUE_VERY_LIGHT)
        
        self.frame_datas.pack(fill="x", pady=(0,10))
 

        self.frame_datas_inner = tk.Frame(
            self.frame_datas, 
            bg=cores.BLUE_VERY_LIGHT,
            padx=20,
            pady=12)
        self.frame_datas_inner.pack(anchor="center")
            

        tk.Label(self.frame_datas_inner,
                 text="Análise Temporal",
                 font=("Arial", 16, "bold"),
                bg=cores.BLUE_VERY_LIGHT,
                fg=cores.PRIMARY_DARK,
                ).grid(row=0, column=0,columnspan=5, pady=(0,12))

        w.criar_label(self.frame_datas_inner,
                      "Data de início:",
                      bg=cores.BLUE_VERY_LIGHT,
                      fg=cores.PRIMARY_DARK).grid(row=1, column=0, padx=(0,5))
        
        self.entry_data_inicio = DateEntry(
            self.frame_datas_inner,
            date_format = "%d-%m-%Y", 
            width=10, 
            bootstyle=cores.PRIMARY_DARK)
        self.entry_data_inicio.grid(row=1, column=1, padx=(0,15))
        

        w.criar_label(self.frame_datas_inner, 
                      "Data de fim:",
                      bg=cores.BLUE_VERY_LIGHT,
                      fg=cores.PRIMARY_DARK).grid(row=1, column=2,padx=(0,5))
        
        self.entry_data_fim = DateEntry(
            self.frame_datas_inner, 
            date_format="%d-%m-%Y",
            width=10,
            bootstyle=cores.PRIMARY_DARK )
        self.entry_data_fim.grid(row=1, column=3, padx=(0,15))


        # criar botão filtrar
        w.criar_botao(
            self.frame_datas_inner,
            "Filtrar", 
            self.filtrar_tabelas,
            bg=cores.PRIMARY,
            fg=cores.CARD,
            activebackground=cores.PRIMARY_DARK,
            activeforeground=cores.CARD).grid(row=1, column=4, padx=(0,0))

        # aréa dos gráficos com scroll

        self.area_graficos = tk.Frame(self.pagina_dashboard, bg=cores.BLUE_VERY_LIGHT)
        self.area_graficos.pack(fill="both", expand=True, pady=(0,10))


        self.frame_graficos = tk.Frame(self.area_graficos, bg=cores.BLUE_VERY_LIGHT)
        self.frame_graficos.pack(fill="both", expand=True)

        # configurar as duas colunas
        self.frame_graficos.grid_columnconfigure((0,1),weight=1, uniform="graficos")
        self.frame_graficos.grid_rowconfigure((0,1), weight=1)

        # gráfico 1
        self.frame_grafico1 = tk.Frame(
            self.frame_graficos,
            highlightbackground="#D6E3F0",
            highlightthickness=1)
        self.frame_grafico1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5) # nsew estica o gráfico para todo o espaço disponível
        
        w.criar_titulo(self.frame_grafico1,
                    "Funcionários com mais Atrasos",
                    font=w.FONTE_SUBTITULO_DASH,
                    fg=cores.PRIMARY_DARK).pack(pady=12)

        self.tabela_atrasos = ttk.Treeview(self.frame_grafico1,
                                           columns=("id", "nome", "numero", "tempo"),
                                           show="headings",
                                           height=8)

        # definir os títulos da coluna 
        self.tabela_atrasos.heading("id", text="ID")
        self.tabela_atrasos.heading("nome", text="Funcionário")
        self.tabela_atrasos.heading("numero", text="Nº Atrasos")
        self.tabela_atrasos.heading("tempo", text="Tempo Total")

        self.tabela_atrasos.column("id", width=100, anchor="center")
        self.tabela_atrasos.column("nome", width=180, anchor="center")
        self.tabela_atrasos.column("numero", width=100, anchor="center")
        self.tabela_atrasos.column("tempo", width=120, anchor="center")
        
        self.tabela_atrasos.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0,10)
        )

        self.tabela_atrasos.pack_forget()

        # Mensagem inicial da tabela de atrasos
        self.mensagem_atrasos = tk.Label(
            self.frame_grafico1,
            text="Por favor, selecione o intervalo de datas que quer visualizar.",
            fg=cores.PRIMARY_DARK,
            font=("Arial", 11),
            wraplength=350
        )
        # gráfico 2
        self.frame_grafico2 = tk.Frame(self.frame_graficos,
                                        highlightbackground= "#D6E3F0",
                                        highlightthickness=1)
        self.frame_grafico2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        w.criar_titulo(self.frame_grafico2,
                    "Funcionários com mais Faltas",
                    font=w.FONTE_SUBTITULO_DASH,
                    fg=cores.PRIMARY_DARK).pack(pady=12)


        self.tabela_faltas = ttk.Treeview(self.frame_grafico2,
                                            columns=("id", "nome", "numero", "tempo"),
                                            show="headings",
                                            height=8)

        # definir os títulos da coluna 
        self.tabela_faltas.heading("id", text="ID")
        self.tabela_faltas.heading("nome", text="Funcionário")
        self.tabela_faltas.heading("numero", text="Nº Atrasos")
        self.tabela_faltas.heading("tempo", text="Tempo Total")

        self.tabela_faltas.column("id", width=100, anchor="center")
        self.tabela_faltas.column("nome", width=180, anchor="center")
        self.tabela_faltas.column("numero", width=100, anchor="center")
        self.tabela_faltas.column("tempo", width=120, anchor="center")
        
        self.tabela_faltas.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0,10)
        )

        self.tabela_faltas.pack_forget()

        # Mensagem inicial da tabela de faltas
        self.mensagem_faltas = tk.Label(
            self.frame_grafico2,
            text="Por favor, selecione o intervalo de datas que quer visualizar.",
            fg=cores.PRIMARY_DARK,
            font=("Arial", 11),
            wraplength=350
        )

       # gráfico 3  
        self.frame_grafico3 = tk.Frame(
            self.frame_graficos,
            highlightbackground="#D6E3F0",
            highlightthickness=1)
        
        self.frame_grafico3.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5) # columnspan gráfico ocupa 2 colunas 
        
        w.criar_titulo(self.frame_grafico3,
                    "Funcionários com mais Horas Extra",
                    font=w.FONTE_SUBTITULO_DASH,
                    fg=cores.PRIMARY_DARK).pack(pady=12)

        self.tabela_extra = ttk.Treeview(self.frame_grafico3,
                                        columns=("id", "nome", "numero", "tempo"),
                                        show="headings",
                                        height=8)
        
        # definir os títulos da coluna 
        self.tabela_extra.heading("id", text="ID")
        self.tabela_extra.heading("nome", text="Funcionário")
        self.tabela_extra.heading("numero", text="Nº Atrasos")
        self.tabela_extra.heading("tempo", text="Tempo Total")

        self.tabela_extra.column("id", width=100, anchor="center")
        self.tabela_extra.column("nome", width=180, anchor="center")
        self.tabela_extra.column("numero", width=100, anchor="center")
        self.tabela_extra.column("tempo", width=120, anchor="center")
        
        self.tabela_extra.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0,10)
        )
        self.tabela_extra.pack_forget()

        # Mensagem inicial da tabela de horas extra
        self.mensagem_extra = tk.Label(
            self.frame_grafico3,
            text="Selecione o intervalo de datas que pretende visualizar no gráfico.",
            fg=cores.PRIMARY_DARK,
            font=("Arial", 11),
            wraplength=500
        )

        # mostrar as mensagem 
        self.mensagem_atrasos.pack(expand=True, pady=20)
        self.mensagem_faltas.pack(expand=True, pady=20)
        self.mensagem_extra.pack(expand=True, pady=20)

        self.atualizar_funcionarios()
        self.atualizar_faltas_medicas()


    def atualizar_funcionarios(self):

        ano = self.filtro_ano.get() # .get buscar o ano que está selecionado na combobox

        consulta = """
            SELECT COUNT(*)
            FROM FUNCIONARIOS
            WHERE YEAR(data_adesao) = %s
            AND estado = "ATIVO"
        """

        total_funcionarios = pd.read_sql(
            consulta,
            conn,
            params=(ano,)
        ).iloc[0, 0]

        self.label_funcionarios.config(text=str(total_funcionarios))


    def atualizar_faltas_medicas(self):

        ano = self.filtro_ano.get()

        consulta = """
            SELECT COUNT(*)
            FROM AUSENCIAS 
            WHERE tipo = %s
            AND YEAR(data_inicio) = %s
        """

        total_faltas_medicas = pd.read_sql(
            consulta,
            conn,
            params=("BAIXA_MEDICA", ano)
        ).iloc[0,0]

        self.label_faltas_medicas.config(text=str(total_faltas_medicas))

    def filtrar_tabelas(self):

        data_inicio = self.entry_data_inicio.get_date()
        data_fim = self.entry_data_fim.get_date()

        if data_inicio > data_fim:
                    messagebox.showerror(
                    "Erro",
                    "A data de fim não pode ser inferior à data de início")
                    return

         # Esconder as mensagens iniciais
        self.mensagem_atrasos.pack_forget()
        self.mensagem_faltas.pack_forget()
        self.mensagem_extra.pack_forget()

        # mostrar as tabelas
        self.tabela_atrasos.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.tabela_faltas.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.tabela_extra.pack(fill="both", expand=True, padx=10, pady=(0,10))


        # limpar os resultados anteriores 

        for tabela in (self.tabela_atrasos, self.tabela_faltas, self.tabela_extra):
             for resultado in tabela.get_children():
                  tabela.delete(resultado)


        # funcionários com mais atrasos 

        consulta_atrasos = """
                SELECT 
                    f.id_funcionario As id,
                    f.nome,
                    COUNT(*) AS numero, 
                    SUM(r.atraso_minutos) AS tempo
                FROM RESULTADOS r
                INNER JOIN FUNCIONARIOS f
                    on r.id_funcionario = f.id_funcionario
                WHERE r.data BETWEEN %s AND %s
                    AND r.atraso_minutos > 0 
                GROUP BY f.id_funcionario, f.nome
                ORDER BY numero DESC, tempo DESC
                LIMIT 5
            """

        dados_atrasos = pd.read_sql(consulta_atrasos, conn,
                                    params=(data_inicio, data_fim))

        if dados_atrasos.empty:
            self.mensagem_atrasos.config(
                text="Não existem atrasos neste intervalo de datas."
            )
            self.mensagem_atrasos.pack(expand=True, pady=20)
            self.tabela_atrasos.pack_forget()

        else:
            for _, linha in dados_atrasos.iterrows():
                self.tabela_atrasos.insert(
                    "", "end",
                    values=(
                        linha["id"],
                        linha["nome"],
                        int(linha["numero"]),
                        f'{int(linha["tempo"])} min'
                    )
                )