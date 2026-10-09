import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import mysql.connector
from ttkbootstrap.widgets import DateEntry

from ligacao import conn
import cores
import widgets as w


class PaginaAtribuicaoHorarios(tk.Frame):

    def __init__(self, parent, id_admin):
        super().__init__(parent, bg=cores.CARD)

        self.id_admin = id_admin
        self.cursor = conn.cursor(buffered=True)

        w.criar_estilo_tabela()

        self.pagina_atribuir_horarios = tk.Frame(
            self, background=cores.CARD
        )
        self.pagina_editar_horarios = tk.Frame(
            self, background=cores.CARD
        )

        self.construir_atribuicao_horarios()
        self.criar_pagina2()

        self.mostrar_pagina1()

        self.carregar_funcionarios()
        self.carregar_horarios()

    # ==================================================
    # FÉRIAS
    # ==================================================

    def adicionar_ferias(self):
        janela = tk.Toplevel(self)
        janela.title("Adicionar Férias")
        janela.transient(self)

        w.criar_label(janela, "Funcionário").pack(
            pady=(10, 2), padx=20
        )

        combo = ttk.Combobox(
            janela,
            font=w.FONTE_LABEL,
            state="readonly",
            width=28,
            values=list(self.funcionarios_map.keys())
        )
        combo.set(self.combo_funcionario.get())
        combo.pack(pady=20)

        w.criar_label(janela, "Data de início:").pack(
            pady=(10, 2), padx=20
        )
        entry_inicio = DateEntry(
            janela,
            date_format="%Y-%m-%d",
            width=14,
            bootstyle=cores.PRIMARY_DARK
        )
        entry_inicio.pack(padx=20)

        w.criar_label(janela, "Data de fim:").pack(
            pady=(10, 2), padx=20
        )
        entry_fim = DateEntry(
            janela,
            date_format="%Y-%m-%d",
            width=14,
            bootstyle=cores.PRIMARY_DARK
        )
        entry_fim.pack(padx=20)

        w.criar_botao(
            janela,
            "Guardar",
            lambda: self.guardar_ferias(
                combo.get().strip(),
                entry_inicio.get().strip(),
                entry_fim.get().strip(),
                janela
            )
        ).pack(pady=15)

    def guardar_ferias(
        self, funcionario_sel, inicio_data, fim_data, janela
    ):
        if not funcionario_sel:
            messagebox.showwarning(
                "Campos em falta",
                "Selecione o funcionário.",
                parent=janela
            )
            return

        id_funcionario = self.funcionarios_map.get(funcionario_sel)

        try:
            inicio = datetime.strptime(
                inicio_data, "%Y-%m-%d"
            ).date()
            fim = datetime.strptime(
                fim_data, "%Y-%m-%d"
            ).date()

            if fim < inicio:
                messagebox.showwarning(
                    "Data inválida",
                    "A data de fim não pode ser anterior à data de início.",
                    parent=janela
                )
                return

            self.cursor.execute(
                """
                SELECT dias_trabalho
                FROM funcionarios
                WHERE id_funcionario = %s
                """,
                (id_funcionario,)
            )

            linha = self.cursor.fetchone()
            valor = linha[0] if linha else None

            if not valor:
                messagebox.showwarning(
                    "Dias de trabalho em falta",
                    "Este funcionário não tem dias de trabalho definidos.",
                    parent=janela
                )
                return

            self.cursor.execute(
                """
                SELECT 1
                FROM AUSENCIAS
                WHERE id_funcionario = %s
                  AND data_inicio <= %s
                  AND data_fim >= %s
                """,
                (id_funcionario, fim, inicio)
            )

            if self.cursor.fetchone():
                messagebox.showwarning(
                    "Ausência já registada",
                    "Este funcionário já tem uma ausência neste período.",
                    parent=janela
                )
                return

            self.cursor.execute(
                """
                INSERT INTO AUSENCIAS
                    (id_funcionario, data_inicio, data_fim,
                     tipo, aprovado_por)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    id_funcionario,
                    inicio,
                    fim,
                    "FÉRIAS",
                    self.id_admin
                )
            )

            conn.commit()
            janela.destroy()

            messagebox.showinfo(
                "Sucesso",
                "Férias guardadas com sucesso!",
                parent=self
            )

        except ValueError:
            messagebox.showerror(
                "Data inválida",
                "Selecione datas válidas.",
                parent=janela
            )

        except mysql.connector.Error as erro:
            conn.rollback()
            print(erro)

            messagebox.showerror(
                "Erro",
                "Não foi possível registar as férias. Tente novamente.",
                parent=janela
            )

    # ==================================================
    # PÁGINA DE ATRIBUIÇÃO DE HORÁRIOS
    # ==================================================

    def construir_atribuicao_horarios(self):

        w.criar_titulo(
            self.pagina_atribuir_horarios,
            "ATRIBUIR HORÁRIOS"
        ).pack(pady=(30, 20))

        frame_formulario = tk.Frame(
            self.pagina_atribuir_horarios,
            background=cores.CARD
        )
        frame_formulario.pack(pady=10)

        # Funcionário
        w.criar_label(
            frame_formulario, "Funcionário:"
        ).grid(
            row=0, column=0,
            padx=(10, 5), pady=5, sticky="e"
        )

        self.combo_funcionario = ttk.Combobox(
            frame_formulario,
            font=w.FONTE_LABEL,
            state="readonly",
            width=20
        )
        self.combo_funcionario.grid(
            row=0, column=1, padx=(0, 20), pady=5
        )

        self.combo_funcionario.bind(
            "<<ComboboxSelected>>",
            lambda e: self.atualizar_lista_atribuicoes()
        )

        # Horário
        w.criar_label(
            frame_formulario, "Horário:"
        ).grid(
            row=0, column=2,
            padx=(10, 5), pady=5, sticky="e"
        )

        self.combo_horario = ttk.Combobox(
            frame_formulario,
            font=w.FONTE_LABEL,
            state="readonly",
            width=20
        )
        self.combo_horario.grid(
            row=0, column=3, padx=(0, 10), pady=5
        )

        # Botões
        frame_botoes = tk.Frame(
            self.pagina_atribuir_horarios,
            background=cores.CARD
        )
        frame_botoes.pack(pady=10)

        w.criar_botao(
            frame_botoes,
            "Férias",
            self.adicionar_ferias
        ).pack(side=tk.LEFT, pady=5)

        w.criar_botao(
            frame_botoes,
            "Atribuir Horário",
            self.atribuir_horario
        ).pack(side=tk.LEFT, padx=10)

        w.criar_botao(
            frame_botoes,
            "Editar Horários",
            self.mostrar_pagina2
        ).pack(side=tk.LEFT, padx=5)

        # Tabela do horário atribuído ao funcionário
        frame_tabela = tk.Frame(
            self.pagina_atribuir_horarios,
            background=cores.CARD
        )
        frame_tabela.pack(
            fill="both", expand=True, padx=30, pady=20
        )

        self.tabela_editar_horarios = ttk.Treeview(
            frame_tabela,
            columns=("horario", "tipo", "entrada", "saida"),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela"
        )

        self.tabela_editar_horarios.heading(
            "horario", text="Horário"
        )
        self.tabela_editar_horarios.heading(
            "tipo", text="Tipo"
        )
        self.tabela_editar_horarios.heading(
            "entrada", text="Entrada"
        )
        self.tabela_editar_horarios.heading(
            "saida", text="Saída"
        )

        self.tabela_editar_horarios.column(
            "horario", width=180, anchor="center"
        )
        self.tabela_editar_horarios.column(
            "tipo", width=100, anchor="center"
        )
        self.tabela_editar_horarios.column(
            "entrada", width=100, anchor="center"
        )
        self.tabela_editar_horarios.column(
            "saida", width=100, anchor="center"
        )

        scroll = ttk.Scrollbar(
            frame_tabela,
            orient="vertical",
            command=self.tabela_editar_horarios.yview
        )
        self.tabela_editar_horarios.configure(
            yscrollcommand=scroll.set
        )

        self.tabela_editar_horarios.pack(
            side="left", fill="both", expand=True
        )
        scroll.pack(side="right", fill="y")

    # ==================================================
    # PÁGINA DE EDIÇÃO DE HORÁRIOS
    # ==================================================

    def criar_pagina2(self):

        w.criar_titulo(
            self.pagina_editar_horarios,
            "EDITAR HORÁRIOS"
        ).pack(pady=(30, 20))

        frame_formulario = tk.Frame(
            self.pagina_editar_horarios,
            background=cores.CARD
        )
        frame_formulario.pack(pady=10)

        w.criar_label(
            frame_formulario, "Nome:"
        ).pack(side=tk.LEFT, pady=5)

        self.entry_nome = w.criar_entrada(frame_formulario)
        self.entry_nome.pack(side=tk.LEFT, padx=10, pady=10)

        w.criar_label(
            frame_formulario, "Entrada:"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_entrada = w.criar_entrada(frame_formulario)
        self.entry_entrada.pack(side=tk.LEFT, padx=10, pady=10)

        w.criar_label(
            frame_formulario, "Início Pausa:"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_pausa = w.criar_entrada(frame_formulario)
        self.entry_pausa.pack(side=tk.LEFT, padx=10, pady=10)

        w.criar_label(
            frame_formulario, "Fim Pausa:"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_fim_pausa = w.criar_entrada(frame_formulario)
        self.entry_fim_pausa.pack(side=tk.LEFT, padx=10, pady=10)

        w.criar_label(
            frame_formulario, "Saída:"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_saida = w.criar_entrada(frame_formulario)
        self.entry_saida.pack(side=tk.LEFT, padx=10, pady=10)

        frame_botoes = tk.Frame(
            self.pagina_editar_horarios,
            background=cores.CARD
        )
        frame_botoes.pack(pady=10)

        w.criar_botao(
            frame_botoes,
            "Feriados",
            self.adicionar_feriado
        ).pack(side=tk.LEFT, pady=5)

        # Mantidos os botões originais de edição.
        # As funções de criar, editar e eliminar horários
        # precisam de ser ligadas às respetivas operações SQL.
        w.criar_botao(
            frame_botoes,
            "Criar",
            lambda: messagebox.showinfo(
                "Informação",
                "A funcionalidade de criação de horários ainda não está implementada."
            )
        ).pack(side=tk.LEFT, padx=5)

        w.criar_botao(
            frame_botoes,
            "Editar",
            lambda: messagebox.showinfo(
                "Informação",
                "A funcionalidade de edição de horários ainda não está implementada."
            )
        ).pack(side=tk.LEFT, padx=5)

        w.criar_botao(
            frame_botoes,
            "Eliminar",
            lambda: messagebox.showinfo(
                "Informação",
                "A funcionalidade de eliminação de horários ainda não está implementada."
            )
        ).pack(side=tk.LEFT, padx=5)

        w.criar_botao(
            self.pagina_editar_horarios,
            "Voltar",
            self.mostrar_pagina1
        ).pack(
            side="bottom", anchor="w", padx=30, pady=15
        )

        frame_tabela = tk.Frame(
            self.pagina_editar_horarios,
            background=cores.CARD
        )
        frame_tabela.pack(
            fill="both", expand=True, padx=30, pady=20
        )

        self.tabela_horarios = ttk.Treeview(
            frame_tabela,
            columns=(
                "id", "nome", "tipo", "entrada",
                "inicio_pausa", "fim_pausa", "saida"
            ),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela"
        )

        cabecalhos = {
            "id": "ID",
            "nome": "Nome",
            "tipo": "Tipo",
            "entrada": "Entrada",
            "inicio_pausa": "Início Pausa",
            "fim_pausa": "Fim Pausa",
            "saida": "Saída"
        }

        larguras = {
            "id": 60,
            "nome": 150,
            "tipo": 100,
            "entrada": 100,
            "inicio_pausa": 120,
            "fim_pausa": 120,
            "saida": 100
        }

        for coluna, titulo in cabecalhos.items():
            self.tabela_horarios.heading(
                coluna, text=titulo
            )
            self.tabela_horarios.column(
                coluna,
                width=larguras[coluna],
                anchor="center"
            )

        scroll = ttk.Scrollbar(
            frame_tabela,
            orient="vertical",
            command=self.tabela_horarios.yview
        )
        self.tabela_horarios.configure(
            yscrollcommand=scroll.set
        )

        self.tabela_horarios.pack(
            side="left", fill="both", expand=True
        )
        scroll.pack(side="right", fill="y")

    # ==================================================
    # FERIADOS
    # ==================================================

    def adicionar_feriado(self):
        janela = tk.Toplevel(self)
        janela.title("Adicionar Feriado")
        janela.transient(self)

        w.criar_label(
            janela, "Data:"
        ).pack(pady=(10, 2), padx=20)

        entry_data = DateEntry(
            janela,
            date_format="%Y-%m-%d",
            width=14,
            bootstyle=cores.PRIMARY_DARK
        )
        entry_data.pack(padx=20)

        w.criar_label(
            janela, "Descrição:"
        ).pack(pady=(10, 2), padx=20)

        entry_descricao = w.criar_entrada(
            janela, largura=32
        )
        entry_descricao.pack(padx=20)

        w.criar_botao(
            janela,
            "Guardar",
            lambda: self.guardar_feriados(
                entry_data.entry.get().strip(),
                entry_descricao.get().strip(),
                janela
            )
        ).pack(pady=15)

    def guardar_feriados(self, data, descricao, janela):

        if not descricao:
            messagebox.showwarning(
                "Campos em falta",
                "Introduza a descrição do feriado.",
                parent=janela
            )
            return

        try:
            data_validada = datetime.strptime(
                data, "%Y-%m-%d"
            ).date()

            self.cursor.execute(
                """
                INSERT INTO FERIADOS (data, descricao)
                VALUES (%s, %s)
                """,
                (data_validada, descricao)
            )

            conn.commit()
            janela.destroy()

            messagebox.showinfo(
                "Sucesso",
                "Feriado guardado com sucesso!",
                parent=self
            )

        except ValueError:
            messagebox.showerror(
                "Data inválida",
                "Selecione uma data válida.",
                parent=janela
            )

        except mysql.connector.Error as erro:
            conn.rollback()
            print(erro)

            messagebox.showerror(
                "Erro",
                "Não foi possível registar o feriado. "
                "Verifique se já existe um registo para essa data.",
                parent=janela
            )

    # ==================================================
    # CARREGAR FUNCIONÁRIOS
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

        self.funcionarios_map = {
            f"{nome} (#{id_})": id_
            for id_, nome in self.cursor.fetchall()
        }

        self.combo_funcionario["values"] = list(
            self.funcionarios_map.keys()
        )

    # ==================================================
    # CARREGAR HORÁRIOS
    # ==================================================

    def carregar_horarios(self):

        self.cursor.execute(
            """
            SELECT id_horario, nome, tipo
            FROM horario
            ORDER BY tipo, nome
            """
        )

        self.horarios_map = {
            f"{nome} [{tipo}]": id_
            for id_, nome, tipo in self.cursor.fetchall()
        }

        self.combo_horario["values"] = list(
            self.horarios_map.keys()
        )

    # ==================================================
    # ATRIBUIR HORÁRIO AO FUNCIONÁRIO
    # ==================================================

    def atribuir_horario(self):

        funcionario_sel = self.combo_funcionario.get().strip()
        horario_sel = self.combo_horario.get().strip()

        if not funcionario_sel or not horario_sel:
            messagebox.showwarning(
                "Campos em falta",
                "Selecione o funcionário e o horário."
            )
            return

        id_funcionario = self.funcionarios_map.get(
            funcionario_sel
        )
        id_horario = self.horarios_map.get(horario_sel)

        if id_funcionario is None or id_horario is None:
            messagebox.showwarning(
                "Seleção inválida",
                "Selecione um funcionário e um horário válidos."
            )
            return

        try:
            self.cursor.execute(
                """
                UPDATE funcionarios
                SET horario = %s
                WHERE id_funcionario = %s
                """,
                (id_horario, id_funcionario)
            )

            if self.cursor.rowcount == 0:
                # Distinguir um funcionário inexistente de um
                # horário que já estava atribuído.
                self.cursor.execute(
                    """
                    SELECT id_funcionario
                    FROM funcionarios
                    WHERE id_funcionario = %s
                    """,
                    (id_funcionario,)
                )

                if not self.cursor.fetchone():
                    conn.rollback()
                    messagebox.showerror(
                        "Erro",
                        "O funcionário selecionado não existe."
                    )
                    return

            conn.commit()

            messagebox.showinfo(
                "Sucesso",
                f"Horário atribuído a {funcionario_sel} com sucesso."
            )

            self.combo_horario.set("")
            self.atualizar_lista_atribuicoes()

        except mysql.connector.Error as erro:
            conn.rollback()
            print(erro)

            messagebox.showerror(
                "Erro",
                "Não foi possível atribuir o horário. Tente novamente."
            )

    # ==================================================
    # MOSTRAR O HORÁRIO DO FUNCIONÁRIO SELECIONADO
    # ==================================================

    def atualizar_lista_atribuicoes(self):

        for item in self.tabela_editar_horarios.get_children():
            self.tabela_editar_horarios.delete(item)

        funcionario_sel = self.combo_funcionario.get().strip()
        id_funcionario = self.funcionarios_map.get(
            funcionario_sel
        )

        if id_funcionario is None:
            return

        try:
            self.cursor.execute(
                """
                SELECT
                    h.nome,
                    h.tipo,
                    h.entrada,
                    h.saida
                FROM funcionarios AS f
                LEFT JOIN horario AS h
                    ON h.id_horario = f.horario
                WHERE f.id_funcionario = %s
                """,
                (id_funcionario,)
            )

            resultado = self.cursor.fetchone()

            if resultado and resultado[0] is not None:
                nome, tipo, entrada, saida = resultado

                self.tabela_editar_horarios.insert(
                    "",
                    tk.END,
                    values=(
                        nome,
                        tipo,
                        entrada if entrada else "-",
                        saida if saida else "-"
                    )
                )
            else:
                self.tabela_editar_horarios.insert(
                    "",
                    tk.END,
                    values=(
                        "Sem horário atribuído",
                        "-",
                        "-",
                        "-"
                    )
                )

        except mysql.connector.Error as erro:
            print(erro)
            messagebox.showerror(
                "Erro",
                "Não foi possível consultar o horário do funcionário."
            )

    # ==================================================
    # NAVEGAÇÃO ENTRE PÁGINAS
    # ==================================================

    def mostrar_pagina2(self):
        self.pagina_atribuir_horarios.pack_forget()
        self.pagina_editar_horarios.pack(
            fill="both", expand=True
        )

    def mostrar_pagina1(self):
        self.pagina_editar_horarios.pack_forget()
        self.pagina_atribuir_horarios.pack(
            fill="both", expand=True
        )