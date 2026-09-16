import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from ligacao import conn


class PaginaPonto(tk.Frame):

    def __init__(self, parent):

        super().__init__(parent)

        self.cursor = conn.cursor()

        # -------------------------
        # TÍTULO
        # -------------------------

        titulo = tk.Label(
            self,
            text="RELÓGIO DE PONTO",
            font=("Arial", 24)
        )

        titulo.pack(pady=30)


        # -------------------------
        # RELÓGIO
        # -------------------------

        self.relogio = tk.Label(
            self,
            font=("Arial", 20)
        )

        self.relogio.pack(pady=10)

        self.atualizar_relogio()


        # -------------------------
        # FUNCIONÁRIO
        # -------------------------

        nome_label = tk.Label(
            self,
            text="Funcionário:",
            font=("Arial", 14)
        )

        nome_label.pack(pady=10)


        self.combo_funcionarios = ttk.Combobox(
            self,
            font=("Arial", 14),
            state="readonly"
        )

        self.combo_funcionarios.pack(pady=5)


        # -------------------------
        # PASSWORD
        # -------------------------

        password_label = tk.Label(
            self,
            text="Senha:",
            font=("Arial", 14)
        )

        password_label.pack(pady=10)


        self.entrada_password = tk.Entry(
            self,
            font=("Arial", 14),
            show="*"
        )

        self.entrada_password.pack(pady=5)


        # -------------------------
        # BOTÃO
        # -------------------------

        botao = tk.Button(
            self,
            text="Fazer Picagem",
            font=("Arial", 14),
            command=self.registar_picagem
        )

        botao.pack(pady=20)


        # -------------------------
        # TABELA
        # -------------------------

        self.tabela = ttk.Treeview(
            self,
            columns=("nome", "data", "tipo"),
            show="headings"
        )

        self.tabela.heading("nome", text="Funcionário")
        self.tabela.heading("data", text="Data")
        self.tabela.heading("tipo", text="Tipo")

        self.tabela.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=20
        )


        # -------------------------
        # CARREGAR DADOS
        # -------------------------

        self.carregar_funcionarios()
        self.atualizar_tabela()


    # ==================================================
    # FUNÇÕES
    # ==================================================

    def atualizar_relogio(self):

        agora = datetime.now()

        hora = agora.strftime("%H:%M:%S")

        self.relogio.config(text=hora)

        self.after(1000, self.atualizar_relogio)


    def carregar_funcionarios(self):

        self.cursor.execute(
            "SELECT nome FROM funcionarios"
        )

        funcionarios = [
            row[0]
            for row in self.cursor.fetchall()
        ]

        self.combo_funcionarios["values"] = funcionarios


    def registar_picagem(self):

        nome = self.combo_funcionarios.get().strip()
        senha = self.entrada_password.get().strip()


        if not nome or not senha:

            messagebox.showwarning(
                "Campos em falta",
                "Preencha o nome e a senha."
            )

            return


        try:

            # --------------------------------
            # VERIFICAR FUNCIONÁRIO E PASSWORD
            # --------------------------------

            self.cursor.execute(
                """
                SELECT id_funcionario
                FROM funcionarios
                WHERE nome = %s
                AND senha = SHA2(%s, 256)
                """,
                (nome, senha)
            )

            funcionario = self.cursor.fetchone()


            if funcionario is None:

                messagebox.showerror(
                    "Erro",
                    "Funcionário ou senha incorretos."
                )

                return


            funcionario_id = funcionario[0]


            # --------------------------------
            # VER ÚLTIMA PICAGEM
            # --------------------------------

            self.cursor.execute(
                """
                SELECT tipo
                FROM picagem
                WHERE id_funcionario = %s
                ORDER BY data DESC
                LIMIT 1
                """,
                (funcionario_id,)
            )

            ultima_picagem = self.cursor.fetchone()


            # --------------------------------
            # DETERMINAR ENTRADA OU SAÍDA
            # --------------------------------

            if (
                ultima_picagem is None
                or ultima_picagem[0] == "SAIDA"
            ):
                tipo = "ENTRADA"

            else:
                tipo = "SAIDA"


            # --------------------------------
            # REGISTAR PICAGEM
            # --------------------------------

            self.cursor.execute(
                """
                INSERT INTO picagem
                (id_funcionario, data, tipo)
                VALUES (%s, %s, %s)
                """,
                (
                    funcionario_id,
                    datetime.now(),
                    tipo
                )
            )


            conn.commit()


            # --------------------------------
            # ATUALIZAR TABELA
            # --------------------------------

            self.atualizar_tabela()


            messagebox.showinfo(
                "Picagem registada",
                f"{tipo.capitalize()} registada com sucesso!"
            )


            # Limpar campos

            self.combo_funcionarios.set("")
            self.entrada_password.delete(0, tk.END)


        except Exception as erro:

            conn.rollback()

            messagebox.showerror(
                "Erro",
                f"Ocorreu um erro:\n{erro}"
            )


    def atualizar_tabela(self):

        # Limpar tabela

        for item in self.tabela.get_children():

            self.tabela.delete(item)


        # Buscar picagens

        self.cursor.execute(
            """
            SELECT
                funcionarios.nome,
                picagem.data,
                picagem.tipo
            FROM picagem
            JOIN funcionarios
                ON funcionarios.id_funcionario =
                   picagem.id_funcionario
            ORDER BY picagem.data DESC
            """
        )

        resultados = self.cursor.fetchall()


        # Inserir na tabela

        for linha in resultados:

            self.tabela.insert(
                "",
                tk.END,
                values=linha
            )