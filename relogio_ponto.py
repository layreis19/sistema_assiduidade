"""
O QUE ESTE FICHEIRO FAZ?
É a página onde os funcionários picam o ponto.
- Mostra um relógio e a lista de funcionários ativos.
- O funcionário escolhe o nome, escreve a senha e clica em Fazer Picagem.
- O programa descobre sozinho se é uma ENTRADA ou uma SAÍDA: alterna em
  relação à última picagem. As pausas (almoço, etc.) são só uma SAÍDA
  seguida de uma ENTRADA; quem as interpreta é o processamento
  posterior, não esta página.
- Usa o horário atual do funcionário (coluna FUNCIONARIOS.horario) para
  avisar se está de folga e para perceber quando uma entrada ficou
  "esquecida" (sem saída) e deve ser dada como abandonada.
- Grava a picagem na tabela PICAGEM.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import bcrypt
import cores 
from ligacao import conn
from calculo_assiduidade import combinar_data_hora, _para_time
from rotulos import rotulo_tipo_picagem


# Se a última picagem foi uma ENTRADA e já passou da hora de saída
# esperada do horário + esta margem sem haver SAIDA, deixamos de a
# considerar "em aberto": foi um esquecimento de picar a saída. Assim a
# primeira picagem do dia seguinte é uma ENTRADA nova, e não a saída em
# falta de ontem. A margem existe para não penalizar quem faz umas horas
# extra sem ser um esquecimento genuíno.
MARGEM_ABANDONO_TURNO = timedelta(hours=4)

# Rede de segurança para quando o horário não dá nenhuma referência de
# hora (sem horário atribuído, FOLGA, ou entrada fora do horário normal):
# a entrada é dada como abandonada passadas estas horas.
LIMITE_SEM_REFERENCIA = timedelta(hours=16)


def calcular_limite_turno(entrada_feita_em, horario):
    """
    Devolve até que momento uma ENTRADA feita em `entrada_feita_em` ainda
    conta como turno em curso (depois disso, é um esquecimento).

    `horario` é o dicionário de obter_horario_atual (ou None).

    - FIXO/TURNO: saída esperada + tolerância + MARGEM_ABANDONO_TURNO.
      Procura-se o turno (de hoje ou de ontem) a que a entrada pertence,
      o que cobre turnos noturnos: uma entrada às 03:00 depois do almoço
      do TURNO NOITE pertence ao turno que começou na véspera.
    - LIVRE: fim da janela + MARGEM_ABANDONO_TURNO.
    - Sem horário, FOLGA, ou entrada fora de qualquer turno:
      LIMITE_SEM_REFERENCIA depois da entrada.
    """

    rede_seguranca = entrada_feita_em + LIMITE_SEM_REFERENCIA

    if horario is None:
        return rede_seguranca

    limite = None
    entrada_h, saida_h = horario["entrada"], horario["saida"]

    if entrada_h is not None and saida_h is not None:

        for dias_atras in (0, 1):
            dia = entrada_feita_em.date() - timedelta(days=dias_atras)

            inicio_janela = datetime.combine(dia, entrada_h) - MARGEM_ABANDONO_TURNO
            saida_esperada = combinar_data_hora(dia, saida_h, entrada_h)
            fim_janela = saida_esperada + timedelta(minutes=horario["tolerancia"]) + MARGEM_ABANDONO_TURNO

            if inicio_janela <= entrada_feita_em <= fim_janela:
                limite = fim_janela
                break

    elif horario["janela_fim"] is not None:
        limite = datetime.combine(entrada_feita_em.date(), horario["janela_fim"]) + MARGEM_ABANDONO_TURNO

    if limite is None or limite <= entrada_feita_em:
        return rede_seguranca

    return limite


def proximo_tipo_picagem(ultima, horario, agora):
    """
    Decide se a próxima picagem é "ENTRADA" ou "SAIDA". Função "pura" (sem
    BD nem interface), para poder ser testada isoladamente.

    `ultima` é (tipo, data) da última picagem válida do funcionário, ou
    None se nunca picou.

    - Nunca picou, ou a última foi SAIDA -> ENTRADA.
    - A última foi ENTRADA e ainda está dentro do turno -> SAIDA.
    - A última foi ENTRADA mas já passou do limite (esqueceu-se da saída)
      -> ENTRADA nova. A entrada antiga fica na BD, para o admin corrigir.
    """

    if ultima is None:
        return "ENTRADA"

    tipo_ultima, data_ultima = ultima

    if tipo_ultima == "SAIDA":
        return "ENTRADA"

    if agora <= calcular_limite_turno(data_ultima, horario):
        return "SAIDA"

    return "ENTRADA"


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
            font=("Arial", 24),
            background=cores.CARD,
            fg=cores.TEXT
        )

        titulo.pack(pady=(30,20))


        # -------------------------
        # RELÓGIO
        # -------------------------

        self.relogio = tk.Label(
            self,
            font=("Arial", 20),
            background=cores.CARD,
            fg=cores.TEXT
        )

        self.relogio.pack(pady=10)

        self.atualizar_relogio()


        # -------------------------
        # FUNCIONÁRIO
        # -------------------------

        nome_label = tk.Label(
            self,
            text="Funcionário:",
            font=("Arial", 12),
            background=cores.CARD,
            fg=cores.TEXT)

        
        nome_label.pack(padx=(10,5),pady=5)

        self.combo_funcionarios = ttk.Combobox(
            self,
            font=("Arial", 12),
            state="readonly",
            width=16
        )

        self.combo_funcionarios.pack(padx=(10,5), pady=5)
        # -------------------------
        # PASSWORD
        # -------------------------

        password_label = tk.Label(
            self,
            text="Senha:",
            font=("Arial", 12),
            background=cores.CARD,
            fg=cores.TEXT
        )

        password_label.pack(padx=(10,5))


        self.entrada_password = tk.Entry(
            self,
            font=("Arial", 12),
            show="*"
        )

        self.entrada_password.pack(pady=(0,15))


        # -------------------------
        # BOTÃO
        # -------------------------

        botao = tk.Button(
            self,
            text="Fazer Picagem",
            font=("Arial", 11),
            bg=cores.PRIMARY,
            fg=cores.CARD,
            activebackground=cores.PRIMARY_DARK,
            activeforeground=cores.CARD,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.registar_picagem,
            padx=14,
            pady=6
        )

        botao.pack(padx=10)


        
        # -------------------------
        # CARREGAR DADOS
        # -------------------------

        self.carregar_funcionarios()
        


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


    def obter_horario_atual(self, id_funcionario):
        """
        Devolve o horário que está atribuído ao funcionário neste momento
        (coluna FUNCIONARIOS.horario) como dicionário:
            {"tipo", "entrada", "saida", "tolerancia", "janela_fim"}
        ou None se não tiver nenhum horário atribuído.
        """

        self.cursor.execute(
            """
            SELECT h.tipo, h.entrada, h.saida, h.tolerancia, h.janela_fim
            FROM funcionarios f
            JOIN horario h ON h.id_horario = f.horario
            WHERE f.id_funcionario = %s
            """,
            (id_funcionario,)
        )

        linha = self.cursor.fetchone()

        if linha is None:
            return None

        tipo, entrada_h, saida_h, tolerancia, janela_fim_h = linha

        # Colunas TIME vêm da BD como timedelta — converter antes de usar
        # em datetime.combine() mais à frente.
        return {
            "tipo": tipo,
            "entrada": _para_time(entrada_h),
            "saida": _para_time(saida_h),
            "tolerancia": tolerancia or 0,
            "janela_fim": _para_time(janela_fim_h),
        }


    def obter_ultima_picagem(self, id_funcionario):
        """Devolve (tipo, data) da última picagem válida (não anulada), ou None."""

        self.cursor.execute(
            """
            SELECT tipo, data
            FROM picagem
            WHERE id_funcionario = %s
              AND anulada = 0
            ORDER BY data DESC, id_picagem DESC
            LIMIT 1
            """,
            (id_funcionario,)
        )

        return self.cursor.fetchone()


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
            # DETERMINAR O TIPO DE PICAGEM (ENTRADA ou SAIDA)
            # --------------------------------

            agora = datetime.now()

            horario = self.obter_horario_atual(funcionario_id)
            ultima = self.obter_ultima_picagem(funcionario_id)

            tipo = proximo_tipo_picagem(ultima, horario, agora)


            # --------------------------------
            # AVISAR SE ESTÁ DE FOLGA (só ao começar, não ao sair)
            # --------------------------------

            if tipo == "ENTRADA" and horario and horario["tipo"] == "FOLGA":

                continuar = messagebox.askyesno(
                    "Funcionário de folga",
                    "Este funcionário tem o horário FOLGA atribuído. Registar a entrada mesmo assim?"
                )

                if not continuar:
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