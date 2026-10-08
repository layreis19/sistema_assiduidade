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

        # se o funcionário tiver inativo ignora
        if funcionario["estado"] == "INATIVO":
            continue

        # se o funcionário não tiver horário ignora
        if funcionario["horario"] is None:
            continue

        data_adesao = funcionario["data_adesao"].date()

        print(data_adesao)

        dia = data_inicio # está no relatórios nos calendários

        while dia <= data_fim: # está nos relatórios nos calendários

            # se o dia for anterior à data de adesão, ignora
            if dia < data_adesao: # se o dia for < que data de adesão 
                dia += timedelta(days=1) 
                continue

            dia += timedelta(days=1)

processar_dados_funcionario()


