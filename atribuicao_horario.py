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
import cores


class PaginaAtribuicaoHorarios(tk.Frame):

    def __init__(self, parent):

        super().__init__(parent, bg=cores.CARD)

        # buffered = true (guarda os resultados da consulta no cursor)
        self.cursor = conn.cursor(buffered=True)


        # Página atribuir horários/editar
        self.pagina_atribuir_horarios = tk.Frame(self, background=cores.CARD)
        self.pagina_editar_horarios = tk.Frame(self,background=cores.CARD)

        self.construir_atribuicao_horarios()
        
        self.criar_pagina2()


        # mostrar por defeito a primeira página 
        self.mostrar_pagina1()

        self.carregar_funcionarios()
        self.carregar_horarios()

    def construir_atribuicao_horarios(self):

        # Título da página atribuir horários
        titulo = tk.Label(
            self.pagina_atribuir_horarios,
            text="ATRIBUIR HORÁRIOS",
            font=("Arial", 24),
            background=cores.CARD, 
            fg=cores.TEXT
        )
        titulo.pack(pady=(30,20))

        # Formulário 
        frame_formulario = tk.Frame(self.pagina_atribuir_horarios,background=cores.CARD)
        
        frame_formulario.pack(pady=10)

        # Funcionário
        tk.Label(
            frame_formulario,
            text="Funcionário:",
            font=("Arial", 12),
            background=cores.CARD,
            fg=cores.TEXT
        ).grid(row=0, column=0, padx=(10,5), pady=5, sticky="e")

        self.combo_funcionario = ttk.Combobox(
            frame_formulario,
            font=("Arial", 12),
            state="readonly",
            width=16
        )
        self.combo_funcionario.grid(
            row=0, 
            column=1, 
            padx=(0,20), 
            pady=5)


        self.combo_funcionario.bind(
            "<<ComboboxSelected>>",
            lambda e: self.atualizar_lista_atribuicoes()
        )

        # Data
        tk.Label(
            frame_formulario,
            text="Data:",
            font=("Arial", 12),
            background=cores.CARD,
            fg=cores.TEXT
        ).grid(
            row=0, 
            column=2, 
            padx=(10,5), 
            pady=5, 
            sticky="e")

        self.entry_data = DateEntry(
            frame_formulario,
            dateformat="%Y-%m-%d",
            width=12,
            bootstyle=cores.PRIMARY_DARK
        )
        self.entry_data.grid(
            row=0, 
            column=3, 
            padx=(0,20), 
            pady=5)

        # Horário
        tk.Label(
            frame_formulario,
            text="Horário:",
            font=("Arial", 12),
            background=cores.CARD,
            fg=cores.TEXT
        ).grid(
            row=0, 
            column=4, 
            padx=(10,5), 
            pady=5, 
            sticky="e")

        self.combo_horario = ttk.Combobox(
            frame_formulario,
            font=("Arial", 12),
            state="readonly",
            width=16
        )
        self.combo_horario.grid(
            row=0, 
            column=5, 
            padx=(0,10), 
            pady=5)


        frame_botoes = tk.Frame(self.pagina_atribuir_horarios, background=cores.CARD)
        frame_botoes.pack(pady=10)

        # Botão atribuir
        botao_atribuir = tk.Button(
            frame_botoes,
            text="Atribuir Horário",
            font=("Arial", 11),
            bg=cores.PRIMARY,
            fg=cores.CARD,
            activebackground=cores.PRIMARY_DARK,
            activeforeground=cores.CARD,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.atribuir_horario,
            padx=14,
            pady=6
        )

        botao_atribuir.pack(side=tk.LEFT,padx=10)



        frame_tabela = tk.Frame(
            self.pagina_atribuir_horarios,
            background=cores.CARD
        )

        frame_tabela.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=20
        )

        # botão para ir para a página de edição de horários 
        botao_seguinte = tk.Button(
            frame_botoes,
            text="Editar Horários",
            font=("Arial", 11),
            bg=cores.PRIMARY,
            fg=cores.CARD,
            activebackground=cores.PRIMARY_DARK,
            activeforeground=cores.CARD,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=6,
            command= self.mostrar_pagina2
        )

        botao_seguinte.pack(
            side="left",
            padx=5)

        frame_tabela_conteudo = tk.Frame(
            frame_tabela,
            background=cores.CARD
        )

        frame_tabela_conteudo.pack(
            fill="both",
            expand=True
        )

        # -----------------------
        # TABELA DE ATRIBUIÇÕES
        # -------------------------

        self.tabela = ttk.Treeview(
            frame_tabela_conteudo,
            columns=("data", 
                     "horario", 
                     "tipo", 
                     "entrada", 
                     "saida"),
            show="headings",
            selectmode="browse",
            style="Pic.Treeview"
        )

        self.tabela.heading("data", text="Data")
        self.tabela.heading("horario", text="Horário")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("entrada", text="Entrada")
        self.tabela.heading("saida", text="Saída")

        # largura das colunas

        self.tabela.column(
            "data",
            width=120,
            anchor="center"
        )

        self.tabela.column(
            "horario",
            width=180,
            anchor="center"
        )

        self.tabela.column(
            "tipo",
            width=120,
            anchor="center"
        )

        self.tabela.column(
            "entrada",
            width=100,
            anchor="center"
        )

        self.tabela.column(
            "saida",
            width=100,
            anchor="center"
        )

        scroll = ttk.Scrollbar(
            frame_tabela_conteudo,
            orient="vertical",
            command=self.tabela.yview
        )

        self.tabela.configure(
            yscrollcommand=scroll.set
        )

        self.tabela.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll.pack(
            side="right",
            fill="y"
        )

    def criar_pagina2(self):

        # Título 
        titulo2 = tk.Label(
            self.pagina_editar_horarios,
            text="EDITAR HORÁRIOS",
            font=("Arial", 24),
            background=cores.CARD,
            fg=cores.TEXT
        )

        titulo2.pack(pady=(30,20))

        # frame label 
        frame_label = tk.Frame(
            self.pagina_editar_horarios,
            background=cores.CARD
        )
        frame_label.pack(pady=10)

        # nome 
        nome_label = tk.Label(
            frame_label, 
            text="Nome:", 
            font=("Arial", 12))
        
        nome_label.pack(side=tk.LEFT,pady=5)
         
        self.entry_nome = tk.Entry(frame_label)
        self.entry_nome.pack(side=tk.LEFT, padx=10, pady=10)

        # Hora

        hora_label = tk.Label(
            frame_label,
            text="Entrada:",
            font=("Arial", 12)
        )

        hora_label.pack(side=tk.LEFT, padx=10, pady=10)

        self.entry_entrada = tk.Entry(frame_label)
                
        self.entry_entrada.pack(side=tk.LEFT, padx=10, pady=10)

        # Inicio da pausa 
        inicio_pausa_label = tk.Label(
            frame_label,
            text="Inicio Pausa:",
            font=("Arial", 12)
        )

        inicio_pausa_label.pack(side=tk.LEFT,padx=10, pady=10)

        self.entry_pausa = tk.Entry(frame_label)
        self.entry_pausa.pack(side=tk.LEFT, padx=10, pady=10)

        # Fim da pausa 
        fim_pausa_label = tk.Label(
            frame_label,
            text="Fim Pausa:",
            font=("Arial", 12)
        )
        fim_pausa_label.pack(side=tk.LEFT,padx=10, pady=10)

        self.entry_fim_pausa = tk.Entry(frame_label)
        self.entry_fim_pausa.pack(side=tk.LEFT, padx=10, pady=10)

        # Saída
        saida_label = tk.Label(
            frame_label,
            text="Saída:",
            font=("Arial", 12)
        )

        saida_label.pack(side=tk.LEFT, padx=10, pady=10)
        self.entry_saida = tk.Entry(frame_label)
        self.entry_saida.pack(side=tk.LEFT, padx=10, pady=10)
        
        
        # frame botões
        frame_botoes = tk.Frame(
            self.pagina_editar_horarios,
            background=cores.CARD
        )

        frame_botoes.pack(pady=10)

        # Botão criar 
        botao_criar = tk.Button(
                    frame_botoes,
                    text="Criar",
                    font=("Arial",11),
                    bg=cores.PRIMARY,
                    fg=cores.CARD,
                    activebackground=cores.PRIMARY_DARK,
                    activeforeground=cores.CARD,
                    relief="flat",
                    bd=0,
                    cursor="hand2",
                    padx=14,
                    pady=6
                )
        
        botao_criar.pack(
            side="left",
            padx=5
        )
            
        # Botão editar

        botao_editar = tk.Button(
            frame_botoes,
            text="Editar",
            font=("Arial", 11),
            bg=cores.PRIMARY,
            fg=cores.CARD,
            activebackground=cores.PRIMARY_DARK,
            activeforeground=cores.CARD,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=6)

        botao_editar.pack(
            side="left",
            padx=5
        )


        # Botão eliminar 

        botao_eliminar = tk.Button(
            frame_botoes,
            text="Eliminar",
            font=("Arial", 11),
            bg=cores.PRIMARY,
            fg=cores.CARD,
            activebackground=cores.PRIMARY_DARK,
            activeforeground=cores.CARD,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=6,
        )


        botao_eliminar.pack(
            side="left",
            padx=5
        )


        # Botão voltar
        botao_voltar = tk.Button(
            self.pagina_editar_horarios,
            text="Voltar",
            font=("Arial", 11),
            bg=cores.PRIMARY,
            fg=cores.CARD,
            activebackground=cores.PRIMARY_DARK,
            activeforeground=cores.CARD,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.mostrar_pagina1
        )

        botao_voltar.pack(
            side="bottom",
            anchor="w",
            padx=30,
            pady=15
        )

        # tabela

        frame_tabela = tk.Frame(
            self.pagina_editar_horarios,
            background=cores.CARD
        )

        frame_tabela.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=20
        )

        frame_tabela_conteudo = tk.Frame(
            frame_tabela,
            background=cores.CARD
        )

        frame_tabela_conteudo.pack(
            fill="both",
            expand=True)

        self.tabela_horarios = ttk.Treeview(
            frame_tabela_conteudo,
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
            style="Pic.Treeview"
        )

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
        scroll = ttk.Scrollbar(
            frame_tabela_conteudo,
            orient="vertical",
            command=self.tabela_horarios.yview
        )

        self.tabela_horarios.configure(yscrollcommand=scroll.set)
        
        self.tabela_horarios.pack(side="left",fill="both", expand=True)
        scroll.pack(side="right",
                    fill="y")


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


    def mostrar_pagina2(self):
        self.pagina_atribuir_horarios.pack_forget()
        self.pagina_editar_horarios.pack(fill="both", expand=True)


    def mostrar_pagina1(self):
        self.pagina_editar_horarios.pack_forget()
        self.pagina_atribuir_horarios.pack(fill="both",expand= True)