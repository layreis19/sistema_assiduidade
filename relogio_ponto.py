"""
O QUE ESTE FICHEIRO FAZ?
É a página onde os funcionários picam o ponto.
- Mostra um relógio e a lista de funcionários ativos.
- O funcionário escolhe o nome, escreve a senha e clica em Fazer Picagem.
- O programa descobre sozinho o tipo de picagem: Entrada, Saída Almoço,
  Volta Almoço ou Saída (depende do horário e da última picagem).
- Avisa se o funcionário está de folga e impede picagens a mais no mesmo dia.
- Grava a picagem na tabela PICAGEM e recalcula os resultados do dia
  (atrasos, horas extra, total trabalhado).
- Mostra numa tabela todas as picagens registadas.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import bcrypt
import cores
from ligacao import conn
from calculo_assiduidade import combinar_data_hora, calcular_e_guardar_dia, _para_time
from rotulos import rotulo_tipo_picagem


# Depois de passar da hora de saída esperada de um turno + esta margem,
# se ainda não houver SAIDA registada, deixamos de considerar esse turno
# "em aberto" — passa a ser tratado como abandonado (esquecimento de
# picar a saída). Isto evita que a entrada do dia seguinte seja mal
# interpretada como se fosse a saída em falta de ontem. A margem existe
# para não penalizar quem faz umas horas extra a mais sem ser um
# esquecimento genuíno.
MARGEM_ABANDONO_TURNO = timedelta(hours=4)


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


    def obter_horario_do_dia(self, id_funcionario, data):
        """
        Devolve (tipo, entrada, saida, inicio_almoco, fim_almoco, tolerancia,
        janela_fim) para o horário atribuído a este funcionário nesta data,
        ou None se não houver nenhum horário atribuído para essa data.
        janela_fim só é relevante para tipo == 'LIVRE' (onde entrada/saida
        são NULL); serve de referência alternativa para saber quando um
        turno livre deixa de estar "em aberto".
        """

        self.cursor.execute(
            """
            SELECT h.tipo, h.entrada, h.saida, h.inicio_almoco, h.fim_almoco,
                   h.tolerancia, h.janela_fim
            FROM funcionario_horario fh
            JOIN horario h ON h.id_horario = fh.id_horario
            WHERE fh.id_funcionario = %s
              AND fh.data = %s
            """,
            (id_funcionario, data)
        )

        horario = self.cursor.fetchone()

        if horario is None:
            return None

        # Colunas TIME vêm da BD como timedelta — converter antes de usar
        # em combinar_data_hora()/datetime.combine() mais à frente.
        tipo, entrada_h, saida_h, inicio_almoco_h, fim_almoco_h, tolerancia, janela_fim_h = horario

        return (
            tipo,
            _para_time(entrada_h),
            _para_time(saida_h),
            _para_time(inicio_almoco_h),
            _para_time(fim_almoco_h),
            tolerancia,
            _para_time(janela_fim_h),
        )


    def _turno_ainda_em_curso(self, data_turno, horario_turno, agora):
        """
        Decide se um turno candidato a "em aberto" ainda é plausível, ou
        se já passou tanto tempo da hora de saída esperada que deve ser
        tratado como abandonado (esquecimento de picar a saída).

        - Se o horário tem 'saida' definida (FIXO/TURNO): o limite é a
          saída esperada (já corrigida para turnos noturnos) + tolerância
          + MARGEM_ABANDONO_TURNO.
        - Se for LIVRE (sem 'saida', só janela): o limite é o fim da
          janela desse dia + MARGEM_ABANDONO_TURNO.
        - Sem horário atribuído nesse dia, ou sem nenhuma referência de
          hora: usa um limite fixo generoso (16h desde a entrada) só como
          rede de segurança, para nunca ficar "aberto" indefinidamente.
        """

        if horario_turno is None:
            return False  # sem horário atribuído: não faz sentido manter aberto

        tipo, entrada_h, saida_h, _inicio_almoco_h, _fim_almoco_h, tolerancia, janela_fim_h = horario_turno

        if entrada_h is None:
            return False

        if saida_h is not None:
            saida_esperada = combinar_data_hora(data_turno, saida_h, entrada_h)
            limite = saida_esperada + timedelta(minutes=tolerancia or 0) + MARGEM_ABANDONO_TURNO

        elif janela_fim_h is not None:
            limite = datetime.combine(data_turno, janela_fim_h) + MARGEM_ABANDONO_TURNO

        else:
            limite = datetime.combine(data_turno, entrada_h) + timedelta(hours=16)

        return agora <= limite


    def obter_turno_ativo(self, id_funcionario):
        """
        Descobre se há um turno "em aberto" para este funcionário — ou
        seja, já houve ENTRADA mas ainda não a SAIDA final, e ainda não
        passou tempo de mais desde a hora de saída esperada (ver
        _turno_ainda_em_curso — isto é o que distingue "ainda a decorrer"
        de "esquecimento de picar a saída, já há muito tempo").

        Sem esta segunda verificação, um funcionário que se esquecesse de
        picar a SAIDA no fim do dia veria a sua entrada do dia SEGUINTE
        interpretada como se fosse a saída em falta de ontem — em vez de
        começar um turno novo hoje.

        Devolve (data_turno, horario_turno, ultima_picagem_tipo):
        - data_turno: a data em FUNCIONARIO_HORARIO a que este turno
          pertence (hoje, se não houver nenhum turno em aberto).
        - horario_turno: o resultado de obter_horario_do_dia para essa data.
        - ultima_picagem_tipo: o tipo da última picagem deste turno, ou
          None se ainda não houve nenhuma (primeira picagem do turno).
        """

        agora = datetime.now()

        # Janela ampla só para ter candidatos a analisar — a decisão real
        # de "ainda em curso vs. abandonado" acontece a seguir, com base
        # no horário específico de cada turno, não nesta constante.
        rede_seguranca = agora - timedelta(hours=48)

        self.cursor.execute(
            """
            SELECT tipo, data
            FROM picagem
            WHERE id_funcionario = %s
              AND anulada = 0
              AND data >= %s
            ORDER BY data DESC
            LIMIT 1
            """,
            (id_funcionario, rede_seguranca)
        )

        ultima = self.cursor.fetchone()

        turno_em_aberto = False

        if ultima is not None and ultima[0] != "SAIDA":

            # Candidato a turno em aberto: descobrir a que dia pertence
            # (a data da ENTRADA mais recente dentro da rede de segurança).
            self.cursor.execute(
                """
                SELECT DATE(data)
                FROM picagem
                WHERE id_funcionario = %s
                  AND anulada = 0
                  AND tipo = 'ENTRADA'
                  AND data >= %s
                ORDER BY data DESC
                LIMIT 1
                """,
                (id_funcionario, rede_seguranca)
            )

            row = self.cursor.fetchone()

            if row is not None:
                data_candidata = row[0]
                horario_candidato = self.obter_horario_do_dia(id_funcionario, data_candidata)

                if self._turno_ainda_em_curso(data_candidata, horario_candidato, agora):
                    turno_em_aberto = True
                    data_turno = data_candidata
                    horario_turno = horario_candidato
                    ultima_tipo = ultima[0]

        if not turno_em_aberto:
            # Sem turno em aberto (ou o candidato já foi dado como
            # abandonado): a próxima picagem começa um turno novo, hoje.
            # O turno antigo incompleto (se existir) fica na BD tal como
            # está, para o admin corrigir depois.
            data_turno = agora.date()
            horario_turno = self.obter_horario_do_dia(id_funcionario, data_turno)
            ultima_tipo = None

        return data_turno, horario_turno, ultima_tipo


    def proximo_tipo_picagem(self, horario_turno, ultima_tipo):
        """
        Decide qual o próximo tipo de picagem, com base na última picagem
        do turno em curso e em o horário ter (ou não) pausa de almoço
        configurada. Função "pura" (sem consultas à BD), para poder ser
        testada isoladamente e reaproveitada facilmente.

        Devolve None se o ciclo do turno já estiver completo (já houve a
        SAIDA final) — nesse caso, não deve ser registada mais nenhuma
        picagem automática; só o admin pode corrigir/adicionar.

        Sem almoço configurado (ou sem horário atribuído): ENTRADA -> SAIDA.
        Com almoço configurado: ENTRADA -> SAIDA_ALMOCO -> VOLTA_ALMOCO -> SAIDA.
        """

        tem_almoco = bool(
            horario_turno and horario_turno[3] is not None and horario_turno[4] is not None
        )

        if ultima_tipo is None:
            return "ENTRADA"

        if not tem_almoco:
            if ultima_tipo == "ENTRADA":
                return "SAIDA"
            return None  # já saiu, ciclo completo

        sequencia = {
            "ENTRADA": "SAIDA_ALMOCO",
            "SAIDA_ALMOCO": "VOLTA_ALMOCO",
            "VOLTA_ALMOCO": "SAIDA",
            "SAIDA": None,  # já completou o turno todo, ciclo completo
        }

        return sequencia[ultima_tipo]


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
            # DESCOBRIR O TURNO EM CURSO (avisar se for folga)
            # --------------------------------

            agora = datetime.now()

            data_turno, horario_turno, ultima_tipo = self.obter_turno_ativo(funcionario_id)

            if horario_turno and horario_turno[0] == "FOLGA":

                continuar = messagebox.askyesno(
                    "Funcionário de folga",
                    "Este funcionário está de folga hoje. Registar a picagem mesmo assim?"
                )

                if not continuar:
                    return


            # --------------------------------
            # DETERMINAR O TIPO DE PICAGEM
            # --------------------------------

            tipo = self.proximo_tipo_picagem(horario_turno, ultima_tipo)

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
            # ATUALIZAR RESULTADOS (atraso/horas extra/horas trabalhadas)
            # --------------------------------
            # Isolado num try/except próprio: um erro aqui não deve impedir
            # a confirmação da picagem, que já está gravada com sucesso.
            # Recalcula sempre o turno todo (não só a picagem de agora),
            # porque só no fim do turno é que "horas_trabalhadas" e
            # "horas_extra_min" ficam completos — chamar isto a cada
            # picagem mantém RESULTADOS sempre atualizado com o que já é
            # possível saber até ao momento.

            try:
                calcular_e_guardar_dia(self.cursor, conn, funcionario_id, data_turno)
            except Exception as erro_resultados:
                print(erro_resultados)


            # --------------------------------
            # ATUALIZAR TABELA
            # --------------------------------

            self.atualizar_tabela()


            messagebox.showinfo(
                "Picagem registada",
                f"{rotulo_tipo_picagem(tipo)} registada com sucesso!"
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


        # Inserir na tabela (com o nome bonito do tipo, não o valor em
        # bruto da BD)

        for nome, data_picagem, tipo in resultados:

            self.tabela.insert(
                "",
                tk.END,
                values=(nome, data_picagem, rotulo_tipo_picagem(tipo))
            )