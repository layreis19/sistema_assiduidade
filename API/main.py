from fastapi import FastAPI

app = FastAPI()

@app.get("/")

def home():
    
  return " API Assiduidade "

@app.get("/estado")

def estado():
    return {"status: ok!"}



