import tkinter as tk 
from ligacao import conn
import cores
import pandas as pd
from datetime import datetime, time, timedelta
import widgets as w
from tkinter import ttk
from ttkbootstrap.widgets import DateEntry



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

        # criar a pagina
        self.pagina_dashboard = tk.Frame(self, background=cores.BLUE_VERY_LIGHT)
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
                                       values=["2024", "2025", "2026"],
                                       state="readonly",
                                        width=8)
        self.filtro_ano.set("2026")
        self.filtro_ano.pack(side="right", padx=(0,10), anchor="e")

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
            None,
            bg=cores.PRIMARY,
            fg=cores.CARD,
            activebackground=cores.PRIMARY_DARK,
            activeforeground=cores.CARD).grid(row=1, column=4, padx=(0,0))
        

        # criar frame gráficos
        self.frame_graficos = tk.Frame(self.pagina_dashboard, bg=cores.BLUE_VERY_LIGHT)
        self.frame_graficos.pack(fill="both", expand=True, pady=(0,10))

        # configurar as duas colunas
        self.frame_graficos.grid_columnconfigure((0,1),weight=1, uniform="graficos")
        self.frame_graficos.grid_rowconfigure((0,1), weight=1)

        # gráfico 1
        self.frame_grafico1 = tk.Frame(
            self.frame_graficos,
            bg=cores.CARD,
            highlightbackground="#D6E3F0",
            highlightthickness=1)
        self.frame_grafico1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5) # nsew estica o gráfico para todo o espaço disponível
        
        w.criar_titulo(self.frame_grafico1,
                    "Funcionários com mais Atrasos",
                    font=w.FONTE_SUBTITULO_DASH,
                    bg=cores.CARD,
                    fg=cores.PRIMARY_DARK).pack(pady=12)
        
        
        # gráfico 2
        self.frame_grafico2 = tk.Frame(self.frame_graficos,
                                       bg= cores.CARD,
                                        highlightbackground= "#D6E3F0",
                                        highlightthickness=1)
        self.frame_grafico2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        w.criar_titulo(self.frame_grafico2,
                    "Funcionários com mais Faltas",
                    font=w.FONTE_SUBTITULO_DASH,
                    bg=cores.CARD,
                    fg=cores.PRIMARY_DARK).pack(pady=12)

       # gráfico 3  
        self.frame_grafico3 = tk.Frame(
            self.frame_graficos,
            bg=cores.CARD,
            highlightbackground="#D6E3F0",
            highlightthickness=1)
        
        self.frame_grafico3.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5) # columnspan gráfico ocupa 2 colunas 
        
        w.criar_titulo(self.frame_grafico3,
                    "Funcionários com mais Horas Extra",
                    font=w.FONTE_SUBTITULO_DASH,
                    bg=cores.CARD,
                    fg=cores.PRIMARY_DARK).pack(pady=12)