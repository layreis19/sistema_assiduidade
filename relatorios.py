import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import mysql.connector
from ligacao import conn
import ttkbootstrap
from ttkbootstrap.widgets import DateEntry
from datetime import datetime




BG = "#EAF6FF"             # Fundo principal
PRIMARY = "#3F8FC1"        # Azul principal
PRIMARY_DARK = "#2F78A8"   # Azul mais escuro
BLUE_LIGHT = "#B5D9EA"     # Azul claro
BLUE_VERY_LIGHT = "#D9EDF7"
CARD = "#FFFFFF"           # Branco
TEXT = "#1E3A52"           # Texto principal
TEXT_SECONDARY = "#6B879C" # Texto secundário
BORDER = "#C7E3F2"


class PaginaRelatorios(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent, bg= CARD)
        self.parent= parent
        self.cursor = conn.cursor(buffered=True)
        
        #cabeçalho da página
        
        frame_topo= tk.Frame(self, bg= BG)
        frame_topo.pack(fill= "x", padx=30,pady=(10))
        
        titulo = tk.Label(  frame_topo,text="RELATÓRIOS DE ASSIDUIDADE",font=("Arial", 22,"bold"),bg=BG,fg=TEXT)
        titulo.pack(pady=50)
        
        
        
        frame_filtros= tk.Frame(self,bg=BG)
        frame_filtros.pack(pady=10)
        
        # filtro por ID do func
        id_label = tk.Label( 
        frame_filtros,text="ID do Funcionário:", 
        font=("Arial", 12),
        bg=BG,
        fg=TEXT )
        id_label.pack(side=tk.LEFT, padx=5)
        
        self.entry_id = tk.Entry(frame_filtros)
        self.entry_id.pack(side=tk.LEFT, padx=(0, 20))
        
        #filtrar por data Inicio
        data_inicio= tk.Label(
            frame_filtros,
            text="Data de Início:",
            font=("Arial",12),
            bg= BG,
            fg=TEXT
        )
        data_inicio.pack(side=tk.LEFT, padx=5)
        
        self.calendario_inicio = DateEntry(
            frame_filtros,
            dateformat="%d/%m/%Y",
            width=15,
            bootstyle="info"
        )
        self.calendario_inicio.pack(side=tk.LEFT, padx=(0, 20))
        
        
        #filtrar por data de fim
        
        data_fim = tk.Label(
            frame_filtros,
            text="Data de Fim",
            font=("Arial",12),
            bg=BG,
            fg=TEXT,
        )
        data_fim.pack(side=tk.LEFT, padx=5)
        
        self.calendario_fim= DateEntry(
            frame_filtros,
            dateformat="%d/%m/%Y",
            width=15,
            bootstyle="info"
        )
        self.calendario_fim.pack(side=tk.LEFT)
      
      
      #botao filtrar  
        btn_filtrar= tk.Button(frame_filtros,
            text="Filtrar",
            font=("Arial",11,"bold"),
            bg=PRIMARY,
            fg="white",
            activebackground=PRIMARY_DARK,
            activeforeground="white",
            bd=0,
            cursor="hand2",
            command=self.filtrar_relatorio
        )
        btn_filtrar.pack(side=tk.LEFT, padx=10, ipady=10)
        
        # botao gerar relatorio
        btn_relatorio= tk.Button(frame_filtros,
                text="Gerar Relatório",
                font=("Arial",11,"bold"),
                bg=PRIMARY,
                fg="white",
                activebackground=PRIMARY_DARK,
                activeforeground="white",
                bd=0,
                cursor="hand2",
               
        )
        btn_relatorio.pack(side=tk.LEFT, padx=10, ipady=10)
                
        

        #tabela resultados
        
        self.tabela= ttk.Treeview(
            self,
            columns=("id_funcionario","nome","data","atrasos","horas_extras","total_horas"),
            show="headings"
        )
        
        self.tabela.heading("id_funcionario", text="id_funcionario")
        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("data", text="Data")
        self.tabela.heading("atrasos", text="Atrasos")
        self.tabela.heading("horas_extras", text="Horas Extras")
        self.tabela.heading("total_horas", text="Total Horas")
        self.tabela.pack(fill="both", expand=True, padx=30, pady=20)
        
    def filtrar_relatorio(self):

        id_funcionario = self.entry_id.get().strip()
        data_inicio = self.calendario_inicio.entry.get().strip()
        data_fim = self.calendario_fim.entry.get().strip()


        # as duas datasd são obrigatórias
        if not data_inicio or not data_fim:
            messagebox.showwarning("Aviso", "Por favor, escolhe a data de início e a data de fim!")
            return

        try:
            data_inicio = datetime.strptime(data_inicio, "%d/%m/%Y").date()
            data_fim = datetime.strptime(data_fim, "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Erro","Data inválida!  Usa o formato dd/mm/aaaa.")
            return


        # a data de início nao pode ser depois da data de fim
        if data_inicio > data_fim:
            messagebox.showerror("Erro", "A data de início não pode ser depois da data de fim!")
            return

        # Se o ID foi preenchido, tem de ser um número válido
        if id_funcionario and not id_funcionario.isdigit():
            messagebox.showerror("Erro", "O ID do funcionário deve ser um número!")
            return

        # --------------------------------
        # LIMPAR TABELA
        # --------------------------------

        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        # --------------------------------
        # CONSULTAR RESULTADOS
        # --------------------------------
        # Junta com funcionarios só para ter o nome a mostrar; o cálculo
        # em si já está feito (é lido de RESULTADOS, não recalculado aqui).

        query = """
            SELECT r.id_funcionario, f.nome, r.data,
                   r.atraso_minutos, r.horas_extra_minutos, r.total_minutos_trabalhados
            FROM resultados r
            JOIN funcionarios f ON f.id_funcionario = r.id_funcionario
            WHERE r.data BETWEEN %s AND %s
        """
        parametros = [data_inicio, data_fim]

        if id_funcionario:
            query += " AND r.id_funcionario = %s"
            parametros.append(int(id_funcionario))

        query += " ORDER BY r.data DESC, f.nome"

        self.cursor.execute(query, parametros)

        def formatar_minutos(minutos):
            horas, mins = divmod(minutos, 60)
            return f"{horas}h{mins:02d}"

        for id_f, nome, data, atraso_min, extra_min, total_min in self.cursor.fetchall():
            self.tabela.insert(
                "",
                tk.END,
                values=(
                    id_f,
                    nome,
                    data.strftime("%d/%m/%Y"),
                    f"{atraso_min} min" if atraso_min else "-",
                    f"{extra_min} min" if extra_min else "-",
                    formatar_minutos(total_min),
                )
            )

        if not self.tabela.get_children():
            messagebox.showinfo(
                "Sem resultados",
                "Não há dados calculados para este período/funcionário."
            )