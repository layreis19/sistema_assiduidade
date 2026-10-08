"""
O QUE ESTE FICHEIRO FAZ?
É a página de relatórios de assiduidade (só para administradores).
- Filtra por ID do funcionário (opcional) e por período (data de início e de fim).
- Mostra numa tabela os atrasos, horas extra e total de horas, lidos da tabela RESULTADOS.
- O botão Gerar Relatório guarda o que está na tabela num ficheiro .txt.
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from ligacao import conn
from ttkbootstrap.widgets import DateEntry
from datetime import datetime, date
import calendar
import cores
import widgets as w
from processamento import processar_dados_funcionario


class PaginaRelatorios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=cores.CARD)

        self.cursor = conn.cursor(buffered=True)
        hoje = date.today()
        primeiro_dia = hoje.replace(day=1)
        ultimo_dia = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])

        w.criar_titulo(self,"RELATÓRIOS DE ASSIDUIDADE").pack(pady=(30,20))

        #Filtros 
        frame_formulario = tk.Frame(self, background=cores.CARD)
        frame_formulario.pack(pady=10)

        w.criar_label(frame_formulario, "Funcionários:").pack(side=tk.LEFT, pady=5)

        self.lista_funcionarios = tk.Listbox(
            frame_formulario,
            selectmode=tk.SINGLE,
            height=4,
            width=25,
            exportselection=False
        )
        self.lista_funcionarios.pack(side=tk.LEFT, padx=10)

        self.ids_funcionarios = []                 

        w.criar_label(frame_formulario, "Data de Início:").pack(side=tk.LEFT, padx=5)
        self.calendario_inicio = DateEntry(
            frame_formulario, 
            dateformat="%d/%m/%Y",
            startdate=primeiro_dia,
            width=12,
            bootstyle=cores.PRIMARY_DARK)
        self.calendario_inicio.pack(side= tk.LEFT, padx=(0,20), pady=5)


        w.criar_label(frame_formulario,"Data de Fim:").pack(side=tk.LEFT, padx=5)
        self.calendario_fim = DateEntry(
            frame_formulario,
            dateformat="%d/%m/%Y",
             startdate=ultimo_dia,
            width=12,
            bootstyle=cores.PRIMARY_DARK)
        self.calendario_fim.pack(side=tk.LEFT, padx=(0,20), pady=5)

        # Botões 
        frame_botoes = tk.Frame(self, background=cores.CARD)
        frame_botoes.pack(pady=10)

        # Botão editar
        w.criar_botao(frame_botoes, "Filtrar", self.filtrar_relatorio).pack(side=tk.LEFT, padx=5)

        # Botão relatório
        w.criar_botao(frame_botoes, "Gerar Relatório", self.gerar_relatorio_txt).pack(side=tk.LEFT, padx=5)



        # FRAME TABELA 
        frame_tabela = tk.Frame(self)
        frame_tabela.pack(fill="both", expand=True, padx=30, pady=20)
       
        # Tabela 
        self.tabela_relatorios = ttk.Treeview(
            frame_tabela,
            columns=(
                "id", 
                "nome", 
                "data", 
                "atrasos", 
                "extras", 
                "total"),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela")


        # Cabeçalhos
        self.tabela_relatorios.heading("id", text="ID")
        self.tabela_relatorios.heading("nome", text="Nome")
        self.tabela_relatorios.heading("data", text="Data")
        self.tabela_relatorios.heading("atrasos", text="Atrasos")
        self.tabela_relatorios.heading("extras", text="Horas Extras")
        self.tabela_relatorios.heading("total", text="Total Horas")

        # Colunas 
        self.tabela_relatorios.column("id", width=60,anchor="center")
        self.tabela_relatorios.column("nome", width=150,anchor="center")
        self.tabela_relatorios.column("data", width=100,anchor="center")
        self.tabela_relatorios.column("atrasos", width=100,anchor="center")
        self.tabela_relatorios.column("extras", width=120,anchor="center")
        self.tabela_relatorios.column("total", width=120,anchor="center")


        # scroll 
        scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela_relatorios.yview)
        self.tabela_relatorios.configure(yscrollcommand=scroll.set)
        self.tabela_relatorios.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        
        self.carregar_funcionarios()
        
        
        
    def carregar_funcionarios(self):
        self.cursor.execute(
            "SELECT id_funcionario, nome, estado FROM funcionarios ORDER BY nome"
        )
        self.funcionarios_map = {}
        for id_, nome, estado in self.cursor.fetchall():
            sufixo = "" if estado == "ATIVO" else " - inativo"
            self.funcionarios_map[f"{nome} (#{id_}){sufixo}"] = id_

        # novo: mostrar os nomes na lista
        for nome in self.funcionarios_map:
            self.lista_funcionarios.insert(tk.END, nome)
        
    def filtrar_relatorio(self):
        
        data_inicio = self.calendario_inicio.entry.get().strip()
        data_fim = self.calendario_fim.entry.get().strip()

        # Converter texto -> data
        try:
            data_inicio = datetime.strptime(data_inicio, "%d/%m/%Y").date()
            data_fim = datetime.strptime(data_fim, "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Erro", "Data inválida! Usa dd/mm/aaaa.")
            return

        if data_inicio > data_fim:
            messagebox.showerror("Erro", "A data de início não pode ser depois da data de fim!")
            return

        # Procurar na base de dados
        sql = """
            SELECT r.id_funcionario, f.nome, r.data,
                   r.atraso_minutos, r.horas_extra_minutos, r.total_minutos_trabalhados
            FROM RESULTADOS r
            JOIN FUNCIONARIOS f ON f.id_funcionario = r.id_funcionario
            WHERE r.data BETWEEN %s AND %s
        """
        valores = [data_inicio, data_fim]
        
        
        escolhidos = []
        for posicao in self.lista_funcionarios.curselection():
            nome = self.lista_funcionarios.get(posicao)
            escolhidos.append(self.funcionarios_map[nome])

        if escolhidos:
            marcadores = []
            for id_f in escolhidos:
                marcadores.append("%s")        # um %s por cada funcionário escolhido

            texto = ",".join(marcadores)        # junta com vírgulas: "%s,%s,%s"

            sql += " AND r.id_funcionario IN (" + texto + ")"
            valores += escolhidos

        self.cursor.execute(sql, valores)
        registos = self.cursor.fetchall()

        # Limpar a tabela e mostrar os novos dados
        self.tabela_relatorios.delete(*self.tabela_relatorios.get_children())

        for id_f, nome, data, atraso, extra, total in registos:
            self.tabela_relatorios.insert("", tk.END, values=(
                id_f,
                nome,
                data.strftime("%d/%m/%Y"),
                f"{atraso} min" if atraso else "-",
                f"{extra} min" if extra else "-",
                f"{total // 60}h{total % 60:02d}",
            ))

        if not registos:
            messagebox.showinfo("Sem resultados", "Não há dados para este período.")

    
    def gerar_relatorio_txt(self):
        linhas = self.tabela_relatorios.get_children()

        if not linhas:
            messagebox.showwarning("Aviso", "Primeiro clica em Filtrar!")
            return

        caminho = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Ficheiro de texto", "*.txt")]
        )
        if not caminho:
            return

        with open(caminho, "w", encoding="utf-8") as f:
            f.write("RELATÓRIO DE ASSIDUIDADE\n")
            f.write("=" * 70 + "\n")
            f.write(f"{'ID':<6}{'NOME':<22}{'DATA':<13}{'ATRASOS':<11}{'EXTRAS':<11}{'TOTAL'}\n")
            f.write("-" * 70 + "\n")

            for item in linhas:
                id_f, nome, data, atraso, extra, total = self.tabela_relatorios.item(item)["values"]
                f.write(f"{id_f:<6}{nome:<22}{data:<13}{atraso:<11}{extra:<11}{total}\n")

            f.write("=" * 70 + "\n")
            f.write(f"Total de registos: {len(linhas)}\n")

        messagebox.showinfo("Sucesso", "Relatório guardado!")