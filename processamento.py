
from datetime import date, datetime, timedelta

from ligacao import conn
from calculo_assiduidade import (
    carregar_horario,
    calcular_picagens,
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


def processar_dados_funcionario(data_inicio, data_fim):
    """
    Processa a assiduidade no intervalo indicado.

    O processamento decide quais os dias aplicáveis.
    O módulo calculo_assiduidade calcula e grava os dias de trabalho.
    Devolve um resumo para apresentar na interface.
    """

    if isinstance(data_inicio, datetime):
        data_inicio = data_inicio.date()
    if isinstance(data_fim, datetime):
        data_fim = data_fim.date()

    if not isinstance(data_inicio, date) or not isinstance(data_fim, date):
        raise ValueError("As datas devem ser objetos date ou datetime.")

    if data_inicio > data_fim:
        raise ValueError("A data inicial não pode ser posterior à final.")

    hoje = date.today()

    resumo = {
        "funcionarios": 0,
        "dias_analisados": 0,
        "resultados_gravados": 0,
        "faltas": 0,
        "ausencias": 0,
        "feriados": 0,
        "dias_sem_horario": 0,
        "dias_sem_trabalho": 0,
        "erros": [],
    }

    cursor = conn.cursor(dictionary=True, buffered=True)
    cursor_calculo = conn.cursor(buffered=True)

    try:
        cursor.execute(
            """
            SELECT id_funcionario, data_adesao, estado, horario
            FROM FUNCIONARIOS
            WHERE estado = 'ATIVO'
            """
        )
        funcionarios = cursor.fetchall()

        # Cache: cada horário só precisa de ser lido uma vez.
        horarios = {}

        for funcionario in funcionarios:
            id_funcionario = funcionario["id_funcionario"]
            adesao = funcionario["data_adesao"]
            data_adesao = (
                adesao.date() if isinstance(adesao, datetime) else adesao
            )

            resumo["funcionarios"] += 1

            dia = data_inicio

            while dia <= data_fim:
                # Não processar dias futuros.
                if dia > hoje:
                    dia += timedelta(days=1)
                    continue

                # O funcionário ainda não fazia parte do sistema.
                if dia < data_adesao:
                    dia += timedelta(days=1)
                    continue

                resumo["dias_analisados"] += 1

                try:
                    # 1. Ausências registadas.
                    cursor.execute(
                        """
                        SELECT tipo
                        FROM AUSENCIAS
                        WHERE id_funcionario = %s
                          AND data_inicio <= %s
                          AND data_fim >= %s
                        LIMIT 1
                        """,
                        (id_funcionario, dia, dia),
                    )
                    ausencia = cursor.fetchone()

                    if ausencia:
                        _guardar_estado(
                            cursor, id_funcionario, dia, ausencia["tipo"]
                        )
                        resumo["ausencias"] += 1
                        resumo["resultados_gravados"] += 1
                        dia += timedelta(days=1)
                        continue

                    # 2. Feriados.
                    cursor.execute(
                        "SELECT data FROM FERIADOS WHERE data = %s",
                        (dia,),
                    )
                    if cursor.fetchone():
                        _guardar_estado(
                            cursor, id_funcionario, dia, "FERIADO"
                        )
                        resumo["feriados"] += 1
                        resumo["resultados_gravados"] += 1
                        dia += timedelta(days=1)
                        continue

                    # 3. Horário atribuído.
                    id_horario = funcionario["horario"]

                    if id_horario is None:
                        _guardar_estado(
                            cursor, id_funcionario, dia, "SEM_HORÁRIO"
                        )
                        resumo["dias_sem_horario"] += 1
                        resumo["resultados_gravados"] += 1
                        dia += timedelta(days=1)
                        continue

                    if id_horario not in horarios:
                        horarios[id_horario] = carregar_horario(
                            cursor_calculo, id_horario
                        )

                    horario = horarios[id_horario]

                    if horario is None:
                        _guardar_estado(
                            cursor, id_funcionario, dia, "SEM_HORÁRIO"
                        )
                        resumo["dias_sem_horario"] += 1
                        resumo["resultados_gravados"] += 1
                        dia += timedelta(days=1)
                        continue

                    # 4. Verificar se era dia de trabalho.
                    dias_trabalho = horario.get("dias_trabalho") or ""
                    dias_trabalho = {
                        d.strip() for d in dias_trabalho.split(",") if d.strip()
                    }
                    dia_semana = DIAS_SEMANA[dia.weekday()]

                    if dia_semana not in dias_trabalho:
                        resumo["dias_sem_trabalho"] += 1
                        dia += timedelta(days=1)
                        continue

                    # 5. Calcular e guardar as picagens.
                    resultado = calcular_picagens(
                        cursor_calculo,
                        id_funcionario,
                        dia,
                        horario,
                    )

                    guardar_resultado(
                        cursor_calculo,
                        conn,
                        id_funcionario,
                        dia,
                        resultado,
                    )

                    resumo["resultados_gravados"] += 1

                    if resultado["falta"]:
                        resumo["faltas"] += 1

                except Exception as erro:
                    conn.rollback()
                    resumo["erros"].append(
                        f"Funcionário {id_funcionario}, "
                        f"{dia.strftime('%d/%m/%Y')}: {erro}"
                    )

                dia += timedelta(days=1)

        conn.commit()
        return resumo

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        cursor_calculo.close()
