# Pra que serve esse ficheiro?
# Este módulo faz UMA coisa: comparar as picagens de um funcionário, num
# dia, com o horário que ele devia cumprir, e dizer se houve falta, atraso
# na entrada, atraso a voltar do almoço, horas extra e horas trabalhadas.
#
# O que NÃO faz (é responsabilidade de quem o chama, o processamento):
# - decidir se o dia conta: funcionário inativo, antes da data de adesão,
#   sem horário, FOLGA, ausência justificada, feriado, dia ainda por
#   acontecer, dia de descanso...
# - percorrer funcionários ou intervalos de datas.
# Isto só deve ser chamado para dias em que havia mesmo expectativa de
# trabalho.
#
# Como funciona com o esquema atual:
# - A tabela PICAGEM só tem ENTRADA e SAIDA genéricas. Aqui emparelham-se
#   em "períodos de trabalho" (ENTRADA -> SAIDA seguinte); as pausas são
#   os intervalos entre períodos.
#
# Uso típico (no processamento):
#     horario = carregar_horario(cursor, id_horario_do_funcionario)
#     resumo  = calcular_picagens(cursor, id_funcionario, dia, horario)
#     guardar_resultado(cursor, conn, id_funcionario, dia, resumo)
#
# Não depende de tkinter nem de nenhuma página: recebe um cursor normal
# (buffered=True, que devolve tuplos — NÃO usar dictionary=True) e devolve
# um dicionário simples.

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
        "falta": None,
        "atraso_entrada_min": None,
        "atraso_volta_almoco_min": None,
        "horas_trabalhadas": None,
        "horas_extra_min": None,
        "periodos": [],
    }


def _ler_periodos(cursor, id_funcionario, janela_inicio, janela_fim):
    """
    Lê as picagens válidas entre janela_inicio e janela_fim e emparelha-as
    em períodos de trabalho: cada ENTRADA abre um período e a SAIDA seguinte
    fecha-o.

    Devolve uma lista de tuplos (entrada, saida) por ordem cronológica.
    `saida` é None quando o período ficou em aberto (só pode acontecer no
    último).

    Regras para picagens fora do padrão (podem vir de correções do admin):
    - ENTRADA quando já há um período em aberto: ignorada.
    - SAIDA quando não há período em aberto: ignorada.
    """

    cursor.execute(
        """
        SELECT tipo, data
        FROM picagem
        WHERE id_funcionario = %s
          AND anulada = 0
          AND data BETWEEN %s AND %s
        ORDER BY data ASC, id_picagem ASC
        """,
        (id_funcionario, janela_inicio, janela_fim)
    )

    periodos = []

    for tipo, quando in cursor.fetchall():
        em_aberto = bool(periodos) and periodos[-1][1] is None

        if tipo == "ENTRADA" and not em_aberto:
            periodos.append([quando, None])
        elif tipo == "SAIDA" and em_aberto:
            periodos[-1][1] = quando

    return [tuple(p) for p in periodos]


def _horas_dos_periodos(periodos):
    """
    Soma das horas de todos os períodos (as pausas ficam de fora, porque
    são o intervalo entre períodos). Devolve None se não houver períodos
    ou se algum não tiver SAIDA: dia incompleto, não dá para calcular.
    """

    if not periodos or any(saida is None for _, saida in periodos):
        return None

    total_segundos = sum((saida - entrada).total_seconds() for entrada, saida in periodos)

    return round(total_segundos / 3600, 2)


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

    periodos = _ler_periodos(cursor, id_funcionario, janela_inicio, janela_fim)
    resultado["periodos"] = periodos

    resultado["falta"] = not periodos

    if not periodos:
        # Sem nenhuma picagem, não há mais nada a calcular.
        return resultado

    entrada_real = periodos[0][0]  # a primeira ENTRADA do dia

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

    # Pausa de almoço: as pausas são os intervalos entre períodos
    # (SAIDA de um, ENTRADA do seguinte). Se houver mais do que uma
    # (ex: almoço e um café), a do almoço é a que começou mais perto da
    # hora de início de almoço esperada.
    houve_pausa = False

    if tem_almoco:
        pausas = [
            (periodos[i][1], periodos[i + 1][0])
            for i in range(len(periodos) - 1)
        ]

        if pausas:
            houve_pausa = True

            _, volta_almoco_real = min(
                pausas,
                key=lambda p: abs((p[0] - inicio_almoco_esperado).total_seconds())
            )

            resultado["atraso_volta_almoco_min"] = minutos_de_atraso(
                volta_almoco_real, fim_almoco_esperado, tolerancia or 0
            )

    # Horas trabalhadas: soma dos períodos (a pausa fica de fora sozinha).
    resultado["horas_trabalhadas"] = _horas_dos_periodos(periodos)

    # Horas extra: excesso face à duração esperada do turno. O almoço só
    # é descontado à duração esperada se houve uma pausa registada; se o
    # funcionário não picou o almoço, o dia é um único período contínuo e
    # compara-se com o turno inteiro (senão a hora de almoço apareceria
    # como hora extra). Só é possível calcular com o turno completo.
    if resultado["horas_trabalhadas"] is not None and saida_esperada is not None:
        duracao_esperada_min = (saida_esperada - entrada_esperada).total_seconds() / 60

        if houve_pausa:
            duracao_almoco_min = (fim_almoco_esperado - inicio_almoco_esperado).total_seconds() / 60
            duracao_esperada_min -= duracao_almoco_min

        excesso_min = round(resultado["horas_trabalhadas"] * 60 - duracao_esperada_min)
        resultado["horas_extra_min"] = max(0, excesso_min)

    return resultado


def _calcular_livre(cursor, id_funcionario, data_turno, resultado,
                     janela_inicio_h, janela_fim_h, horas_diarias_exigidas):
    """
    Cálculo para LIVRE: sem hora de entrada fixa, por isso não há "atraso"
    a medir (só interessa se cumpriu as horas exigidas). As horas são a
    soma dos períodos ENTRADA/SAIDA do dia (as pausas ficam de fora), dentro
    do mesmo dia civil — horário livre não atravessa a meia-noite, ao
    contrário de TURNO.
    """

    inicio_dia = datetime.combine(data_turno, time.min)
    fim_dia = datetime.combine(data_turno, time(23, 59, 59))

    periodos = _ler_periodos(cursor, id_funcionario, inicio_dia, fim_dia)
    resultado["periodos"] = periodos

    resultado["falta"] = not periodos

    if not periodos:
        return resultado

    # Sem hora de entrada fixa não há atraso a medir — fica sempre None
    # (não é 0, porque 0 significaria "avaliado e sem atraso"; None
    # significa "este conceito não se aplica a este tipo de horário").

    resultado["horas_trabalhadas"] = _horas_dos_periodos(periodos)

    if resultado["horas_trabalhadas"] is not None and horas_diarias_exigidas is not None:
        excesso_min = round(resultado["horas_trabalhadas"] * 60 - float(horas_diarias_exigidas) * 60)
        resultado["horas_extra_min"] = max(0, excesso_min)

    return resultado


# ======================================================================
# API PÚBLICA
# ======================================================================

def carregar_horario(cursor, id_horario):
    """
    Lê um horário da tabela HORARIO e devolve-o como dicionário (com as
    colunas TIME já convertidas para datetime.time), pronto a passar a
    calcular_picagens. Devolve None se o id não existir.

    Há poucos horários no catálogo: se o processamento chamar isto para
    muitos funcionários, pode guardar o resultado num dicionário
    {id_horario: horario} e só ler cada um uma vez.
    """

    cursor.execute(
        """
        SELECT tipo, entrada, saida, inicio_almoco, fim_almoco,
               tolerancia, janela_inicio, janela_fim, horas_diarias_exigidas, dias_trabalho
        FROM horario
        WHERE id_horario = %s
        """,
        (id_horario,)
    )

    linha = cursor.fetchone()

    if linha is None:
        return None

    (tipo, entrada_h, saida_h, inicio_almoco_h, fim_almoco_h,
     tolerancia, janela_inicio_h, janela_fim_h, horas_diarias_exigidas, dias_trabalho) = linha

    # Colunas TIME vêm da BD como timedelta — converter antes de usar.
    return {
        "tipo": tipo,
        "entrada": _para_time(entrada_h),
        "saida": _para_time(saida_h),
        "inicio_almoco": _para_time(inicio_almoco_h),
        "fim_almoco": _para_time(fim_almoco_h),
        "tolerancia": tolerancia or 0,
        "janela_inicio": _para_time(janela_inicio_h),
        "janela_fim": _para_time(janela_fim_h),
        "horas_diarias_exigidas": horas_diarias_exigidas,
        "dias_trabalho": dias_trabalho,
    }


def calcular_picagens(cursor, id_funcionario, data_turno, horario):
    """
    Compara as picagens do funcionário no turno que começou em `data_turno`
    com o `horario` (dicionário de carregar_horario).

    Devolve um dicionário:
    {
        "falta": bool (True = não picou nada nesse turno),
        "atraso_entrada_min": int ou None,
        "atraso_volta_almoco_min": int ou None,
        "horas_trabalhadas": float ou None (horas, 2 casas; None se algum
                             período ficou sem SAIDA ou não há picagens),
        "horas_extra_min": int ou None,
        "periodos": [(entrada, saida), ...]  (saida = None se ficou em aberto),
    }

    Levanta ValueError se o horário não tiver nada que se possa comparar
    com picagens: tipo FOLGA, ou FIXO/TURNO sem hora de entrada (erro no
    catálogo HORARIO). Quem chama deve ter tratado a FOLGA antes.
    """

    resultado = _resultado_vazio()

    tipo = horario["tipo"]

    if tipo == "FOLGA":
        raise ValueError("calcular_picagens não se aplica a horários FOLGA: trate a folga antes de chamar.")

    if tipo == "LIVRE":
        return _calcular_livre(
            cursor, id_funcionario, data_turno, resultado,
            horario["janela_inicio"], horario["janela_fim"], horario["horas_diarias_exigidas"]
        )

    if horario["entrada"] is None:
        raise ValueError(f"Horário {tipo} sem hora de entrada: verifique a tabela HORARIO.")

    return _calcular_fixo_ou_turno(
        cursor, id_funcionario, data_turno, resultado,
        horario["entrada"], horario["saida"],
        horario["inicio_almoco"], horario["fim_almoco"], horario["tolerancia"]
    )


def guardar_resultado(cursor, conn, id_funcionario, data_turno, resumo):
    """Insere ou atualiza o resultado diário de assiduidade."""

    atraso_minutos = (
        (resumo["atraso_entrada_min"] or 0)
        + (resumo["atraso_volta_almoco_min"] or 0)
    )

    horas_extra_minutos = resumo["horas_extra_min"] or 0

    horas_trabalhadas = resumo["horas_trabalhadas"]
    total_minutos_trabalhados = (
        round(horas_trabalhadas * 60)
        if horas_trabalhadas is not None
        else 0
    )

    # Distinguir uma falta de um dia com picagens incompletas.
    if resumo["falta"]:
        tipo = "FALTA"
    elif resumo["periodos"] and horas_trabalhadas is None:
        tipo = "INCOMPLETO"
    else:
        tipo = "NORMAL"

    cursor.execute(
        """
        INSERT INTO RESULTADOS (
            id_funcionario,
            data,
            atraso_minutos,
            horas_extra_minutos,
            total_minutos_trabalhados,
            tipo
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            atraso_minutos = VALUES(atraso_minutos),
            horas_extra_minutos = VALUES(horas_extra_minutos),
            total_minutos_trabalhados = VALUES(total_minutos_trabalhados),
            tipo = VALUES(tipo),
            calculado_em = CURRENT_TIMESTAMP
        """,
        (
            id_funcionario,
            data_turno,
            atraso_minutos,
            horas_extra_minutos,
            total_minutos_trabalhados,
            tipo,
        ),
    )

    conn.commit()
