import tkinter as tk
from tkinter import ttk
from ligacao import conn
from datetime import datetime, timedelta
from tkinter import messagebox
import widgets as w 
import cores


# Criar a classe chamada PaginaPresencas
# Herda o tk.Frame(janela/área dentro da aplicação)
class PaginaPresencas(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=cores.CARD)

        # Cursor da base de dados
        self.cursor = conn.cursor(buffered=True)

        w.criar_estilo_tabela()
        
        # Titulo 
        w.criar_titulo(self,"CONTROLO DE PRESENÇAS").pack(pady=(30,20))
        
        # FRAME
        frame_kpi= tk.Frame(self)
        frame_kpi.pack(pady=10)

        # KPI total de funcionários
        self.label_total_kpi = tk.Frame(frame_kpi, width=220, height=110, relief = "solid", borderwidth=1)
        self.label_total_kpi.pack(side=tk.LEFT,padx=10)
        self.label_total_kpi.pack_propagate(False)

        # LABEL total funcionários
        w.criar_label(self.label_total_kpi, "TOTAL DE FUNCIONÁRIOS").pack(pady=(15,5))
        self.label_funcionarios = w.criar_label(self.label_total_kpi, "0", negrito=True)
        self.label_funcionarios.config(font=("Arial", 22, "bold"))
        self.label_funcionarios.pack()


        # KPI funcionários presentes
        self.label_funcionarios_presentes = tk.Frame(frame_kpi, width=220, height=110, relief="solid", borderwidth=1)
        self.label_funcionarios_presentes.pack(side=tk.LEFT, padx=10)
        self.label_funcionarios_presentes.pack_propagate(False)

       
        # LABEL Funcionários presentes
        w.criar_label(self.label_funcionarios_presentes,"PRESENTES").pack(pady=(15,5))
        self.label_presentes = w.criar_label(self.label_funcionarios_presentes, "0", negrito=True, cor="green")
        self.label_presentes.config(font=("Arial", 22, "bold"))
        self.label_presentes.pack()


        # KPI funcionários ausentes
        self.label_funcionarios_ausentes = tk.Frame(frame_kpi, width=220, height=110, relief="solid", borderwidth=1)
        self.label_funcionarios_ausentes.pack(side=tk.LEFT, padx=10)
        self.label_funcionarios_ausentes.pack_propagate(False)

        # LABEL Funcionários ausentes
        w.criar_label(self.label_funcionarios_ausentes,"AUSENTES").pack(pady=(15,5))
        self.label_ausentes = w.criar_label(self.label_funcionarios_ausentes, "0", negrito=True, cor="red")
        self.label_ausentes.config(font=("Arial", 22, "bold"))
        self.label_ausentes.pack()


        # FRAME FORMULÁRIO
        frame_formulario = tk.Frame(self, background=cores.CARD)
        frame_formulario.pack(pady=10)

        # pesquisa por id 

        self.id_pesquisa = tk.StringVar()
        w.criar_label(frame_formulario, "ID Funcionário:").pack(side=tk.LEFT, padx=5)
        self.entry_id = w.criar_entrada(frame_formulario, textvariable=self.id_pesquisa)
        self.entry_id.pack(side=tk.LEFT, padx=10, pady=10)


        self.filtro = tk.StringVar(value="Todos")
        w.criar_label(frame_formulario, "Estado").pack(side=tk.LEFT, padx=5)


        # Caixa para escolher o filtro
        # ("Em Pausa" reposto: sem esta opção, quem está em pausa não
        # aparecia em nenhum filtro específico, só em "Todos".)

        combo_filtro = ttk.Combobox(frame_formulario, font=w.FONTE_LABEL,
            values=(
                "Todos",
                "Presentes",
                "Ausentes"
                ),
                state="readonly",
                width=16)

        combo_filtro.pack(side=tk.LEFT, padx=10, pady=5)
        combo_filtro.bind(
            "<<ComboboxSelected>>", 
            lambda filtro: (self.filtro.set(combo_filtro.get()), self.id_pesquisa.set(""), self.atualizar_presenca()))

        # FRAME BOTÃO
        frame_botoes = tk.Frame(self, background=cores.CARD)
        frame_botoes.pack(pady=10)

        w.criar_botao(frame_botoes, "Pesquisar", self.atualizar_presenca).pack(side=tk.LEFT, padx=5)


        # FRAME TABELA
        frame_tabela = tk.Frame(self, background=cores.CARD)
        frame_tabela.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Tabela
        self.tabela_presencas = ttk.Treeview(
            frame_tabela,
            columns=(
                "id_funcionario",
                "nome",
                "estado"
            ),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela")

        # Cabeçalhos
        self.tabela_presencas.heading("id_funcionario",text="ID_Funcionário")
        self.tabela_presencas.heading("nome",text="Funcionário")
        self.tabela_presencas.heading("estado",text="Estado")


        # Largura das colunas
        self.tabela_presencas.column("id_funcionario",width=60,anchor="w")
        self.tabela_presencas.column("nome",width=250, anchor="w")
        self.tabela_presencas.column("estado",width=150,anchor="center")


        # Scroll 
        scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela_presencas.yview)
        self.tabela_presencas.configure(yscrollcommand=scroll.set)
        self.tabela_presencas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Cores da tabela
        self.tabela_presencas.tag_configure("presente",foreground="#008000")
        self.tabela_presencas.tag_configure("ausente",foreground="#d00000")


        # data do dia de trabalho atual 
        agora = datetime.now()

        # se for antes das 6 da manhã
        if agora.hour < 6:
            self.dia_atual = agora.date() - timedelta(days=1) # é o dia atual - 1 (ou seja, pertence ao dia de trabalho anterior)
        else:
            self.dia_atual = agora.date()

        # atualizar a tabela 
        self.atualizar_presenca()

        # automaticamente a cada 1 minuto
        self.after(60000, self.verificar_dia)


    def verificar_dia(self):

        agora = datetime.now()
        if agora.hour < 6:
            dia_trabalho = agora.date() - timedelta(days=1)
        else:
            dia_trabalho = agora.date()

        # verificar se começou um novo dia de trabalho 
        if dia_trabalho != self.dia_atual:
            self.dia_atual = dia_trabalho
            
            self.atualizar_presenca()
            
         # automaticamente a cada 1 minuto
        self.after(60000, self.verificar_dia)

    def atualizar_presenca(self):

        for linha in self.tabela_presencas.get_children():
              self.tabela_presencas.delete(linha)

        agora = datetime.now()

        if agora.hour < 6:
            dia_trabalho = agora.date() - timedelta(days=1)

        else:
            dia_trabalho = agora.date()

        inicio_turno = datetime.combine(
            dia_trabalho,
            datetime.min.time()).replace(hour=6)

        fim_turno = inicio_turno + timedelta(hours=25)

  

        # procurar na base de dados
        # (picagem.anulada = 0 no ON, não no WHERE, para continuar a ser um
        # LEFT JOIN de verdade: um funcionário cujas únicas picagens de hoje
        # estejam anuladas continua a aparecer, como AUSENTE, em vez de
        # desaparecer da lista.)

        self.cursor.execute("""
        SELECT 
            funcionarios.id_funcionario,
            funcionarios.nome,
            picagem.tipo
        
        FROM funcionarios
        
        LEFT JOIN picagem
        ON funcionarios.id_funcionario = picagem.id_funcionario 
        AND picagem.data >= %s
        AND picagem.data < %s
        AND picagem.anulada = 0
            
        ORDER BY 
        funcionarios.id_funcionario,
        picagem.data""", (inicio_turno, fim_turno))

        # Guardar os resultados
        picagens = self.cursor.fetchall()


        # Criar o dicionário 
        dicionario_funcionarios = {}

        # percorrer todas as picagens
        # (como a query está ordenada por picagem.data crescente, a última
        # picagem de cada funcionário sobrescreve as anteriores no
        # dicionário — fica sempre a mais recente do dia.)

        for picagem in picagens:
            id_funcionario = picagem[0]
            nome = picagem[1]
            tipo = picagem[2]

            if id_funcionario not in dicionario_funcionarios:
                
                dicionario_funcionarios[id_funcionario] = {
                    "nome": nome,
                    "numero_picagens": 0}

            if tipo is not None:
                dicionario_funcionarios[id_funcionario]["numero_picagens"] += 1

        # Atualizar os kpis
        self.atualizar_kpis(dicionario_funcionarios)

        # Só usamos o ID quando a função for chamada pelo botão

        id_pesquisado = self.id_pesquisa.get().strip()

        if id_pesquisado:
            # encontramos o funcionario 
            funcionario_encontrado = False

            # Procurar funcionário pelo ID
            for id_funcionario, dados in dicionario_funcionarios.items():
                if str(id_funcionario) != id_pesquisado:
                    continue

                # encontramos o funcionario 
                funcionario_encontrado = True

                # determinar o estado
                # ENTRADA (PRESENTE).
                # SAIDA (AUSENTE).

                if dados["numero_picagens"]  %2 != 0:
                    estado = "PRESENTE"
                    tag = "presente"

                else: 
                    estado = "AUSENTE"
                    tag = "ausente"


                self.tabela_presencas.insert(
                    "",
                    "end",
                    values=(
                        id_funcionario,
                        dados["nome"],
                        estado
                    ),
                    tags=(tag,)
                )
                
            # Verificar se o ID pesquisado existe
            if not funcionario_encontrado:
                messagebox.showwarning(
                    "Funcionário", 
                    "ID não existe.")

                # limpar o texto do campo ID
                self.id_pesquisa.set("")
                self.entry_id.focus()

            return

        # Se não for introduzido ID utilizar o filtro

        filtro = self.filtro.get()

        for id_funcionario, dados in dicionario_funcionarios.items():

            nome = dados["nome"]


            if dados["numero_picagens"] %2 !=0:
                estado = "PRESENTE"
                tag = "presente"
                    
            else:  # tipo == "SAIDA" ou tipo is None
                estado = "AUSENTE"
                tag = "ausente"

            # Filtro presentes

            if filtro == "Presentes" and estado != "PRESENTE":
                continue

            if filtro == "Ausentes" and estado != "AUSENTE":
                continue

            self.tabela_presencas.insert(
                "",
                "end",
                values=(
                    id_funcionario,
                    nome,
                    estado),
                    tags=(tag,)
                    )

    def atualizar_kpis(self, dicionario_funcionarios):

        # calcular o total
        total = len(dicionario_funcionarios)
        presentes = 0 
        ausentes = 0

        # percorrer os dados dos funcionários
        for dados in dicionario_funcionarios.values():
             
            numero_picagens = dados["numero_picagens"]

            if numero_picagens %2 !=0:
                presentes += 1

            else:
                ausentes += 1


        # mostrar os valores nos kpis
        self.label_funcionarios.config(text=str(total))
        self.label_presentes.config(text=str(presentes))
        self.label_ausentes.config(text=str(ausentes))