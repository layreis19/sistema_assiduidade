from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import obter_ligacao
from seguranca import token, senha_correta

router = APIRouter(prefix="/auth", tags= ["Autenticação"])

class LoginIn(BaseModel):
    
    id_funcionario : int 
    senha: str
    
    
@router.post("/login")
def login(dados: LoginIn):
    ligacao= obter_ligacao()
    try:
        cursor= ligacao.cursor(dictionary= True)
        cursor.execute(
            """ SELECT id_funcionario, nome, senha
            FROM funcionarios
            WHERE id_funcionario= %s
            AND estado = 'ATIVO'
            AND data_demissao IS NULL
            
            """,
            (dados.id_funcionario,)
        )
        func = cursor.fetchone()
    
    finally:
        
        ligacao.close()
     
     # se nao encontrar o funcionario ou senha errada    
    if not func or not senha_correta(dados.senha, func["senha"]):
        raise HTTPException(status_code= 401, detail= "Número ou senha incorretos.")
    return {"token": token(func["id_funcionario"]), "nome":func["nome"]}
        
        







