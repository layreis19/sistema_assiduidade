# Pra que serve esse ficheiro?
# Nomes "bonitos" a mostrar ao utilizador para cada tipo de picagem.
# Os valores internos na base de dados (ENTRADA, SAIDA_ALMOCO,
# VOLTA_ALMOCO, SAIDA) mantêm-se como estão — mudar isto exigiria uma
# migração à BD. Isto é só o texto mostrado nas mensagens/rótulos da
# interface, centralizado aqui para não haver um texto diferente em cada
# ficheiro que precise de mostrar o tipo de uma picagem.
#
# "Pausa" em vez de "Almoço": o mesmo turno pode ter uma pausa que não é
# almoço nenhum (ex: TURNO NOITE, onde a pausa cai a meio da madrugada).

ROTULO_TIPO_PICAGEM = {
    "ENTRADA": "Entrada",
    "SAIDA_ALMOCO": "Entrada Pausa",
    "VOLTA_ALMOCO": "Volta Pausa",
    "SAIDA": "Saída",
}


def rotulo_tipo_picagem(tipo):
    """
    Devolve o nome a mostrar para um tipo de picagem. Se for um tipo
    desconhecido (não devia acontecer, mas mais vale não rebentar),
    devolve o próprio valor tal como veio.
    """
    return ROTULO_TIPO_PICAGEM.get(tipo, tipo)