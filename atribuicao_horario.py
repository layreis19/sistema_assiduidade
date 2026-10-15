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
        self.id_horario_editar = None
        self.cursor = conn.cursor(buffered=True)

        w.criar_estilo_tabela()

        self.pagina_atribuir_horarios = tk.Frame(self, background=cores.CARD)
        self.pagina_editar_horarios = tk.Frame(self, background=cores.CARD)
        self.pagina_ferias = tk.Frame(self, background=cores.CARD)

        self.construir_atribuicao_horarios()
        self.criar_pagina2()
        self.criar_pagina_ferias()
        self.mostrar_pagina1()

        self.carregar_funcionarios()
        self.carregar_horarios()

        self.carregar_tabela_horarios()


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
            self.mostrar_pagina_ferias
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
            frame_formulario, "Designação:"
        ).pack(side=tk.LEFT, pady=5)

        self.entry_nome = w.criar_entrada(frame_formulario)
        self.entry_nome.pack(side=tk.LEFT, padx=10, pady=10)

        w.criar_label(
            frame_formulario, "Entrada (HH:MM):"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_entrada = w.criar_entrada(frame_formulario)
        self.entry_entrada.pack(side=tk.LEFT, padx=10, pady=10)

        w.criar_label(
            frame_formulario, "Saída (HH:MM):"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_saida = w.criar_entrada(frame_formulario)
        self.entry_saida.pack(side=tk.LEFT, padx=10, pady=10)


        w.criar_label(frame_formulario, "Tipo:"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_tipo = ttk.Combobox(frame_formulario, values=["FIXO", "TURNO"], state="readonly", width=12)
        self.entry_tipo.pack(side=tk.LEFT, padx=10, pady=10)


        frame_formulario_2 = tk.Frame(
            self.pagina_editar_horarios,
            background=cores.CARD)

        frame_formulario_2.pack(pady=10)

        w.criar_label(
            frame_formulario_2, "Início Pausa (HH:MM):"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_pausa = w.criar_entrada(frame_formulario_2)
        self.entry_pausa.pack(side=tk.LEFT, padx=10, pady=10)

        w.criar_label(
            frame_formulario_2, "Fim Pausa (HH:MM):"
        ).pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_fim_pausa = w.criar_entrada(frame_formulario_2)
        self.entry_fim_pausa.pack(side=tk.LEFT, padx=10, pady=10)


        w.criar_label(
            frame_formulario_2, "Tolerância:"
            ).pack(side=tk.LEFT, padx=10, pady=10)
        self.entry_tolerancia = w.criar_entrada(frame_formulario_2)
        self.entry_tolerancia.pack(side=tk.LEFT, padx=10, pady=10)

        frame_botoes = tk.Frame(
            self.pagina_editar_horarios,
            background=cores.CARD
        )
        frame_botoes.pack(pady=10)

        w.criar_label(frame_formulario_2, "Dias de Trabalho:").pack(side=tk.LEFT, padx=10, pady=10)
        
        self.lista_dias_trabalho = tk.Listbox(
            frame_formulario_2, 
            selectmode=tk.MULTIPLE,
            height=4,
            width=20,
            exportselection=False)

        dias = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]

        for dia in dias:
            self.lista_dias_trabalho.insert(tk.END, dia)


        # barra de scroll
        scroll_dias = tk.Scrollbar(frame_formulario_2, orient=tk.VERTICAL, command=self.lista_dias_trabalho.yview)
        self.lista_dias_trabalho.configure(yscrollcommand=scroll_dias.set)
        self.lista_dias_trabalho.pack(side=tk.LEFT, padx=(10,0))
        scroll_dias.pack(side=tk.LEFT, fill=tk.Y)   
        
        
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
            self.criar_horario
        ).pack(side=tk.LEFT, padx=5)

        w.criar_botao(
            frame_botoes,
            "Editar",
            self.editar_horario).pack(side=tk.LEFT, padx=5)

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
                "inicio_pausa", "fim_pausa", "saida", "tolerancia", "dias_trabalho"
            ),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela"
        )

        self.tabela_horarios.heading("id", text="ID")
        self.tabela_horarios.heading("nome", text="Nome")
        self.tabela_horarios.heading("tipo", text="Tipo")
        self.tabela_horarios.heading("entrada", text="Entrada")
        self.tabela_horarios.heading("inicio_pausa", text="Início Pausa")
        self.tabela_horarios.heading("fim_pausa", text="Fim Pausa")
        self.tabela_horarios.heading("saida", text="Saída")
        self.tabela_horarios.heading("tolerancia", text="Tolerância")
        self.tabela_horarios.heading("dias_trabalho", text="Dias Trabalho")

        self.tabela_horarios.column("id", width=40, anchor="center")
        self.tabela_horarios.column("nome", width=150, anchor="center")
        self.tabela_horarios.column("tipo", width=100, anchor="center")
        self.tabela_horarios.column("entrada", width=100, anchor="center")
        self.tabela_horarios.column("inicio_pausa", width=100, anchor="center")
        self.tabela_horarios.column("fim_pausa", width=100, anchor="center")
        self.tabela_horarios.column("saida", width=100, anchor="center")
        self.tabela_horarios.column("tolerancia", width=40, anchor="center")
        self.tabela_horarios.column("dias_trabalho", width=150, anchor="center")

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

    def criar_horario(self):

        nome = self.entry_nome.get().strip().upper()
        entrada = self.entry_entrada.get().strip()
        inicio_pausa = self.entry_pausa.get().strip()
        fim_pausa = self.entry_fim_pausa.get().strip()
        tolerancia = self.entry_tolerancia.get().strip()
        saida = self.entry_saida.get().strip()
        tipo = self.entry_tipo.get()
        dias_selecionados = self.lista_dias_trabalho.curselection()

        dias_trabalho = ",".join(self.lista_dias_trabalho.get(i)
                                 for i in dias_selecionados)

        if not nome or not entrada or not inicio_pausa or not fim_pausa or not tolerancia or not saida or not tipo or not dias_trabalho:
            messagebox.showerror(
                "Erro",
                "Todos os campos são obrigatórios!"
            )
            return

        if inicio_pausa <= entrada: 
            messagebox.showerror(
                "Erro!",
                "A hora da Início de Pausa tem que ser superior à hora de Entrada!")
            return

        elif fim_pausa <= inicio_pausa:
            messagebox.showerror(
                "Erro!",
                "A hora de Fim de Pausa tem que ser superior à hora de Início de Pausa!")
            return

        elif saida <= fim_pausa:
            messagebox.showerror(
                "Erro!",
                "A hora de Saída tem que ser superior à hora de Fim de Pausa!")
            return

        try:
            tolerancia = int(tolerancia)

            if tolerancia <0:
                messagebox.showerror(
                    "Erro", 
                    "A tolerância não pode ser negativa!")
                return
        except ValueError:
            messagebox.showerror(
                "Erro",
                "A tolerância tem que ser um número inteiro!")
            return
       
        try:
            self.cursor.execute(
                """
                INSERT INTO HORARIO
                (nome, entrada, inicio_almoco, fim_almoco, saida, tolerancia, tipo, dias_trabalho)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (nome, entrada, inicio_pausa, fim_pausa, saida, tolerancia, tipo, dias_trabalho)
            )

            conn.commit()
            self.carregar_tabela_horarios()

            # limpar campos
            self.entry_nome.delete(0, tk.END)
            self.entry_entrada.delete(0, tk.END)
            self.entry_pausa.delete(0,tk.END)
            self.entry_fim_pausa.delete(0, tk.END)
            self.entry_saida.delete(0, tk.END)
            self.entry_tolerancia.delete(0, tk.END)
            self.entry_tipo.delete(0, tk.END)

            messagebox.showinfo(
                "Sucesso",
                "Horário criado com sucesso!"
            )
            


        except mysql.connector.Error as erro:
            conn.rollback()

            messagebox.showerror(
                "Erro",
                f"Erro ao adicionar horário: {erro}"
            )


    def carregar_tabela_horarios(self):

        for item in self.tabela_horarios.get_children():
            self.tabela_horarios.delete(item)

        try:
            self.cursor.execute("""
            SELECT
                id_horario,
                nome,
                tipo,
                entrada, 
                inicio_almoco,
                fim_almoco,
                saida, 
                tolerancia,
                dias_trabalho
            FROM horario
            ORDER BY id_horario
            """
        )

            horarios = self.cursor.fetchall()
            ordem_dias = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]
            for horario in horarios:
                horario = list(horario)

                dias = horario[8]
                if dias:
                    dias_selecionados = str(dias).replace("{","").replace("}", "")
                    dias_selecionados = dias_selecionados.replace('"', "").replace("'", "")
                    dias_selecionados = [ dia.strip() for dia in dias_selecionados.split(",")]

                    dias_ordenados = [ dia for dia in ordem_dias if dia in dias_selecionados]

                    horario[8] = ", ".join(dias_ordenados)

                else:
                    horario[8] = ""
                    
                self.tabela_horarios.insert(
                    "",
                    tk.END,
                    values=horario
                )

        except mysql.connector.Error as erro:
            messagebox.showerror(
                "Erro",
                f"Não foi possível carregar os horários. \n{erro}",
                parent=self)

    def criar_pagina_ferias(self):
        w.criar_titulo(self.pagina_ferias,
                       "GESTÃO DE FÉRIAS").pack(pady=(30,20))

        frame_formulario = tk.Frame(self.pagina_ferias, background=cores.CARD)
        frame_formulario.pack(pady=10)

        frame_botoes = tk.Frame(self.pagina_ferias, background=cores.CARD)
        frame_botoes.pack(pady=10)

        w.criar_label(frame_formulario,
                      "Funcionário:"
                      ).grid(row=0, column=0, padx=(10,5), pady=10, sticky="e")

        self.combo_funcionario_ferias = ttk.Combobox(
            frame_formulario, 
            font=w.FONTE_LABEL,
            state="readonly",
            width=20)

        self.combo_funcionario_ferias.grid(row=0, column=1, padx=(0,20), pady=10)

        self.combo_funcionario_ferias.bind(
            "<<ComboboxSelected>>",
            lambda funcionario: self.atualizar_lista_atribuicoes())

        w.criar_label(frame_formulario, "Data de Início:").grid(row=0, column=2, padx=(0,5), pady=10, sticky="e")
        self.entry_inicio = DateEntry(
            frame_formulario,
            date_format="%d-%m-%Y",
            width=14,
            bootstyle=cores.PRIMARY_DARK
        )
        self.entry_inicio.grid(row=0, column=3, padx=(0,20), pady=10, sticky="w")


        w.criar_label(frame_formulario, "Data de fim:").grid(row=0, column=4, padx=(0,5), pady=10, sticky="e")
        self.entry_fim = DateEntry(
            frame_formulario,
            date_format="%d-%m-%Y",
            width=14,
            bootstyle=cores.PRIMARY_DARK
        )
        self.entry_fim.grid(row=0, column=5, padx=(0,10), pady=10, sticky="w")

        w.criar_botao(
            frame_botoes,
            "Guardar",
            lambda: (
                messagebox.showwarning(
                    "Funcionário não selecionado",
                    "Por favor, selecione um funcionário.",
                    parent=self)
                if not self.combo_funcionario_ferias.get().strip()
                else self.guardar_ferias(
                    self.combo_funcionario_ferias.get().strip(),
                    self.entry_inicio.entry.get().strip(),
                    self.entry_fim.entry.get().strip(),
                    self.pagina_ferias)
            )).pack(side=tk.LEFT, padx=5)

        w.criar_botao(frame_botoes,
                      "Alterar",
                      self.alterar_ferias).pack(side=tk.LEFT, padx=5)

        w.criar_botao(frame_botoes, 
                      "Cancelar",
                      self.cancelar_ferias).pack(side=tk.LEFT, padx=5)

        w.criar_botao(self.pagina_ferias,
                      "Voltar",
                      self.mostrar_pagina1).pack(side="bottom", anchor="w", padx=30, pady=15)

        frame_tabela = tk.Frame(self.pagina_ferias,background=cores.CARD)
        frame_tabela.pack(fill="both", expand=True, padx=30, pady=20)

        self.tabela_ferias= ttk.Treeview(
            frame_tabela,
            columns=("id_aus", "id_func", "nome", "inicio_ferias", "fim_ferias", "estado"),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela")


        self.tabela_ferias.heading("id_aus", text="ID Ausência")
        self.tabela_ferias.heading("id_func", text="ID Funcionário")
        self.tabela_ferias.heading("nome", text="Nome")
        self.tabela_ferias.heading("inicio_ferias", text="Início Férias")
        self.tabela_ferias.heading("fim_ferias", text="Fim Férias")
        self.tabela_ferias.heading("estado", text="Estado")

        self.tabela_ferias.column("id_aus", width=60, anchor="center")
        self.tabela_ferias.column("id_func", width=150, anchor="center")
        self.tabela_ferias.column("nome", width=100, anchor="center")
        self.tabela_ferias.column("inicio_ferias", width=120, anchor="center")
        self.tabela_ferias.column("fim_ferias", width=120, anchor="center")
        self.tabela_ferias.column("estado", width=100, anchor="center")

         # Cores da tabela
        self.tabela_ferias.tag_configure("CANCELADO",foreground="#d00000")
        
        
        scroll = ttk.Scrollbar(
            frame_tabela,
            orient="vertical",
            command=self.tabela_ferias.yview
        )
        self.tabela_ferias.configure(
            yscrollcommand=scroll.set
        )

        self.tabela_ferias.pack(
            side="left", fill="both", expand=True
        )
        scroll.pack(side="right", fill="y")

    def carregar_ferias(self):
        for item in self.tabela_ferias.get_children():
            self.tabela_ferias.delete(item)

        try:
            self.cursor.execute("""
            SELECT
                a.id,
                f.id_funcionario,
                f.nome,
                a.data_inicio,
                a.data_fim,
                a.estado
            FROM AUSENCIAS AS a
            INNER JOIN funcionarios AS f
                ON a.id_funcionario = f.id_funcionario
            WHERE a.tipo = "Ferias"
            ORDER BY a.estado, a.data_inicio
            """
            )

            ferias = self.cursor.fetchall()

            for id, id_funcionario, nome, inicio, fim, estado in ferias:
                self.tabela_ferias.insert(
                    "",
                    tk.END,
                    values=(
                        id,
                        id_funcionario,
                        nome, 
                        inicio.strftime("%d-%m-%Y"), 
                        fim.strftime("%d-%m-%Y"),
                        estado),
                        tags=("CANCELADO",) if estado =="CANCELADO" else()
                )
        except mysql.connector.Error as erro:
            print(erro)

            messagebox.showerror(
                "Erro",
                "Não foi possível carregar as férias.",
                parent=self
            )


    def alterar_ferias(self):
        item_selecionado = self.tabela_ferias.selection()
        if not item_selecionado:
            messagebox.showerror(
                "Erro",
                "Selecione um funcionário para alterar!"
            )
            return
        
                
        # obter os dados da linha selecionada
        valores = self.tabela_ferias.item(item_selecionado[0], "values")

        if valores[-1] == "CANCELADO":
            messagebox.showwarning("AVISO!", "Não pode alterar férias canceladas!", parent = self)
            return
        
        inicio = datetime.strptime(valores[3], "%d-%m-%Y").date()
        fim = datetime.strptime(valores[4], "%d-%m-%Y").date()
        
        self.janela_alterar = tk.Toplevel(self)
        self.janela_alterar.title("Alterar Férias")

        w.criar_label(self.janela_alterar, "Data de Início:").pack(padx=10, pady=(10,0))
        # dias 
        self.entry_inicio_alterar = DateEntry(
            self.janela_alterar,
            date_format="%d-%m-%Y",
            first_weekday=0,
            bootstyle=cores.PRIMARY_DARK)

        self.entry_inicio_alterar.pack(padx=10, pady=10)

        self.entry_inicio_alterar.set_date(inicio)


        w.criar_label(self.janela_alterar, "Data de Fim:").pack(padx=10, pady=(10,0))
        self.entry_fim_alterar = DateEntry(
            self.janela_alterar,
            date_format="%d-%m-%Y",
            first_weekday=0,
            bootstyle=cores.PRIMARY_DARK)

        self.entry_fim_alterar.pack(padx=10, pady=10)
        self.entry_fim_alterar.set_date(fim)

        w.criar_botao(
            self.janela_alterar,
            "Guardar alterações",
            self.guardar_alteracoes_ferias).pack(padx=10, pady=10)

    def guardar_alteracoes_ferias(self):
        item_selecionado = self.tabela_ferias.selection()

        if not item_selecionado:
            return

       
        valores = self.tabela_ferias.item(item_selecionado[0], "values")

        id_ausencia = valores[0]

        inicio = self.entry_inicio_alterar.entry.get().strip()
        fim = self.entry_fim_alterar.entry.get().strip()

        try:
            data_inicio = datetime.strptime(inicio, "%d-%m-%Y").date()
            data_fim = datetime.strptime(fim, "%d-%m-%Y").date()

            if data_fim < data_inicio:
                messagebox.showerror(
                    "Erro",
                    "A data de fim não pode ser anterior à data de início!",
                    parent = self.janela_alterar
                )
                return

            self.cursor.execute("""
            UPDATE AUSENCIAS
            SET 
                data_inicio = %s,
                data_fim = %s
            WHERE id = %s
            """, (
                data_inicio,
                data_fim,
                id_ausencia
            ))

            conn.commit()
            self.janela_alterar.destroy()

            self.carregar_ferias()

            messagebox.showinfo(
                "Sucesso!",
                "Férias alteradas com sucesso!",
                parent=self
            )

        except ValueError:
            messagebox.showerror(
                "Erro",
                "As datas introduzidas são inválidas.",
                parent=self.janela_alterar
        )

        except mysql.connector.Error as erro:
            conn.rollback()
            messagebox.showerror(
                "Erro",
                f"Não foi possível alterar as férias. \n{erro}",
                parent=self.janela_alterar
            )

    def mostrar_pagina_ferias(self):
        self.pagina_atribuir_horarios.pack_forget()
        self.pagina_editar_horarios.pack_forget()

        self.carregar_funcionarios()

        self.combo_funcionario_ferias["values"] = list(self.funcionarios_map.keys())

        self.carregar_ferias()

        self.pagina_ferias.pack(fill="both", expand=True)

    def guardar_ferias(self, funcionario_sel, inicio_data, fim_data, janela):
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
                inicio_data, "%d-%m-%Y"
            ).date()
            fim = datetime.strptime(
                fim_data, "%d-%m-%Y"
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
                SELECT h.dias_trabalho
                FROM funcionarios AS f
                INNER JOIN horario AS h 
                    ON f.horario = h.id_horario
                WHERE f.id_funcionario = %s
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
            
            id_admin = self.id_admin() if callable(self.id_admin) else self.id_admin
            if id_admin is None:
                messagebox.showerror(
                    "Erro",
                    "Não foi possível identificar o administrador autenticado.",
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
                    "FERIAS",
                    id_admin
                )
            )

            conn.commit()
            if isinstance(janela, tk.Toplevel):
                janela.destroy()

            self.carregar_ferias()

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
                f"Não foi possível registar as férias. Tente novamente.\n{erro}",
                parent=janela
            )

    def cancelar_ferias(self):
            item_selecionado = self.tabela_ferias.selection()
            if not item_selecionado:
                messagebox.showerror(
                    "Erro",
                    "Selecione um funcionário para cancelar as férias!"
                )
                return

            valores = self.tabela_ferias.item(item_selecionado[0], "values")

            if valores[-1]=="CANCELADO":
                messagebox.showwarning("AVISO!", "Férias já canceladas!!", parent=self)
                return

            
            id_ausencia = valores[0]

            try:
                self.cursor.execute(
                    '''UPDATE ausencias
                    SET estado = 'CANCELADO'
                    WHERE id = %s''',
                    (id_ausencia,)
                )
                conn.commit()
            
            
                self.carregar_ferias()

                messagebox.showinfo(
                    "Sucesso!",
                    "Cancelado com sucesso!",
                    parent=self
                )

            

            except mysql.connector.Error as erro:
                conn.rollback()
                messagebox.showerror(
                    "Erro",
                    f"Não foi possível cancelar as férias. \n{erro}",
                    parent=self
                )
            
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
            date_format="%d-%m-%Y",
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
                data, "%d-%m-%Y"
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

    def editar_horario(self):
    

        item_selecionado = self.tabela_horarios.selection()

        if not item_selecionado:
            messagebox.showwarning(
                "Erro!",
                "Selecione um horário da tabela.",
                parent=self
            )
            return

        valores = self.tabela_horarios.item(item_selecionado[0], "values")

        janela = tk.Toplevel(self)
        janela.title("Editar Horário")
        janela.geometry("500x800")
        janela.transient(self.winfo_toplevel())
        janela.grab_set()

        id_horario = valores[0]

        frame_formulario = tk.Frame(janela,background=cores.CARD)
        frame_formulario.pack(padx=20, pady=20, fill="x")

        frame_botao = tk.Frame(janela, background=cores.CARD)
        frame_botao.pack(side="bottom", fill="x", padx=20, pady=10)

        w.criar_label(frame_formulario, "Designação:").pack(anchor="w")
        entry_nome = w.criar_entrada(frame_formulario)
        entry_nome.pack(fill="x", pady=(0,10))

        w.criar_label(frame_formulario, "Entrada (HH:MM):").pack(anchor="w")
        entry_entrada = w.criar_entrada(frame_formulario)
        entry_entrada.pack(fill="x", pady=(0,10))

        w.criar_label(frame_formulario, "Saída (HH:MM):").pack(anchor="w")
        entry_saida = w.criar_entrada(frame_formulario)
        entry_saida.pack(fill="x", pady=(0,10))
    

        w.criar_label(frame_formulario, "Tipo:").pack(anchor="w")
        entry_tipo = ttk.Combobox(frame_formulario, values=["FIXO", "TURNO"], state="readonly", width=12)
        entry_tipo.pack(fill="x", pady=(0,10))

        w.criar_label(frame_formulario, "Início Pausa (HH:MM):").pack(anchor="w")
        entry_pausa = w.criar_entrada(frame_formulario)
        entry_pausa.pack(fill="x", pady=(0,10))

        w.criar_label(frame_formulario, "Fim Pausa (HH:MM):").pack(anchor="w")
        entry_fim_pausa = w.criar_entrada(frame_formulario)
        entry_fim_pausa.pack(fill="x", pady=(0,10))

        w.criar_label(frame_formulario, "Tolerância (minutos):").pack(anchor="w")
        entry_tolerancia = w.criar_entrada(frame_formulario)
        entry_tolerancia.pack(fill="x", pady=(0,10))

        w.criar_label(frame_formulario, "Dias de Trabalho").pack(anchor="w")
        lista_dias = tk.Listbox(frame_formulario, selectmode=tk.MULTIPLE,exportselection=False, height=7)
        lista_dias.pack(fill="x", pady=(0,10))

        for dia in ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]:
            lista_dias.insert(tk.END, dia)

        def guardar_alteracoes_horario():
            
            nome = entry_nome.get().strip().upper()
            entrada = entry_entrada.get().strip()
            saida = entry_saida.get().strip()
            tipo = entry_tipo.get()
            inicio_pausa = entry_pausa.get().strip()
            fim_pausa = entry_fim_pausa.get().strip()
            tolerancia = entry_tolerancia.get().strip()

            dias_selecionados = lista_dias.curselection()
            
            dias_trabalho = ",".join(lista_dias.get(i)for i in dias_selecionados)
            
            if not nome or not entrada or not inicio_pausa or not fim_pausa or not tolerancia or not saida or not tipo or not dias_trabalho:
                messagebox.showerror(
                    "Erro",
                    "Todos os campos são obrigatórios!"
                )
                return

            if inicio_pausa <= entrada: 
                messagebox.showerror(
                    "Erro!",
                    "A hora da Início de Pausa tem que ser superior à hora de Entrada!")
                return

            elif fim_pausa <= inicio_pausa:
                messagebox.showerror(
                    "Erro!",
                    "A hora de Fim de Pausa tem que ser superior à hora de Início de Pausa!")
                return

            elif saida <= fim_pausa:
                messagebox.showerror(
                    "Erro!",
                    "A hora de Saída tem que ser superior à hora de Fim de Pausa!")
                return

            try:
                tolerancia = int(tolerancia)

                if tolerancia <0:
                    messagebox.showerror(
                        "Erro", 
                        "A tolerância não pode ser negativa!")
                    return
            except ValueError:
                messagebox.showerror(
                    "Erro",
                    "A tolerância tem que ser um número inteiro!")
                return
            
            try:
                self.cursor.execute(
                    """
                    UPDATE HORARIO
                    SET nome = %s,
                        entrada = %s,
                        inicio_almoco = %s,
                        fim_almoco = %s,
                        saida = %s,
                        tolerancia = %s,
                        tipo = %s,
                        dias_trabalho = %s
                    WHERE id_horario = %s
                    """,
                    (nome, entrada, inicio_pausa, fim_pausa, saida, tolerancia, tipo, dias_trabalho, id_horario)
                )

                conn.commit()
                
                self.carregar_tabela_horarios()
                self.carregar_horarios()

                janela.destroy()

                messagebox.showinfo(
                    "Sucesso",
                    "Horário atualizado com sucesso!"
                )
                


            except mysql.connector.Error as erro:
                conn.rollback()

                messagebox.showerror(
                    "Erro",
                    f"Erro ao atualizar horário: {erro}",
                    parent=janela
                )

            pass

        w.criar_botao(frame_botao, "Guardar", guardar_alteracoes_horario).pack(anchor="center", pady=5)
            
        

         



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
        self.pagina_ferias.pack_forget()
        self.pagina_editar_horarios.pack(
            fill="both", expand=True
        )

    def mostrar_pagina1(self):
        self.pagina_editar_horarios.pack_forget()
        self.pagina_ferias.pack_forget()
        self.pagina_atribuir_horarios.pack(
            fill="both", expand=True
        )