from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

@app.get("/")

def home():
    
  return " API Assiduidade "

@app.get("/estado")

def estado():
    return {"status: ok!"}
  
  
  
  

  



