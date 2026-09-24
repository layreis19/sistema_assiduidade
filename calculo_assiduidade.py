# Pra que serve esse ficheiro?
# Este módulo calcula, para um funcionário e um dia (o dia a que um turno foi
# ATRIBUÍDO em FUNCIONARIO_HORARIO — não necessariamente a data civil das
# picagens, por causa de turnos noturnos que atravessam a meia-noite),
# se houve falta, atraso na entrada, atraso a voltar do almoço, horas extra
# e horas efetivamente trabalhadas. Também sabe gravar esse resultado na
# tabela RESULTADOS, para os relatórios lerem diretamente de lá em vez de
# recalcularem tudo a cada pedido.
#
# Não depende de tkinter nem de nenhuma página em concreto: recebe um cursor
# já aberto (buffered=True) e devolve um dicionário simples. Isto permite
# que tanto relatorios.py como ctrl_presencas.py e relogio_ponto.py (e
# testes soltos) usem a mesma lógica, sem duplicar queries nem regras de
# negócio.

from datetime import datetime, timedelta, time


def _para_time(valor):
    """
    O mysql-connector-python devolve colunas TIME como datetime.timedelta,
    não como datetime.time (porque um TIME em SQL pode ultrapassar as 24h,
    o que datetime.time não consegue representar). Como os horários deste
    sistema nunca passam das 24h, convertemos sempre timedelta -> time,
    para podermos usar datetime.combine() sem rebentar.
    """

    if valor is None:
        return None

    if isinstance(valor, timedelta):
        total_segundos = int(valor.total_seconds())
        horas, resto = divmod(total_segundos, 3600)
        minutos, segundos = divmod(resto, 60)
        return time(horas % 24, minutos, segundos)

    return valor  # já é um datetime.time (ou None)


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


def _resultado_vazio():
    return {
        "tipo_horario": None,
        "motivo_sem_avaliacao": None,
        "falta": None,
        "atraso_entrada_min": None,
        "atraso_volta_almoco_min": None,
        "horas_trabalhadas": None,
        "horas_extra_min": None,
        "picagens": {"entrada": None, "saida_almoco": None, "volta_almoco": None, "saida": None},
    }


def _calcular_fixo_ou_turno(cursor, id_funcionario, data_turno, resultado,
                             entrada_h, saida_h, inicio_almoco_h, fim_almoco_h, tolerancia):
    """
    Cálculo para FIXO/TURNO: horário com hora de entrada fixa, eventual
    pausa de almoço, e turno que pode atravessar a meia-noite.
    """

    tem_almoco = inicio_almoco_h is not None and fim_almoco_h is not None

    entrada_esperada = datetime.combine(data_turno, entrada_h)
    saida_esperada = combinar_data_hora(data_turno, saida_h, entrada_h) if saida_h else None

    if tem_almoco:
        inicio_almoco_esperado = combinar_data_hora(data_turno, inicio_almoco_h, entrada_h)
        fim_almoco_esperado = combinar_data_hora(data_turno, fim_almoco_h, entrada_h)
    else:
        inicio_almoco_esperado = None
        fim_almoco_esperado = None

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

    resultado["falta"] = entrada_real is None

    if entrada_real is None:
        # Sem nenhuma picagem, não há mais nada a calcular.
        return resultado

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

    # Horas trabalhadas
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

    # Horas extra: excesso face à duração esperada do turno (já descontado
    # o almoço, se aplicável). Só é possível calcular com o turno completo.
    if resultado["horas_trabalhadas"] is not None and saida_esperada is not None:
        duracao_esperada_min = (saida_esperada - entrada_esperada).total_seconds() / 60

        if tem_almoco:
            duracao_almoco_min = (fim_almoco_esperado - inicio_almoco_esperado).total_seconds() / 60
            duracao_esperada_min -= duracao_almoco_min

        excesso_min = round(resultado["horas_trabalhadas"] * 60 - duracao_esperada_min)
        resultado["horas_extra_min"] = max(0, excesso_min)

    return resultado


def _calcular_livre(cursor, id_funcionario, data_turno, resultado,
                     janela_inicio_h, janela_fim_h, horas_diarias_exigidas):
    """
    Cálculo para LIVRE: sem hora de entrada fixa, por isso não há "atraso"
    a medir (só interessa se cumpriu a janela e as horas exigidas). Um
    único par ENTRADA/SAIDA por dia (decisão já tomada no relógio de
    ponto), dentro do mesmo dia civil — horário livre não atravessa a
    meia-noite, ao contrário de TURNO.
    """

    cursor.execute(
        """
        SELECT tipo, data
        FROM picagem
        WHERE id_funcionario = %s
          AND anulada = 0
          AND DATE(data) = %s
          AND tipo IN ('ENTRADA', 'SAIDA')
        ORDER BY data ASC
        """,
        (id_funcionario, data_turno)
    )

    for tipo, quando in cursor.fetchall():
        chave = tipo.lower()
        if resultado["picagens"].get(chave) is None:
            resultado["picagens"][chave] = quando

    entrada_real = resultado["picagens"]["entrada"]
    saida_real = resultado["picagens"]["saida"]

    resultado["falta"] = entrada_real is None

    if entrada_real is None:
        return resultado

    # Sem hora de entrada fixa não há atraso a medir — fica sempre None
    # (não é 0, porque 0 significaria "avaliado e sem atraso"; None
    # significa "este conceito não se aplica a este tipo de horário").

    if saida_real:
        resultado["horas_trabalhadas"] = round(
            (saida_real - entrada_real).total_seconds() / 3600, 2
        )

        if horas_diarias_exigidas is not None:
            excesso_min = round(resultado["horas_trabalhadas"] * 60 - float(horas_diarias_exigidas) * 60)
            resultado["horas_extra_min"] = max(0, excesso_min)

    return resultado


def calcular_dia(cursor, id_funcionario, data_turno):
    """
    Calcula o resumo de assiduidade de um funcionário para o turno que lhe
    foi atribuído em `data_turno` (FUNCIONARIO_HORARIO.data).

    Devolve um dicionário:
    {
        "tipo_horario": "FIXO" / "TURNO" / "LIVRE" / "FOLGA" / None,
        "motivo_sem_avaliacao": None / "SEM_HORARIO" / "FOLGA" / "AUSENCIA" / "FERIADO",
        "falta": bool ou None (None = não avaliável, ver motivo_sem_avaliacao),
        "atraso_entrada_min": int ou None,
        "atraso_volta_almoco_min": int ou None,
        "horas_trabalhadas": float ou None (horas, arredondado a 2 casas),
        "horas_extra_min": int ou None,
        "picagens": {"entrada": ..., "saida_almoco": ..., "volta_almoco": ..., "saida": ...},
    }
    """

    resultado = _resultado_vazio()

    # --------------------------------
    # 1. HORÁRIO ATRIBUÍDO NESSE DIA
    # --------------------------------

    cursor.execute(
        """
        SELECT h.tipo, h.entrada, h.saida, h.inicio_almoco, h.fim_almoco,
               h.tolerancia, h.janela_inicio, h.janela_fim, h.horas_diarias_exigidas
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

    (tipo_horario, entrada_h, saida_h, inicio_almoco_h, fim_almoco_h,
     tolerancia, janela_inicio_h, janela_fim_h, horas_diarias_exigidas) = horario

    # Colunas TIME vêm da BD como timedelta — converter antes de usar.
    entrada_h = _para_time(entrada_h)
    saida_h = _para_time(saida_h)
    inicio_almoco_h = _para_time(inicio_almoco_h)
    fim_almoco_h = _para_time(fim_almoco_h)
    janela_inicio_h = _para_time(janela_inicio_h)
    janela_fim_h = _para_time(janela_fim_h)

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
    # 3. CÁLCULO ESPECÍFICO DO TIPO DE HORÁRIO
    # --------------------------------

    if tipo_horario == "LIVRE":
        return _calcular_livre(
            cursor, id_funcionario, data_turno, resultado,
            janela_inicio_h, janela_fim_h, horas_diarias_exigidas
        )

    if entrada_h is None:
        # FIXO/TURNO sem entrada definida não devia acontecer (erro de
        # configuração no catálogo HORARIO) — fica sinalizado em vez de
        # rebentar mais à frente com uma comparação a None.
        resultado["motivo_sem_avaliacao"] = "HORARIO_MAL_CONFIGURADO"
        return resultado

    return _calcular_fixo_ou_turno(
        cursor, id_funcionario, data_turno, resultado,
        entrada_h, saida_h, inicio_almoco_h, fim_almoco_h, tolerancia
    )


def calcular_periodo(cursor, id_funcionario, data_inicio, data_fim):
    """
    Aplica calcular_dia a cada dia entre data_inicio e data_fim (inclusive),
    devolvendo uma lista de dicionários no formato:
        [{"data": date, **resultado_de_calcular_dia}, ...]

    Serve de base direta para relatórios por semana/mês — quem chamar esta
    função é que decide como agregar (somar atrasos, contar faltas, etc.).
    Não grava nada em RESULTADOS; para isso, ver calcular_e_guardar_dia.
    """

    resultados = []
    dia_atual = data_inicio

    while dia_atual <= data_fim:
        resumo = calcular_dia(cursor, id_funcionario, dia_atual)
        resumo["data"] = dia_atual
        resultados.append(resumo)
        dia_atual += timedelta(days=1)

    return resultados


# ======================================================================
# GRAVAÇÃO EM RESULTADOS
# ======================================================================
#
# Só é gravada uma linha em RESULTADOS quando havia mesmo expectativa de
# trabalho nesse dia (FIXO/TURNO/LIVRE com horário atribuído). Dias de
# FOLGA, AUSENCIA, FERIADO ou sem horário atribuído não geram linha — a
# ausência de linha significa "não se esperava trabalho"; uma linha com
# total_minutos_trabalhados = 0 significa sempre uma falta real. Sem esta
# distinção, os dois casos ficariam indistinguíveis para quem lesse só a
# tabela RESULTADOS (que não tem nenhuma coluna de estado/motivo).

DIAS_SEM_EXPECTATIVA_DE_TRABALHO = ("SEM_HORARIO", "FOLGA", "AUSENCIA", "FERIADO", "HORARIO_MAL_CONFIGURADO")


def calcular_e_guardar_dia(cursor, conn, id_funcionario, data_turno):
    """
    Calcula o resumo do dia (calcular_dia) e grava/atualiza a linha
    correspondente em RESULTADOS. Usa ON DUPLICATE KEY UPDATE, apoiado na
    UNIQUE (id_funcionario, data) da tabela — chamar esta função várias
    vezes para o mesmo dia (ex: a cada picagem) simplesmente atualiza a
    mesma linha, sem criar duplicados.

    Devolve sempre o resumo (dicionário de calcular_dia), para quem chamar
    poder decidir se quer mostrar alguma mensagem, sem repetir o cálculo.
    Faz commit próprio, para poder ser chamada de forma independente de
    quem a invoca (ex: logo a seguir a uma picagem).
    """

    resumo = calcular_dia(cursor, id_funcionario, data_turno)

    if resumo["motivo_sem_avaliacao"] in DIAS_SEM_EXPECTATIVA_DE_TRABALHO:
        return resumo  # nada a gravar neste dia

    atraso_minutos = (resumo["atraso_entrada_min"] or 0) + (resumo["atraso_volta_almoco_min"] or 0)
    horas_extra_minutos = resumo["horas_extra_min"] or 0

    horas_trabalhadas = resumo["horas_trabalhadas"]
    total_minutos_trabalhados = round(horas_trabalhadas * 60) if horas_trabalhadas is not None else 0

    cursor.execute(
        """
        INSERT INTO resultados
            (id_funcionario, data, atraso_minutos, horas_extra_minutos, total_minutos_trabalhados)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            atraso_minutos = VALUES(atraso_minutos),
            horas_extra_minutos = VALUES(horas_extra_minutos),
            total_minutos_trabalhados = VALUES(total_minutos_trabalhados),
            calculado_em = CURRENT_TIMESTAMP
        """,
        (id_funcionario, data_turno, atraso_minutos, horas_extra_minutos, total_minutos_trabalhados)
    )

    conn.commit()

    return resumo


def calcular_e_guardar_periodo(cursor, conn, id_funcionario, data_inicio, data_fim):
    """
    Aplica calcular_e_guardar_dia a cada dia entre data_inicio e data_fim
    (inclusive). Útil para recalcular retroativamente (ex: depois de uma
    retificação de picagem pelo admin, ou para preencher RESULTADOS pela
    primeira vez com dias que já tinham picagens antes desta tabela existir).
    """

    resultados = []
    dia_atual = data_inicio

    while dia_atual <= data_fim:
        resumo = calcular_e_guardar_dia(cursor, conn, id_funcionario, dia_atual)
        resumo["data"] = dia_atual
        resultados.append(resumo)
        dia_atual += timedelta(days=1)

    return resultados