import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import bcrypt

from ligacao import conn


class PaginaPonto(tk.Frame):

    def __init__(self, parent):

        super().__init__(parent)

        self.cursor = conn.cursor(buffered=True)

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
            """
            SELECT id_funcionario, nome
            FROM funcionarios
            WHERE estado = 'ATIVO'
            ORDER BY nome
            """
        )

        # Mapa "Nome (#id)" -> id_funcionario.
        # Nunca identificamos o funcionário pelo nome sozinho: dois funcionários
        # podem ter o mesmo nome, e o nome não tem UNIQUE na base de dados.
        self.funcionarios_map = {
            f"{nome} (#{id_})": id_
            for id_, nome in self.cursor.fetchall()
        }

        self.combo_funcionarios["values"] = list(self.funcionarios_map.keys())


    def obter_horario_do_dia(self, id_funcionario, data_hoje):
        """
        Devolve (tipo_horario, inicio_almoco, fim_almoco) para o horário
        atribuído a este funcionário nesta data, ou None se não houver
        nenhum horário atribuído para hoje.
        """

        self.cursor.execute(
            """
            SELECT h.tipo, h.inicio_almoco, h.fim_almoco
            FROM funcionario_horario fh
            JOIN horario h ON h.id_horario = fh.id_horario
            WHERE fh.id_funcionario = %s
              AND fh.data = %s
            """,
            (id_funcionario, data_hoje)
        )

        return self.cursor.fetchone()


    def determinar_tipo_picagem(self, id_funcionario, data_hoje):
        """
        Decide qual o próximo tipo de picagem para este funcionário hoje,
        com base na última picagem válida do dia e em o horário atribuído
        ter (ou não) pausa de almoço configurada.

        Devolve None se o ciclo do dia já estiver completo (já houve a
        SAIDA final) — nesse caso, não deve ser registada mais nenhuma
        picagem automática; só o admin pode corrigir/adicionar.

        Sem almoço configurado (ou sem horário atribuído): ENTRADA -> SAIDA.
        Com almoço configurado: ENTRADA -> SAIDA_ALMOCO -> VOLTA_ALMOCO -> SAIDA.
        """

        horario_hoje = self.obter_horario_do_dia(id_funcionario, data_hoje)
        tem_almoco = bool(
            horario_hoje and horario_hoje[1] is not None and horario_hoje[2] is not None
        )

        self.cursor.execute(
            """
            SELECT tipo
            FROM picagem
            WHERE id_funcionario = %s
              AND DATE(data) = %s
              AND anulada = 0
            ORDER BY data DESC
            LIMIT 1
            """,
            (id_funcionario, data_hoje)
        )

        ultima_picagem = self.cursor.fetchone()

        if ultima_picagem is None:
            return "ENTRADA"

        tipo_anterior = ultima_picagem[0]

        if not tem_almoco:
            # Sem pausa: só um par ENTRADA -> SAIDA por dia.
            if tipo_anterior == "ENTRADA":
                return "SAIDA"
            return None  # já saiu hoje, ciclo completo

        sequencia = {
            "ENTRADA": "SAIDA_ALMOCO",
            "SAIDA_ALMOCO": "VOLTA_ALMOCO",
            "VOLTA_ALMOCO": "SAIDA",
            "SAIDA": None,  # já completou o dia todo, ciclo completo
        }

        return sequencia[tipo_anterior]


    def registar_picagem(self):

        selecao = self.combo_funcionarios.get().strip()
        senha = self.entrada_password.get().strip()

        if not selecao or not senha:

            messagebox.showwarning(
                "Campos em falta",
                "Selecione o funcionário e preencha a senha."
            )

            return

        funcionario_id = self.funcionarios_map.get(selecao)

        if funcionario_id is None:

            messagebox.showerror(
                "Erro",
                "Selecione um funcionário válido na lista."
            )

            return

        try:

            # --------------------------------
            # VERIFICAR FUNCIONÁRIO E PASSWORD
            # --------------------------------

            self.cursor.execute(
                """
                SELECT senha, estado
                FROM funcionarios
                WHERE id_funcionario = %s
                """,
                (funcionario_id,)
            )

            funcionario = self.cursor.fetchone()

            if funcionario is None:

                messagebox.showerror(
                    "Erro",
                    "Funcionário não encontrado."
                )

                return

            senha_hash, estado = funcionario

            if estado != "ATIVO":

                messagebox.showerror(
                    "Erro",
                    "Funcionário inativo."
                )

                return

            if not bcrypt.checkpw(
                senha.encode("utf-8"),
                senha_hash.encode("utf-8")
            ):

                messagebox.showerror(
                    "Erro",
                    "Funcionário ou senha incorretos."
                )

                return


            # --------------------------------
            # AVISAR SE ESTIVER DE FOLGA HOJE
            # --------------------------------

            agora = datetime.now()
            data_hoje = agora.date()

            horario_hoje = self.obter_horario_do_dia(funcionario_id, data_hoje)

            if horario_hoje and horario_hoje[0] == "FOLGA":

                continuar = messagebox.askyesno(
                    "Funcionário de folga",
                    "Este funcionário está de folga hoje. Registar a picagem mesmo assim?"
                )

                if not continuar:
                    return


            # --------------------------------
            # DETERMINAR O TIPO DE PICAGEM
            # --------------------------------

            tipo = self.determinar_tipo_picagem(funcionario_id, data_hoje)

            if tipo is None:

                messagebox.showerror(
                    "Ciclo do dia concluído",
                    "Este funcionário já completou o horário de hoje.\n"
                    "Qualquer correção deve ser feita pelo administrador."
                )

                return


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
                    agora,
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
                f"{tipo.replace('_', ' ').capitalize()} registada com sucesso!"
            )


            # Limpar campos

            self.combo_funcionarios.set("")
            self.entrada_password.delete(0, tk.END)


        except Exception as erro:

            conn.rollback()
            print(erro)  # visibilidade no terminal durante o desenvolvimento

            messagebox.showerror(
                "Erro",
                "Ocorreu um erro ao registar a picagem. Tente novamente!"
            )


    def atualizar_tabela(self):

        # Limpar tabela

        for item in self.tabela.get_children():

            self.tabela.delete(item)


        # Buscar picagens (só as válidas, não anuladas)

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
            WHERE picagem.anulada = 0
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