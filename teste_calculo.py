from datetime import date
from ligacao import conn
from calculo_assiduidade import calcular_dia

cursor = conn.cursor(buffered=True)
cursor.execute("""
    SELECT f.id_funcionario, f.nome, h.nome
    FROM funcionarios f LEFT JOIN horario h ON h.id_horario = f.horario
    ORDER BY 1
""")
for id_, nome, horario in cursor.fetchall():
    r = calcular_dia(cursor, id_, date.today())
    print(id_, nome, "|", horario, "->", r["tipo_horario"], r["motivo_sem_avaliacao"], r["falta"])