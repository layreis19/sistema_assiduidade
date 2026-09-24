import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from ligacao import conn
from ttkbootstrap.widgets import DateEntry
from datetime import datetime

BG = "#EAF6FF"
PRIMARY = "#3F8FC1"
PRIMARY_DARK = "#2F78A8"
CARD = "#FFFFFF"
TEXT = "#1E3A52"


class PaginaRelatorios(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=CARD)
        self.cursor = conn.cursor(buffered=True)

       
        frame_topo = tk.Frame(self, bg=BG)
        frame_topo.pack(fill="x", padx=30, pady=10)
        tk.Label(frame_topo, text="RELATÓRIOS DE ASSIDUIDADE",
                 font=("Arial", 22, "bold"), bg=BG, fg=TEXT).pack(pady=50)

        # ----- Filtros -----
        frame_filtros = tk.Frame(self, bg=BG)
        frame_filtros.pack(pady=10)

        tk.Label(frame_filtros, text="ID do Funcionário:",
                 font=("Arial", 12), bg=BG, fg=TEXT).pack(side=tk.LEFT, padx=5)
        self.entry_id = tk.Entry(frame_filtros)
        self.entry_id.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(frame_filtros, text="Data de Início:",
                 font=("Arial", 12), bg=BG, fg=TEXT).pack(side=tk.LEFT, padx=5)
        self.calendario_inicio = DateEntry(frame_filtros, dateformat="%d/%m/%Y",
                                           width=15, bootstyle="info")
        self.calendario_inicio.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(frame_filtros, text="Data de Fim:",
                 font=("Arial", 12), bg=BG, fg=TEXT).pack(side=tk.LEFT, padx=5)
        self.calendario_fim = DateEntry(frame_filtros, dateformat="%d/%m/%Y",
                                        width=15, bootstyle="info")
        self.calendario_fim.pack(side=tk.LEFT)

        # ----- Botões -----
        tk.Button(frame_filtros, text="Filtrar", font=("Arial", 11, "bold"),
                  bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK,
                  activeforeground="white", bd=0, cursor="hand2",
                  command=self.filtrar_relatorio).pack(side=tk.LEFT, padx=10, ipady=10)

        tk.Button(frame_filtros, text="Gerar Relatório", font=("Arial", 11, "bold"),
                  bg=PRIMARY, fg="white", activebackground=PRIMARY_DARK,
                  activeforeground="white", bd=0, cursor="hand2",
                  command=self.gerar_relatorio_txt).pack(side=tk.LEFT, padx=10, ipady=10)

        # ----- Tabela -----
        self.tabela = ttk.Treeview(
            self,
            columns=("id", "nome", "data", "atrasos", "extras", "total"),
            show="headings"
        )
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("data", text="Data")
        self.tabela.heading("atrasos", text="Atrasos")
        self.tabela.heading("extras", text="Horas Extras")
        self.tabela.heading("total", text="Total Horas")
        self.tabela.pack(fill="both", expand=True, padx=30, pady=20)

   
    def filtrar_relatorio(self):
        id_func = self.entry_id.get().strip()
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

        if id_func and not id_func.isdigit():
            messagebox.showerror("Erro", "O ID deve ser um número!")
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

        if id_func:
            sql += " AND r.id_funcionario = %s"
            valores.append(int(id_func))

        sql += " ORDER BY r.data DESC, f.nome"

        self.cursor.execute(sql, valores)
        registos = self.cursor.fetchall()

        # Limpar a tabela e mostrar os novos dados
        self.tabela.delete(*self.tabela.get_children())

        for id_f, nome, data, atraso, extra, total in registos:
            self.tabela.insert("", tk.END, values=(
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
        linhas = self.tabela.get_children()

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
                id_f, nome, data, atraso, extra, total = self.tabela.item(item)["values"]
                f.write(f"{id_f:<6}{nome:<22}{data:<13}{atraso:<11}{extra:<11}{total}\n")

            f.write("=" * 70 + "\n")
            f.write(f"Total de registos: {len(linhas)}\n")

        messagebox.showinfo("Sucesso", "Relatório guardado!")