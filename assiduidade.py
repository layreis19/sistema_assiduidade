import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox





conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="reis2016",
    database="ASSIDUIDADE"
)

cursor = conn.cursor()

print("Ligação bem sucedida!")

janela = tk.Tk()
janela.title("Gestão de Assiduidade")
janela.geometry("800x800")



janela.mainloop()