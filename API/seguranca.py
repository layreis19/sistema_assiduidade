import os
import bcrypt
import jwt
from  fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime, timedelta, timezone
import database

 # 
CHAVE_SECRETA = os.getenv("JWT_CHAVE")
if not CHAVE_SECRETA:
    raise RuntimeError(
        "Falta a JWT_CHAVE no ficheiro .env "
        "Gera uma com: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
#validade token
HORAS_VALIDADE = 8

#diz ao FastAPI que o token vem no cabeçalho do pedido
esquema= HTTPBearer()

#recebe a senha escrita  e a senha da BD
def senha_correta(senha_escrita, senha_guardada):
    if not senha_guardada:
        return False
    return bcrypt.checkpw(senha_escrita.encode(), senha_guardada.encode())
    

# criar token id funcionario com validade de 8 horas 
# .UTC = hora atual em hora universal
#timedelta=  um intervalo de tempo 8h
def token(id_funcionario):
    expira = datetime.now(timezone.utc) + timedelta(hours = HORAS_VALIDADE)
    return jwt.encode(
        {"sub": str(id_funcionario), "exp": expira},
        CHAVE_SECRETA,
        algorithm="HS256"
    )
    
    
def funcionario_atual (credenciais:HTTPAuthorizationCredentials = Depends(esquema)):
    try:
        dados=jwt.decode(credenciais.credentials, CHAVE_SECRETA, algorithms= ["HS256"])
        return int(dados["sub"])
    except Exception:
        raise HTTPException(status_code= 401, detail="Sessão inválida ou expirada.")
    
    
    

    
    
    
    
