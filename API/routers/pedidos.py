from fastapi import APIRouter, HTTPException,Depends
from pydantic import BaseModel
from database import obter_ligacao
from datetime import date
from seguranca import funcionario_atual




router = APIRouter(prefix="/pedidos", tags= ["Pedidos de ferias"])

class pedidoIn(BaseModel):
    data_inicio: date
    data_fim: date
    

#ver meus pedidos
@router.get("/meus")
def meus_pedidos(id_func: int = Depends(funcionario_atual)):
    ligacao= obter_ligacao()
    
    try:
        cursor= ligacao.cursor(dictionary= True)
        cursor.execute(
            """ SELECT id, data_inicio, data_fim, estado, motivo_rejeicao
            FROM pedidos_ferias
            WHERE id_funcionario= %s
            ORDER BY data_inicio DESC
            """,
            (id_func,),    
        )
        return cursor.fetchall()
    
    finally:
        ligacao.close()

    
#criar um pedido   
@router.post("")
def criar_pedido(pedido: pedidoIn, id_func: int = Depends(funcionario_atual)):
    if pedido.data_fim < pedido.data_inicio:
        raise HTTPException(400,"A data de fim não pode ser anterior á de inicio.")
    
    if pedido.data_inicio < date.today():
        raise HTTPException(400, "Não pode pedir ferias em datas passadas.")
    
    ligacao = obter_ligacao()
    
    try:
        cursor = ligacao.cursor()
        #verifica se existe algum pedido deste funcionário, pendente ou aprovado, que colida com as datas novas
        cursor.execute(
        """ SELECT id FROM pedidos_ferias
        WHERE id_funcionario = %s
        AND estado IN ('PENDENTE', 'APROVADO')
        AND data_inicio <= %s AND data_fim >= %s
        LIMIT 1
        """,
        (id_func, pedido.data_fim, pedido.data_inicio),
        )
        
        if cursor.fetchone():
            raise HTTPException( 400, "Já tem um pedido para estas datas.")
        
         # verifica se existe ausencias para essas datas
        cursor.execute(
            """
            SELECT id FROM ausencias
            WHERE id_funcionario = %s
            AND estado <> 'CANCELADO'
            AND data_inicio <= %s
            AND data_fim >= %s
            LIMIT 1""",
            (id_func, pedido.data_fim, pedido.data_inicio),
              
        )
        if cursor.fetchone():
            raise HTTPException(400, "Já tem ausências marcadas nessas datas." )
        
        cursor.execute(
            #cria um novo pedido  de ferias
            """
            INSERT INTO pedidos_ferias (id_funcionario, data_inicio, data_fim)
            VALUES (%s,%s,%s) """,
            (id_func, pedido.data_inicio, pedido.data_fim),
        )
        
        ligacao.commit()
        return {"mensagem": "Pedido enviado.", "id": cursor.lastrowid}
    
    finally:
        ligacao.close()
        
        
        
    
#cancelar um pedido
@router.delete("/{id_pedido}")
def cancelar_pedido(id_pedido: int, id_func: int = Depends(funcionario_atual)):
    ligacao= obter_ligacao()
    
    try:
        cursor = ligacao.cursor()
        #mudar para o estado cancelado 
        cursor.execute(
            """ UPDATE pedidos_ferias SET estado = 'CANCELADO'
                WHERE id= %s
                AND id_funcionario = %s 
                AND estado = 'PENDENTE'
            """,
            (id_pedido,id_func)
        )
        ligacao.commit()
        if cursor.rowcount == 0:
            raise HTTPException(400, "Só é possivel cancelar pedidos pendentes seus")
        return {"mensagem": "Pedido cancelado."}
    
    finally:
        ligacao.close()
        

    