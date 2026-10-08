from datetime import datetime, timedelta
from ligacao import conn

def processar_dados_funcionario(data_inicio, data_fim):

    cursor = conn.cursor(dictionary=True) # recebemos os dados em dicionário + fácil para trabalhar com eles

    cursor.execute("""
        SELECT 
            id_funcionario,
            data_adesao,
            estado,
            horario 
        FROM FUNCIONARIOS
        """)

    funcionarios = cursor.fetchall() # guardo todos os dados nesta variável 
    
    for funcionario in funcionarios:

        id_funcionario = funcionario["id_funcionario"]
        data_adesao = funcionario["data_adesao"].date()
        estado = funcionario["estado"]

        # se o funcionário tiver inativo ignora
        if estado == "INATIVO":
            continue

        dia = data_inicio # está no relatórios nos calendários

        while dia <= data_fim: # está nos relatórios nos calendários

            # se o dia for anterior à data de adesão, ignora
            if dia < data_adesao: # se o dia for < que data de adesão 
                dia += timedelta(days=1) 
                continue


            # verificar ausências
            cursor.execute("""
            SELECT 
                tipo
            FROM AUSENCIAS
            WHERE id_funcionario = %s
            AND data_inicio <= %s
            AND data_fim >= %s
        """, (id_funcionario, dia, dia))

            ausencia = cursor.fetchone()

            if ausencia:

                cursor.execute("""
                    INSERT INTO RESULTADOS
                        (id_funcionario, data, tipo)
                    VALUES(%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                        tipo = VALUES(tipo)
                """, (id_funcionario, dia, ausencia["tipo"]))

                conn.commit()

                dia += timedelta(days=1)
                continue

            # verificar os feriados
            cursor.execute("""
            SELECT
                data, descricao
            FROM FERIADOS
            WHERE data = %s
            """, (dia, ))

            feriado = cursor.fetchone()

            if feriado:
                cursor.execute("""
                INSERT INTO RESULTADOS
                    (id_funcionario, data, tipo)
                VALUES(%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    tipo = VALUES(tipo)
            """, (id_funcionario, dia, "FERIADO"))

                conn.commit()

                dia += timedelta(days=1)
                continue

            # verificar folga

        

            folga = cursor.fetchone()

            if folga:
                cursor.execute("""
                INSERT INTO RESULTADOS
                    (id_funcionario, data, tipo)
                VALUES(%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    tipo = VALUES(tipo)
                """, (
                    id_funcionario,
                    dia,
                    "FOLGA"))

                conn.commit()

                dia += timedelta(days=1)
                continue

            # se o funcionário não tiver horário
            if funcionario["horario"] is None:

                cursor.execute("""
                INSERT INTO RESULTADOS
                    (id_funcionario, data, tipo)
                VALUES(%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    tipo = VALUES(tipo)
                """, (
                    id_funcionario,
                    dia,
                    "SEM_HORÁRIO"
                ))
                conn.commit()

                dia += timedelta(days=1)
                continue


    

    

            
           
