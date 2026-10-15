# Pra que serve esse ficheiro?
# Percorre os funcionários e os dias de um intervalo e decide o que fica
# registado em RESULTADOS para cada dia: folga semanal (nada), ausência,
# feriado, sem horário, ou dia de trabalho (calculado por
# calculo_assiduidade.py, que compara as picagens com o horário).
#
# Regras importantes:
# - Só se processam dias que já terminaram (até ontem). Hoje ainda está a
#   decorrer: quem ainda não chegou ficaria registado como falta.
# - Antes de processar cada funcionário apagam-se os resultados antigos do
#   período e voltam a gerar-se. Assim, se o horário, as ausências ou as
#   picagens mudaram desde a última vez, nunca sobram linhas de regras
#   antigas.
# - Os dias em que a pessoa não trabalha (fora de HORARIO.dias_trabalho) não
#   geram linha nenhuma, mesmo que caiam dentro de umas férias ou num
#   feriado: férias e feriados contam-se em dias de trabalho.
# - Só contam ausências com estado CONFIRMADO.
# - No dia de adesão só entra se a pessoa picou (a data_adesao tem hora: quem
#   é criado à tarde não deve ter falta nessa manhã).
#
# Usa um único cursor com tuplos (é o que o calculo_assiduidade espera:
# com dictionary=True o desempacotamento das picagens parte-se sem avisar).

from datetime import date, datetime, timedelta

from ligacao import conn
from calculo_assiduidade import (
    carregar_horario,
    calcular_picagens,
    calcular_picagens_folga,
    guardar_resultado,
)


DIAS_SEMANA = {
    0: "SEG",
    1: "TER",
    2: "QUA",
    3: "QUI",
    4: "SEX",
    5: "SAB",
    6: "DOM",
}


def _para_date(valor):
    return valor.date() if isinstance(valor, datetime) else valor


def _normalizar_dias_trabalho(dias):
    """
    O driver devolve a coluna SET como set (ou como texto "SEG,TER").
    Devolve sempre um set de strings em maiúsculas.
    """
    if not dias:
        return set()

    if isinstance(dias, str):
        dias = dias.split(",")

    return {str(d).strip().upper() for d in dias if str(d).strip()}


def _guardar_estado(cursor, id_funcionario, dia, tipo):
    """Guarda um estado diário sem manter valores de cálculos antigos."""
    cursor.execute(
        """
        INSERT INTO RESULTADOS (
            id_funcionario, data, atraso_minutos,
            horas_extra_minutos, total_minutos_trabalhados, tipo
        )
        VALUES (%s, %s, 0, 0, 0, %s)
        ON DUPLICATE KEY UPDATE
            atraso_minutos = 0,
            horas_extra_minutos = 0,
            total_minutos_trabalhados = 0,
            tipo = VALUES(tipo),
            calculado_em = CURRENT_TIMESTAMP
        """,
        (id_funcionario, dia, tipo),
    )


def _processar_dia(cursor, id_funcionario, dia, e_dia_de_adesao,
                   horario, dias_trabalho, ausencias, feriados):
    """
    Decide o que acontece neste dia e grava o resultado.
    Devolve (contador_do_resumo, gravou_linha).
    """

    # 1. Folga semanal: verificar se houve trabalho efetivo.
    #    Sem picagens, grava FOLGA; com picagens, calcula o trabalho sem
    #    comparar com o horário normal desse dia.
    if horario is not None and DIAS_SEMANA[dia.weekday()] not in dias_trabalho:
        resultado_folga = calcular_picagens_folga(
            cursor, id_funcionario, dia
        )

        if not resultado_folga["periodos"]:
            _guardar_estado(cursor, id_funcionario, dia, "FOLGA")
            return "dias_sem_trabalho", True

        tipo_resultado = (
            "INCOMPLETO_FOLGA"
            if resultado_folga["horas_trabalhadas"] is None
            else "TRABALHO_FOLGA"
        )

        guardar_resultado(
            cursor, conn, id_funcionario, dia,
            resultado_folga,
            tipo_override=tipo_resultado
        )
        return "trabalho_em_folga", True

    # 2. Ausências confirmadas.
    for inicio, fim, tipo in ausencias:
        if inicio <= dia <= fim:
            _guardar_estado(cursor, id_funcionario, dia, tipo)
            return "ausencias", True

    # 3. Feriados.
    if dia in feriados:
        _guardar_estado(cursor, id_funcionario, dia, "FERIADO")
        return "feriados", True

    # 4. Sem horário atribuído.
    if horario is None:
        _guardar_estado(cursor, id_funcionario, dia, "SEM_HORÁRIO")
        return "dias_sem_horario", True

    # 5. Dia de trabalho: comparar as picagens com o horário.
    resultado = calcular_picagens(cursor, id_funcionario, dia, horario)

    if resultado["falta"] and e_dia_de_adesao:
        return None, False

    guardar_resultado(cursor, conn, id_funcionario, dia, resultado)

    return ("faltas" if resultado["falta"] else None), True


def processar_dados_funcionario(data_inicio, data_fim, ids_funcionarios=None):
    """
    Processa a assiduidade no intervalo indicado e devolve um resumo para
    apresentar na interface. Só processa dias até ontem.

    ids_funcionarios (opcional): lista de ids a processar. Sem ela, processa
    todos os funcionários ativos. Serve para recalcular só quem foi afetado
    por uma correção de picagens, em vez de reprocessar toda a gente.
    """

    data_inicio = _para_date(data_inicio)
    data_fim = _para_date(data_fim)

    if not isinstance(data_inicio, date) or not isinstance(data_fim, date):
        raise ValueError("As datas devem ser objetos date ou datetime.")

    if data_inicio > data_fim:
        raise ValueError("A data inicial não pode ser posterior à final.")

    # Hoje ainda não terminou: não se pode dizer que alguém faltou.
    ultimo_dia = min(data_fim, date.today() - timedelta(days=1))

    if data_inicio > ultimo_dia:
        raise ValueError(
            "Só é possível processar dias que já terminaram (até ontem)."
        )

    resumo = {
        "funcionarios": 0,
        "dias_analisados": 0,
        "resultados_gravados": 0,
        "faltas": 0,
        "ausencias": 0,
        "feriados": 0,
        "dias_sem_horario": 0,
        "dias_sem_trabalho": 0,
        "trabalho_em_folga": 0,
        "erros": [],
    }

    cursor = conn.cursor(buffered=True)

    try:
        if ids_funcionarios is None:
            cursor.execute(
                """
                SELECT id_funcionario, data_adesao, horario
                FROM FUNCIONARIOS
                WHERE estado = 'ATIVO'
                ORDER BY id_funcionario
                """
            )
            funcionarios = cursor.fetchall()

        else:
            ids = list(ids_funcionarios)

            if ids:
                # um %s por id (só marcadores: os valores vão como parâmetros)
                marcadores = ", ".join(["%s"] * len(ids))
                cursor.execute(
                    f"""
                    SELECT id_funcionario, data_adesao, horario
                    FROM FUNCIONARIOS
                    WHERE estado = 'ATIVO'
                      AND id_funcionario IN ({marcadores})
                    ORDER BY id_funcionario
                    """,
                    ids,
                )
                funcionarios = cursor.fetchall()
            else:
                funcionarios = []

        cursor.execute(
            "SELECT data FROM FERIADOS WHERE data BETWEEN %s AND %s",
            (data_inicio, ultimo_dia),
        )
        feriados = {linha[0] for linha in cursor.fetchall()}

        # Cache: cada horário só precisa de ser lido uma vez.
        horarios = {}

        for id_funcionario, adesao, id_horario in funcionarios:
            resumo["funcionarios"] += 1
            data_adesao = _para_date(adesao)

            horario = None
            if id_horario is not None:
                if id_horario not in horarios:
                    horarios[id_horario] = carregar_horario(cursor, id_horario)
                horario = horarios[id_horario]

            # Horário mal configurado: um único erro, em vez de um por dia.
            if (horario is not None
                    and horario["tipo"] in ("FIXO", "TURNO")
                    and horario["entrada"] is None):
                resumo["erros"].append(
                    f"Funcionário {id_funcionario}: o horário atribuído não "
                    "tem hora de entrada (verifique a tabela HORARIO)."
                )
                continue

            dias_trabalho = (
                _normalizar_dias_trabalho(horario["dias_trabalho"])
                if horario is not None else set()
            )

            # Apagar os resultados antigos do período e gerá-los de novo.
            cursor.execute(
                """
                DELETE FROM RESULTADOS
                WHERE id_funcionario = %s AND data BETWEEN %s AND %s
                """,
                (id_funcionario, data_inicio, ultimo_dia),
            )
            conn.commit()

            cursor.execute(
                """
                SELECT data_inicio, data_fim, tipo
                FROM AUSENCIAS
                WHERE id_funcionario = %s
                  AND estado = 'CONFIRMADO'
                  AND data_inicio <= %s
                  AND data_fim >= %s
                ORDER BY data_inicio
                """,
                (id_funcionario, ultimo_dia, data_inicio),
            )
            ausencias = cursor.fetchall()

            # Antes da adesão a pessoa ainda não fazia parte do sistema.
            dia = max(data_inicio, data_adesao)

            while dia <= ultimo_dia:
                resumo["dias_analisados"] += 1

                try:
                    contador, gravou = _processar_dia(
                        cursor, id_funcionario, dia, dia == data_adesao,
                        horario, dias_trabalho, ausencias, feriados,
                    )
                    # Um commit por dia: se um dia falhar, o rollback só
                    # desfaz esse dia e nunca os anteriores.
                    conn.commit()

                except Exception as erro:
                    conn.rollback()
                    resumo["erros"].append(
                        f"Funcionário {id_funcionario}, "
                        f"{dia.strftime('%d/%m/%Y')}: {erro}"
                    )

                else:
                    if contador:
                        resumo[contador] += 1
                    if gravou:
                        resumo["resultados_gravados"] += 1

                dia += timedelta(days=1)

        return resumo

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()