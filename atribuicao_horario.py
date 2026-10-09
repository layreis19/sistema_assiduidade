# Pra que serve esse ficheiro?
# Este ficheiro é responsável pela página de atribuição de horários a funcionários.
# Permite ao admin escolher um funcionário, uma data e um horário (do catálogo já
# existente na tabela HORARIO) e gravar essa atribuiç
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
import cores
import widgets as w


class PaginaAtribuicaoHorarios(tk.Frame):
    def __init__(self, parent, id_admin):

        super().__init__(parent, bg=cores.CARD)

        self.id_admin = id_admin
        # buffered = true (guarda os resultados da consulta no cursor)
        self.cursor = conn.cursor(buffered=True)

        w.criar_estilo_tabela()

        # Página atribuir horários/editar
        self.pagina_atribuir_horarios = tk.Frame(self, background=cores.CARD)
        self.pagina_editar_horarios = tk.Frame(self, background=cores.CARD)

        self.construir_atribuicao_horarios()
        
        self.criar_pagina2()


        # mostrar por defeito a primeira página 
        self.mostrar_pagina1()

        self.carregar_funcionarios()
        self.carregar_horarios()

    def adicionar_ferias(self):
        janela = tk.Toplevel(self)
        janela.title("Adicionar Férias")
        janela.transient(self)

        # funcionário
        w.criar_label(janela, "Funcionário").pack(pady=(10,2), padx=20)
        combo = ttk.Combobox(janela, font=w.FONTE_LABEL, state="readonly", width=28, values=list(self.funcionarios_map.keys()),)

        combo.set(self.combo_funcionario.get())
        combo.pack(pady=20)

        # data início 
        w.criar_label(janela, "Data de início:").pack(pady=(10,2), padx=20)
        entry_inicio = DateEntry(janela, date_format="%Y-%m-%d", width=14, bootstyle=cores.PRIMARY_DARK)
        entry_inicio.pack(padx=20)

        # data fim
        w.criar_label(janela, "Data de Fim:").pack(pady=(10,2), padx=20)
        entry_fim = DateEntry(janela, date_format="%Y-%m-%d", width=14, bootstyle=cores.PRIMARY_DARK)
        entry_fim.pack(padx=20)

        w.criar_botao(janela,
                      "Guardar",
                      lambda: self.guardar_ferias(
                          combo.get().strip(),
                          entry_inicio.get().strip(),
                          entry_fim.get().strip(),
                          janela,
                      ),
                      ).pack(pady=15)

    def guardar_ferias(self, id_funcionario, inicio_data, fim_data, janela):
        if not id_funcionario:
            messagebox.showwarning(
                "Campos em falta", 
                "Selecione o funcionário.",
                parent=janela,)
            return

        id_funcionario = self.funcionarios_map.get(id_funcionario)

        try: 
            inicio = datetime.strptime(inicio_data, "%Y-%m-%d").date()
            fim = datetime.strptime(fim_data, "%Y-%m-%d").date()


            # não permitir que a data do fim seja anterior à data de início
            if fim < inicio:
                messagebox.showwarning(
                    "A data de fim não pode ser anterior à data de início.",
                    parent=janela,)
                return

            # dias que o funcionário trabalha
            self.cursor.execute(
                """
                SELECT dias_trabalho
                FROM funcionarios 
                WHERE id_funcionario = %s
                """,
                (id_funcionario,),
                )
            
            linha = self.cursor.fetchone()
            valor = linha[0] if linha else None

            if not valor:
                messagebox.showwarning(
                    "Dias de trabalho em falta",
                    "Este funcionário não tem dias de trabalho definidos.",
                    parent=janela,)

                return
            
            self.cursor.execute("""
            SELECT 1 FROM AUSENCIAS
            WHERE id_funcionario = %s
                AND data_inicio <= %s
                AND data_fim >= %s
            """,
            (id_funcionario, fim, inicio),)

            if self.cursor.fetchone():
                messagebox.showwarning(
                    "Ausência já registada",
                    "Este funcionário já tem uma ausência neste período.",
                    parent=janela,)

                return

            self.cursor.execute("""
                INSERT INTO AUSENCIAS
                    (id_funcionario, data_inicio, data_fim, tipo, aprovado_por)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (id_funcionario, inicio, fim, "FÉRIAS", self.id_admin),)
            
            conn.commit()
            janela.destroy()
            messagebox.showinfo(
                "Férias guardadas com sucesso!",
                parent=self,)

        except ValueError:
            messagebox.showerror(
                "Data inválida",
                "Selecione datas válidas.",
                parent=janela,)

        except mysql.connector.Error as erro:
            conn.rollback()
            print(erro)
            messagebox.showerror(
                "Erro",
                "Não foi possível registar as férias. Tente novamente.",
                parent=janela,
            )

    def construir_atribuicao_horarios(self):

        # Título da página atribuir horários
        w.criar_titulo(self.pagina_atribuir_horarios,"ATRIBUIR HORÁRIOS").pack(pady=(30,20))

        # Formulário 
        frame_formulario = tk.Frame(self.pagina_atribuir_horarios, background=cores.CARD)
        frame_formulario.pack(pady=10)

        # Funcionário
        w.criar_label(frame_formulario,"Funcionário:").grid(row=0, column=0, padx=(10,5), pady=5, sticky="e")

        self.combo_funcionario = ttk.Combobox(frame_formulario,font=w.FONTE_LABEL, state="readonly", width=16)
        self.combo_funcionario.grid(row=0, column=1, padx=(0,20), pady=5)


        self.combo_funcionario.bind(
            "<<ComboboxSelected>>",
            lambda e: self.atualizar_lista_atribuicoes())

        # Data
        w.criar_label(frame_formulario, "Data:").grid(row=0, column=2, padx=(10,5), pady=5, sticky="e")

        self.entry_data = DateEntry(frame_formulario, dateformat="%Y-%m-%d", width=12, bootstyle=cores.PRIMARY_DARK)
        self.entry_data.grid(row=0, column=3, padx=(0,20), pady=5)

        # Horário
        w.criar_label(frame_formulario, "Horário:").grid(row=0, column=4, padx=(10,5), pady=5, sticky="e")

        self.combo_horario = ttk.Combobox(frame_formulario, font=w.FONTE_LABEL, state="readonly", width=16)
        self.combo_horario.grid(row=0, column=5, padx=(0,10), pady=5)

        # botões
        frame_botoes = tk.Frame(self.pagina_atribuir_horarios, background=cores.CARD)
        frame_botoes.pack(pady=10)

        # botão criar férias
        w.criar_botao(frame_botoes, "Férias", self.adicionar_ferias).pack(side=tk.LEFT, pady=5)

        # Botão atribuir
        w.criar_botao(frame_botoes,"Atribuir Horário",self.atribuir_horario).pack(side=tk.LEFT,padx=10)

        # botão para ir para a página de edição de horários 
        w.criar_botao(frame_botoes, "Editar Horários", self.mostrar_pagina2).pack(side=tk.LEFT,padx=5)

        # FRAME TABELA
        frame_tabela = tk.Frame(self.pagina_atribuir_horarios, background=cores.CARD)
        frame_tabela.pack(fill="both", expand=True, padx=30, pady=20)

        # Tabela 
        self.tabela_editar_horarios = ttk.Treeview(
            frame_tabela,
            columns=("data", 
                     "horario", 
                     "tipo", 
                     "entrada", 
                     "saida"),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela"
        )

        # Cabeçalhos
        self.tabela_editar_horarios.heading("data", text="Data")
        self.tabela_editar_horarios.heading("horario", text="Horário")
        self.tabela_editar_horarios.heading("tipo", text="Tipo")
        self.tabela_editar_horarios.heading("entrada", text="Entrada")
        self.tabela_editar_horarios.heading("saida", text="Saída")

        # largura das colunas
        self.tabela_editar_horarios.column("data",width=120,anchor="center")
        self.tabela_editar_horarios.column("horario",width=180,anchor="center")
        self.tabela_editar_horarios.column("tipo",width=100,anchor="center")
        self.tabela_editar_horarios.column("entrada",width=100,anchor="center")
        self.tabela_editar_horarios.column("saida",width=100,anchor="center")

        scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela_editar_horarios.yview)
        self.tabela_editar_horarios.configure(yscrollcommand=scroll.set)
        self.tabela_editar_horarios.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def criar_pagina2(self):

        # Título 
        w.criar_titulo(self.pagina_editar_horarios,"EDITAR HORÁRIOS",).pack(pady=(30,20))

        # frame label 
        frame_formulario = tk.Frame(self.pagina_editar_horarios, background=cores.CARD)
        frame_formulario.pack(pady=10)

        # Nome 
        w.criar_label(frame_formulario,"Nome:").pack(side=tk.LEFT,pady=5)
        self.entry_nome = w.criar_entrada(frame_formulario)
        self.entry_nome.pack(side=tk.LEFT, padx=10, pady=10)

        # Entrada
        w.criar_label(frame_formulario,"Entrada:").pack(side=tk.LEFT, padx=10, pady=10)
        self.entry_entrada = w.criar_entrada(frame_formulario)
        self.entry_entrada.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Inicio da pausa 
        w.criar_label(frame_formulario,"Inicio Pausa:").pack(side=tk.LEFT,padx=10, pady=10)
        self.entry_pausa = w.criar_entrada(frame_formulario)
        self.entry_pausa.pack(side=tk.LEFT, padx=10, pady=10)

        # Fim da pausa 
        w.criar_label(frame_formulario,"Fim Pausa:").pack(side=tk.LEFT,padx=10, pady=10)
        self.entry_fim_pausa = w.criar_entrada(frame_formulario)
        self.entry_fim_pausa.pack(side=tk.LEFT, padx=10, pady=10)

        # Saída
        w.criar_label(frame_formulario,"Saída:").pack(side=tk.LEFT, padx=10, pady=10)
        self.entry_saida = w.criar_entrada(frame_formulario)
        self.entry_saida.pack(side=tk.LEFT, padx=10, pady=10)
        
        
        # frame botões
        frame_botoes = tk.Frame(self.pagina_editar_horarios, background=cores.CARD)
        frame_botoes.pack(pady=10)

        # Botão 
        w.criar_botao(frame_botoes, "Feriados", self.adicionar_feriado). pack(side=tk.LEFT, pady=5)

        # Botão criar 
        w.criar_botao(frame_botoes, "Criar", self.pagina_editar_horarios).pack(side=tk.LEFT, padx=5)
            
        # Botão editar
        w.criar_botao(frame_botoes, "Editar", self.pagina_editar_horarios).pack(side=tk.LEFT, padx=5)

        # Botão eliminar 
        w.criar_botao(frame_botoes, "Eliminar", self.pagina_editar_horarios).pack(side=tk.LEFT, padx=5)

        # Botão voltar
        w.criar_botao(self.pagina_editar_horarios, "Voltar", self.mostrar_pagina1).pack(side="bottom",anchor="w",padx=30, pady=15)

        # FRAME TABELA
        frame_tabela = tk.Frame(self.pagina_editar_horarios, background=cores.CARD)
        frame_tabela.pack(fill="both", expand=True, padx=30,pady=20)
        
        # Tabela 
        self.tabela_horarios = ttk.Treeview(
            frame_tabela,
            columns=(
                "id",
                "nome",
                "tipo",
                "entrada",
                "inicio_pausa",
                "fim_pausa",
                "saida"
            ),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela")

        
        # Cabeçalhos
        self.tabela_horarios.heading("id", text="ID")
        self.tabela_horarios.heading("nome", text="Nome")
        self.tabela_horarios.heading("tipo", text="Tipo")
        self.tabela_horarios.heading("entrada", text="Entrada")
        self.tabela_horarios.heading("inicio_pausa", text="Inicio Pausa")
        self.tabela_horarios.heading("fim_pausa", text="Fim Pausa")
        self.tabela_horarios.heading("saida", text="Saída")


        # larguras das colunas
        self.tabela_horarios.column("id", width=60,anchor="center")
        self.tabela_horarios.column("nome", width=150,anchor="center")
        self.tabela_horarios.column("tipo", width=100,anchor="center")
        self.tabela_horarios.column("entrada", width=100,anchor="center")
        self.tabela_horarios.column("inicio_pausa", width=120,anchor="center")
        self.tabela_horarios.column("fim_pausa", width=120,anchor="center")
        self.tabela_horarios.column("saida", width=100,anchor="center")


        # scroll 
        scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela_horarios.yview)
        self.tabela_horarios.configure(yscrollcommand=scroll.set)
        self.tabela_horarios.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

 
    def adicionar_feriado(self):
        janela = tk.Toplevel(self)
        janela.title("Adicionar Feriado")
        janela.transient(self)

        # data
        w.criar_label(janela, "Data:").pack(pady=(10,2), padx=20)
        entry_data = DateEntry(
            janela, date_format="%Y-%m-%d", width=14, bootstyle=cores.PRIMARY_DARK)
        entry_data.pack(padx=20)

        # descrição
        w.criar_label(janela, "Descrição:").pack(pady=(10,2), padx=20)
        entry_descricao = w.criar_entrada(janela, largura=32)
        entry_descricao.pack(padx=20)

        w.criar_botao(janela, 
                    "Guardar", 
                    lambda: self.guardar_feriados(
                        entry_data.entry.get().strip(),
                        entry_descricao.get().strip(), 
                        janela,),).pack(pady=15)


    def guardar_feriados(self, data, descricao, janela):
        if not descricao:
            messagebox.showwarning(
                "Campos em falta",
                "Introduza a descrição do feriado.",
                parent=janela
            )
            return
        try:
            data_validada = datetime.strptime(data, "%Y-%m-%d").date()

            self.cursor.execute("""
                INSERT INTO FERIADOS (data,descricao)
                VALUES (%s, %s)
            """, (data_validada, descricao))

            conn.commit()

            janela.destroy()

            messagebox.showinfo(
                "Sucesso",
                "Feriado guardado com sucesso!",
                parent=self,)

        except ValueError:
            messagebox.showerror(
                "Data Inválida",
                "Selecione uma data válida.",
                parent=janela,)
                
        except mysql.connector.Error as erro:
            conn.rollback()
            print(erro)

            messagebox.showerror(
                "Erro",
                "Não foi possível registar o feriado."
                "Verifique se já existe um registo para essa data.",
                parent=janela,)
   


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
                UPDATE funcionarios
                SET horario = %s
                WHERE id_funcionario = %s
                
                """,
                (id_funcionario,id_horario)
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
        for item in self.tabela_editar_horarios.get_children():
            self.tabela_editar_horarios.delete(item)

        funcionario_sel = self.combo_funcionario.get().strip()

        id_funcionario = self.funcionarios_map.get( funcionario_sel)

        if id_funcionario is None:
            return

        self.cursor.execute(
            """
            SELECT
                h.nome,
                h.tipo,
                h.entrada,
                h.saida
            FROM funcionario f
            JOIN horario h
                ON h.id_horario = f.horario
            WHERE f.id_funcionario = %s
            """,
            (id_funcionario,)
        )

        for data, nome, tipo, entrada, saida in self.cursor.fetchall():

            self.tabela_editar_horarios.insert(
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


    def mostrar_pagina2(self):
        self.pagina_atribuir_horarios.pack_forget()
        self.pagina_editar_horarios.pack(fill="both", expand=True)


    def mostrar_pagina1(self):
        self.pagina_editar_horarios.pack_forget()
        self.pagina_atribuir_horarios.pack(fill="both",expand= True)