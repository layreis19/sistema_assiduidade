from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth
from routers import pedidos


app = FastAPI( title="API Assiduidade")

#ROTAS
app.include_router(auth.router)
app.include_router(pedidos.router)


@app.get("/ola")
def ola():
    
  return  {"mensagem": " Olá! API Assiduidade está a funcionar."}

@app.get("/estado")

def estado():
    return {"status: ok!"}
  
  
  
  

  



