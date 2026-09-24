# Pra que serve esse ficheiro?
# Este módulo calcula, para um funcionário e um dia (o dia a que um turno foi
# ATRIBUÍDO em FUNCIONARIO_HORARIO — não necessariamente a data civil das
# picagens, por causa de turnos noturnos que atravessam a meia-noite),
# se houve falta, atraso na entrada, atraso a voltar do almoço, e quantas
# horas foram efetivamente trabalhadas.
#
# Não depende de tkinter nem de nenhuma página em concreto: recebe um cursor
# já aberto (buffered=True) e devolve um dicionário simples. Isto permite
# que tanto relatorios.py como ctrl_presencas.py (e testes soltos) usem a
# mesma lógica, sem duplicar queries nem regras de negócio.

from datetime import datetime, timedelta


def combinar_data_hora(data_base, hora, hora_entrada):
    """
    Combina uma data com uma hora, assumindo que essa hora cai no dia
    SEGUINTE a data_base se for numericamente menor que hora_entrada.

    Isto cobre turnos que atravessam a meia-noite (ex: entrada às 22:00,
    fim_almoco às 03:00): 03:00 < 22:00, logo assume-se dia seguinte.
    Para horários normais (onde saida/inicio_almoco/fim_almoco são sempre
    >= entrada), esta condição nunca dispara, por isso não há efeito
    nenhum nesses casos.
    """

    dt = datetime.combine(data_base, hora)

    if hora < hora_entrada:
        dt += timedelta(days=1)

    return dt


def calcular_dia(cursor, id_funcionario, data_turno):
    """
    Calcula o resumo de assiduidade de um funcionário para o turno que lhe
    foi atribuído em `data_turno` (FUNCIONARIO_HORARIO.data).

    Devolve um dicionário:
    {
        "tipo_horario": "FIXO" / "TURNO" / "LIVRE" / "FOLGA" / None,
        "motivo_sem_avaliacao": None / "SEM_HORARIO" / "FOLGA" / "AUSENCIA" / "FERIADO",
        "falta": bool ou None (None = não avaliável, ver motivo_sem_avaliacao),
        "atraso_entrada_min": int ou None (None = sem picagem de entrada, ou não aplicável),
        "atraso_volta_almoco_min": int ou None,
        "horas_trabalhadas": float ou None (horas, arredondado a 2 casas),
        "picagens": {"entrada": datetime ou None, "saida_almoco": ..., "volta_almoco": ..., "saida": ...},
    }
    """

    resultado = {
        "tipo_horario": None,
        "motivo_sem_avaliacao": None,
        "falta": None,
        "atraso_entrada_min": None,
        "atraso_volta_almoco_min": None,
        "horas_trabalhadas": None,
        "picagens": {"entrada": None, "saida_almoco": None, "volta_almoco": None, "saida": None},
    }

    # --------------------------------
    # 1. HORÁRIO ATRIBUÍDO NESSE DIA
    # --------------------------------

    cursor.execute(
        """
        SELECT h.tipo, h.entrada, h.saida, h.inicio_almoco, h.fim_almoco, h.tolerancia
        FROM funcionario_horario fh
        JOIN horario h ON h.id_horario = fh.id_horario
        WHERE fh.id_funcionario = %s
          AND fh.data = %s
        """,
        (id_funcionario, data_turno)
    )

    horario = cursor.fetchone()

    if horario is None:
        resultado["motivo_sem_avaliacao"] = "SEM_HORARIO"
        return resultado

    tipo_horario, entrada_h, saida_h, inicio_almoco_h, fim_almoco_h, tolerancia = horario
    resultado["tipo_horario"] = tipo_horario

    if tipo_horario == "FOLGA":
        resultado["motivo_sem_avaliacao"] = "FOLGA"
        resultado["falta"] = False
        return resultado

    # --------------------------------
    # 2. AUSÊNCIA JUSTIFICADA OU FERIADO
    # --------------------------------

    cursor.execute(
        """
        SELECT 1 FROM ausencias
        WHERE id_funcionario = %s
          AND %s BETWEEN data_inicio AND data_fim
        LIMIT 1
        """,
        (id_funcionario, data_turno)
    )

    if cursor.fetchone():
        resultado["motivo_sem_avaliacao"] = "AUSENCIA"
        resultado["falta"] = False
        return resultado

    cursor.execute("SELECT 1 FROM feriados WHERE data = %s", (data_turno,))

    if cursor.fetchone():
        resultado["motivo_sem_avaliacao"] = "FERIADO"
        resultado["falta"] = False
        return resultado

    # --------------------------------
    # 3. TIPO LIVRE — sem hora de entrada fixa, não há "atraso" a medir
    #    aqui (só janela + horas exigidas, decidido à parte).
    # --------------------------------

    if tipo_horario == "LIVRE" or entrada_h is None:
        # Sem uma "entrada esperada" não há forma de ancorar o resto do
        # cálculo (turno noturno, janelas de procura de picagens, etc.).
        # Fica registado que o horário existe, mas sem avaliação de
        # atraso/falta por esta função — isso é tratado à parte para LIVRE.
        resultado["motivo_sem_avaliacao"] = "LIVRE_SEM_ENTRADA_FIXA"
        return resultado

    tem_almoco = inicio_almoco_h is not None and fim_almoco_h is not None

    # --------------------------------
    # 4. HORAS ESPERADAS (com correção para turnos noturnos)
    # --------------------------------

    entrada_esperada = datetime.combine(data_turno, entrada_h)
    saida_esperada = combinar_data_hora(data_turno, saida_h, entrada_h) if saida_h else None

    if tem_almoco:
        inicio_almoco_esperado = combinar_data_hora(data_turno, inicio_almoco_h, entrada_h)
        fim_almoco_esperado = combinar_data_hora(data_turno, fim_almoco_h, entrada_h)
    else:
        inicio_almoco_esperado = None
        fim_almoco_esperado = None

    # --------------------------------
    # 5. PICAGENS REAIS DESTE TURNO
    # --------------------------------
    # Janela generosa à volta da entrada esperada, em vez de filtrar por
    # DATE(data) = data_turno: cobre turnos noturnos (a saída cai no dia
    # civil seguinte) sem depender de nenhuma outra lógica auxiliar.

    janela_inicio = entrada_esperada - timedelta(hours=4)
    janela_fim = entrada_esperada + timedelta(hours=20)

    cursor.execute(
        """
        SELECT tipo, data
        FROM picagem
        WHERE id_funcionario = %s
          AND anulada = 0
          AND data BETWEEN %s AND %s
        ORDER BY data ASC
        """,
        (id_funcionario, janela_inicio, janela_fim)
    )

    for tipo, quando in cursor.fetchall():
        chave = tipo.lower()  # "entrada", "saida_almoco", "volta_almoco", "saida"
        if resultado["picagens"].get(chave) is None:
            resultado["picagens"][chave] = quando

    entrada_real = resultado["picagens"]["entrada"]
    saida_almoco_real = resultado["picagens"]["saida_almoco"]
    volta_almoco_real = resultado["picagens"]["volta_almoco"]
    saida_real = resultado["picagens"]["saida"]

    # --------------------------------
    # 6. FALTA
    # --------------------------------

    resultado["falta"] = entrada_real is None

    if entrada_real is None:
        # Sem nenhuma picagem, não há mais nada a calcular.
        return resultado

    # --------------------------------
    # 7. ATRASOS (entrada e volta do almoço são independentes)
    # --------------------------------

    def minutos_de_atraso(real, esperado, tolerancia_min):
        if real is None or esperado is None:
            return None
        diferenca_min = (real - esperado).total_seconds() / 60
        if diferenca_min <= tolerancia_min:
            return 0
        return round(diferenca_min - tolerancia_min)

    resultado["atraso_entrada_min"] = minutos_de_atraso(
        entrada_real, entrada_esperada, tolerancia or 0
    )

    if tem_almoco:
        resultado["atraso_volta_almoco_min"] = minutos_de_atraso(
            volta_almoco_real, fim_almoco_esperado, tolerancia or 0
        )

    # --------------------------------
    # 8. HORAS TRABALHADAS
    # --------------------------------

    if tem_almoco:
        if saida_almoco_real and volta_almoco_real and saida_real:
            periodo_manha = (saida_almoco_real - entrada_real).total_seconds()
            periodo_tarde = (saida_real - volta_almoco_real).total_seconds()
            resultado["horas_trabalhadas"] = round((periodo_manha + periodo_tarde) / 3600, 2)
    else:
        if saida_real:
            resultado["horas_trabalhadas"] = round(
                (saida_real - entrada_real).total_seconds() / 3600, 2
            )

    return resultado


def calcular_periodo(cursor, id_funcionario, data_inicio, data_fim):
    """
    Aplica calcular_dia a cada dia entre data_inicio e data_fim (inclusive),
    devolvendo uma lista de dicionários no formato:
        [{"data": date, **resultado_de_calcular_dia}, ...]

    Serve de base direta para relatórios por semana/mês — quem chamar esta
    função é que decide como agregar (somar atrasos, contar faltas, etc.).
    """

    resultados = []
    dia_atual = data_inicio

    while dia_atual <= data_fim:
        resumo = calcular_dia(cursor, id_funcionario, dia_atual)
        resumo["data"] = dia_atual
        resultados.append(resumo)
        dia_atual += timedelta(days=1)

    return resultados