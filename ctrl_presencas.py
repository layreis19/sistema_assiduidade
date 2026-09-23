import tkinter as tk
from tkinter import ttk
from ligacao import conn

# Criar a classe chamada PaginaPresencas
# Herda o tk.Frame(janela/área dentro da aplicação)
class PaginaPresencas(tk.Frame):

    # Atualizar as presenças e o self significa que estou a trabalhar com a própria PáginaPresencas
    def atualizar_presenca(self):

        # Vou buscar todas as linhas que existem na tabela
        for linha in self.tabela.get_children():
            # Apago os dados que já estão na tabela 
            self.tabela.delete(linha)

        # A condição "picagem.anulada = 0" está no ON, não no WHERE, para
        # continuar a ser um LEFT JOIN de verdade: um funcionário cujas
        # únicas picagens estejam anuladas deve continuar a aparecer como
        # AUSENTE (tipo = NULL), em vez de desaparecer da lista por completo.
        self.cursor.execute("""
        SELECT funcionarios.id_funcionario,
               funcionarios.nome,
               picagem.tipo
        FROM funcionarios
        LEFT JOIN picagem
            ON funcionarios.id_funcionario = picagem.id_funcionario
           AND picagem.anulada = 0
        ORDER BY funcionarios.id_funcionario, picagem.data
    """)

        picagens = self.cursor.fetchall()


        # Para cada funcionário vai-se guardar 
        # o nome e a última picagem encontrada
        dicionario_funcionarios = {}

        for picagem in picagens:

            id_funcionario = picagem[0]
            nome = picagem[1]
            tipo = picagem[2]

            dicionario_funcionarios[id_funcionario] = {
                "nome": nome,
                "tipo": tipo
            }

        # Definir as cores
        self.tabela.tag_configure("presente", foreground="green")
        self.tabela.tag_configure("ausente", foreground="red")
        self.tabela.tag_configure("pausa", foreground="orange")

        # Percorrer os funcionários e obter o nome e o tipo
        for id_funcionario, dados in dicionario_funcionarios.items():

            nome = dados["nome"]
            tipo = dados["tipo"]

            # ENTRADA e VOLTA_ALMOCO significam que a pessoa está a trabalhar
            # neste momento; SAIDA_ALMOCO é um estado próprio (em pausa), não
            # ausência nem presença; SAIDA e "sem picagem nenhuma" (None)
            # contam como ausente.
            if tipo in ("ENTRADA", "VOLTA_ALMOCO"):
                estado = "PRESENTE"
                tag = "presente"

            elif tipo == "SAIDA_ALMOCO":
                estado = "EM PAUSA"
                tag = "pausa"

            else:  # tipo == "SAIDA" ou tipo is None
                estado = "AUSENTE"
                tag = "ausente"


            # filtrar por estado

            if self.filtro.get() == "Presentes" and estado != "PRESENTE":
                continue

            if self.filtro.get() == "Ausentes" and estado != "AUSENTE":
                continue

            if self.filtro.get() == "Em Pausa" and estado != "EM PAUSA":
                continue

            self.tabela.insert(
                "",
                "end",
                values=(id_funcionario, nome, estado),
                tags=(tag,)
            )

    def __init__(self, parent):
        super().__init__(parent)

        titulo = tk.Label(
            self,
            text="CONTROLO DE PRESENÇAS",
            font=("Arial", 24)
        )

        titulo.pack(pady=50)

        # Onde vão ficar os filtros
        self.frame_filtros = tk.Frame(self)
        self.frame_filtros.pack(padx=10)
        
        # Variável que guarda o filtro escolhido 
        self.filtro = tk.StringVar(value="Todos")


        # Texto: Estado
        tk.Label(self.frame_filtros,
                 text="Estado:"
        ).pack(side="left",padx=5)


        # Caixa para escolher o filtro 
        combo_filtro = ttk.Combobox(
            self.frame_filtros,
            textvariable=self.filtro,
            values=("Todos", "Presentes", "Ausentes", "Em Pausa"),
            state="readonly",
            width=12
        )
        combo_filtro.pack(side="left",padx=5)

        # Quando escolher uma opção,
        # Atualizar a tabela 
        combo_filtro.bind(
            "<<ComboboxSelected>>",
            lambda atualizar : self.atualizar_presenca()
        )

        # Criar a tabela
        self.tabela = ttk.Treeview(
            self, 
            columns=("id_funcionario", "nome", "estado"),
            show="headings")

        self.tabela.heading("id_funcionario", text="ID_Funcionário")
        self.tabela.heading("nome", text="Funcionário")
        self.tabela.heading("estado", text="Estado")

        self.tabela.pack(pady=10)
           

        # Cursos da base de dados 
        self.cursor = conn.cursor(buffered=True)


        # Atualizar a tabela 
        self.atualizar_presenca()