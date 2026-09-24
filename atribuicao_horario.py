# Pra que serve esse ficheiro?
# Este ficheiro é responsável pela página de atribuição de horários a funcionários.
# Permite ao admin escolher um funcionário, uma data e um horário (do catálogo já
# existente na tabela HORARIO) e gravar essa atribuição em FUNCIONARIO_HORARIO.
# Também mostra, para o funcionário selecionado, os horários já atribuídos.
#
# A atribuição é sempre por UM dia (não por intervalo). Isto é proposital: a
# UNIQUE(id_funcionario, data) na base de dados garante que nunca existem dois
# horários diferentes atribuídos ao mesmo funcionário no mesmo dia. Se o admin
# atribuir um horário a um dia que já tinha outro, este substitui o anterior
# (ON DUPLICATE KEY UPDATE), o que serve também para corrigir enganos.


import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import mysql.connector
from ttkbootstrap.widgets import DateEntry
from ligacao import conn


class PaginaAtribuicaoHorarios(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)

        self.cursor = conn.cursor(buffered=True)

        titulo = tk.Label(
            self,
            text="ATRIBUIÇÃO DE HORÁRIOS",
            font=("Arial", 24),
            background=bo
        )
        titulo.pack(pady=30)

        # -------------------------
        # FORMULÁRIO
        # -------------------------

        frame_formulario = tk.Frame(self)
        frame_formulario.pack(pady=10)

        # Funcionário
        tk.Label(
            frame_formulario,
            text="Funcionário:",
            font=("Arial", 12)
        ).grid(row=0, column=0, padx=(10,5), pady=5, sticky="e")

        self.combo_funcionario = ttk.Combobox(
            frame_formulario,
            font=("Arial", 12),
            state="readonly",
            width=16
        )
        self.combo_funcionario.grid(row=0, column=1, padx=(0,20), pady=5)

        self.combo_funcionario.bind(
            "<<ComboboxSelected>>",
            lambda e: self.atualizar_lista_atribuicoes()
        )

        # Data
        tk.Label(
            frame_formulario,
            text="Data:",
            font=("Arial", 12)
        ).grid(row=0, column=2, padx=(10,5), pady=5, sticky="e")

        self.entry_data = DateEntry(
            frame_formulario,
            dateformat="%Y-%m-%d",
            width=12,
            bootstyle=PRIMARY_DARK
        )
        self.entry_data.grid(row=0, column=3, padx=(0,20), pady=5)

        # Horário
        tk.Label(
            frame_formulario,
            text="Horário:",
            font=("Arial", 12)
        ).grid(row=0, column=4, padx=(10,5), pady=5, sticky="e")

        self.combo_horario = ttk.Combobox(
            frame_formulario,
            font=("Arial", 12),
            state="readonly",
            width=16
        )
        self.combo_horario.grid(row=0, column=5, padx=(0,10), pady=5)

        # Botão atribuir
        btn_atribuir = tk.Button(
            self,
            text="Atribuir Horário",
            font=("Arial", 12),
            command=self.atribuir_horario
            
        )
        btn_atribuir.pack(expand=True, pady=15)

        # -------------------------
        # TABELA DE ATRIBUIÇÕES
        # -------------------------

        self.tabela = ttk.Treeview(
            self,
            columns=("data", "horario", "tipo", "entrada", "saida"),
            show="headings"
        )

        self.tabela.heading("data", text="Data")
        self.tabela.heading("horario", text="Horário")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("entrada", text="Entrada")
        self.tabela.heading("saida", text="Saída")

        self.tabela.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=20
        )

        # -------------------------
        # CARREGAR DADOS INICIAIS
        # -------------------------

        self.carregar_funcionarios()
        self.carregar_horarios()

    # ==================================================
    # CARREGAR COMBOBOXES
    # ==================================================

    def carregar_funcionarios(self):
        self.cursor.execute(
            """
            SELECT id_funcionario, nome
            FROM funcionarios
            WHERE estado = 'ATIVO'
            ORDER BY nome
            """
        )

        # Mapa "Nome (#id)" -> id_funcionario,
        # para nunca depender do nome sozinho
        self.funcionarios_map = {
            f"{nome} (#{id_})": id_
            for id_, nome in self.cursor.fetchall()
        }

        self.combo_funcionario["values"] = list(
            self.funcionarios_map.keys()
        )

    def carregar_horarios(self):
        self.cursor.execute(
            """
            SELECT id_horario, nome, tipo
            FROM horario
            ORDER BY tipo, nome
            """
        )

        # Mapa "Nome [TIPO]" -> id_horario
        self.horarios_map = {
            f"{nome} [{tipo}]": id_
            for id_, nome, tipo in self.cursor.fetchall()
        }

        self.combo_horario["values"] = list(
            self.horarios_map.keys()
        )

    # ==================================================
    # ATRIBUIR HORÁRIO
    # ==================================================

    def atribuir_horario(self):

        funcionario_sel = self.combo_funcionario.get().strip()
        horario_sel = self.combo_horario.get().strip()

        # O DateEntry devolve a data como texto através de .get()
        data_texto = self.entry_data.entry.get().strip()

        if not funcionario_sel or not horario_sel:
            messagebox.showwarning(
                "Campos em falta",
                "Selecione o funcionário, a data e o horário."
            )
            return

        id_funcionario = self.funcionarios_map.get(funcionario_sel)
        id_horario = self.horarios_map.get(horario_sel)

        # Validar formato da data antes de ir à base de dados
        try:
            data = datetime.strptime(
                data_texto,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            messagebox.showerror(
                "Data inválida",
                "Selecione uma data válida no calendário."
            )
            return

        try:
            # ON DUPLICATE KEY UPDATE: se já existir horário nesse dia
            # para este funcionário, substitui em vez de rebentar
            # com erro de duplicado.
            self.cursor.execute(
                """
                INSERT INTO funcionario_horario
                    (id_funcionario, id_horario, data)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    id_horario = VALUES(id_horario)
                """,
                (
                    id_funcionario,
                    id_horario,
                    data
                )
            )

            conn.commit()

            messagebox.showinfo(
                "Sucesso",
                f"Horário atribuído para {data.strftime('%Y-%m-%d')}."
            )

            # Limpar seleção do horário
            self.combo_horario.set("")

            # Atualizar tabela
            self.atualizar_lista_atribuicoes()

        except mysql.connector.Error as erro:
            conn.rollback()

            print(erro)

            messagebox.showerror(
                "Erro",
                "Não foi possível atribuir o horário. "
                "Tente novamente!"
            )

    # ==================================================
    # LISTAR ATRIBUIÇÕES DO FUNCIONÁRIO SELECIONADO
    # ==================================================

    def atualizar_lista_atribuicoes(self):

        # Limpar tabela
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        funcionario_sel = self.combo_funcionario.get().strip()

        id_funcionario = self.funcionarios_map.get(
            funcionario_sel
        )

        if id_funcionario is None:
            return

        self.cursor.execute(
            """
            SELECT
                fh.data,
                h.nome,
                h.tipo,
                h.entrada,
                h.saida
            FROM funcionario_horario fh
            JOIN horario h
                ON h.id_horario = fh.id_horario
            WHERE fh.id_funcionario = %s
            ORDER BY fh.data DESC
            """,
            (id_funcionario,)
        )

        for data, nome, tipo, entrada, saida in self.cursor.fetchall():

            self.tabela.insert(
                "",
                tk.END,
                values=(
                    data.strftime("%Y-%m-%d") if data else "",
                    nome,
                    tipo,
                    entrada if entrada else "-",
                    saida if saida else "-"
                )
            )